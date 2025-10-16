#!/usr/bin/env python3
"""
Dataset Bundler Script

This script reads JSON files from output/{exercise_number}/json/ directories,
extracts question data to create TXT files, copies JSON files to metadata/, 
and copies associated images to imgs/ folder with consistent naming.
"""

import os
import json
import glob
import shutil
import re
from datetime import datetime
from pathlib import Path


def find_json_files(base_path="output"):
    """Find all JSON files in output/{exercise_number}/json/ directories."""
    json_files = []
    
    # Check if we're in the questions directory or parent directory
    if os.path.exists("questions/output"):
        base_path = "questions/output"
    elif os.path.exists("output"):
        base_path = "output"
    else:
        print(f"Warning: Neither 'output' nor 'questions/output' directory found")
        return []
    
    pattern = os.path.join(base_path, "*/json/*.json")
    
    for json_file in glob.glob(pattern):
        json_files.append(json_file)
    
    # Sort numerically by exercise number and question number
    def sort_key(filepath):
        # Extract exercise and question numbers from path like "output/1/json/5.json"
        parts = filepath.split(os.sep)
        exercise_num = int(parts[-3])  # exercise number
        question_num = int(os.path.splitext(parts[-1])[0])  # question number
        return (exercise_num, question_num)
    
    return sorted(json_files, key=sort_key)


def find_associated_image(json_file):
    """Find associated image file for a JSON file."""
    # Extract exercise number and question number from JSON file path
    # e.g., output/1/json/5.json -> exercise 1, question 5
    path_parts = json_file.split(os.sep)
    exercise_num = path_parts[-3]  # exercise number
    question_num = os.path.splitext(path_parts[-1])[0]  # question number without .json
    
    # Look for images in data/{exercise_num}/raw/ and data/{exercise_num}/imgs/
    image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.bmp']
    
    # Determine the correct data path
    data_base = "data"
    if os.path.exists("questions/data"):
        data_base = "questions/data"
    
    # Check imgs folder first (processed images)
    imgs_folder = os.path.join(data_base, exercise_num, "imgs")
    if os.path.exists(imgs_folder):
        for ext in image_extensions:
            image_path = os.path.join(imgs_folder, f"{question_num}{ext}")
            if os.path.exists(image_path):
                return image_path
    
    # Check raw folder as fallback
    raw_folder = os.path.join(data_base, exercise_num, "raw")
    if os.path.exists(raw_folder):
        for ext in image_extensions:
            image_path = os.path.join(raw_folder, f"{question_num}{ext}")
            if os.path.exists(image_path):
                return image_path
    
    return None


def extract_question_data(json_data):
    """Extract question title, text, choices, and type from JSON data."""
    question_title = json_data.get("question_title", "")
    question_text = json_data.get("question_text", "")
    question_type = json_data.get("type", "")
    choices = json_data.get("choices", [])
    
    # Handle different choice formats
    formatted_choices = []
    if choices is None:
        # No choices available
        pass
    elif isinstance(choices, list) and len(choices) > 0:
        if isinstance(choices[0], dict):
            # Check if it's the standard format with "text" field
            if "text" in choices[0]:
                # Format: [{"id": "A", "text": "...", "is_correct": ...}, ...]
                for choice in choices:
                    if isinstance(choice, dict):
                        choice_id = choice.get("id", "")
                        choice_text = choice.get("text", "")
                        if choice_id and choice_text:
                            formatted_choices.append(f"{choice_id}. {choice_text}")
            elif "options" in choices[0]:
                # Format: [{"id": "BLANK_1", "options": ["option1", "option2"]}, ...]
                for choice in choices:
                    if isinstance(choice, dict):
                        choice_id = choice.get("id", "")
                        options = choice.get("options", [])
                        if choice_id and options:
                            formatted_choices.append(f"{choice_id}:")
                            for i, option in enumerate(options, 1):
                                formatted_choices.append(f"  {i}. {option}")
        elif isinstance(choices[0], str):
            # Format: ["option1", "option2", ...]
            for i, choice_text in enumerate(choices, 1):
                if choice_text:
                    formatted_choices.append(f"{i}. {choice_text}")
    
    return question_title, question_text, formatted_choices, question_type


def get_question_type_text(question_type):
    """Get the instruction text based on question type."""
    type_texts = {
        "multiple_choice_radio": "SCELTA MULTIPLA\n**Cosa devi fare:** scegli l'unica risposta esatta tra quelle proposte",
        "multiple_choice_check": "SCELTA MULTIPLA\n**Cosa devi fare:** scegli tutte le risposte esatta tra quelle proposte",
        "true_false": "VERO O FALSO\n**Cosa devi fare:** vero o falso? Scegli la risposta esatta",
        "completion_open": "COMPLETAMENTO APERTO\n**Cosa devi fare**: completa l'esercizio con le risposte che ti sembrano esatte",
        "positioning": "POSIZIONAMENTO\n**Cosa devi fare**: completa le parti mancanti dell'esercizio con le alternative proposte",
        "completion_closed": "COMPLETAMENTO CHIUSO\n**Cosa devi fare**: scegli la risposta esatta per ogni gruppo di opzioni proposte",
        "select_errors": "TROVA ERRORE\n**Cosa devi fare**: seleziona le parti di testo che ritieni sbagliate. Controlla il contatore per verificare di aver selezionato il numero giusto di errori"
    }
    return type_texts.get(question_type, "")


