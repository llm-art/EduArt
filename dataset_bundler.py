#!/usr/bin/env python3
"""
Dataset Bundler Script

This script navigates all folders with a subfolder called structured/ in questions/.
Inside each structured folder, it processes all subfolders (e.g., 2010, 1, etc.)
and extracts JSON files to create TXT files of questions, copies JSON files to metadata/,
and copies associated images to imgs/ folder with consistent naming.

The script supports filtering by question type (default: multiple_choice_radio).
Images are automatically optimized for Claude API compliance.
"""

import os
import json
import glob
import shutil
import re
import click
import base64
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from PIL import Image
from typing import Dict, Tuple


# Claude API Image Optimization Configuration
IMAGE_OPTIMIZATION_CONFIG = {
    'enabled': True,  # Set to False to disable optimization
    'max_base64_size': 5 * 1024 * 1024,  # 5 MB hard limit
    'recommended_max_dimension': 1568,  # Recommended max dimension
    'recommended_megapixels': 1.15,  # Recommended megapixels
    'optimal_tokens': 1600,  # Optimal token count
    'quality_start': 90,  # Starting JPEG quality
    'quality_min': 70,  # Minimum JPEG quality
    # Optimal sizes for common aspect ratios (from Claude docs)
    'optimal_sizes': {
        (1, 1): (1092, 1092),    # 1:1
        (3, 4): (951, 1268),     # 3:4
        (4, 3): (1268, 951),     # 4:3
        (2, 3): (896, 1344),     # 2:3
        (3, 2): (1344, 896),     # 3:2
        (9, 16): (819, 1456),    # 9:16
        (16, 9): (1456, 819),    # 16:9
        (1, 2): (784, 1568),     # 1:2
        (2, 1): (1568, 784),     # 2:1
    }
}

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


# Image Optimization Functions
def get_base64_size(image_path: str) -> int:
    """Get the size of the image when base64 encoded (as sent to API)"""
    with open(image_path, 'rb') as f:
        encoded = base64.b64encode(f.read())
        return len(encoded)


def calculate_image_tokens(width: int, height: int) -> int:
    """Calculate approximate tokens: (width * height) / 750"""
    return int((width * height) / 750)


def get_closest_aspect_ratio(width: int, height: int) -> Tuple[int, int]:
    """Find the closest standard aspect ratio"""
    current_ratio = width / height
    
    closest_ratio = None
    min_diff = float('inf')
    
    for ratio_tuple in IMAGE_OPTIMIZATION_CONFIG['optimal_sizes'].keys():
        ratio_value = ratio_tuple[0] / ratio_tuple[1]
        diff = abs(current_ratio - ratio_value)
        if diff < min_diff:
            min_diff = diff
            closest_ratio = ratio_tuple
    
    return closest_ratio


def calculate_optimal_size(width: int, height: int) -> Tuple[int, int]:
    """
    Calculate optimal size based on Claude's recommendations:
    1. Try to match optimal sizes for common aspect ratios
    2. Otherwise, scale to 1.15 megapixels within 1568px
    """
    aspect_ratio = get_closest_aspect_ratio(width, height)
    
    # Check if we're close to a standard aspect ratio (within 5%)
    current_ratio = width / height
    standard_ratio = aspect_ratio[0] / aspect_ratio[1]
    
    if abs(current_ratio - standard_ratio) / standard_ratio < 0.05:
        # Use optimal size for this aspect ratio
        optimal_size = IMAGE_OPTIMIZATION_CONFIG['optimal_sizes'][aspect_ratio]
        return optimal_size
    
    # Otherwise, scale to recommended limits
    current_megapixels = (width * height) / 1_000_000
    recommended_max_dim = IMAGE_OPTIMIZATION_CONFIG['recommended_max_dimension']
    recommended_mp = IMAGE_OPTIMIZATION_CONFIG['recommended_megapixels']
    
    # If already within limits, keep original size
    if (current_megapixels <= recommended_mp and
        width <= recommended_max_dim and
        height <= recommended_max_dim):
        return (width, height)
    
    # Scale down to fit within 1568px and 1.15 megapixels
    scale_for_dimension = min(recommended_max_dim / max(width, height), 1.0)
    scale_for_megapixels = min((recommended_mp * 1_000_000 / (width * height)) ** 0.5, 1.0)
    
    scale = min(scale_for_dimension, scale_for_megapixels)
    
    new_width = int(width * scale)
    new_height = int(height * scale)
    
    return (new_width, new_height)


