#!/usr/bin/env python3
"""
AP Art History Question Viewer Web Application

Displays AP Art History questions, artwork images, and answers from structured JSON files.
"""

from flask import Flask, render_template, jsonify, send_from_directory
import json
from pathlib import Path

app = Flask(__name__)

# Base paths
BASE_DIR = Path(__file__).parent.parent  # ap_art_history directory
STRUCTURED_DIR = BASE_DIR / "structured"


def get_exercises():
    """Get list of exercise years from structured folder"""
    if not STRUCTURED_DIR.exists():
        return []
    
    exercises = []
    for item in STRUCTURED_DIR.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            exercises.append(item.name)
    
    return sorted(exercises)


def get_pages(exercise):
    """Get list of page files for a specific exercise"""
    json_dir = STRUCTURED_DIR / exercise / "json"
    if not json_dir.exists():
        return []
    
    pages = []
    for item in json_dir.iterdir():
        if item.is_file() and item.suffix == '.json':
            try:
                page_num = int(item.stem)
                pages.append(page_num)
            except ValueError:
                pass  # Skip non-numeric filenames
    
    return sorted(pages)


def load_page_data(exercise, page_num):
    """Load page data with all questions"""
    json_path = STRUCTURED_DIR / exercise / "json" / f"{page_num}.json"
    
    if not json_path.exists():
        return None
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            page_data = json.load(f)
        
        # Check if artwork image exists
        artwork_image = page_data.get('artwork_image', '')
        if artwork_image:
            # Images are in structured/{exercise}/imgs/
            artwork_path = STRUCTURED_DIR / exercise / artwork_image
            page_data['has_artwork'] = artwork_path.exists()
            page_data['artwork_url'] = f"/artwork/{exercise}/{Path(artwork_image).name}"
        else:
            page_data['has_artwork'] = False
            page_data['artwork_url'] = None
        
        # Process each question to add metadata
        for question in page_data.get('questions', []):
            # Format choices for display
            if question.get('choices'):
                for choice in question['choices']:
                    # Check if this choice is the correct answer
                    answers = question.get('answers', [])
                    if answers:
                        correct_id = answers[0].get('id', '')
                        choice['is_correct'] = (choice.get('id') == correct_id)
                    else:
                        choice['is_correct'] = False
        
        return page_data
        
    except Exception as e:
        return {"error": f"Failed to load page data: {str(e)}"}


@app.route('/')
def index():
    """Main viewer page"""
    return render_template('viewer.html')


@app.route('/api/exercises')
def api_exercises():
    """API endpoint to get list of exercises"""
    return jsonify(get_exercises())


@app.route('/api/pages/<exercise>')
def api_pages(exercise):
    """API endpoint to get list of pages for an exercise"""
    pages = get_pages(exercise)
    return jsonify(pages)


@app.route('/api/page/<exercise>/<int:page_num>')
def api_page(exercise, page_num):
    """API endpoint to get page data with all questions"""
    data = load_page_data(exercise, page_num)
    if data is None:
        return jsonify({"error": "Page not found"}), 404
    return jsonify(data)


@app.route('/api/question/<exercise>/<int:page_num>/<int:question_num>')
def api_question(exercise, page_num, question_num):
    """API endpoint to get a specific question from a page"""
    page_data = load_page_data(exercise, page_num)
    if page_data is None:
        return jsonify({"error": "Page not found"}), 404
    
    # Find the specific question
    for question in page_data.get('questions', []):
        if question.get('question') == question_num:
            # Include page-level data with the question
            return jsonify({
                'page': page_num,
                'exercise': exercise,
                'artwork_image': page_data.get('artwork_image', ''),
                'artwork_url': page_data.get('artwork_url'),
                'has_artwork': page_data.get('has_artwork', False),
                'image_reference': page_data.get('image_references', ''),
                'question': question
            })
    
    return jsonify({"error": "Question not found"}), 404


@app.route('/artwork/<exercise>/<path:filename>')
def serve_artwork(exercise, filename):
    """Serve artwork images from the structured/{exercise}/imgs directory"""
    imgs_dir = STRUCTURED_DIR / exercise / "imgs"
    return send_from_directory(imgs_dir, filename)


if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    templates_dir = Path(__file__).parent / 'templates'
    templates_dir.mkdir(exist_ok=True)
    
    print(f"Starting AP Art History Question Viewer...")
    print(f"Structured directory: {STRUCTURED_DIR}")
    print(f"Available exercises: {get_exercises()}")
    print(f"Access the viewer at: http://localhost:5002")
    
    app.run(debug=True, host='0.0.0.0', port=5002)
