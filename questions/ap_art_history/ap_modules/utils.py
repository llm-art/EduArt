"""
Utility Functions for AP Art History Question Processing

This module provides utility functions for:
- Answer key parsing and loading
- HTML content loading
- Directory setup and management
- Question post-processing
"""

from pathlib import Path
from typing import Dict, List
import re


def parse_answer_key(answer_text: str) -> Dict[int, str]:
    """
    Parse the answer key from text like:
    '1-C, 2-B, 3-A, 4-B, 5-C, 6-D, 7-C, 8-A, 9-C, 10-A, ...'
    
    Args:
        answer_text: Text containing answer key in "question-answer" format
        
    Returns:
        Dictionary mapping question number to answer letter
    """
    answers = {}
    # Match patterns like "1-C" or "1 - C"
    pattern = r'(\d+)\s*-\s*([A-D])'
    matches = re.findall(pattern, answer_text)
    
    for match in matches:
        question_num = int(match[0])
        answer_letter = match[1]
        answers[question_num] = answer_letter
    
    return answers


def extract_answer_key_from_pdf(pdf_path: Path) -> str:
    """
    Extract answer key from PDF.
    
    Looks for patterns like "Answers—Section I, Part A" followed by
    "1-C, 2-B, 3-A, 4-B, 5-C, 6-D, 7-C, 8-A, 9-C, 10-A, ..."
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Answer key string in format "1-C, 2-B, 3-A, ..."
    """
    from ap_modules.pdf_service import PDFService
    
    pdf_service = PDFService()
    doc = pdf_service.fitz.open(pdf_path)
    
    answer_key = None
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        
        # Look for answer section header
        if "Answers" in text and "Section I" in text:
            print(f"  Found answer section on page {page_num + 1}")
            
            # Extract answer pattern: "1-C, 2-B, 3-A, ..."
            # Look for patterns like "1-C" or "1-A"
            pattern = r'(\d+\s*-\s*[A-D](?:\s*,\s*)?)'
            matches = re.findall(pattern, text)
            
            if matches:
                # Join all matches and clean up
                answer_key = ''.join(matches)
                answer_key = answer_key.strip().rstrip(',')
                print(f"  Extracted {len(matches)} answers from PDF")
                break
    
    doc.close()
    
    if not answer_key:
        print("  ⚠️  Could not find answer key in PDF")
        return ""
    
    return answer_key


def load_answer_key(raw_path: Path, exercise: str) -> Dict[int, str]:
    """
    Load answer key from a text file or extract from PDF if missing.
    
    Expected file: raw/{exercise}/answers.txt
    Format: "1-C, 2-B, 3-A, 4-B, ..."
    
    If answers.txt doesn't exist, automatically extracts from PDF.
    
    Args:
        raw_path: Path to raw data directory
        exercise: Exercise identifier (e.g., "2010")
        
    Returns:
        Dictionary mapping question number to answer letter
    """
    answer_file = raw_path / exercise / "answers.txt"
    
    # Try to load existing answers.txt
    if answer_file.exists():
        with open(answer_file, 'r', encoding='utf-8') as f:
            answer_text = f.read()
        
        answers = parse_answer_key(answer_text)
        print(f"✓ Loaded {len(answers)} answers from answer key file")
        return answers
    
    # If answers.txt doesn't exist, try to extract from PDF
    print(f"⚠️  Answer key file not found: {answer_file}")
    print("Attempting to extract answer key from PDF...")
    
    pdf_dir = raw_path / exercise / "pdf"
    pdf_files = list(pdf_dir.glob("*.pdf")) if pdf_dir.exists() else []
    
    if not pdf_files:
        print("  ❌ No PDF found for answer extraction")
        print("Questions will be created without correct answers.")
        return {}
    
    pdf_path = pdf_files[0]
    
    try:
        # Extract answer key from PDF
        answer_text = extract_answer_key_from_pdf(pdf_path)
        
        if not answer_text:
            print("  ❌ Failed to extract answer key from PDF")
            print("Questions will be created without correct answers.")
            return {}
        
        # Save extracted answers to file for future use
        answer_file.write_text(answer_text, encoding='utf-8')
        print(f"  ✓ Saved extracted answers to {answer_file}")
        
        # Parse and return
        answers = parse_answer_key(answer_text)
        print(f"✓ Loaded {len(answers)} answers from PDF")
        return answers
        
    except Exception as e:
        print(f"  ❌ Error extracting answers from PDF: {e}")
        print("Questions will be created without correct answers.")
        return {}


def load_html_content(html_path: Path) -> str:
    """
    Load HTML content from file.
    
    Args:
        html_path: Path to the HTML file
        
    Returns:
        HTML content as string
    """
    if not html_path.exists():
        print(f"⚠️  HTML file not found: {html_path}")
        return ""
    
    with open(html_path, 'r', encoding='utf-8') as f:
        return f.read()


