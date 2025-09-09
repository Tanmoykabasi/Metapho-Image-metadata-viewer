import os
import exifread
from flask import Flask, request, render_template, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'photo' not in request.files:
        return jsonify({'error': 'No photo part'})

    photo = request.files['photo']

    if photo.filename == '':
        return jsonify({'error': 'No selected photo'})

    if photo:
        tags = exifread.process_file(photo)
        metadata = {}
        for tag, value in tags.items():
            if tag not in ('JPEGThumbnail', 'TIFFThumbnail'):
                metadata[tag] = str(value)

        return jsonify(metadata)

if __name__ == '__main__':
    app.run(debug=True)
