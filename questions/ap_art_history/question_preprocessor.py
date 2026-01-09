#!/usr/bin/env python3
"""
AP Art History Question Preprocessor

This script processes AP Art History exam HTML and screenshots to extract multiple-choice questions
into structured JSON format.

USAGE:
    python question_preprocessor.py -e 2010 --min-question 1 --max-question 32

REQUIREMENTS:
    - transformers: Qwen2-VL-Instruct local model (optional)
    - langchain-google-genai: Gemini 2.5 Pro API integration (optional)
    - langchain-core: Pipeline orchestration
    - pillow: Image handling
    - python-dotenv: Environment configuration
"""

import click
from pathlib import Path
import sys
import json
from typing import Dict, List, Optional
import re

# Add parent directory to path for shared modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.core.config import ProcessorConfig
from modules.core.exceptions import ProcessingError, ConfigurationError
from modules.services.vision_service import VisionModelService
from modules.managers.prompt_manager import PromptManager
from modules.config import Config

# Import local AP Art History modules
from ap_modules.pdf_service import PDFService
from ap_modules.utils import (
    load_answer_key,
    load_html_content,
    count_png_files_in_raw,
    setup_directories,
    post_process_question,
    extract_artwork_images
)
from ap_modules.image_processor import extract_artwork_images_with_labels


