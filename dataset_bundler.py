#!/usr/bin/env python3
"""
Dataset Bundler Script

This script navigates all folders with a subfolder called structured/ in questions/.
Inside each structured folder, it processes all subfolders (e.g., 2010, 1, etc.) 
and extracts JSON files to create TXT files of questions, copies JSON files to metadata/,
and copies associated images to imgs/ folder with consistent naming.

The script supports filtering by question type (default: multiple_choice_radio).
"""

import os
import json
import glob
import shutil
import re
import click
from datetime import datetime
from pathlib import Path
from collections import defaultdict


# Report configuration - single point for modifications
REPORT_CONFIG = {
    'readme_filename': 'README.md',
    'metadata_filename': 'metadata.json',
    'default_version': 0.1,
    'version_increment': 0.1,
    'sections': [
        'creation_datetime',
        'processing_time',
        'version',
        'exercise_count',
        'question_count',
        'questions_by_type',
        'ai_calls_summary',
        'cost_analysis'
    ],
    'pricing': {
        'Google gemini-2.5-flash-lite': {
            'input_cost_per_million': 0.1,  # $0.1 per 1M input tokens
            'output_cost_per_million': 0.4  # $0.4 per 1M output tokens
        }
    }
}


def find_structured_folders():
    """Find all folders with a 'structured' subfolder in questions/."""
    structured_folders = []
    questions_dir = Path("questions")
    
    if not questions_dir.exists():
        print("Warning: 'questions' directory not found")
        return []
    
    # Look for all subdirectories in questions/ that contain a 'structured' folder
    for item in questions_dir.iterdir():
        if item.is_dir():
            structured_path = item / "structured"
            if structured_path.exists() and structured_path.is_dir():
                structured_folders.append(structured_path)
    
    return structured_folders


def find_json_files_in_structured(structured_path, question_types):
    """
    Find all JSON files in structured/{subfolder}/json/ directories.
    
    Args:
        structured_path: Path to the structured folder
        question_types: List of question types to filter by
        
    Returns:
        List of tuples: (json_file_path, source_folder_name, subfolder_name)
    """
    json_files = []
    
    # Get source name (e.g., "myzanichelli" or "ap_art_history")
    source_name = structured_path.parent.name
    
    # Iterate through all subfolders in structured/
    for subfolder in structured_path.iterdir():
        if not subfolder.is_dir():
            continue
        
        # Look for json/ directory inside each subfolder
        json_dir = subfolder / "json"
        if not json_dir.exists() or not json_dir.is_dir():
            continue
        
        # Find all JSON files in this json/ directory
        for json_file in json_dir.glob("*.json"):
            # Check if this JSON file contains questions of the desired type
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Handle both single question format and multiple questions format
                questions_to_check = []
                if "questions" in data and isinstance(data["questions"], list):
                    # Multiple questions in one file
                    questions_to_check = data["questions"]
                elif "type" in data:
                    # Single question format
                    questions_to_check = [data]
                
                # Check if any question matches the desired types
                for question in questions_to_check:
                    if question.get("type") in question_types:
                        json_files.append((json_file, source_name, subfolder.name))
                        break  # Found at least one matching question, add file once
                        
            except Exception as e:
                print(f"Warning: Could not read {json_file}: {e}")
                continue
    
    return json_files


def find_associated_image(json_file_path, image_ref, source_name, exercise_num, question_num):
    """
    Find associated image file for a question.
    
    Args:
        json_file_path: Path to the JSON file
        image_ref: Image reference from JSON (e.g., "imgs/2.jpg" or None)
        source_name: Source name (e.g., "myzanichelli" or "ap_art_history")
        exercise_num: Exercise number
        question_num: Question number
        
    Returns:
        Path to image file if found, None otherwise
    """
    # First, try using the image reference if provided
    if image_ref:
        # Get the parent directory of the json file (e.g., structured/2010/)
        json_parent = json_file_path.parent.parent
        
        # Construct the image path relative to the json parent
        image_path = json_parent / image_ref
        
        if image_path.exists():
            return image_path
    
    # For myzanichelli, try looking in the raw folder
    if source_name == "myzanichelli" and exercise_num is not None and question_num is not None:
        raw_image_path = Path(f"questions/myzanichelli/raw/{exercise_num}/imgs/{question_num}.jpg")
        if raw_image_path.exists():
            return raw_image_path
    
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
        "multiple_choice_radio": "SCELTA MULTIPLA\n**Cosa devi fare:** scegli la risposta esatte tra quelle proposte",
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

    if question_text:
        content.append(question_text)
        content.append("")

    if choices:
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


