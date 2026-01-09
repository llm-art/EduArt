#!/usr/bin/env python3
"""
Extract Answer Key from AP Art History PDF

This script extracts the answer key from the PDF and saves it to answers.txt

USAGE:
    python extract_answers.py 2010

REQUIREMENTS:
    pip install PyMuPDF
"""

import click
from pathlib import Path
import re
import sys

from ap_modules.pdf_service import PDFService


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
    pdf_service = PDFService()
    doc = pdf_service.fitz.open(pdf_path)
    
    answer_key = None
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        
        # Look for answer section header
        if "Answers" in text and "Section I" in text:
            print(f"Found answer section on page {page_num + 1}")
            
            # Extract answer pattern: "1-C, 2-B, 3-A, ..."
            # Look for patterns like "1-C" or "1-A"
            pattern = r'(\d+\s*-\s*[A-D](?:\s*,\s*)?)'
            matches = re.findall(pattern, text)
            
            if matches:
                # Join all matches and clean up
                answer_key = ''.join(matches)
                answer_key = answer_key.strip().rstrip(',')
                print(f"Extracted {len(matches)} answers")
                break
    
    doc.close()
    
    if not answer_key:
        print("⚠️  Warning: Could not find answer key in PDF")
        return ""
    
    return answer_key


@click.command()
@click.argument('year')
def main(year):
    """Extract answer key from AP Art History PDF and save to answers.txt."""
    
    print("=== AP Art History Answer Key Extractor ===")
    print(f"Year: {year}")
    
    base_dir = Path(__file__).parent
    year_short = year[-2:]  # Get last 2 digits
    pdf_name = f"ap{year_short}_frq_art_history.pdf"
    
    pdf_path = base_dir / "raw" / year / "pdf" / pdf_name
    output_path = base_dir / "raw" / year / "answers.txt"
    
    if not pdf_path.exists():
        print(f"❌ PDF not found: {pdf_path}")
        return 1
    
    try:
        # Extract answer key
        answer_key = extract_answer_key_from_pdf(pdf_path)
        
        if not answer_key:
            print("❌ Failed to extract answer key")
            return 1
        
        # Save to file
        output_path.write_text(answer_key, encoding='utf-8')
        
        print(f"\n{'='*60}")
        print(f"SUCCESS")
        print(f"{'='*60}")
        print(f"Answer key extracted and saved to: {output_path}")
        print(f"Content preview: {answer_key[:100]}...")
        
        # Parse and display count
        from ap_modules.utils import parse_answer_key
        answers = parse_answer_key(answer_key)
        print(f"Total answers: {len(answers)}")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