def optimize_image_for_claude(input_path: str, output_path: str) -> Dict:
    """
    Optimize a single image according to Claude's guidelines.
    Returns dict with optimization statistics.
    """
    if not IMAGE_OPTIMIZATION_CONFIG['enabled']:
        # Just copy the file if optimization is disabled
        shutil.copy2(input_path, output_path)
        return {'optimized': False, 'copied': True}
    
    try:
        # Open image
        img = Image.open(input_path)
        original_width, original_height = img.size
        original_file_size = os.path.getsize(input_path)
        original_base64_size = get_base64_size(input_path)
        original_tokens = calculate_image_tokens(original_width, original_height)
        
        # Calculate optimal size
        new_width, new_height = calculate_optimal_size(original_width, original_height)
        
        # Check if optimization is needed
        max_base64 = IMAGE_OPTIMIZATION_CONFIG['max_base64_size']
        recommended_max_dim = IMAGE_OPTIMIZATION_CONFIG['recommended_max_dimension']
        recommended_mp = IMAGE_OPTIMIZATION_CONFIG['recommended_megapixels']
        
        needs_optimization = (
            original_base64_size > max_base64 or
            original_width > recommended_max_dim or
            original_height > recommended_max_dim or
            (original_width * original_height) / 1_000_000 > recommended_mp
        )
        
        if not needs_optimization:
            # Image is already optimal, just copy it
            shutil.copy2(input_path, output_path)
            return {
                'optimized': False,
                'copied': True,
                'already_optimal': True,
                'original_tokens': original_tokens
            }
        
        # Resize if needed
        if (new_width, new_height) != (original_width, original_height):
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Save with optimization
        quality = IMAGE_OPTIMIZATION_CONFIG['quality_start']
        img.save(output_path, 'JPEG', quality=quality, optimize=True)
        
        # Check if we need to reduce quality further to meet size limit
        quality_min = IMAGE_OPTIMIZATION_CONFIG['quality_min']
        while quality > quality_min:
            current_base64_size = get_base64_size(output_path)
            if current_base64_size <= max_base64:
                break
            quality -= 5
            img.save(output_path, 'JPEG', quality=quality, optimize=True)
        
        # Get final stats
        final_file_size = os.path.getsize(output_path)
        final_base64_size = get_base64_size(output_path)
        final_tokens = calculate_image_tokens(new_width, new_height)
        
        return {
            'optimized': True,
            'copied': False,
            'original': {
                'width': original_width,
                'height': original_height,
                'file_size_mb': round(original_file_size / 1024 / 1024, 2),
                'base64_size_mb': round(original_base64_size / 1024 / 1024, 2),
                'tokens': original_tokens,
            },
            'final': {
                'width': new_width,
                'height': new_height,
                'file_size_mb': round(final_file_size / 1024 / 1024, 2),
                'base64_size_mb': round(final_base64_size / 1024 / 1024, 2),
                'tokens': final_tokens,
                'quality': quality,
            },
            'savings': {
                'tokens_saved': original_tokens - final_tokens,
                'tokens_percent': round((1 - final_tokens / original_tokens) * 100, 1) if original_tokens > 0 else 0,
                'size_saved_mb': round((original_base64_size - final_base64_size) / 1024 / 1024, 2),
            }
        }
    except Exception as e:
        # On error, try to copy the original file
        try:
            shutil.copy2(input_path, output_path)
            return {'optimized': False, 'copied': True, 'error': str(e)}
        except:
            return {'optimized': False, 'copied': False, 'error': str(e)}


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
    
    # Track image optimization statistics
    image_optimization_stats = {
        'total_images': 0,
        'optimized_count': 0,
        'already_optimal_count': 0,
        'reused_count': 0,
        'total_original_tokens': 0,
        'total_final_tokens': 0,
        'total_tokens_saved': 0,
        'optimizations': []
    }
    
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
                            
                            # Track reused image
                            image_optimization_stats['reused_count'] += 1
                            
                            print(f"Processed: {json_file_path.name} (Q{question_data.get('question', '?')}) -> {file_id}.txt, {file_id}.json, reusing image {existing_file_id}{existing_ext}")
                        else:
                            # Optimize and copy image with same file_id as the text and json files
                            # Always save as .jpg after optimization
                            image_ext = ".jpg"
                            image_filename = f"{file_id}{image_ext}"
                            image_dest_path = imgs_dir / image_filename
                            
                            # Optimize image for Claude API
                            optimization_result = optimize_image_for_claude(str(image_file), str(image_dest_path))
                            
                            # Track this image to avoid future duplicates
                            image_mapping[image_file_abs] = (file_id, image_ext)
                            
                            # Set standardized fields pointing to dataset/imgs
                            question_data_copy['has_image'] = True
                            question_data_copy['image'] = f"imgs/{file_id}{image_ext}"
                            
                            # Track image optimization statistics
                            image_optimization_stats['total_images'] += 1
                            
                            # Add optimization info to metadata
                            if optimization_result.get('optimized'):
                                question_data_copy['image_optimization'] = {
                                    'optimized': True,
                                    'original_tokens': optimization_result['original']['tokens'],
                                    'final_tokens': optimization_result['final']['tokens'],
                                    'tokens_saved': optimization_result['savings']['tokens_saved'],
                                    'tokens_saved_percent': optimization_result['savings']['tokens_percent']
                                }
                                
                                # Track optimization stats
                                image_optimization_stats['optimized_count'] += 1
                                image_optimization_stats['total_original_tokens'] += optimization_result['original']['tokens']
                                image_optimization_stats['total_final_tokens'] += optimization_result['final']['tokens']
                                image_optimization_stats['total_tokens_saved'] += optimization_result['savings']['tokens_saved']
                                
                                # Record individual optimization
                                image_optimization_stats['optimizations'].append({
                                    'file_id': file_id,
                                    'source_file': str(image_file),
                                    'original_dimensions': f"{optimization_result['original']['width']}x{optimization_result['original']['height']}",
                                    'final_dimensions': f"{optimization_result['final']['width']}x{optimization_result['final']['height']}",
                                    'original_tokens': optimization_result['original']['tokens'],
                                    'final_tokens': optimization_result['final']['tokens'],
                                    'tokens_saved': optimization_result['savings']['tokens_saved'],
                                    'tokens_saved_percent': optimization_result['savings']['tokens_percent'],
                                    'original_size_mb': optimization_result['original']['base64_size_mb'],
                                    'final_size_mb': optimization_result['final']['base64_size_mb'],
                                    'quality': optimization_result['final']['quality']
                                })
                                
                                opt_info = f" (optimized: {optimization_result['savings']['tokens_percent']:+.0f}% tokens)"
                            elif optimization_result.get('already_optimal'):
                                question_data_copy['image_optimization'] = {
                                    'optimized': False,
                                    'already_optimal': True,
                                    'tokens': optimization_result['original_tokens']
                                }
                                
                                # Track already optimal
                                image_optimization_stats['already_optimal_count'] += 1
                                image_optimization_stats['total_original_tokens'] += optimization_result['original_tokens']
                                image_optimization_stats['total_final_tokens'] += optimization_result['original_tokens']
                                
                                # Add to optimizations list for logging (even though not optimized)
                                # Get image info for already optimal images
                                try:
                                    img = Image.open(str(image_file))
                                    width, height = img.size
                                    file_size = os.path.getsize(str(image_file))
                                    base64_size = get_base64_size(str(image_file))
                                    
                                    image_optimization_stats['optimizations'].append({
                                        'file_id': file_id,
                                        'source_file': str(image_file),
                                        'final_dimensions': f"{width}x{height}",
                                        'final_tokens': optimization_result['original_tokens'],
                                        'final_size_mb': round(base64_size / 1024 / 1024, 2),
                                        'quality': 'original'
                                    })
                                except:
                                    pass
                                
                                opt_info = " (already optimal)"
                            else:
                                opt_info = ""
                            
                            print(f"Processed: {json_file_path.name} (Q{question_data.get('question', '?')}) -> {file_id}.txt, {file_id}.json, {file_id}{image_ext}{opt_info}")
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

    # Generate and write image optimization log as text file
    if image_optimization_stats['total_images'] > 0:
        optimization_log_file = dataset_path / 'image_optimization.log'
        
        with open(optimization_log_file, 'w', encoding='utf-8') as f:
            f.write("IMAGE OPTIMIZATION LOG\n")
            f.write("=" * 110 + "\n")
            f.write(f"Generated: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total images processed: {image_optimization_stats['total_images']}\n")
            f.write(f"Optimized: {image_optimization_stats['optimized_count']} | Already optimal: {image_optimization_stats['already_optimal_count']}\n")
            f.write("=" * 110 + "\n\n")
            
            # Write table header
            f.write(f"{'Filename':<20} {'Dimensions':<18} {'Aspect Ratio':<15} {'MP':<8} {'Base64 Size (MB)':<18} {'Quality':<8}\n")
            f.write("-" * 110 + "\n")
            
            # Collect all image data (both optimized and already optimal)
            all_image_data = []
            
            # Add optimized images
            for opt in image_optimization_stats['optimizations']:
                all_image_data.append({
                    'file_id': opt['file_id'],
                    'dimensions': opt['final_dimensions'],
                    'base64_size': opt['final_size_mb'],
                    'tokens': opt['final_tokens'],
                    'quality': opt.get('quality', 'N/A')
                })
            
            # Sort by file_id
            all_image_data.sort(key=lambda x: x['file_id'])
            
            # Write all image details
            for img_data in all_image_data:
                file_id = img_data['file_id']
                dimensions = img_data['dimensions']
                
                # Calculate aspect ratio from dimensions
                try:
                    width, height = map(int, dimensions.split('x'))
                    aspect_ratio = round(width / height, 2)
                    mp = (width * height) / 1_000_000
                except:
                    aspect_ratio = "N/A"
                    mp = 0.0
                
                base64_size = img_data['base64_size']
                quality = img_data['quality']
                
                f.write(f"{file_id:<20} {dimensions:<18} {str(aspect_ratio):<15} {mp:<8.2f} {base64_size:<18.2f} {str(quality):<8}\n")
            
            f.write("\n" + "=" * 110 + "\n")
            f.write(f"Total: {len(all_image_data)} images\n")

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
    
    # Print image optimization summary
    if image_optimization_stats['total_images'] > 0:
        print(f"\nImage Optimization Summary:")
        print(f"  - Total images processed: {image_optimization_stats['total_images']}")
        print(f"  - Optimized: {image_optimization_stats['optimized_count']}")
        print(f"  - Already optimal: {image_optimization_stats['already_optimal_count']}")
        print(f"  - Reused (duplicates): {image_optimization_stats['reused_count']}")
        if image_optimization_stats['total_tokens_saved'] > 0:
            tokens_saved_pct = round((image_optimization_stats['total_tokens_saved'] / image_optimization_stats['total_original_tokens'] * 100), 1)
            print(f"  - Tokens saved: {image_optimization_stats['total_tokens_saved']:,} ({tokens_saved_pct}%)")
            original_cost = image_optimization_stats['total_original_tokens'] / image_optimization_stats['total_images'] * 1000 * 3.0 / 1_000_000
            final_cost = image_optimization_stats['total_final_tokens'] / image_optimization_stats['total_images'] * 1000 * 3.0 / 1_000_000
            print(f"  - Cost savings: ${original_cost - final_cost:.2f} per 1K images")
        if image_optimization_stats['optimizations']:
            optimization_log_file = dataset_path / 'image_optimization.log'
            print(f"  - Optimization log: {optimization_log_file}")


if __name__ == "__main__":
    main()
