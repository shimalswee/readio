from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
import os
from werkzeug.utils import secure_filename
import PyPDF2
import pdfplumber
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

# Configure upload settings
UPLOAD_FOLDER = '/tmp/uploads'  # Changed for Vercel
ALLOWED_EXTENSIONS = {'pdf', 'epub'}
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB limit

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file_path):
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Error extracting text: {e}")
        text = ""
    return text

@app.route('/')
def index():
    return render_template('index.html')

# Keep only this one upload route
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            # Create uploads directory if it doesn't exist
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            # Extract text from PDF and store it
            text_content = extract_text_from_pdf(file_path)
            return redirect(url_for('read_book', filename=filename))
        except Exception as e:
            print(f"Upload error: {e}")
            return "Error uploading file", 500

@app.route('/read/<filename>')
def read_book(filename):
    return render_template('reader.html', filename=filename)

@app.route('/get_text/<filename>')
def get_text(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    text_content = extract_text_from_pdf(file_path)
    return jsonify({'text': text_content})

# For Vercel deployment
app = app

if __name__ == '__main__':
    app.run(debug=True)
