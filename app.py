from flask import Flask, render_template, request, redirect, url_for, send_from_directory, make_response
import os
import json
from werkzeug.utils import secure_filename
from google.cloud import storage
from google.oauth2 import service_account

app = Flask(__name__, static_folder='static', static_url_path='/static')

# Configure upload settings
ALLOWED_EXTENSIONS = {'pdf', 'epub'}
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB limit

# GCS Configuration
BUCKET_NAME = "readio-storage"  # Replace with your actual bucket name
credentials_json = os.getenv('GOOGLE_CREDENTIALS')

if credentials_json:
    credentials_dict = json.loads(credentials_json)
    credentials = service_account.Credentials.from_service_account_info(credentials_dict)
    storage_client = storage.Client(credentials=credentials)
else:
    storage_client = storage.Client()

bucket = storage_client.bucket(BUCKET_NAME)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        blob = bucket.blob(filename)
        blob.upload_from_string(
            file.read(),
            content_type=file.content_type
        )
        # Remove blob.make_public() since we're using uniform access
        return redirect(url_for('read_book', filename=filename))

@app.route('/read/<filename>')
def read_book(filename):
    return render_template('reader.html', filename=filename)

@app.route('/get-pdf/<filename>')
def get_pdf(filename):
    try:
        blob = bucket.blob(filename)
        pdf_content = blob.download_as_bytes()
        response = make_response(pdf_content)
        response.headers['Content-Type'] = 'application/pdf'
        return response
    except Exception as e:
        print(f"Error accessing file: {e}")
        return f"Error accessing file: {str(e)}", 500

@app.route('/uploads/<filename>')
def serve_file(filename):
    try:
        blob = bucket.blob(filename)
        url = blob.public_url
        return redirect(url)
    except Exception as e:
        print(f"Error serving file: {e}")
        return f"Error serving file: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)
