import os
import logging
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, current_app
from hashlib import sha256
from datetime import datetime

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Set up logging
logging.basicConfig(level=logging.INFO)

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

blockchain = []


class PatientRecord:
    def __init__(self, name, uid, age, evidence_path):
        self.timestamp = datetime.now()
        self.name = name
        self.uid = uid
        self.age = age
        self.evidence_path = evidence_path
        self.previous_hash = self.calculate_previous_hash()
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        hash_data = str(self.timestamp) + self.name + str(self.uid) + str(self.age) + self.evidence_path
        return sha256(hash_data.encode()).hexdigest()

    def calculate_previous_hash(self):
        if len(blockchain) > 0:
            previous_record = blockchain[-1]
            return previous_record.hash
        else:
            return None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/add_record', methods=['GET', 'POST'])
def add_record():
    if request.method == 'POST':
        name = request.form['name']
        uid = request.form['uid']
        age = request.form['age']

        # Save the uploaded evidence file
        evidence_file = request.files['evidence']
        evidence_path = os.path.join(app.config['UPLOAD_FOLDER'], evidence_file.filename)
        evidence_file.save(evidence_path)

        # Create and add a new record to the blockchain
        new_record = PatientRecord(name, uid, age, evidence_path)
        blockchain.append(new_record)

        return redirect(url_for('index'))

    return render_template('add_record.html')


@app.route('/blockchain')
def display_blockchain():
    return render_template('blockchain.html', blockchain=blockchain)


@app.route('/record/<uid>')
def view_record(uid):
    record = next((r for r in blockchain if r.uid == uid), None)
    if record:
        return render_template('view_record.html', record=record)
    else:
        return 'Record not found', 404


@app.route('/download/<uid>')
def download_file(uid):
    # Find the record with the given UID
    record = next((r for r in blockchain if r.uid == uid), None)

    if record:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], os.path.basename(record.evidence_path))

        # Log the file path to check if it is correct
        current_app.logger.info(f"Downloading file: {file_path}")

        if os.path.exists(file_path):
            return send_from_directory(current_app.config['UPLOAD_FOLDER'], os.path.basename(record.evidence_path),
                                       as_attachment=True)
        else:
            current_app.logger.error(f"File not found: {file_path}")
            return 'File not found', 404
    else:
        current_app.logger.error(f"No record found for UID: {uid}")
        return 'File not found', 404


if __name__ == '__main__':
    app.run(debug=True)
