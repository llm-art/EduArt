"""Dataset report and metadata generation for bundled datasets."""

import os
import re
import glob
import json
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
  categorization_fields = ['art_historical', 'cultural_tradition', 'disciplinary_domain', 'epistemic_level', 'language']
  stats = {
      'sources': set(),
      'total_questions': 0,
      'questions_by_type': defaultdict(int),
      'questions_with_images': 0,
      'categorization': {field: defaultdict(int) for field in categorization_fields},
      # Cross-tabulation: category_value × question_type
      'categorization_by_type': {field: defaultdict(lambda: defaultdict(int)) for field in categorization_fields},
      # has_image × question_type
      'images_by_type': defaultdict(lambda: {'with_image': 0, 'without_image': 0}),
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

        # Count questions by type, images, and categorization
        for question in questions_to_process:
          question_type = question.get("type", "unknown")
          stats['questions_by_type'][question_type] += 1
          stats['total_questions'] += 1

          # Count questions with images
          has_image = question.get("has_image", False)
          if has_image:
            stats['questions_with_images'] += 1
            stats['images_by_type'][question_type]['with_image'] += 1
          else:
            stats['images_by_type'][question_type]['without_image'] += 1

          # Count categorization fields
          for field in categorization_fields:
            value = question.get(field)
            if value is not None:
              if isinstance(value, list):
                for item in value:
                  stats['categorization'][field][item] += 1
                  stats['categorization_by_type'][field][item][question_type] += 1
              else:
                stats['categorization'][field][value] += 1
                stats['categorization_by_type'][field][value][question_type] += 1

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


def generate_report(start_time, end_time, stats, dataset_dir, version, first_question_by_type=None):
  """Generate the dataset bundle report in markdown format."""
  if first_question_by_type is None:
    first_question_by_type = {}
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

**Questions with Images:** {stats['questions_with_images']}

**Total Cost:** ${total_cost:.4f}

## Questions by Type

"""

  # Add questions by type section with example screenshots
  for question_type, count in sorted(stats['questions_by_type'].items()):
    report_content += f"- **{question_type}:** {count}\n"

    # Add example screenshot if available
    if question_type in first_question_by_type:
      example_info = first_question_by_type[question_type]
      report_content += f"  - Example: ![{question_type} example]({example_info['screenshot_path']}) (from {example_info['source']}, exercise {example_info['exercise']}, question {example_info['question']})\n"

  # Add categorization statistics section with cross-tabulation by question type
  if any(stats['categorization'][field] for field in stats['categorization']):
    report_content += f"""
## Categorization Statistics

"""
    field_labels = {
        'art_historical': 'Art Historical',
        'cultural_tradition': 'Cultural Tradition',
        'disciplinary_domain': 'Disciplinary Domain',
        'epistemic_level': 'Epistemic Level',
        'language': 'Language',
    }

    # Get all question types present in the dataset
    all_question_types = sorted(stats['questions_by_type'].keys())

    for field in ['art_historical', 'cultural_tradition', 'disciplinary_domain', 'epistemic_level', 'language']:
      if field in stats['categorization'] and stats['categorization'][field]:
        label = field_labels.get(field, field)
        report_content += f"### {label}\n\n"

        # Build table header
        header = "| Value |"
        separator = "|-------|"
        for qtype in all_question_types:
          header += f" {qtype} |"
          separator += "-------|"
        header += " Total |\n"
        separator += "-------|\n"

        report_content += header
        report_content += separator

        # Get all values for this field, sorted by total count (descending)
        values_with_counts = [(value, count) for value, count in stats['categorization'][field].items()]
        values_with_counts.sort(key=lambda x: -x[1])

        # Build table rows
        for value, total_count in values_with_counts:
          row = f"| {value} |"
          for qtype in all_question_types:
            count = stats['categorization_by_type'][field][value][qtype]
            row += f" {count} |"
          row += f" {total_count} |\n"
          report_content += row

        report_content += "\n"

    # Add image statistics table
    if stats['images_by_type']:
      report_content += f"### With/Without Image\n\n"

      # Build table header
      header = "| Has Image |"
      separator = "|-----------|"
      for qtype in all_question_types:
        header += f" {qtype} |"
        separator += "-------|"
      header += " Total |\n"
      separator += "-------|\n"

      report_content += header
      report_content += separator

      # Row for "With Image"
      row_with = "| Yes |"
      total_with = 0
      for qtype in all_question_types:
        count = stats['images_by_type'][qtype]['with_image']
        row_with += f" {count} |"
        total_with += count
      row_with += f" {total_with} |\n"
      report_content += row_with

      # Row for "Without Image"
      row_without = "| No |"
      total_without = 0
      for qtype in all_question_types:
        count = stats['images_by_type'][qtype]['without_image']
        row_without += f" {count} |"
        total_without += count
      row_without += f" {total_without} |\n"
      report_content += row_without

      report_content += "\n"

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
      "questions_with_images": stats['questions_with_images'],
      "questions_by_type": dict(stats['questions_by_type']),
      "categorization": {field: dict(counts) for field, counts in stats['categorization'].items() if counts},
      "categorization_by_type": {
          field: {value: dict(type_counts) for value, type_counts in value_counts.items()}
          for field, value_counts in stats['categorization_by_type'].items()
          if value_counts
      },
      "images_by_type": {qtype: dict(counts) for qtype, counts in stats['images_by_type'].items()},
      "sources": sorted(list(stats['sources'])),
      "ai_calls": ai_calls_list,
      "last_updated": end_time.strftime('%Y-%m-%d %H:%M:%S')
  }

  return metadata
