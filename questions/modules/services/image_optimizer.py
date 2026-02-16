"""Image optimization service for Claude API compliance."""

import os
import shutil
import base64
from typing import Dict, Tuple
from PIL import Image


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
  scale_for_megapixels = min(
    (recommended_mp * 1_000_000 / (width * height)) ** 0.5, 1.0)

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
    new_width, new_height = calculate_optimal_size(
      original_width, original_height)

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
