# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
#

from collections import defaultdict
from functools import lru_cache
import shutil, json

from nevergrad.instrumentation import Instrumentation
from nevergrad.optimization import optimizerlib
import re

from access.evaluation.general import evaluate_simplifier_on_turkcorpus
from access.evaluation.utils import combine_metrics
from access.fairseq.base import (fairseq_preprocess, fairseq_train, fairseq_generate, get_fairseq_exp_dir,
                                 )
from access.resources.datasets import has_lines_in_common
from access.preprocessors import get_preprocessors, get_preprocessor_by_name
from access.resources.datasets import create_preprocessed_dataset
from access.resources.paths import get_data_filepath, get_dataset_dir
from access.simplifiers import get_fairseq_simplifier, get_preprocessed_simplifier
from access.utils.training import (print_method_name, print_args, print_result, print_running_time,
                                   )
from access.utils.helpers import get_allowed_kwargs

from access.resources.paths import BEST_MODEL_DIR
from pathlib import Path

import mlflow 

def check_dataset(dataset):
    # Sanity check with evaluation dataset
    assert not has_lines_in_common(get_data_filepath(dataset, 'train', 'complex'),
                                   get_data_filepath('turkcorpus', 'valid', 'complex'))
    assert not has_lines_in_common(get_data_filepath(dataset, 'train', 'complex'),
                                   get_data_filepath('turkcorpus', 'test', 'complex'))


def prepare_exp_dir():
    exp_dir = get_fairseq_exp_dir()
    print(f"Preparing experiment directory: {exp_dir}")
    if exp_dir.exists():
        print(f"Removing existing experiment directory: {exp_dir}")
        shutil.rmtree(exp_dir)
    exp_dir.mkdir(parents=True)
    # Path to existing dictionaries
    dict_dir = BEST_MODEL_DIR
    print(f"Copying dictionary files from {dict_dir} to {exp_dir}")
    if dict_dir.exists():
        shutil.copy(dict_dir / 'dict.complex.txt', exp_dir)
        shutil.copy(dict_dir / 'dict.simple.txt', exp_dir)
    return exp_dir


def get_simplifier(exp_dir, preprocessors_kwargs, generate_kwargs):
    # TODO: Take kwargs as input and separate between get_preprocessors kwargs and generate_kwargs
    preprocessors = get_preprocessors(preprocessors_kwargs)
    simplifier = get_fairseq_simplifier(exp_dir, **generate_kwargs)
    return get_preprocessed_simplifier(simplifier, preprocessors=preprocessors)


def find_best_parametrization(exp_dir, metrics_coefs, preprocessors_kwargs, parametrization_budget=64):
    @lru_cache()
    def evaluate_parametrization(**instru_kwargs):
        # Note that we use default generate kwargs instead of provided one because they are faster
        preprocessors_kwargs = instru_kwargs_to_preprocessors_kwargs(instru_kwargs)
        simplifier = get_simplifier(exp_dir, preprocessors_kwargs=preprocessors_kwargs, generate_kwargs={})
        scores = evaluate_simplifier_on_turkcorpus(simplifier, phase='valid')
        print(scores)
        return combine_metrics(scores['bleu'], scores['sari_legacy'], scores['fkgl'], metrics_coefs)

    def preprocessors_kwargs_to_instru_kwargs(preprocessors_kwargs):
        instru_kwargs = {}
        for preprocessor_name, preprocessor_kwargs in preprocessors_kwargs.items():
            assert '_' not in preprocessor_name
            preprocessor = get_preprocessor_by_name(preprocessor_name)(**preprocessor_kwargs)
            # First we set the values from preprocessors_kwargs which are constant
            for kwarg_name, kwarg_value in preprocessor_kwargs.items():
                instru_kwargs[f'{preprocessor_name}_{kwarg_name}'] = kwarg_value
            # Then we overwrite some of these values with nevergrad variables when necessary
            for kwarg_name, kwarg_value in preprocessor.get_nevergrad_variables().items():
                instru_kwargs[f'{preprocessor_name}_{kwarg_name}'] = kwarg_value
        return instru_kwargs

    def instru_kwargs_to_preprocessors_kwargs(instru_kwargs):
        preprocessors_kwargs = defaultdict(dict)
        for key, value in instru_kwargs.items():
            preprocessor_name, kwarg_name = re.match(r'([a-zA-Z0-9]+)_([a-z0-9_]+)', key).groups()
            preprocessors_kwargs[preprocessor_name][kwarg_name] = value
        return dict(preprocessors_kwargs)

    instru_kwargs = preprocessors_kwargs_to_instru_kwargs(preprocessors_kwargs)
    instru = Instrumentation(**instru_kwargs)
    if instru.dimension == 0:
        return preprocessors_kwargs
    # No need to search a lot when there is only a few parameters
    parametrization_budget = min(32**instru.dimension, parametrization_budget)
    optimizer = optimizerlib.ScrHammersleySearch(instrumentation=instru, budget=parametrization_budget, num_workers=1)
    recommendation = optimizer.optimize(evaluate_parametrization, verbosity=0)
    return instru_kwargs_to_preprocessors_kwargs(recommendation.kwargs)


