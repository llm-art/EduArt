"""OCR service for text extraction from images."""

import json
from pathlib import Path
from typing import Optional, Dict, Any
from paddleocr import PaddleOCR

from ..core.exceptions import OCRError, FileOperationError
from ..core.types import ProcessingResult
from ..config import Config


class OCRService:
    """Service for OCR text extraction using PaddleOCR."""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize OCR service with configuration."""
        self.config = config or Config
        self.ocr_model = None
        self._is_loaded = False
    
    def load_model(self) -> None:
        """Load PaddleOCR model for Italian text recognition."""
        if self._is_loaded:
            return
            
        try:
            print("Loading PaddleOCR model...")
            
            self.ocr_model = PaddleOCR(
                lang=self.config.OCR_LANG,
                text_detection_model_name=self.config.TEXT_DETECTION_MODEL,
                text_recognition_model_name=self.config.TEXT_RECOGNITION_MODEL,
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
            )
            
            self._is_loaded = True
            print("✅ PaddleOCR model loaded successfully")
            
        except Exception as e:
            raise OCRError(f"Failed to load OCR model: {e}")
    
    def extract_text(self, image_path: Path, save_results: bool = True, 
                    output_dir: Optional[Path] = None) -> str:
        """
        Extract text from image using OCR.
        
        Args:
            image_path: Path to the image file
            save_results: Whether to save OCR results to JSON
            output_dir: Directory to save OCR results (optional)
            
        Returns:
            Extracted text as string
            
        Raises:
            OCRError: If OCR processing fails
            FileOperationError: If file operations fail
        """
        if not self._is_loaded:
            self.load_model()
        
        if not image_path.exists():
            raise FileOperationError(f"Image file not found: {image_path}")
        
        try:
            print(f"Running OCR on: {image_path}")
            
            # Run OCR prediction
            output = self.ocr_model.predict(input=str(image_path))
            
            # Extract and concatenate text
            ocr_text = ""
            for res in output:
                if save_results and output_dir:
                    # Save individual OCR result to JSON
                    ocr_file = output_dir / f"{image_path.stem}.json"
                    ocr_file.parent.mkdir(parents=True, exist_ok=True)
                    res.save_to_json(save_path=str(ocr_file))
                
                # Concatenate recognized text
                if 'rec_texts' in res:
                    ocr_text += " ".join(res['rec_texts']) + " "
            
            ocr_text = ocr_text.strip()
            print(f"OCR extracted {len(ocr_text)} characters")
            
            return ocr_text
            
        except Exception as e:
            raise OCRError(f"OCR processing failed for {image_path}: {e}")
    
    def load_existing_ocr(self, ocr_file_path: Path) -> Optional[str]:
        """
        Load OCR text from existing JSON file.
        
        Args:
            ocr_file_path: Path to the OCR JSON file
            
        Returns:
            OCR text if file exists and is valid, None otherwise
        """
        if not ocr_file_path.exists():
            return None
        
        try:
            with open(ocr_file_path, 'r', encoding='utf-8') as f:
                ocr_data = json.load(f)
            
            # Extract text from OCR JSON structure
            ocr_text = ""
            if 'rec_texts' in ocr_data:
                ocr_text = " ".join(ocr_data['rec_texts'])
            
            if ocr_text:
                print(f"Loaded existing OCR from {ocr_file_path} ({len(ocr_text)} chars)")
                return ocr_text.strip()
                
        except Exception as e:
            print(f"Warning: Could not load existing OCR file {ocr_file_path}: {e}")
        
        return None
    
    def process_with_cache(self, image_path: Path, ocr_cache_path: Path, 
                          force_ocr: bool = False) -> str:
        """
        Process image with OCR caching support.
        
        Args:
            image_path: Path to the image file
            ocr_cache_path: Path to the OCR cache file
            force_ocr: Whether to force OCR processing even if cache exists
            
        Returns:
            Extracted OCR text
        """
        # Try to load from cache first
        if not force_ocr:
            cached_text = self.load_existing_ocr(ocr_cache_path)
            if cached_text:
                return cached_text
        
        # Run OCR and save results
        ocr_text = self.extract_text(
            image_path=image_path,
            save_results=True,
            output_dir=ocr_cache_path.parent
        )
        
        return ocr_text
    
    def is_available(self) -> bool:
        """Check if OCR service is available."""
        try:
            if not self._is_loaded:
                self.load_model()
            return True
        except Exception:
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get OCR model information."""
        return {
            "service": "PaddleOCR",
            "language": self.config.OCR_LANG,
            "text_detection_model": self.config.TEXT_DETECTION_MODEL,
            "text_recognition_model": self.config.TEXT_RECOGNITION_MODEL,
            "loaded": self._is_loaded
        }