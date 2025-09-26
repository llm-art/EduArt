"""
Content downloading utilities.

This module handles downloading images and other content from URLs.
"""

import aiohttp
import aiofiles
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse


class ContentDownloader:
    """Handles downloading of images and other content."""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def download_image(self, image_url: str, save_path: Path) -> bool:
        """
        Download an image from URL to the specified path.
        
        Args:
            image_url: URL of the image to download
            save_path: Path where to save the image
            
        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"Downloading image: {image_url}")
            
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            async with self.session.get(image_url) as response:
                if response.status == 200:
                    # Ensure directory exists
                    save_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Write image data to file
                    async with aiofiles.open(save_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
                    
                    print(f"✓ Image downloaded: {save_path.name}")
                    return True
                else:
                    print(f"❌ Failed to download image: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error downloading image {image_url}: {e}")
            return False
    
    async def download_multiple_images(
        self, 
        image_info_list: List[Dict[str, Any]], 
        question_number: int,
        save_dir: Path
    ) -> List[Dict[str, Any]]:
        """
        Download multiple images for a question.
        
        Args:
            image_info_list: List of image info dictionaries
            question_number: Question number for naming
            save_dir: Directory to save images
            
        Returns:
            List of successfully downloaded image info
        """
        downloaded_images = []
        
        for i, image_info in enumerate(image_info_list):
            try:
                image_url = image_info['src']
                
                # Determine file extension from URL
                extension = self._get_file_extension(image_url)
                
                # Create filename: {question_number}.{extension} or {question_number}_{index}.{extension}
                if i == 0:
                    filename = f"{question_number}.{extension}"
                else:
                    filename = f"{question_number}_{i+1}.{extension}"
                
                save_path = save_dir / filename
                
                # Download the image
                success = await self.download_image(image_url, save_path)
                
                if success:
                    downloaded_images.append({
                        'filename': filename,
                        'path': save_path,
                        'url': image_url,
                        'alt': image_info.get('alt', ''),
                        'index': i
                    })
                    
            except Exception as e:
                print(f"❌ Error processing image {i+1} for question {question_number}: {e}")
                continue
        
        print(f"✓ Downloaded {len(downloaded_images)} images for question {question_number}")
        return downloaded_images
    
    def _get_file_extension(self, url: str) -> str:
        """
        Get file extension from URL.
        
        Args:
            url: Image URL
            
        Returns:
            File extension (default: 'jpg')
        """
        try:
            parsed_url = urlparse(url)
            path_parts = parsed_url.path.split('.')
            
            if len(path_parts) > 1:
                extension = path_parts[-1].lower()
                # Validate extension
                valid_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg']
                if extension in valid_extensions:
                    return extension
            
            # Default fallback
            return 'jpg'
            
        except Exception:
            return 'jpg'
    
    def normalize_image_url(self, src: str, base_url: str) -> str:
        """
        Normalize an image URL to be absolute.
        
        Args:
            src: Image source URL (may be relative)
            base_url: Base URL of the page
            
        Returns:
            Absolute URL
        """
        try:
            # Skip data URLs
            if src.startswith('data:'):
                return src
            
            # Handle protocol-relative URLs
            if src.startswith('//'):
                return 'https:' + src
            
            # Handle absolute URLs
            if src.startswith('http'):
                return src
            
            # Handle relative URLs
            if src.startswith('/'):
                return urljoin(base_url, src)
            
            # Handle relative paths
            return urljoin(base_url, src)
            
        except Exception as e:
            print(f"Error normalizing URL {src}: {e}")
            return src
    
    def should_skip_image(self, src: str, alt: str = "") -> bool:
        """
        Determine if an image should be skipped based on its properties.
        
        Args:
            src: Image source URL
            alt: Alt text
            
        Returns:
            True if image should be skipped
        """
        # Skip data URLs
        if src.startswith('data:'):
            return True
        
        # Skip common UI elements based on URL patterns
        skip_patterns = [
            'icon', 'logo', 'button', 'arrow', 'spinner', 
            'loading', 'placeholder', 'avatar', 'badge'
        ]
        
        src_lower = src.lower()
        alt_lower = alt.lower()
        
        for pattern in skip_patterns:
            if pattern in src_lower or pattern in alt_lower:
                return True
        
        return False
    
    def filter_content_images(self, images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter images to keep only content-related ones.
        
        Args:
            images: List of image info dictionaries
            
        Returns:
            Filtered list of images
        """
        filtered_images = []
        
        for img_info in images:
            src = img_info.get('src', '')
            alt = img_info.get('alt', '')
            
            # Skip if should be filtered out
            if self.should_skip_image(src, alt):
                continue
            
            # Additional filtering based on size if available
            width = img_info.get('width')
            height = img_info.get('height')
            
            if width and height:
                try:
                    w, h = int(width), int(height)
                    # Skip very small images (likely UI elements)
                    if w < 50 or h < 50:
                        continue
                except (ValueError, TypeError):
                    pass
            
            filtered_images.append(img_info)
        
        return filtered_images
    
    async def close(self):
        """Close the HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None