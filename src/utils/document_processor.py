"""
Document Processor - Utility for PDF/Image handling
"""

from pathlib import Path
from typing import List, Union
import cv2
import numpy as np
from PIL import Image
import logging

try:
    from pdf2image import convert_from_path
except ImportError:
    convert_from_path = None


class DocumentProcessor:
    """Handles document conversion and preprocessing"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def convert_pdf_to_images(
        self,
        pdf_path: Union[str, Path],
        dpi: int = 300
    ) -> List[np.ndarray]:
        """Convert PDF to images"""
        if convert_from_path is None:
            raise ImportError("pdf2image not installed. Install with: pip install pdf2image")
        
        try:
            # Convert PDF to PIL images
            pil_images = convert_from_path(str(pdf_path), dpi=dpi)
            
            # Convert to numpy arrays
            images = []
            for pil_img in pil_images:
                img_array = np.array(pil_img)
                # Convert RGB to BGR for OpenCV
                img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                images.append(img_bgr)
            
            return images
        
        except Exception as e:
            self.logger.error(f"Error converting PDF: {str(e)}")
            raise
    
    def load_image(self, image_path: Union[str, Path]) -> np.ndarray:
        """Load image file"""
        img = cv2.imread(str(image_path))
        if img is None:
            raise ValueError(f"Could not load image: {image_path}")
        return img
    
    def save_image(
        self,
        image: np.ndarray,
        output_path: Union[str, Path]
    ):
        """Save image to file"""
        cv2.imwrite(str(output_path), image)
