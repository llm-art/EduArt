"""
Image Processor for AP Art History

This module handles extraction and combination of artwork images from PDFs.
Artwork images are shown on separate pages (e.g., "QUESTIONS 1-7: LEFT IMAGE")
and need to be combined side-by-side.
"""

from pathlib import Path
from typing import Dict, List, Tuple, Optional
import re

try:
    from PIL import Image
except ImportError:
    Image = None


def extract_artwork_images_with_labels(base_dir: Path, exercise: str) -> Dict[str, Dict]:
    """
    Extract artwork images from PDF and identify which questions they relate to.
    
    Args:
        base_dir: Base directory path
        exercise: Exercise identifier (e.g., "2010")
        
    Returns:
        Dictionary mapping question ranges to image information:
        {
            "1-7": {
                "left": "path/to/left_image.jpg",
                "right": "path/to/right_image.jpg",
                "combined": "path/to/combined_image.jpg",
                "question_page": 2
            }
        }
    """
    from .pdf_service import PDFService
    
    pdf_dir = base_dir / "raw" / exercise / "pdf"
    html_dir = base_dir / "raw" / exercise / "html"
    screenshot_dir = base_dir / "raw" / exercise / "screenshot"
    imgs_output_dir = base_dir / "structured" / exercise / "imgs"
    imgs_output_dir.mkdir(parents=True, exist_ok=True)
    
    # Scan HTML files to find artwork image pages and END OF PART pages
    artwork_pages = {}  # {page_num: {"range": "1-7", "position": "LEFT"}}
    end_of_part_pages = set()  # Pages with "END OF PART" text
    
    for html_file in sorted(html_dir.glob("*.html")):
        page_num = int(html_file.stem)
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for END OF PART marker
        if re.search(r'END OF PART', content, re.IGNORECASE):
            end_of_part_pages.add(page_num)
            print(f"  Detected END OF PART on page {page_num}")
        
        # Look for patterns:
        # 1. "QUESTIONS 1-7: LEFT IMAGE" or "RIGHT IMAGE" (2010 format with LEFT/RIGHT)
        # 2. "QUESTIONS 1-8: IMAGE" (2011 format, single image)
        
        # Try pattern with LEFT/RIGHT first
        match = re.search(r'QUESTIONS?\s+(\d+)-(\d+):\s+(LEFT|RIGHT)\s+IMAGE', content, re.IGNORECASE)
        if match:
            start_q, end_q, position = match.groups()
            q_range = f"{start_q}-{end_q}"
            artwork_pages[page_num] = {
                "range": q_range,
                "position": position.upper(),
                "start_q": int(start_q),
                "end_q": int(end_q)
            }
            print(f"  Found {position} image for questions {q_range} on page {page_num}")
        else:
            # Try pattern without LEFT/RIGHT (single image)
            match = re.search(r'QUESTIONS?\s+(\d+)-(\d+):\s+IMAGE', content, re.IGNORECASE)
            if match:
                start_q, end_q = match.groups()
                q_range = f"{start_q}-{end_q}"
                artwork_pages[page_num] = {
                    "range": q_range,
                    "position": "SINGLE",  # Mark as single image (not left/right pair)
                    "start_q": int(start_q),
                    "end_q": int(end_q)
                }
                print(f"  Found single image for questions {q_range} on page {page_num}")
    
    if not artwork_pages:
        print("  No artwork image pages found")
        return {}
    
    # Group by question range
    grouped_images = {}  # {range: {"left": page, "right": page, "single": page}}
    for page_num, info in artwork_pages.items():
        q_range = info["range"]
        position = info["position"]
        
        if q_range not in grouped_images:
            grouped_images[q_range] = {"start_q": info["start_q"], "end_q": info["end_q"]}
        
        grouped_images[q_range][position.lower()] = page_num
    
    # Extract and combine images from screenshots
    result = {}
    
    # Sort by question range to process in order
    sorted_ranges = sorted(grouped_images.items(), key=lambda x: x[1]['start_q'])
    
    # Block numbering starts at 1
    block_num = 1
    
    for q_range, info in sorted_ranges:
        left_page = info.get("left")
        right_page = info.get("right")
        single_page = info.get("single")
        
        # Determine question page number (where the questions are, before artwork pages)
        if single_page:
            question_page = single_page - 1
        elif left_page:
            question_page = left_page - 1
        elif right_page:
            question_page = right_page - 1
        else:
            continue
        
        # Final output path uses block number (sequential: 1, 2, 3, ...)
        final_output_path = imgs_output_dir / f"{block_num}.jpg"
        
        images_to_combine = []
        
        # Handle single image (no left/right pair)
        if single_page:
            # Extract artwork from screenshot and save to final location
            screenshot_path = screenshot_dir / f"{single_page}.png"
            if screenshot_path.exists():
                # Pass END OF PART info to cropping function
                is_end_of_part = single_page in end_of_part_pages
                cropped = crop_artwork_from_screenshot(screenshot_path, final_output_path, 
                                                      is_end_of_part_page=is_end_of_part)
                
                if cropped:
                    print(f"  ✓ Block {block_num}: Questions {q_range} → {final_output_path.name}")
                    
                    result[q_range] = {
                        "combined": str(cropped),
                        "question_page": question_page,
                        "block_num": block_num,
                        "start_q": info["start_q"],
                        "end_q": info["end_q"]
                    }
                    block_num += 1
            continue
        
        # Extract left image from screenshot (temporary)
        if left_page:
            screenshot_path = screenshot_dir / f"{left_page}.png"
            if screenshot_path.exists():
                is_end_of_part = left_page in end_of_part_pages
                left_cropped = crop_artwork_from_screenshot(screenshot_path, None,
                                                           is_end_of_part_page=is_end_of_part)
                if left_cropped:
                    images_to_combine.append(left_cropped)
        
        # Extract right image from screenshot (temporary)
        if right_page:
            screenshot_path = screenshot_dir / f"{right_page}.png"
            if screenshot_path.exists():
                is_end_of_part = right_page in end_of_part_pages
                right_cropped = crop_artwork_from_screenshot(screenshot_path, None,
                                                            is_end_of_part_page=is_end_of_part)
                if right_cropped:
                    images_to_combine.append(right_cropped)
        
        # Combine images side by side (for left/right pairs)
        if images_to_combine:
            combined = combine_images_side_by_side(images_to_combine, final_output_path)
            
            if combined:
                print(f"  ✓ Block {block_num}: Questions {q_range} (left+right combined) → {final_output_path.name}")
                
                result[q_range] = {
                    "combined": str(combined),
                    "question_page": question_page,
                    "block_num": block_num,
                    "start_q": info["start_q"],
                    "end_q": info["end_q"]
                }
                block_num += 1
    
    return result