def create_txt_content(question_title, question_text, choices, question_type=""):
    """Create the content for the TXT file."""
    content = []
    
    if question_title:
        content.append(f"Title: {question_title}")
        content.append("")
    
    # Add question type instructions
    type_text = get_question_type_text(question_type)
    if type_text:
        content.append(type_text)
        content.append("")
    
    if question_text:
        content.append(f"Question: {question_text}")
        content.append("")
    
    if choices:
        content.append("Choices:")
        for choice in choices:
            content.append(choice)
    
    return "\n".join(content)


def get_next_file_id(data_dir):
    """Get the next available 4-digit file identifier."""
    existing_files = glob.glob(os.path.join(data_dir, "*.txt"))
    
    if not existing_files:
        return "0001"
    
    # Extract numbers from existing files
    numbers = []
    for file_path in existing_files:
        filename = os.path.basename(file_path)
        if filename.endswith(".txt") and len(filename) == 8:  # XXXX.txt
            try:
                num = int(filename[:4])
                numbers.append(num)
            except ValueError:
                continue
    
    if numbers:
        next_num = max(numbers) + 1
    else:
        next_num = 1
    
    return f"{next_num:04d}"


def update_metadata(metadata_file, processed_files, start_time, end_time):
    """Create or update the metadata file."""
    metadata = {
        "last_updated": end_time.isoformat(),
        "processing_sessions": []
    }
    
    # Load existing metadata if file exists
    if os.path.exists(metadata_file):
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            pass
    
    # Add new processing session
    session = {
        "timestamp": start_time.isoformat(),
        "duration_seconds": (end_time - start_time).total_seconds(),
        "files_processed": len(processed_files),
        "source_files": processed_files
    }
    
    metadata["processing_sessions"].append(session)
    metadata["last_updated"] = end_time.isoformat()
    
    # Count total files in data directory
    data_dir = os.path.join(os.path.dirname(metadata_file), "..", "data")
    metadata["total_files"] = len(glob.glob(os.path.join(data_dir, "*.txt")))
    
    # Write updated metadata
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)


def main():
    """Main function to process all JSON files and create dataset."""
    start_time = datetime.now()
    
    # Create dataset directory structure
    dataset_dir = "dataset"
    data_dir = os.path.join(dataset_dir, "data")
    metadata_dir = os.path.join(dataset_dir, "metadata")
    imgs_dir = os.path.join(dataset_dir, "imgs")
    
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(metadata_dir, exist_ok=True)
    os.makedirs(imgs_dir, exist_ok=True)
    
    # Find all JSON files
    json_files = find_json_files()
    
    if not json_files:
        print("No JSON files found in output/*/json/ directories")
        return
    
    print(f"Found {len(json_files)} JSON files to process")
    
    processed_files = []
    
    for json_file in json_files:
        try:
            # Read JSON file
            with open(json_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # Get next file identifier
            file_id = get_next_file_id(data_dir)
            
            # Extract question data
            question_title, question_text, choices, question_type = extract_question_data(json_data)
            
            # Create TXT file content
            txt_content = create_txt_content(question_title, question_text, choices, question_type)
            
            # Write TXT file to data/ folder
            txt_filename = f"{file_id}.txt"
            txt_path = os.path.join(data_dir, txt_filename)
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(txt_content)
            
            # Copy JSON file to metadata/ folder
            json_filename = f"{file_id}.json"
            json_path = os.path.join(metadata_dir, json_filename)
            shutil.copy2(json_file, json_path)
            
            # Look for and copy associated image
            image_file = find_associated_image(json_file)
            if image_file:
                # Get image extension
                _, ext = os.path.splitext(image_file)
                image_filename = f"{file_id}{ext}"
                image_path = os.path.join(imgs_dir, image_filename)
                shutil.copy2(image_file, image_path)
                print(f"Processed: {json_file} -> {file_id}.txt, {file_id}.json, {file_id}{ext}")
            else:
                print(f"Processed: {json_file} -> {file_id}.txt, {file_id}.json (no image)")
            
            processed_files.append(json_file)
            
        except Exception as e:
            print(f"Error processing {json_file}: {str(e)}")
            continue
    
    end_time = datetime.now()
    
    # Update metadata
    metadata_file = os.path.join(metadata_dir, "processing_metadata.json")
    update_metadata(metadata_file, processed_files, start_time, end_time)
    
    print(f"\nProcessing complete!")
    print(f"Processed {len(processed_files)} files")
    print(f"Output directories:")
    print(f"  - Text files: {data_dir}")
    print(f"  - JSON metadata: {metadata_dir}")
    print(f"  - Images: {imgs_dir}")
    print(f"Duration: {(end_time - start_time).total_seconds():.2f} seconds")


if __name__ == "__main__":
    main()