def check_and_resolve_args(kwargs):
    if kwargs.get('diverse_beam_groups_ratio', None) is not None:
        diverse_beam_groups = max(int(kwargs['beam'] * kwargs['diverse_beam_groups_ratio']), 1)
        print(f'diverse_beam_groups={diverse_beam_groups}')
        assert kwargs['beam'] % diverse_beam_groups == 0
        kwargs['diverse_beam_groups'] = diverse_beam_groups
    else:
        diverse_beam_groups = None
    return kwargs


@print_method_name
@print_args
@print_result
@print_running_time
def fairseq_train_and_evaluate(dataset, metrics_coefs=[1, 1, 1], parametrization_budget=64, **kwargs):
    print("Starting MLFlow run...")

    # MLFlow: set tracking URI and experiment
    mlflow.set_tracking_uri("http://34.118.112.8:3003")
    mlflow.set_experiment("fairseq_access")
    
    with mlflow.start_run():
        check_dataset(dataset)
        kwargs = check_and_resolve_args(kwargs)
        exp_dir = prepare_exp_dir()        
        preprocessors_kwargs = kwargs.get('preprocessors_kwargs', {})
        preprocessors = get_preprocessors(preprocessors_kwargs)
        if len(preprocessors) > 0:
            dataset = create_preprocessed_dataset(dataset, preprocessors, n_jobs=1)
            shutil.copy(get_dataset_dir(dataset) / 'preprocessors.pickle', exp_dir)
        preprocessed_dir = fairseq_preprocess(dataset)
        train_kwargs = get_allowed_kwargs(fairseq_train, preprocessed_dir, exp_dir, **kwargs)

        # MLFlow: log dictionaries and preprocessors
        mlflow.log_artifact(exp_dir)

        fairseq_train(preprocessed_dir, exp_dir=exp_dir, **train_kwargs)
        # Evaluation
        generate_kwargs = get_allowed_kwargs(fairseq_generate, 'complex_filepath', 'pred_filepath', exp_dir, **kwargs)
        # recommended_preprocessors_kwargs = find_best_parametrization(exp_dir, metrics_coefs, preprocessors_kwargs,
        #                                                             parametrization_budget)
        # print(f'recommended_preprocessors_kwargs={recommended_preprocessors_kwargs}')
        simplifier = get_simplifier(exp_dir, preprocessors_kwargs, generate_kwargs)
        scores = evaluate_simplifier_on_turkcorpus(simplifier, phase='valid')
        print(f'scores={scores}')
        score = combine_metrics(scores['bleu'], scores['sari_legacy'], scores['fkgl'], metrics_coefs)
        return score