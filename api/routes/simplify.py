from flask import Blueprint, request, render_template, jsonify
from services.simplification_service import simplify_sentence
from services.db_service import write_sentence_pairs

simplify_bp = Blueprint('simplify', __name__)

@simplify_bp.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        complex_sentence = request.form['complex_sentence']
        print(f"Received complex sentence: {complex_sentence}")
        if complex_sentence:
            simplified_sentence = simplify_sentence(complex_sentence)
            sentence_pair = {'original': complex_sentence, 'simple': simplified_sentence}
            write_sentence_pairs([sentence_pair], labeled=False)
            return render_template('index.html', complex_sentence=complex_sentence, simplified_sentence=simplified_sentence)

    return render_template('index.html')

@simplify_bp.route('/api/simplify', methods=['POST'])
def api_simplify():
    data = request.json
    complex_sentence = data.get('complex_sentence')
    print(f"Received API request with sentence: {complex_sentence}")
    if not complex_sentence:
        return jsonify({"error": "No complex sentence provided"}), 400

    simplified_sentence = simplify_sentence(complex_sentence)
    sentence_pair = {'original': complex_sentence, 'simple': simplified_sentence}
    write_sentence_pairs([sentence_pair], labeled=False)
    return jsonify({"complex_sentence": complex_sentence, "simplified_sentence": simplified_sentence})