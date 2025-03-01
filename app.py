import os
import random
import string
import sqlite3
from flask import Flask, request, jsonify, render_template, send_file

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
DATABASE = 'file_sharing.db'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Database initialization (if not exists)
def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS file_sharing (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT,
                    filename TEXT,
                    latitude REAL,
                    longitude REAL)''')
    conn.commit()
    conn.close()

init_db()

# Function to generate unique code
def generate_unique_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

# Landing page
@app.route('/')
def index():
    return render_template('index.html')

# Route for sending files
@app.route('/send', methods=['POST', 'GET'])
def send_file():
    if request.method == 'POST':
        file = request.files['file']
        latitude = float(request.form['latitude'])
        longitude = float(request.form['longitude'])

        if file:
            # Save the file
            filename = file.filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Generate a unique code for the file
            code = generate_unique_code()

            # Store file details in the database
            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()
            c.execute('INSERT INTO file_sharing (code, filename, latitude, longitude) VALUES (?, ?, ?, ?)', 
                      (code, filename, latitude, longitude))
            conn.commit()
            conn.close()

            # Return the unique code to the sender
            return render_template('send.html', code=code)

    return render_template('send.html')

# Route for receiving files
@app.route('/receive', methods=['POST', 'GET'])
def receive_file():
    if request.method == 'POST':
        code = request.form['code']

        try:
            # Database lookup for the code
            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()
            c.execute('SELECT * FROM file_sharing WHERE code=?', (code,))
            file_entry = c.fetchone()
            conn.close()

            if not file_entry:
                print(f"Error: Code {code} not found in the database.")
                return jsonify({'error': 'Invalid or expired code.'}), 404

            filename = file_entry[2]  # File name from the database
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            # Check if the file exists
            if not os.path.exists(file_path):
                print(f"Error: File {filename} not found in {file_path}.")
                return jsonify({'error': 'File not found on the server.'}), 404

            # Send the file for download
            return send_file(
                file_path,
                download_name=filename,  # Set the filename for the downloaded file
                as_attachment=True  # Specify it should be downloaded
            )

        except Exception as e:
            print(f"Unhandled Exception: {str(e)}")
            return jsonify({'error': 'Internal server error occurred.'}), 500

    return render_template('receive.html')

if __name__ == '__main__':
    app.run(debug=True)