def count_png_files_in_raw(exercise: str, base_path: Path) -> int:
    """
    Count the number of PNG files in the screenshot folder for the given exercise.
    
    Args:
        exercise: Exercise identifier (e.g., "2010")
        base_path: Base directory path
        
    Returns:
        Number of PNG files found
    """
    raw_path = base_path / "raw" / exercise / "screenshot"
    
    if not raw_path.exists():
        print(f"Warning: Screenshot folder does not exist: {raw_path}")
        return 0
    
    png_files = list(raw_path.glob("*.png"))
    png_count = len(png_files)
    
    print(f"Found {png_count} PNG files in {raw_path}")
    return png_count


def setup_directories(base_path: Path, exercise: str) -> None:
    """
    Create necessary directory structure for an exercise.
    
    Args:
        base_path: Base directory path
        exercise: Exercise identifier (e.g., "2010")
    """
    directories = [
        base_path / "raw" / exercise / "screenshot",
        base_path / "raw" / exercise / "html",
        base_path / "raw" / exercise / "pdf",
        base_path / "raw" / exercise / "imgs",  # For extracted artwork images
        base_path / "raw" / exercise / "combined_images",  # For combined side-by-side images
        base_path / "structured" / exercise / "json",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    
    print(f"✓ Directory structure created for exercise {exercise}")


def post_process_question(
    question_data: Dict,
    question_num: int,
    exercise: str,
    answer_key: Dict[int, str],
    artwork_images_map: Dict[int, List[str]]
) -> Dict:
    """
    Post-process the extracted question data to add metadata and correct answer.
    
    Args:
        question_data: Raw question data from vision model
        question_num: Question number
        exercise: Exercise identifier (e.g., "2010")
        answer_key: Dictionary mapping question numbers to answer letters
        artwork_images_map: Dictionary mapping question numbers to artwork image paths
        
    Returns:
        Processed question data
    """
    # Add metadata
    question_data['exercise'] = exercise
    question_data['question'] = question_num
    
    # Add correct answer if available
    if question_num in answer_key:
        answer_letter = answer_key[question_num]
        # Find the choice text for this answer
        answer_text = None
        for choice in question_data.get('choices', []):
            if choice['id'] == answer_letter:
                answer_text = choice['text']
                break
        
        if answer_text:
            question_data['answers'] = [{
                "id": answer_letter,
                "description": answer_text
            }]
    
    # Add artwork images if available
    # These are the actual artwork images referenced in the question, not the PDF page screenshot
    if question_num in artwork_images_map:
        question_data['images'] = artwork_images_map[question_num]
    elif 'images' not in question_data:
        question_data['images'] = []
    
    # Ensure image_references field exists
    if 'image_references' not in question_data:
        question_data['image_references'] = None
    
    return question_data


def extract_artwork_images(base_dir: Path, exercise: str) -> Dict[int, List[str]]:
    """
    Extract artwork images from PDF pages and create mapping to questions.
    
    This function extracts embedded images from the PDF and saves them to the imgs/ folder.
    It creates a mapping of which questions reference which artwork images.
    
    Args:
        base_dir: Base directory path
        exercise: Exercise identifier (e.g., "2010")
        
    Returns:
        Dictionary mapping question numbers to lists of artwork image paths
    """
    from ap_modules.pdf_service import PDFService
    
    pdf_dir = base_dir / "raw" / exercise / "pdf"
    imgs_dir = base_dir / "raw" / exercise / "imgs"
    
    # Check if images already extracted
    existing_images = list(imgs_dir.glob("*.jpg")) + list(imgs_dir.glob("*.png")) + list(imgs_dir.glob("*.jpeg"))
    if existing_images:
        print(f"Found {len(existing_images)} existing artwork images in {imgs_dir}")
        # TODO: Implement mapping logic based on image filenames or metadata
        return {}
    
    # Find PDF file
    pdf_files = list(pdf_dir.glob("*.pdf")) if pdf_dir.exists() else []
    if not pdf_files:
        print(f"⚠️  No PDF found for artwork extraction in {pdf_dir}")
        return {}
    
    pdf_path = pdf_files[0]
    
    try:
        # Extract images from PDF
        pdf_service = PDFService()
        extracted_images = pdf_service.extract_images_from_pdf(pdf_path, imgs_dir)
        
        # TODO: Implement intelligent mapping of images to question ranges
        # For now, return empty mapping
        # Future enhancement: Parse page text to identify "QUESTIONS 1-7: LEFT IMAGE" patterns
        # and create appropriate mappings
        return {}
        
    except Exception as e:
        print(f"⚠️  Error extracting artwork images: {e}")
        return {}
