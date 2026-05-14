"""OCR Module Initialization"""
from .medical_ocr import MedicalDocumentOCR, extract_text_from_document, DocumentOCROutput

__all__ = ['MedicalDocumentOCR', 'extract_text_from_document', 'DocumentOCROutput']