def combine_images_side_by_side(images_input: List, output_path: Path) -> Optional[Path]:
    """
    Combine multiple images side by side with padding, vertical centering, and labels.
    
    Args:
        images_input: List of PIL Image objects or Path objects to image files
        output_path: Path to save combined image
        
    Returns:
        Path to combined image or None if failed
    """
    if not Image:
        print("  ⚠️  PIL/Pillow not installed, cannot combine images")
        return None
    
    if not images_input:
        return None
    
    try:
        from PIL import ImageDraw, ImageFont
        
        # Open images (or use directly if already Image objects)
        images = []
        for img_input in images_input:
            if hasattr(img_input, 'size') and hasattr(img_input, 'mode'):  # PIL Image
                images.append(img_input)
            else:  # Path
                images.append(Image.open(img_input))
        
        # Get dimensions
        widths, heights = zip(*(img.size for img in images))
        
        # Configuration
        padding = 40  # Padding between images
        top_margin = 60  # Space for labels above images
        bottom_margin = 20
        side_margin = 20
        label_height = 40  # Height for label text
        
        # Calculate combined dimensions
        max_height = max(heights)
        total_width = sum(widths) + (len(images) - 1) * padding + 2 * side_margin
        total_height = max_height + top_margin + bottom_margin
        
        # Create new image with white background
        combined = Image.new('RGB', (total_width, total_height), (255, 255, 255))
        draw = ImageDraw.Draw(combined)
        
        # Try to use a nice font, fallback to default
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        except:
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
            except:
                font = ImageFont.load_default()
        
        # Labels
        labels = ["LEFT", "RIGHT"]
        
        # Paste images side by side with centering
        x_offset = side_margin
        for idx, img in enumerate(images):
            # Calculate vertical offset to center image
            y_offset = top_margin + (max_height - img.height) // 2
            
            # Draw label above image
            label = labels[idx] if idx < len(labels) else f"IMAGE {idx + 1}"
            
            # Calculate label position (centered above image)
            bbox = draw.textbbox((0, 0), label, font=font)
            label_width = bbox[2] - bbox[0]
            label_x = x_offset + (img.width - label_width) // 2
            label_y = top_margin - label_height
            
            # Draw label
            draw.text((label_x, label_y), label, fill=(0, 0, 0), font=font)
            
            # Paste image
            combined.paste(img, (x_offset, y_offset))
            x_offset += img.width + padding
        
        # Save
        combined.save(output_path, 'JPEG', quality=95)
        
        # Close images
        for img in images:
            img.close()
        
        return output_path
        
    except Exception as e:
        print(f"  ❌ Error combining images: {e}")
        import traceback
        traceback.print_exc()
        return None


