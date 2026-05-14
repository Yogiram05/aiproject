"""
Medical Document OCR Engine
Handles extraction of text from medical documents (prescriptions, lab reports, discharge summaries)
Supports both handwritten and printed documents in English and Hindi
"""

import cv2
import numpy as np
from PIL import Image
from typing import Dict, List, Tuple, Optional, Union
from pathlib import Path
import json
import logging
from dataclasses import dataclass
from datetime import datetime

try:
    from paddleocr import PaddleOCR
except ImportError:
    PaddleOCR = None

try:
    import pytesseract
except ImportError:
    pytesseract = None

try:
    import easyocr
except ImportError:
    easyocr = None


@dataclass
class OCRResult:
    """OCR Result Data Structure"""
    text: str
    confidence: float
    bounding_box: List[Tuple[int, int]]
    page_number: int = 1


@dataclass
class DocumentOCROutput:
    """Complete OCR Output for a Document"""
    raw_text: str
    structured_results: List[OCRResult]
    document_type: str
    processing_time: float
    metadata: Dict


class MedicalDocumentOCR:
    """
    Medical Document OCR Engine
    Supports multiple OCR backends: PaddleOCR (best for handwriting), Tesseract, EasyOCR
    """
    
    def __init__(
        self,
        engine: str = "paddleocr",
        languages: List[str] = ["en", "hi"],
        confidence_threshold: float = 0.6
    ):
        """
        Initialize OCR Engine
        
        Args:
            engine: OCR engine to use ('paddleocr', 'tesseract', 'easyocr')
            languages: List of languages to support
            confidence_threshold: Minimum confidence score for text extraction
        """
        self.engine = engine.lower()
        self.languages = languages
        self.confidence_threshold = confidence_threshold
        self.logger = logging.getLogger(__name__)
        
        # Initialize OCR engine
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialize the selected OCR engine"""
        if self.engine == "paddleocr":
            if PaddleOCR is None:
                raise ImportError("PaddleOCR not installed. Install with: pip install paddleocr paddlepaddle")
            
            self.ocr_model = PaddleOCR(
                use_angle_cls=True,
                lang='en'  # Primary language
            )
            self.logger.info("PaddleOCR initialized successfully")
            
        elif self.engine == "tesseract":
            if pytesseract is None:
                raise ImportError("Pytesseract not installed. Install with: pip install pytesseract")
            self.ocr_model = pytesseract
            self.logger.info("Tesseract OCR initialized successfully")
            
        elif self.engine == "easyocr":
            if easyocr is None:
                raise ImportError("EasyOCR not installed. Install with: pip install easyocr")
            self.ocr_model = easyocr.Reader(self.languages)
            self.logger.info("EasyOCR initialized successfully")
            
        else:
            raise ValueError(f"Unsupported OCR engine: {self.engine}")
    
    def preprocess_image(self, image: Union[np.ndarray, str, Path]) -> np.ndarray:
        """
        Preprocess image for better OCR accuracy
        
        Args:
            image: Input image (numpy array or file path)
            
        Returns:
            Preprocessed image
        """
        # Load image if path is provided
        if isinstance(image, (str, Path)):
            img = cv2.imread(str(image))
        else:
            img = image.copy()
        
        # Convert to grayscale
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray, h=10)
        
        # Adaptive thresholding for better text extraction
        binary = cv2.adaptiveThreshold(
            denoised,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11,
            2
        )
        
        # Morphological operations to remove noise
        kernel = np.ones((1, 1), np.uint8)
        processed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        # Increase contrast
        processed = cv2.convertScaleAbs(processed, alpha=1.5, beta=0)
        
        return processed
    
    def extract_text_paddleocr(self, image: np.ndarray) -> List[OCRResult]:
        """Extract text using PaddleOCR"""
        results = []
        
        # Run OCR
        ocr_output = self.ocr_model.ocr(image, cls=True)
        
        if ocr_output is None or len(ocr_output) == 0:
            return results
        
        # Process results
        for line in ocr_output[0]:
            if line is None:
                continue
                
            bbox = line[0]
            text_info = line[1]
            text = text_info[0]
            confidence = text_info[1]
            
            if confidence >= self.confidence_threshold:
                results.append(OCRResult(
                    text=text,
                    confidence=confidence,
                    bounding_box=bbox,
                    page_number=1
                ))
        
        return results
    
    def extract_text_tesseract(self, image: np.ndarray) -> List[OCRResult]:
        """Extract text using Tesseract"""
        results = []
        
        # Get detailed OCR data
        data = pytesseract.image_to_data(
            image,
            output_type=pytesseract.Output.DICT,
            lang='+'.join(self.languages)
        )
        
        # Process results
        n_boxes = len(data['text'])
        for i in range(n_boxes):
            confidence = float(data['conf'][i])
            text = data['text'][i].strip()
            
            if confidence >= (self.confidence_threshold * 100) and text:
                x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                bbox = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
                
                results.append(OCRResult(
                    text=text,
                    confidence=confidence / 100.0,
                    bounding_box=bbox,
                    page_number=1
                ))
        
        return results
    
    def extract_text_easyocr(self, image: np.ndarray) -> List[OCRResult]:
        """Extract text using EasyOCR"""
        results = []
        
        # Run OCR
        ocr_output = self.ocr_model.readtext(image)
        
        # Process results
        for detection in ocr_output:
            bbox, text, confidence = detection
            
            if confidence >= self.confidence_threshold:
                results.append(OCRResult(
                    text=text,
                    confidence=confidence,
                    bounding_box=bbox,
                    page_number=1
                ))
        
        return results
    
    def process_document(
        self,
        image_path: Union[str, Path],
        document_type: str = "unknown"
    ) -> DocumentOCROutput:
        """
        Process a medical document and extract text
        
        Args:
            image_path: Path to document image
            document_type: Type of document (prescription, lab_report, discharge_summary)
            
        Returns:
            DocumentOCROutput with extracted text and metadata
        """
        start_time = datetime.now()
        
        # Load and preprocess image
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        processed_image = self.preprocess_image(image)
        
        # Extract text based on selected engine
        if self.engine == "paddleocr":
            structured_results = self.extract_text_paddleocr(processed_image)
        elif self.engine == "tesseract":
            structured_results = self.extract_text_tesseract(processed_image)
        elif self.engine == "easyocr":
            structured_results = self.extract_text_easyocr(processed_image)
        else:
            raise ValueError(f"Unknown OCR engine: {self.engine}")
        
        # Combine all text
        raw_text = "\n".join([result.text for result in structured_results])
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Create metadata
        metadata = {
            "image_path": str(image_path),
            "image_size": image.shape[:2],
            "ocr_engine": self.engine,
            "languages": self.languages,
            "total_text_blocks": len(structured_results),
            "average_confidence": np.mean([r.confidence for r in structured_results]) if structured_results else 0.0,
            "timestamp": datetime.now().isoformat()
        }
        
        return DocumentOCROutput(
            raw_text=raw_text,
            structured_results=structured_results,
            document_type=document_type,
            processing_time=processing_time,
            metadata=metadata
        )
    
    def batch_process(
        self,
        image_paths: List[Union[str, Path]],
        document_types: Optional[List[str]] = None
    ) -> List[DocumentOCROutput]:
        """
        Process multiple documents
        
        Args:
            image_paths: List of image paths
            document_types: Optional list of document types
            
        Returns:
            List of DocumentOCROutput
        """
        if document_types is None:
            document_types = ["unknown"] * len(image_paths)
        
        results = []
        for image_path, doc_type in zip(image_paths, document_types):
            try:
                result = self.process_document(image_path, doc_type)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Error processing {image_path}: {str(e)}")
                continue
        
        return results
    
    def save_results(self, output: DocumentOCROutput, save_path: Union[str, Path]):
        """Save OCR results to JSON file"""
        result_dict = {
            "raw_text": output.raw_text,
            "document_type": output.document_type,
            "processing_time": output.processing_time,
            "structured_results": [
                {
                    "text": r.text,
                    "confidence": r.confidence,
                    "bounding_box": r.bounding_box,
                    "page_number": r.page_number
                }
                for r in output.structured_results
            ],
            "metadata": output.metadata
        }
        
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(result_dict, f, indent=2, ensure_ascii=False)


# Convenience function
def extract_text_from_document(
    image_path: Union[str, Path],
    engine: str = "paddleocr",
    document_type: str = "unknown"
) -> str:
    """
    Quick function to extract text from a medical document
    
    Args:
        image_path: Path to document image
        engine: OCR engine to use
        document_type: Type of document
        
    Returns:
        Extracted text as string
    """
    ocr = MedicalDocumentOCR(engine=engine)
    result = ocr.process_document(image_path, document_type)
    return result.raw_text
