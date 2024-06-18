import os
import tempfile

from flask import Flask, request, jsonify, make_response
from pdfminer.high_level import extract_text
from docx import Document
import hubspot
from pprint import pprint
from hubspot.crm.companies import SimplePublicObjectInputForCreate, ApiException

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

@app.route('/')
def index():
    return jsonify({'message': 'Hello, World!'})

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

        return jsonify({'text': text}), 200
    finally:
        os.unlink(temp_filepath)

@app.route('/new-lead', methods=['POST', 'OPTIONS'])
def new_lead():
    if request.method == "OPTIONS": # CORS preflight
        return _build_cors_preflight_response()
    elif request.method != "POST":
        return _corsify_actual_response(jsonify({'error': 'Invalid request method {}'.format(request.method)})), 405
    
    client = hubspot.Client.create(access_token=os.environ.get('HS_ACCESS_TOKEN'))

    data = request.json
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    email = data.get('email')
    company_name = data.get('company_name')
    company_size = data.get('company_size')
    source = data.get('source')
    message = data.get('message')

    if not first_name or not last_name or not email or not company_name or not company_size or not source:
        return _corsify_actual_response(jsonify({'error': 'Missing required fields'})), 400

    contact_properties = {
        "firstname": first_name,
        "lastname": last_name,
        "email": email,
        "numemployees": company_size,
        "company": company_name,
        "hs_lead_status": "NEW",
        "source_url": source,
        "message": message
    }

    contactObject = SimplePublicObjectInputForCreate(
        properties=contact_properties,
    )
    try:
        response = client.crm.contacts.basic_api.create(
            simple_public_object_input_for_create=contactObject
        )
        pprint(response)
    except ApiException as e:
        return jsonify({'error': e}), 400
    
    return _corsify_actual_response(jsonify({'message': 'Lead created successfully'})), 200

def _build_cors_preflight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add('Access-Control-Allow-Headers', "*")
    response.headers.add('Access-Control-Allow-Methods', "*")
    return response

def _corsify_actual_response(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

if __name__ == '__main__':
    app.run(debug=True) 