def crop_artwork_from_screenshot(screenshot_path: Path, output_path: Optional[Path] = None,
                                  is_end_of_part_page: bool = False):
    """
    Crop artwork from a screenshot using intelligent content detection.
    
    This detects the actual artwork boundaries by finding non-white content
    and automatically crops to the content area with minimal margins.
    
    Args:
        screenshot_path: Path to screenshot PNG file
        output_path: Path to save cropped artwork (if None, returns PIL Image object)
        is_end_of_part_page: Whether this page contains "END OF PART" text (enables aggressive cropping)
        
    Returns:
        Path to cropped image if output_path provided, or PIL Image object, or None if failed
    """
    if not Image:
        print("  ⚠️  PIL/Pillow not installed, cannot crop images")
        return None
    
    try:
        from PIL import ImageOps, ImageChops
        
        # Open screenshot
        img = Image.open(screenshot_path)
        width, height = img.size
        
        # Step 1: Determine initial crop based on whether this is an END OF PART page
        # END OF PART pages have answer keys at the bottom that need aggressive cropping
        if is_end_of_part_page:
            initial_bottom = int(height * 0.63)  # Very aggressive crop for END OF PART
            page_num = int(screenshot_path.stem)
            print(f"  END OF PART page {page_num}: using aggressive bottom crop at 63%")
        else:
            initial_bottom = int(height * 0.88)  # Standard crop
        
        # Step 2: Do aggressive initial crop to remove obvious headers/footers
        initial_top = int(height * 0.15)    # Remove top 15% (header area)
        initial_left = int(width * 0.06)     # Remove 6% from sides
        initial_right = int(width * 0.94)
        
        # Crop to potential content area
        rough_crop = img.crop((initial_left, initial_top, initial_right, initial_bottom))
        
        # Step 3: Now do content-aware detection on the remaining area
        gray = rough_crop.convert('L')
        
        # Use more aggressive threshold to focus on actual image content (not text)
        threshold = 245  # Higher = more selective
        binary = gray.point(lambda x: 0 if x < threshold else 255, '1')
        
        # Invert to get content as white
        inverted = ImageOps.invert(binary.convert('L'))
        
        # Get bounding box of content
        bbox = inverted.getbbox()
        
        if bbox:
            rel_left, rel_top, rel_right, rel_bottom = bbox
            
            # Crop from the rough crop
            content_crop = rough_crop.crop((rel_left, rel_top, rel_right, rel_bottom))
            
            # Step 4: Add white padding around the cropped content
            padding = int(max(content_crop.width, content_crop.height) * 0.03)  # 3% padding
            
            # Create new image with white background and padding
            padded_width = content_crop.width + 2 * padding
            padded_height = content_crop.height + 2 * padding
            cropped = Image.new('RGB', (padded_width, padded_height), (255, 255, 255))
            
            # Paste content in center
            cropped.paste(content_crop, (padding, padding))
            content_crop.close()
        else:
            # If no content detected, use rough crop with padding
            padding = int(max(rough_crop.width, rough_crop.height) * 0.03)
            padded_width = rough_crop.width + 2 * padding
            padded_height = rough_crop.height + 2 * padding
            cropped = Image.new('RGB', (padded_width, padded_height), (255, 255, 255))
            cropped.paste(rough_crop, (padding, padding))
        
        rough_crop.close()
        img.close()
        
        # If output path specified, save and return path
        if output_path:
            cropped.save(output_path, 'JPEG', quality=95)
            cropped.close()
            return output_path
        
        # Otherwise return the Image object for further processing
        return cropped
        
    except Exception as e:
        print(f"  ❌ Error cropping screenshot: {e}")
        import traceback
        traceback.print_exc()
        return None


