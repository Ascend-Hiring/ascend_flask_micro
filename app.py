import os
import tempfile

from flask import Flask, request, jsonify
from pdfminer.high_level import extract_text
from docx import Document

app = Flask(__name__)

def parse_pdf(file_path):
    text = extract_text(file_path)
    return text

def parse_docx(file_path):
    document = Document(file_path)
    full_text = []
    for paragraph in document.paragraphs:
        full_text.append(paragraph.text)
    return '\n'.join(full_text)

@app.route('/parse', methods=['POST'])
def parse_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    

    file = request.files['file']
    file_contents = file.read()
    file_name = file.filename

    with tempfile.NamedTemporaryFile(delete=False) as temp_file:  
        temp_file.write(file_contents)
        temp_filepath = temp_file.name

    try:
        if file_name.endswith('.pdf'):
            text = parse_pdf(temp_filepath)
        elif file_name.endswith('.docx'):
            text = parse_docx(temp_filepath)
        else:
            return jsonify({'error': 'Unsupported file type'}), 400

        return jsonify({'text': text})
    finally:
        os.unlink(temp_filepath)

if __name__ == '__main__':
    app.run(debug=True) 
