from flask import Blueprint, request, render_template, redirect, url_for, session

from db.connect import query
from services.db_service import write_sentence_pairs
from services.annotation_service import delete_unlabeled_row

annotate_bp = Blueprint('annotate', __name__)

@annotate_bp.route('/annotate', methods=['GET', 'POST'])
def annotate():
    if 'skipped_ids' not in session:
        session['skipped_ids'] = []

    if request.method == 'POST':
        annotation = request.form.get('annotation')
        if not annotation:
            return redirect(url_for('annotate.annotate'))

        id_ = request.form['_id']
        original = request.form['original']
        simplified = request.form['simplified']
        
        if annotation == 'yes' or annotation == 'no':
            pairs = [{'original': original, 'simple': simplified}] if annotation == 'yes' else [{'original': original, 'simple': request.form['rewrite']}]
            write_sentence_pairs(pairs, labeled=True)
            delete_unlabeled_row(id_)
        elif annotation == 'skip':
            session['skipped_ids'].append(str(id_))
            session.modified = True  
        
        return redirect(url_for('annotate.annotate'))

    unlabeled_data = query()
    rendered_data = [pair for pair in unlabeled_data if str(pair['id']) not in session['skipped_ids']]
    
    if not rendered_data:
        return "No more data to annotate."
    
    pair = rendered_data[0]
    return render_template('annotate.html', original=pair['original'], simplified=pair['simplified'], id_=pair['id'])

@annotate_bp.route('/reset')
def reset():
    session.pop('skipped_ids', None)
    return redirect(url_for('annotate.annotate'))