def find_all_page_images(imgs_dir: Path, page_num: int) -> List[Path]:
    """
    Find all extracted images for a given page number.
    
    Images are typically named: page_{page_num}_img_1.{ext}, page_{page_num}_img_2.{ext}, etc.
    
    Args:
        imgs_dir: Directory containing extracted images
        page_num: Page number
        
    Returns:
        List of image paths, sorted by image number
    """
    images = []
    
    # Look for all possible extensions
    for ext in ['jpeg', 'jpg', 'png']:
        img_index = 1
        while True:
            img_path = imgs_dir / f"page_{page_num}_img_{img_index}.{ext}"
            if img_path.exists():
                images.append(img_path)
                img_index += 1
            else:
                break
    
    # Sort by image index (extracted from filename)
    images.sort(key=lambda p: int(p.stem.split('_')[-1]))
    return images


def combine_images_vertically(image_paths: List[Path], output_path: Path) -> Optional[Path]:
    """
    Combine multiple image tiles vertically (top to bottom).
    
    This is used when a large artwork is split into multiple horizontal strips.
    The images are stacked from top to bottom in order.
    
    Args:
        image_paths: List of image file paths (in order from top to bottom)
        output_path: Path to save combined image
        
    Returns:
        Path to combined image or None if failed
    """
    if not Image:
        print("  ⚠️  PIL/Pillow not installed, cannot combine images")
        return None
    
    if not image_paths:
        return None
    
    try:
        # Open all images
        images = [Image.open(img_path) for img_path in image_paths]
        
        # Get dimensions
        widths, heights = zip(*(img.size for img in images))
        
        # Calculate combined dimensions
        # Width = maximum width across all tiles
        # Height = sum of all heights
        max_width = max(widths)
        total_height = sum(heights)
        
        # Create new image with white background
        combined = Image.new('RGB', (max_width, total_height), (255, 255, 255))
        
        # Paste images vertically (top to bottom)
        y_offset = 0
        for img in images:
            # Center horizontally if image is narrower
            x_offset = (max_width - img.width) // 2
            combined.paste(img, (x_offset, y_offset))
            y_offset += img.height
        
        # Save
        combined.save(output_path, 'JPEG', quality=95)
        
        # Close images
        for img in images:
            img.close()
        
        return output_path
        
    except Exception as e:
        print(f"  ❌ Error combining images vertically: {e}")
        import traceback
        traceback.print_exc()
        return None