def process_ap_page_batch(exercise: str, page_num: int, base_dir: Path,
                          prompts_dir: Path, metadata_ai: bool) -> List[Dict]:
    """
    Process a page that may contain multiple questions using HTML and screenshot.
    
    Args:
        exercise: Exercise identifier (e.g., "2010")
        page_num: Page number
        base_dir: Base directory path
        prompts_dir: Prompts directory path
        metadata_ai: Whether to track AI metadata
        
    Returns:
        List of processed question dictionaries
    """
    try:
        print(f"\n=== Processing Page {page_num} (Batch Mode) ===")
        
        # Initialize services
        vision_service = VisionModelService()
        prompt_manager = PromptManager(prompts_dir=prompts_dir)
        vision_service.set_prompt_manager(prompt_manager)
        
        # Paths
        image_path = base_dir / "raw" / exercise / "screenshot" / f"{page_num}.png"
        html_path = base_dir / "raw" / exercise / "html" / f"{page_num}.html"
        
        if not image_path.exists():
            print(f"❌ Image not found: {image_path}")
            return []
        
        # Step 1: Load HTML content
        print("Step 1: Loading HTML content...")
        html_text = load_html_content(html_path)
        
        # Step 2: Batch extraction using special prompt
        print("Step 2: Batch question extraction...")
        
        # Load batch extraction prompt
        batch_prompt_file = prompts_dir / "extract_ap_art_history_batch.txt"
        if not batch_prompt_file.exists():
            print(f"❌ Batch prompt not found: {batch_prompt_file}")
            return []
        
        with open(batch_prompt_file, 'r', encoding='utf-8') as f:
            batch_prompt_template = f.read()
        
        user_prompt = batch_prompt_template.format(
            ocr_text="",  # No OCR text
            html_text=html_text
        )
        
        system_prompt = "You are an expert at extracting structured data from academic exam documents."
        
        # Call vision model with increased token limit for batch extraction
        # Batch responses need more tokens as they contain multiple questions
        response = vision_service.chat(
            image_path=str(image_path),
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            description="batch question extraction",
            max_tokens=4096  # Increased for batch extraction
        )
        
        # Parse response
        import re
        response = re.sub(r"^(?:```(?:json)?\s*)", "", response)
        response = re.sub(r"```\s*$", "", response, flags=re.MULTILINE)
        
        # Log raw response for debugging
        if Config.VERBOSE:
            print(f"Raw response length: {len(response)} characters")
            print(f"Raw response preview (first 500 chars):\n{response[:500]}")
            print(f"Raw response end (last 200 chars):\n{response[-200:]}")
        
        try:
            batch_data = json.loads(response)
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            print(f"Response length: {len(response)} characters")
            
            # Always show response end when there's an error (not just in verbose mode)
            print(f"Response beginning:\n{response[:300]}")
            print(f"Response ending:\n{response[-300:]}")
            
            # Try to repair common JSON issues
            try:
                # Remove any trailing incomplete content
                last_brace = response.rfind('}')
                if last_brace > 0:
                    repaired_response = response[:last_brace + 1]
                    batch_data = json.loads(repaired_response)
                    print("✓ Successfully repaired JSON response by truncating at last '}'")
                else:
                    raise e
            except Exception as repair_error:
                print(f"⚠️  Could not repair JSON: {repair_error}")
                print(f"⚠️  Skipping page {page_num}")
                return []
        
        # Check if this page has actual questions
        if not batch_data.get('has_questions', True):
            reason = batch_data.get('reason', 'no questions detected')
            print(f"⚠️  Page {page_num} has no questions: {reason}")
            return []
        
        # Extract questions
        questions = batch_data.get('questions', [])
        image_ref = batch_data.get('image_reference', '')
        page_header = batch_data.get('page_header', '')
        
        if not questions:
            print(f"⚠️  No questions found on page {page_num}")
            return []
        
        print(f"✓ Extracted {len(questions)} questions from page {page_num}")
        if image_ref:
            print(f"  Image reference: {image_ref}")
        
        # Save ONE JSON file per page containing all questions
        output_path = base_dir / "structured" / exercise / "json" / f"{page_num}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        page_data = {
            "page": page_num,
            "exercise": exercise,
            "page_header": page_header,
            "image_references": image_ref,
            "questions": []
        }
        
        results = []
        for q in questions:
            q_num = q.get('question_number')
            if not q_num:
                continue
            
            question_dict = {
                "question": q_num,
                "type": "multiple_choice_radio",
                "question_text": q.get('question_text'),
                "choices": q.get('choices', []),
                "answers": [],  # Will be filled in post-processing
                "images": [],  # Will be filled in post-processing
                "language": "en"
            }
            
            page_data['questions'].append(question_dict)
            results.append(question_dict)
            print(f"  ✓ Question {q_num} added to page")
        
        # Save the page JSON with all questions
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(page_data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Saved page {page_num} with {len(results)} questions to {output_path.name}")
        
        return results
        
    except Exception as e:
        print(f"❌ Error processing page {page_num}: {e}")
        if Config.VERBOSE:
            import traceback
            traceback.print_exc()
        return []


def process_single_ap_question(exercise: str, question_num: int, base_dir: Path,
                               prompts_dir: Path, metadata_ai: bool) -> Optional[Dict]:
    """
    Process a single AP Art History question using HTML and screenshot.
    (Legacy function - use process_ap_page_batch for pages with multiple questions)
    
    Args:
        exercise: Exercise identifier (e.g., "2010")
        question_num: Question number
        base_dir: Base directory path
        prompts_dir: Prompts directory path
        metadata_ai: Whether to track AI metadata
        
    Returns:
        Processed question data dictionary or None if failed
    """
    try:
        print(f"\n=== Processing Question {exercise}/{question_num} ===")
        
        # Initialize services
        vision_service = VisionModelService()
        prompt_manager = PromptManager(prompts_dir=prompts_dir)
        vision_service.set_prompt_manager(prompt_manager)
        
        # Paths
        image_path = base_dir / "raw" / exercise / "screenshot" / f"{question_num}.png"
        html_path = base_dir / "raw" / exercise / "html" / f"{question_num}.html"
        output_path = base_dir / "structured" / exercise / "json" / f"{question_num}.json"
        
        if not image_path.exists():
            print(f"❌ Image not found: {image_path}")
            return None
        
        # Step 1: Load HTML content
        print("Step 1: Loading HTML content...")
        html_text = load_html_content(html_path)
        
        # Step 2: Vision model processing with HTML + image
        print("Step 2: Vision model processing...")
        
        # For AP Art History, we know it's multiple choice
        question_type = "multiple_choice_radio"
        
        question_data = vision_service.process_question_with_detected_type(
            image_path=str(image_path),
            ocr_text="",  # No OCR text
            html_text=html_text,
            question_type=question_type,
            exercise=int(exercise) if exercise.isdigit() else 0,
            question=question_num,
            track_metadata=metadata_ai
        )
        
        # Check if this page actually has a question
        if question_data.question_text is None and not question_data.choices:
            print(f"⚠️  No actual question found on page {question_num} - skipping")
            return None
        
        # Step 3: Convert to dictionary and save
        print("Step 3: Saving results...")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Serialize choices to dictionaries
        serialized_choices = []
        if question_data.choices:
            for choice in question_data.choices:
                if hasattr(choice, 'id') and hasattr(choice, 'text'):
                    # Choice object
                    serialized_choices.append({
                        "id": choice.id,
                        "text": choice.text
                    })
                elif isinstance(choice, dict):
                    # Already a dict
                    serialized_choices.append(choice)
                else:
                    # String or other format
                    serialized_choices.append(choice)
        
        question_dict = {
            "exercise": question_data.exercise,
            "question": question_data.question,
            "type": question_data.type,
            "question_text": question_data.question_text,
            "choices": serialized_choices,
            "answers": question_data.answers if question_data.answers else [],
            "images": [],  # Will be filled in post-processing
            "image_references": None,
            "language": "en"
        }
        
        # Add AI metadata if tracking
        if metadata_ai and question_data.ai_calls:
            question_dict["ai_calls"] = [
                {
                    "description": call.description,
                    "model_name": call.model_name,
                    "input_tokens": call.input_tokens,
                    "output_tokens": call.output_tokens,
                    "total_tokens": call.total_tokens,
                    "processing_time": call.processing_time,
                    "timestamp": call.timestamp
                }
                for call in question_data.ai_calls
            ]
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(question_dict, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Question {exercise}/{question_num} processed successfully")
        return question_dict
        
    except Exception as e:
        print(f"❌ Error processing question {exercise}/{question_num}: {e}")
        if Config.VERBOSE:
            import traceback
            traceback.print_exc()
        return None


@click.command()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose/debug output')
@click.option('--exercise', '-e', multiple=True, type=str, help='Exercise identifier(s) to process (e.g., 2010, 2011)')
@click.option('--min-question', default=1, help='Minimum question number to process', show_default=True)
@click.option('--max-question', default=32, help='Maximum question number to process', show_default=True)
@click.option('--metadata-ai/--no-metadata-ai', default=True, help='Track AI call metadata including token usage', show_default=True)
@click.option('--skip-pdf-conversion', is_flag=True, help='Skip automatic PDF conversion even if screenshots are missing')
@click.option('--batch-page', type=int, default=None, help='Process a specific page in batch mode (extracts all questions from that page)')
def main(verbose, exercise, min_question, max_question, metadata_ai, skip_pdf_conversion, batch_page):
    """Process AP Art History questions from HTML and screenshots."""
    
    try:
        # Handle default case when no exercises are specified
        if not exercise:
            exercise = ("2010",)  # Default to 2010 exam
        
        print("=== AP Art History Question Preprocessor ===")
        print(f"Configuration: {Config.get_model_info()}")
        print(f"Verbose: {verbose}")
        print(f"Exercises to process: {list(exercise)}")
        print(f"Requested questions: {min_question}-{max_question}")
        print(f"AI metadata tracking: {metadata_ai}")
        print(f"Skip PDF conversion: {skip_pdf_conversion}")
        
        # Set global verbose flag for models
        Config.VERBOSE = verbose
        
        base_dir = Path(__file__).parent
        prompts_dir = Path(__file__).parent.parent.parent / "prompts"
        
        # Process each exercise (year)
        total_exercises = len(exercise)
        successful_exercises = 0
        
        for i, current_exercise in enumerate(exercise, 1):
            print(f"\n{'='*60}")
            print(f"Processing Exercise {current_exercise} ({i}/{total_exercises})")
            print(f"{'='*60}")
            
            # Setup directories
            setup_directories(base_dir, current_exercise)
            
            # Check if screenshots exist
            screenshot_dir = base_dir / "raw" / current_exercise / "screenshot"
            existing_screenshots = list(screenshot_dir.glob("*.png")) if screenshot_dir.exists() else []
            
            # Check if HTML and imgs directories exist and have content
            html_dir = base_dir / "raw" / current_exercise / "html"
            imgs_dir = base_dir / "raw" / current_exercise / "imgs"
            existing_html = list(html_dir.glob("*.html")) if html_dir.exists() else []
            existing_imgs = list(imgs_dir.glob("*")) if imgs_dir.exists() else []
            
            # Determine if we need to extract from PDF
            need_screenshots = len(existing_screenshots) == 0
            need_html_imgs = len(existing_html) == 0 or len(existing_imgs) == 0
            
            if (need_screenshots or need_html_imgs) and not skip_pdf_conversion:
                if need_screenshots:
                    print(f"⚠️  No screenshots found in {screenshot_dir}")
                if need_html_imgs:
                    print(f"⚠️  HTML/images not found - needed for artwork detection")
                
                print("Attempting to extract from PDF...")
                
                # Try to find PDF file
                pdf_dir = base_dir / "raw" / current_exercise / "pdf"
                pdf_files = list(pdf_dir.glob("*.pdf")) if pdf_dir.exists() else []
                
                if pdf_files:
                    pdf_path = pdf_files[0]  # Use first PDF found
                    print(f"Found PDF: {pdf_path}")
                    try:
                        pdf_service = PDFService()
                        
                        # Convert PDF to screenshots if needed
                        if need_screenshots:
                            print("Converting PDF to screenshots...")
                            pdf_service.convert_pdf_to_images(pdf_path, screenshot_dir, dpi=300)
                        
                        # Extract text to HTML (for artwork detection labels)
                        # Note: We don't extract images here - we crop them directly from screenshots
                        if need_html_imgs:
                            print("Extracting text to HTML for artwork detection...")
                            pdf_service.extract_text_to_html(pdf_path, html_dir)
                        
                    except Exception as e:
                        print(f"❌ Error converting PDF: {e}")
                        print("Please ensure PyMuPDF is installed: pip install PyMuPDF")
                        print("You can also manually place PNG images in the screenshot directory.")
                        continue
                else:
                    print(f"❌ No PDF found in {pdf_dir}")
                    print("Please provide either:")
                    print(f"  1. PNG images in {screenshot_dir}")
                    print(f"  2. PDF file in {pdf_dir}")
                    continue
            elif need_screenshots:
                print(f"❌ No screenshots found and PDF conversion is skipped.")
                print(f"Please place PNG images in {screenshot_dir}")
                continue
            else:
                print(f"Found {len(existing_screenshots)} existing screenshots")
                if len(existing_html) > 0:
                    print(f"Found {len(existing_html)} HTML files")
                if len(existing_imgs) > 0:
                    print(f"Found {len(existing_imgs)} extracted images")
            
            # Load answer key
            answer_key = load_answer_key(base_dir / "raw", current_exercise)
            
            # Count actual PNG files in the raw folder
            actual_png_count = count_png_files_in_raw(current_exercise, base_dir)
            
            # Use the minimum between max_question and actual PNG count
            effective_max_question = min(max_question, actual_png_count)
            
            print(f"Available PNG files: {actual_png_count}")
            print(f"Effective questions: {min_question}-{effective_max_question}")
            
            # Check if we have any questions to process
            if effective_max_question < min_question:
                print(f"⚠️  Skipping exercise {current_exercise}: No questions to process.")
                continue
            
            # Create question range
            question_range = range(min_question, effective_max_question + 1)
            
            print(f"\nStarting processing of exercise {current_exercise}, questions {min_question}-{effective_max_question}...")
            print(f"Using {Config.MODEL_TYPE.upper()} model")

            try:
                # Use batch processing by default (one JSON per page with multiple questions)
                print("Processing pages in batch mode (multiple questions per page)...")
                successful_count = 0
                failed_count = 0
                total_questions_extracted = 0
                
                if batch_page is not None:
                    # Process a single specific page
                    page_range = [batch_page]
                else:
                    # Process all pages from min to max
                    page_range = range(min_question, effective_max_question + 1)
                
                for page_num in page_range:
                    # Stop if we've already extracted enough questions
                    if total_questions_extracted >= max_question:
                        print(f"✓ Reached target of {max_question} questions, stopping.")
                        break
                    
                    results = process_ap_page_batch(
                        exercise=current_exercise,
                        page_num=page_num,
                        base_dir=base_dir,
                        prompts_dir=prompts_dir,
                        metadata_ai=metadata_ai
                    )
                    
                    if results:
                        # Track highest question number extracted
                        for result in results:
                            q_num = result.get('question')
                            if q_num and q_num > total_questions_extracted:
                                total_questions_extracted = q_num
                        
                        successful_count += len(results)
                        print(f"✓ Page {page_num}: extracted {len(results)} questions (total: {total_questions_extracted})")
                    else:
                        failed_count += 1
                        print(f"⚠️  Page {page_num}: no questions found or page skipped")
                
                processed_pages = len([p for p in page_range])
                print(f"\n✓ Processed {successful_count} questions successfully across {processed_pages} pages")
                
                # Extract and combine artwork images
                print("\nExtracting and combining artwork images...")
                artwork_mapping = extract_artwork_images_with_labels(base_dir, current_exercise)
                
                # Post-process to add answers, rename to blocks, and add artwork images
                print("Post-processing and renaming files to block numbers...")
                json_dir = base_dir / "structured" / current_exercise / "json"
                imgs_dir = base_dir / "structured" / current_exercise / "imgs"
                
                # Process all page JSON files and rename to blocks
                for page_file in sorted(json_dir.glob("*.json"), key=lambda x: int(x.stem) if x.stem.isdigit() else 999):
                    with open(page_file, 'r', encoding='utf-8') as f:
                        page_data = json.load(f)
                    
                    page_num = page_data.get('page')
                    
                    # Find which block this page belongs to
                    block_num = None
                    block_image = None
                    for q_range, artwork_info in artwork_mapping.items():
                        if artwork_info.get('question_page') == page_num:
                            block_num = artwork_info.get('block_num')
                            block_image = f"imgs/{block_num}.jpg"
                            break
                    
                    # Skip pages without questions/artwork
                    if block_num is None:
                        print(f"  ⚠️ Skipping {page_file.name} (no artwork block)")
                        continue
                    
                    # Post-process each question in the page
                    updated_questions = []
                    for question in page_data.get('questions', []):
                        question_num = question.get('question')
                        
                        # Add correct answer
                        if question_num and question_num in answer_key:
                            answer_letter = answer_key[question_num]
                            answer_text = None
                            for choice in question.get('choices', []):
                                if choice.get('id') == answer_letter:
                                    answer_text = choice.get('text')
                                    break
                            
                            if answer_text:
                                question['answers'] = [{
                                    "id": answer_letter,
                                    "description": answer_text
                                }]
                        
                        # Add artwork image path (relative path using block number)
                        question['images'] = [block_image] if block_image else []
                        
                        updated_questions.append(question)
                    
                    # Update page data and add block number
                    page_data['block'] = block_num
                    page_data['questions'] = updated_questions
                    if block_image:
                        page_data['artwork_image'] = block_image
                    
                    # Save with block number as filename
                    block_file = json_dir / f"{block_num}.json"
                    with open(block_file, 'w', encoding='utf-8') as f:
                        json.dump(page_data, f, indent=2, ensure_ascii=False)
                    
                    # Remove old page file if different
                    if page_file != block_file:
                        page_file.unlink()
                    
                    print(f"  ✓ Block {block_num}: {len(updated_questions)} questions → {block_file.name}")
                
                print(f"✓ Post-processing complete")
                
                if successful_count > 0:
                    print(f"\n✅ Exercise {current_exercise} completed!")
                    print(f"Successfully processed: {successful_count} questions across {processed_pages} pages")
                    print(f"Results saved to: questions/ap_art_history/structured/{current_exercise}/json/")
                    print(f"Format: One JSON file per page (page_N.json) containing all questions on that page")
                    successful_exercises += 1
                else:
                    print(f"\n❌ Exercise {current_exercise} failed - no questions processed successfully")
                
            except Exception as e:
                print(f"❌ Error processing exercise {current_exercise}: {e}")
                if verbose:
                    import traceback
                    traceback.print_exc()
                continue
        
        # Final summary
        print(f"\n{'='*60}")
        print(f"FINAL SUMMARY")
        print(f"{'='*60}")
        print(f"Total exercises requested: {total_exercises}")
        print(f"Successfully processed: {successful_exercises}")
        print(f"Failed: {total_exercises - successful_exercises}")
        
        if successful_exercises == total_exercises:
            print("🎉 All exercises processed successfully!")
        elif successful_exercises > 0:
            print(f"⚠️  {successful_exercises} out of {total_exercises} exercises processed successfully")
        else:
            print("❌ No exercises were processed successfully")
        
    except ConfigurationError as e:
        print(f"❌ Configuration error: {e}")
        return 1
    except ProcessingError as e:
        print(f"❌ Processing error: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
