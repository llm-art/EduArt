#!/usr/bin/env python3
"""
Answer Viewer Web Application
Displays questions and answers from the datasets/answers directory
"""

from flask import Flask, render_template, jsonify, send_from_directory
import json
import os
from pathlib import Path

app = Flask(__name__)

# Base paths
BASE_DIR = Path(__file__).parent.parent  # Go up to main datasets directory
ANSWERS_DIR = BASE_DIR / "answers"
METADATA_DIR = BASE_DIR / "dataset" / "metadata"
IMAGES_DIR = BASE_DIR / "dataset" / "imgs"


def get_models():
    """Get list of model directories from answers folder"""
    if not ANSWERS_DIR.exists():
        return []
    
    models = []
    for item in ANSWERS_DIR.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            models.append(item.name)
    
    return sorted(models)


def get_questions(model_name):
    """Get list of question files for a specific model"""
    model_dir = ANSWERS_DIR / model_name
    if not model_dir.exists():
        return []
    
    questions = []
    for item in model_dir.iterdir():
        if item.is_file() and item.suffix == '.json':
            questions.append(item.stem)
    
    return sorted(questions)


def load_question_data(model_name, question_id):
    """Load and merge question data from metadata and answer files"""
    # Load question metadata
    metadata_path = METADATA_DIR / f"{question_id}.json"
    answer_path = ANSWERS_DIR / model_name / f"{question_id}.json"
    
    result = {
        "question_id": question_id,
        "question_data": {},
        "evaluation": {},
        "ai_calls": []
    }
    
    # Load question metadata (has question text, choices, image info)
    if metadata_path.exists():
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                
                # Check if image file exists
                image_filename = f"{question_id}.jpg"
                image_file = IMAGES_DIR / image_filename
                has_image = image_file.exists()
                
                result["question_data"] = {
                    "question_text": metadata.get("question_text", ""),
                    "question_title": metadata.get("question_title", ""),
                    "question_type": metadata.get("type", ""),
                    "has_image": has_image,
                    "image_path": image_filename if has_image else None,
                    "correct_answers": metadata.get("answers", []),
                    "choices": metadata.get("choices", []),
                    "language": metadata.get("language", "")
                }
        except Exception as e:
            result["error"] = f"Failed to load metadata: {str(e)}"
    
    # Load answer/evaluation data
    if answer_path.exists():
        try:
            with open(answer_path, 'r', encoding='utf-8') as f:
                answer_data = json.load(f)
                result["evaluation"] = answer_data.get("evaluation", {})
                result["ai_calls"] = answer_data.get("ai_calls", [])
        except Exception as e:
            result["error"] = f"Failed to load answer: {str(e)}"
    
    return result if (metadata_path.exists() or answer_path.exists()) else None


@app.route('/')
def index():
    """Main viewer page"""
    return render_template('viewer.html')


@app.route('/api/models')
def api_models():
    """API endpoint to get list of models"""
    return jsonify(get_models())


@app.route('/api/questions/<model_name>')
def api_questions(model_name):
    """API endpoint to get list of questions for a model"""
    questions = get_questions(model_name)
    return jsonify(questions)


@app.route('/api/question/<model_name>/<question_id>')
def api_question(model_name, question_id):
    """API endpoint to get question data"""
    data = load_question_data(model_name, question_id)
    if data is None:
        return jsonify({"error": "Question not found"}), 404
    return jsonify(data)


@app.route('/images/<path:filename>')
def serve_image(filename):
    """Serve images from the dataset/imgs directory"""
    return send_from_directory(IMAGES_DIR, filename)


if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    templates_dir = BASE_DIR / 'website' / 'templates'
    templates_dir.mkdir(exist_ok=True)
    
    print(f"Starting Answer Viewer...")
    print(f"Answers directory: {ANSWERS_DIR}")
    print(f"Available models: {get_models()}")
    print(f"Access the viewer at: http://localhost:5001")
    
    app.run(debug=True, host='0.0.0.0', port=5001)