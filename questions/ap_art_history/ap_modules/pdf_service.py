"""
PDF Service Module

This module provides PDF processing functionality for AP Art History exams,
including:
- Converting PDF pages to PNG images
- Extracting embedded images from PDFs
- Extracting text and converting to HTML format
"""

from pathlib import Path
from typing import List, Optional
import sys


class PDFService:
    """Service for handling PDF operations using PyMuPDF."""
    
    def __init__(self):
        """Initialize PDF service and check for PyMuPDF dependency."""
        try:
            import fitz  # PyMuPDF
            self.fitz = fitz
        except ImportError:
            raise ImportError(
                "PyMuPDF is required for PDF operations. "
                "Install with: pip install PyMuPDF"
            )
    
    def convert_pdf_to_images(
        self,
        pdf_path: Path,
        output_dir: Path,
        dpi: int = 300,
        start_page: Optional[int] = None,
        end_page: Optional[int] = None
    ) -> List[Path]:
        """
        Convert PDF pages to PNG images.
        
        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory to save images
            dpi: DPI resolution for images (default: 300)
            start_page: First page to extract (1-indexed, None = start from beginning)
            end_page: Last page to extract (1-indexed, None = extract until end)
            
        Returns:
            List of paths to created images
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Converting PDF to images: {pdf_path}")
        doc = self.fitz.open(pdf_path)
        
        total_pages = len(doc)
        print(f"PDF has {total_pages} pages")
        
        # Determine page range
        start_idx = (start_page - 1) if start_page else 0
        end_idx = end_page if end_page else total_pages
        
        # Validate range
        start_idx = max(0, start_idx)
        end_idx = min(total_pages, end_idx)
        
        print(f"Extracting pages {start_idx + 1} to {end_idx} at {dpi} DPI...")
        
        # Calculate zoom factor for DPI (PyMuPDF default is 72 DPI)
        zoom = dpi / 72
        mat = self.fitz.Matrix(zoom, zoom)
        
        image_paths = []
        for page_num in range(start_idx, end_idx):
            page = doc[page_num]
            
            # Render page to pixmap
            pix = page.get_pixmap(matrix=mat)
            
            # Save as PNG
            image_path = output_dir / f"{page_num + 1}.png"
            pix.save(str(image_path))
            image_paths.append(image_path)
            print(f"  ✓ Saved page {page_num + 1} → {image_path.name}")
        
        doc.close()
        print(f"✓ Converted {len(image_paths)} pages to images at {dpi} DPI")
        return image_paths
    
    def extract_images_from_pdf(self, pdf_path: Path, output_dir: Path) -> List[Path]:
        """
        Extract embedded images from PDF pages and save them to output directory.
        
        This extracts the actual artwork images embedded in the PDF pages,
        not the page renders themselves.
        
        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory to save extracted images (e.g., raw/{year}/imgs/)
            
        Returns:
            List of paths to extracted image files
        """
        print(f"Extracting images from PDF: {pdf_path}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        doc = self.fitz.open(pdf_path)
        extracted_images = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                xref = img[0]  # Image reference number
                
                # Extract image
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                
                # Save image with descriptive name
                image_filename = f"page_{page_num + 1}_img_{img_index + 1}.{image_ext}"
                image_path = output_dir / image_filename
                
                with open(image_path, "wb") as img_file:
                    img_file.write(image_bytes)
                
                extracted_images.append(image_path)
                print(f"  ✓ Extracted {image_filename}")
        
        doc.close()
        print(f"✓ Extracted {len(extracted_images)} images from PDF")
        return extracted_images
    
    def extract_text_and_images_to_html(
        self,
        pdf_path: Path,
        html_dir: Path,
        imgs_dir: Path
    ) -> int:
        """
        Extract text and images from PDF and save as HTML pages.
        
        Each PDF page is converted to an HTML file with:
        - Text content wrapped in <p> tags
        - Embedded images extracted and referenced via <img> tags
        
        Args:
            pdf_path: Path to the PDF file
            html_dir: Directory to save HTML files
            imgs_dir: Directory to save extracted images
            
        Returns:
            Number of pages processed
        """
        html_dir.mkdir(parents=True, exist_ok=True)
        imgs_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Extracting text and images from PDF: {pdf_path}")
        doc = self.fitz.open(pdf_path)
        
        page_count = len(doc)
        for page_num in range(page_count):
            page = doc[page_num]
            page_html = "<html><head><meta charset='utf-8'></head><body>\n"
            
            # Extract text
            text = page.get_text("text")
            # Convert text to HTML paragraphs
            for line in text.split('\n'):
                if line.strip():
                    page_html += f"<p>{line}</p>\n"
            
            # Extract images
            image_list = page.get_images()
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                
                # Save image
                img_filename = f"page_{page_num + 1}_img_{img_index + 1}.{image_ext}"
                img_path = imgs_dir / img_filename
                img_path.write_bytes(image_bytes)
                
                # Add image tag to HTML
                page_html += f'<img src="../imgs/{img_filename}" alt="Image {img_index + 1}">\n'
            
            page_html += "</body></html>"
            
            # Save HTML page
            html_path = html_dir / f"{page_num + 1}.html"
            html_path.write_text(page_html, encoding='utf-8')
            
            print(f"  ✓ Processed page {page_num + 1}")
        
        doc.close()
        print(f"✓ Extraction complete. Processed {page_count} pages")
        print(f"  HTML files: {html_dir}")
        print(f"  Images: {imgs_dir}")
        return page_count
    
    def extract_text_to_html(self, pdf_path: Path, html_dir: Path) -> int:
        """
        Extract only text from PDF and save as HTML pages (no images).
        
        This is used when we only need text labels for detection,
        and images will be extracted separately from screenshots.
        
        Args:
            pdf_path: Path to the PDF file
            html_dir: Directory to save HTML files
            
        Returns:
            Number of pages processed
        """
        html_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Extracting text from PDF: {pdf_path}")
        doc = self.fitz.open(pdf_path)
        
        page_count = len(doc)
        for page_num in range(page_count):
            page = doc[page_num]
            page_html = "<html><head><meta charset='utf-8'></head><body>\n"
            
            # Extract only text (no images)
            text = page.get_text("text")
            # Convert text to HTML paragraphs
            for line in text.split('\n'):
                if line.strip():
                    page_html += f"<p>{line}</p>\n"
            
            page_html += "</body></html>"
            
            # Save HTML page
            html_path = html_dir / f"{page_num + 1}.html"
            html_path.write_text(page_html, encoding='utf-8')
            
            if page_num % 5 == 0:  # Progress update every 5 pages
                print(f"  Processed {page_num + 1}/{page_count} pages")
        
        doc.close()
        print(f"✓ Text extraction complete. Processed {page_count} pages")
        print(f"  HTML files: {html_dir}")
        return page_count
