from flask import Blueprint, request, render_template, redirect, url_for

from db.connect import query
from services.db_service import write_sentence_pairs
from services.annotation_service import delete_unlabeled_row

annotate_bp = Blueprint('annotate', __name__)

@annotate_bp.route('/annotate', methods=['GET', 'POST'])
def annotate():
    if request.method == 'POST':
        id_ = request.form['_id']
        original = request.form['original']
        simplified = request.form['simplified']
        annotation = request.form['annotation']
        
        if annotation == 'yes':
            print('Yes')
            pairs = [{'original': original, 'simple': simplified}]
            write_sentence_pairs(pairs, labeled=True)
        elif annotation == 'no':
            rewritten = request.form['rewrite']
            print(rewritten)
            pairs = [{'original': original, 'simple': rewritten}]
            write_sentence_pairs(pairs, labeled=True)
        
        delete_unlabeled_row(id_)
        return redirect(url_for('annotate.annotate'))

    unlabeled_data = query()
    
    if not unlabeled_data: 
        return "No more data to annotate."
    
    pair = unlabeled_data[0]
    original = pair['original']
    simplified = pair['simplified']
    id_ = pair['id']
    
    return render_template('annotate.html', original=original, simplified=simplified, id_=id_)

@annotate_bp.route('/reset')
def reset():
    return redirect(url_for('annotate.annotate'))