#!/usr/bin/env python3
"""
Minimal script to resize images in all exercise raw directories to 720p (1280x720).
Processes all data/{exercise_num}/raw directories and replaces original images.
"""

import os
from PIL import Image
import glob

def resize_to_720p(image_path):
    """Resize image to 720p (1280x720) maintaining aspect ratio."""
    try:
        with Image.open(image_path) as img:
            # Target resolution for 720p
            target_width = 1280
            target_height = 720
            
            # Calculate aspect ratios
            img_ratio = img.width / img.height
            target_ratio = target_width / target_height
            
            # Resize maintaining aspect ratio
            if img_ratio > target_ratio:
                # Image is wider, fit to width
                new_width = target_width
                new_height = int(target_width / img_ratio)
            else:
                # Image is taller, fit to height
                new_height = target_height
                new_width = int(target_height * img_ratio)
            
            # Resize the image
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Save back to the same file
            resized_img.save(image_path, optimize=True, quality=95)
            print(f"Resized {os.path.basename(image_path)}: {img.width}x{img.height} -> {new_width}x{new_height}")
            
    except Exception as e:
        print(f"Error processing {image_path}: {e}")

def main():
    """Main function to resize all images in all exercise raw directories."""
    # Base path to the data directory
    base_dir = "/Users/gspinaci/projects/llm-art/datasets/questions/data"
    
    # Find all exercise directories (numeric directories)
    exercise_dirs = []
    for item in os.listdir(base_dir):
        item_path = os.path.join(base_dir, item)
        if os.path.isdir(item_path) and item.isdigit():
            raw_dir = os.path.join(item_path, "raw")
            if os.path.exists(raw_dir):
                exercise_dirs.append((item, raw_dir))
    
    if not exercise_dirs:
        print("No exercise directories with raw folders found.")
        return
    
    print(f"Found {len(exercise_dirs)} exercise directories with raw folders...")
    
    total_images = 0
    
    # Process each exercise directory
    for exercise_num, raw_dir in sorted(exercise_dirs, key=lambda x: int(x[0])):
        print(f"\nProcessing exercise {exercise_num}...")
        
        # Find all PNG images in the directory
        image_pattern = os.path.join(raw_dir, "*.png")
        image_files = glob.glob(image_pattern)
        
        if not image_files:
            print(f"  No PNG images found in exercise {exercise_num}/raw")
            continue
        
        print(f"  Found {len(image_files)} PNG images to resize...")
        
        # Process each image
        for image_path in sorted(image_files):
            resize_to_720p(image_path)
            total_images += 1
    
    print(f"\nResizing complete! Processed {total_images} images across {len(exercise_dirs)} exercise directories.")

if __name__ == "__main__":
    main()