def get_previous_version(dataset_dir):
    """Get version from previous metadata file, if it exists."""
    # Convert to absolute path to handle relative paths correctly
    dataset_path = Path(dataset_dir).resolve()

    # Check if dataset directory exists
    if not dataset_path.exists():
        return None

    # Try to get version from metadata.json first (more reliable)
    metadata_file = dataset_path / REPORT_CONFIG['metadata_filename']
    if metadata_file.exists() and metadata_file.is_file():
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                return metadata.get('version')
        except Exception as e:
            print(
                f"Warning: Could not read previous version from {metadata_file}: {e}")

    # Fallback to README.md
    readme_file = dataset_path / REPORT_CONFIG['readme_filename']
    if readme_file.exists() and readme_file.is_file():
        try:
            with open(readme_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Look for version line in format "**Version:** X.X"
                version_match = re.search(r'\*\*Version:\*\* (\d+\.\d+)', content)
                if version_match:
                    return float(version_match.group(1))
        except Exception as e:
            print(
                f"Warning: Could not read previous version from {readme_file}: {e}")

    return None


def collect_statistics_from_metadata(metadata_files):
    """Collect statistics about the dataset from processed metadata files."""
    stats = {
        'sources': set(),
        'total_questions': 0,
        'questions_by_type': defaultdict(int),
        'ai_calls': {}
    }

    # Process each metadata JSON file to get source info, question types, and AI calls
    for json_file in metadata_files:
        try:
            # Read JSON to get question type and extract source info
            with open(json_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
                
                # Handle both single question and multiple questions format
                questions_to_process = []
                if "questions" in json_data and isinstance(json_data["questions"], list):
                    questions_to_process = json_data["questions"]
                    # Track the source (e.g., "ap_art_history/2010")
                    source = json_data.get("source", "unknown")
                    stats['sources'].add(source)
                elif "type" in json_data:
                    questions_to_process = [json_data]
                    source = json_data.get("source", "unknown")
                    stats['sources'].add(source)
                
                # Count questions by type
                for question in questions_to_process:
                    question_type = question.get("type", "unknown")
                    stats['questions_by_type'][question_type] += 1
                    stats['total_questions'] += 1

                # Process AI calls if present
                ai_calls = json_data.get("ai_calls", [])
                for ai_call in ai_calls:
                    description = ai_call.get("description", "unknown")
                    model_name = ai_call.get("model_name", "unknown")

                    # Create a unique key for this AI call type
                    call_key = f"{description}_{model_name}"

                    if call_key not in stats['ai_calls']:
                        stats['ai_calls'][call_key] = {
                            'description': description,
                            'model_name': model_name,
                            'input_tokens': 0,
                            'output_tokens': 0,
                            'total_tokens': 0,
                            'processing_time': 0.0,
                            'call_count': 0
                        }

                    # Aggregate the numeric values
                    stats['ai_calls'][call_key]['input_tokens'] += ai_call.get(
                        'input_tokens', 0)
                    stats['ai_calls'][call_key]['output_tokens'] += ai_call.get(
                        'output_tokens', 0)
                    stats['ai_calls'][call_key]['total_tokens'] += ai_call.get(
                        'total_tokens', 0)
                    stats['ai_calls'][call_key]['processing_time'] += ai_call.get(
                        'processing_time', 0.0)
                    stats['ai_calls'][call_key]['call_count'] += 1

        except Exception as e:
            print(f"Warning: Could not process statistics for {json_file}: {e}")
            continue

    return stats


def calculate_ai_costs(stats):
    """Calculate the total cost of AI calls based on token usage and pricing."""
    total_cost = 0.0
    cost_breakdown = {}

    for call_data in stats['ai_calls'].values():
        model_name = call_data['model_name']
        input_tokens = call_data['input_tokens']
        output_tokens = call_data['output_tokens']

        # Get pricing for this model (default to 0 if not found)
        pricing = REPORT_CONFIG['pricing'].get(model_name, {
            'input_cost_per_million': 0.0,
            'output_cost_per_million': 0.0
        })

        # Calculate costs (convert tokens to millions)
        input_cost = (input_tokens / 1_000_000) * pricing['input_cost_per_million']
        output_cost = (output_tokens / 1_000_000) * \
            pricing['output_cost_per_million']
        call_cost = input_cost + output_cost

        cost_breakdown[f"{call_data['description']} ({model_name})"] = {
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'input_cost': input_cost,
            'output_cost': output_cost,
            'total_cost': call_cost
        }

        total_cost += call_cost

    return total_cost, cost_breakdown


def generate_report(start_time, end_time, stats, dataset_dir, version):
    """Generate the dataset bundle report in markdown format."""
    # Calculate processing time
    processing_time = end_time - start_time

    # Calculate AI costs
    total_cost, cost_breakdown = calculate_ai_costs(stats)

    # Generate report content
    report_content = f"""# Dataset Bundle Report

**Creation Date & Time:** {start_time.strftime('%Y-%m-%d %H:%M:%S')}

**Processing Time:** {processing_time.total_seconds():.2f} seconds

**Version:** {version:.1f}

**Number of Sources:** {len(stats['sources'])}

**Number of Questions:** {stats['total_questions']}

**Total Cost:** ${total_cost:.4f}

## Questions by Type

"""

    # Add questions by type section
    for question_type, count in sorted(stats['questions_by_type'].items()):
        report_content += f"- **{question_type}:** {count}\n"

    # Add sources section
    if stats['sources']:
        report_content += f"""
## Sources

"""
        for source in sorted(stats['sources']):
            report_content += f"- {source}\n"

    # Add AI calls section
    if stats['ai_calls']:
        report_content += f"""
## AI Calls Summary

"""
        for call_data in stats['ai_calls'].values():
            report_content += f"""### {call_data['description'].title()}
- **Model:** {call_data['model_name']}
- **Input Tokens:** {call_data['input_tokens']:,}
- **Output Tokens:** {call_data['output_tokens']:,}
- **Total Tokens:** {call_data['total_tokens']:,}
- **Processing Time:** {call_data['processing_time']:.2f} seconds

"""

    # Add cost breakdown section
    if cost_breakdown:
        report_content += f"""
## Cost Breakdown

"""
        for call_type, cost_data in cost_breakdown.items():
            report_content += f"""### {call_type}
- **Input Tokens:** {cost_data['input_tokens']:,} (${cost_data['input_cost']:.4f})
- **Output Tokens:** {cost_data['output_tokens']:,} (${cost_data['output_cost']:.4f})
- **Total Cost:** ${cost_data['total_cost']:.4f}

"""

        report_content += f"**Grand Total:** ${total_cost:.4f}\n"

    report_content += f"""
---
*Report generated automatically by dataset bundler script*
*Last updated: {end_time.strftime('%Y-%m-%d %H:%M:%S')}*
"""

    return report_content


def generate_metadata(start_time, end_time, stats, dataset_dir, version):
    """Generate the dataset bundle metadata in JSON format."""
    # Calculate processing time
    processing_time = end_time - start_time

    # Convert AI calls dictionary to list format for JSON
    ai_calls_list = []
    for call_data in stats['ai_calls'].values():
        ai_calls_list.append({
            "description": call_data['description'],
            "model_name": call_data['model_name'],
            "input_tokens": call_data['input_tokens'],
            "output_tokens": call_data['output_tokens'],
            "total_tokens": call_data['total_tokens'],
            "processing_time": call_data['processing_time']
        })

    # Generate metadata structure
    metadata = {
        "creation_datetime": start_time.strftime('%Y-%m-%d %H:%M:%S'),
        "processing_time_seconds": processing_time.total_seconds(),
        "version": version,
        "source_count": len(stats['sources']),
        "question_count": stats['total_questions'],
        "questions_by_type": dict(stats['questions_by_type']),
        "sources": sorted(list(stats['sources'])),
        "ai_calls": ai_calls_list,
        "last_updated": end_time.strftime('%Y-%m-%d %H:%M:%S')
    }

    return metadata


@click.command()
@click.option('--question-type', 
              multiple=True,
              default=['multiple_choice_radio'],
              help='Question type(s) to include (can be specified multiple times). Default: multiple_choice_radio')
@click.option('--version', type=float, help='Specify version number for the report')
@click.option('--output-dir', default='dataset', help='Output directory for the dataset (default: dataset)')
def main(question_type, version, output_dir):
    """Main function to process all JSON files and create dataset."""
    start_time = datetime.now()
    
    # Convert question_type tuple to list
    question_types = list(question_type)
    
    print(f"Filtering by question types: {', '.join(question_types)}")

    # Read previous version BEFORE removing the dataset directory
    dataset_dir = output_dir
    previous_version = None
    if version is None:
        previous_version = get_previous_version(dataset_dir)

    # Remove existing dataset directory for fresh start
    if os.path.exists(dataset_dir):
        shutil.rmtree(dataset_dir)
        print(f"Removed existing dataset directory: {dataset_dir}")

    # Create dataset directory structure
    dataset_path = Path(dataset_dir)
    data_dir = dataset_path / "data"
    metadata_dir = dataset_path / "metadata"
    imgs_dir = dataset_path / "imgs"

    data_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)
    imgs_dir.mkdir(parents=True, exist_ok=True)

    # Find all structured folders
    structured_folders = find_structured_folders()
    
    if not structured_folders:
        print("No structured folders found in questions/")
        return
    
    print(f"Found {len(structured_folders)} structured folder(s)")

    processed_files = []
    skipped_files = []
    processed_metadata_files = []
    
    # Track image files to avoid duplicates
    # Key: absolute path to source image, Value: (file_id, extension) of first copy
    image_mapping = {}
    
    # Collect all JSON files from all structured folders first
    all_json_files = []
    for structured_path in structured_folders:
        json_files = find_json_files_in_structured(structured_path, question_types)
        all_json_files.extend(json_files)
    
    if not all_json_files:
        print("No matching JSON files found in any structured folders")
        return
    
    # Sort all files by: source_name, subfolder (as int), json filename (as int)
    def sort_key(item):
        json_file_path, source_name, subfolder_name = item
        try:
            subfolder_num = int(subfolder_name)
        except ValueError:
            subfolder_num = 0
        
        try:
            json_filename = json_file_path.stem  # filename without extension
            json_num = int(json_filename)
        except ValueError:
            json_num = 0
        
        return (source_name, subfolder_num, json_num)
    
    all_json_files.sort(key=sort_key)
    
    print(f"Found {len(all_json_files)} JSON file(s) with matching question types across all sources")
    
    # Process each JSON file
    for json_file_path, source_name, subfolder_name in all_json_files:
            try:
                # Read JSON file
                with open(json_file_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                
                # Handle both single question and multiple questions format
                questions_to_process = []
                if "questions" in json_data and isinstance(json_data["questions"], list):
                    # Multiple questions in one file - filter by type
                    for question in json_data["questions"]:
                        if question.get("type") in question_types:
                            questions_to_process.append(question)
                elif "type" in json_data:
                    # Single question format
                    if json_data.get("type") in question_types:
                        questions_to_process.append(json_data)
                
                # Process each question
                for question_data in questions_to_process:
                    # Get next file identifier
                    file_id = get_next_file_id(data_dir)
                    
                    # Extract question data
                    question_title, question_text, choices, question_type_val = extract_question_data(
                        question_data)
                    
                    # Create TXT file content
                    txt_content = create_txt_content(
                        question_title, question_text, choices, question_type_val)
                    
                    # Write TXT file to data/ folder
                    txt_filename = f"{file_id}.txt"
                    txt_path = data_dir / txt_filename
                    with open(txt_path, 'w', encoding='utf-8') as f:
                        f.write(txt_content)
                    
                    # Look for and copy associated image
                    # Handle both "images" (array) and "image" (single) fields
                    image_ref = None
                    if "images" in question_data:
                        images = question_data.get("images", [])
                        if images and len(images) > 0:
                            image_ref = images[0]
                    elif "image" in question_data:
                        image_ref = question_data.get("image")
                    
                    # Get exercise and question numbers for image lookup
                    exercise_num = question_data.get("exercise")
                    question_num = question_data.get("question")
                    
                    image_file = find_associated_image(json_file_path, image_ref, source_name, exercise_num, question_num)
                    
                    # Add source information to the question data
                    question_data_copy = question_data.copy()
                    question_data_copy['source'] = f"{source_name}/{subfolder_name}"
                    question_data_copy['source_file'] = str(json_file_path)
                    
                    # Normalize image metadata format
                    # Remove old "images" array field if present
                    if "images" in question_data_copy:
                        del question_data_copy["images"]
                    
                    # Set standardized image fields
                    if image_file:
                        # Get absolute path of source image for deduplication
                        image_file_abs = image_file.resolve()
                        
                        # Check if this image has already been copied
                        if image_file_abs in image_mapping:
                            # Reuse the existing image file
                            existing_file_id, existing_ext = image_mapping[image_file_abs]
                            question_data_copy['has_image'] = True
                            question_data_copy['image'] = f"imgs/{existing_file_id}{existing_ext}"
                            
                            print(f"Processed: {json_file_path.name} (Q{question_data.get('question', '?')}) -> {file_id}.txt, {file_id}.json, reusing image {existing_file_id}{existing_ext}")
                        else:
                            # Copy image with same file_id as the text and json files
                            # Keep original extension
                            image_ext = image_file.suffix
                            image_filename = f"{file_id}{image_ext}"
                            image_dest_path = imgs_dir / image_filename
                            shutil.copy2(image_file, image_dest_path)
                            
                            # Track this image to avoid future duplicates
                            image_mapping[image_file_abs] = (file_id, image_ext)
                            
                            # Set standardized fields pointing to dataset/imgs
                            question_data_copy['has_image'] = True
                            question_data_copy['image'] = f"imgs/{file_id}{image_ext}"
                            
                            print(f"Processed: {json_file_path.name} (Q{question_data.get('question', '?')}) -> {file_id}.txt, {file_id}.json, {file_id}{image_ext}")
                    else:
                        # No image found
                        question_data_copy['has_image'] = False
                        question_data_copy['image'] = None
                        
                        print(f"Processed: {json_file_path.name} (Q{question_data.get('question', '?')}) -> {file_id}.txt, {file_id}.json (no image)")
                    
                    # Save JSON file to metadata/ folder with normalized image fields
                    json_filename = f"{file_id}.json"
                    json_path = metadata_dir / json_filename
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(question_data_copy, f, indent=2, ensure_ascii=False)
                    
                    processed_files.append(str(json_file_path))
                    processed_metadata_files.append(str(json_path))
                
            except Exception as e:
                print(f"  Error processing {json_file_path}: {str(e)}")
                skipped_files.append(str(json_file_path))
                continue

    end_time = datetime.now()

    # Collect statistics
    stats = collect_statistics_from_metadata(processed_metadata_files)

    # Calculate version once for both files
    if version is None:
        if previous_version is not None:
            version = previous_version + REPORT_CONFIG['version_increment']
        else:
            version = REPORT_CONFIG['default_version']

    # Generate and write README.md
    report_content = generate_report(
        start_time, end_time, stats, dataset_dir, version)
    readme_file = dataset_path / REPORT_CONFIG['readme_filename']
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(report_content)

    # Generate and write metadata.json
    metadata = generate_metadata(
        start_time, end_time, stats, dataset_dir, version)
    metadata_file = dataset_path / REPORT_CONFIG['metadata_filename']
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"Processing complete!")
    print(f"{'='*60}")
    print(f"Processed {len(set(processed_files))} source file(s)")
    print(f"Created {stats['total_questions']} question(s)")
    print(f"Skipped {len(skipped_files)} file(s)")
    print(f"Output directories:")
    print(f"  - Text files: {data_dir}")
    print(f"  - JSON metadata: {metadata_dir}")
    print(f"  - Images: {imgs_dir}")
    print(f"Duration: {(end_time - start_time).total_seconds():.2f} seconds")
    print(f"Reports generated:")
    print(f"  - README: {readme_file}")
    print(f"  - Metadata: {metadata_file}")


if __name__ == "__main__":
    main()
