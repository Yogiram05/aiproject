"""
Main FastAPI Application
Healthcare OCR & Clinical Document Intelligence System
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from typing import Optional, List, Dict
from pathlib import Path
import shutil
import json
import logging
from datetime import datetime
import uuid

# Import our modules
import sys
sys.path.append(str(Path(__file__).parent.parent))

from config import settings
from src.ocr.medical_ocr import MedicalDocumentOCR
from src.nlp.entity_extractor import ClinicalEntityExtractor
from src.nlp.code_mapper import MedicalCodeMapper
from src.claims.claims_engine import ClaimsAutomationEngine
from src.privacy.phi_redactor import PHIRedactor
from src.fraud.fraud_detector import FraudDetector
from src.utils.document_processor import DocumentProcessor
from src.utils.pdf_generator import generate_redacted_pdf, generate_claim_summary_pdf

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered Medical Document Processing & Claims Automation Platform"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (frontend)
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Initialize components
ocr_engine = MedicalDocumentOCR(engine=settings.OCR_ENGINE)
entity_extractor = ClinicalEntityExtractor()
code_mapper = MedicalCodeMapper()
claims_engine = ClaimsAutomationEngine()
phi_redactor = PHIRedactor()
fraud_detector = FraudDetector(fraud_threshold=settings.FRAUD_THRESHOLD)


@app.get("/")
async def root():
    """Root endpoint - serve dashboard"""
    return FileResponse("frontend/index.html")


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/v1/upload")
async def upload_document(
    file: UploadFile = File(...),
    document_type: Optional[str] = "unknown"
):
    """
    Upload a medical document for processing
    
    Args:
        file: Document file (PDF/Image)
        document_type: Type of document (prescription, lab_report, discharge_summary)
    
    Returns:
        Document ID and basic info
    """
    try:
        # Generate unique document ID
        doc_id = str(uuid.uuid4())
        
        # Validate file extension
        file_ext = Path(file.filename).suffix.lower().replace('.', '')
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed: {settings.ALLOWED_EXTENSIONS}"
            )
        
        # Save uploaded file
        upload_path = settings.UPLOAD_DIR / f"{doc_id}{Path(file.filename).suffix}"
        with open(upload_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Document uploaded: {doc_id} ({file.filename})")
        
        return {
            "document_id": doc_id,
            "filename": file.filename,
            "document_type": document_type,
            "upload_path": str(upload_path),
            "timestamp": datetime.now().isoformat(),
            "message": "Document uploaded successfully"
        }
    
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/process/{document_id}")
async def process_document(
    document_id: str,
    document_type: str = "unknown",
    enable_phi_redaction: bool = True,
    enable_fraud_detection: bool = True
):
    """
    Process uploaded document - OCR, entity extraction, code mapping
    
    Args:
        document_id: Document ID from upload
        document_type: Type of document
        enable_phi_redaction: Enable PHI redaction
        enable_fraud_detection: Enable fraud detection
    
    Returns:
        Processed document data
    """
    try:
        # Find uploaded document
        upload_files = list(settings.UPLOAD_DIR.glob(f"{document_id}*"))
        if not upload_files:
            raise HTTPException(status_code=404, detail="Document not found")
        
        upload_path = upload_files[0]
        
        logger.info(f"Processing document: {document_id}")
        
        # Step 1: OCR
        logger.info("Running OCR...")
        ocr_result = ocr_engine.process_document(upload_path, document_type)
        
        # Step 2: Entity Extraction
        logger.info("Extracting entities...")
        entities = entity_extractor.extract_entities(ocr_result.raw_text)
        
        # Step 3: Code Mapping
        logger.info("Mapping medical codes...")
        
        # Map diagnoses to ICD-10
        icd10_mappings = {}
        for diagnosis in entities['diagnoses']:
            icd10_code = code_mapper.map_diagnosis_to_icd10(diagnosis.name)
            if icd10_code:
                icd10_mappings[diagnosis.name] = {
                    "code": icd10_code.code,
                    "description": icd10_code.description,
                    "confidence": icd10_code.confidence
                }
        
        # Map lab tests to LOINC
        loinc_mappings = {}
        for lab_test in entities['lab_tests']:
            loinc_code = code_mapper.map_lab_test_to_loinc(lab_test.test_name)
            if loinc_code:
                loinc_mappings[lab_test.test_name] = {
                    "code": loinc_code.code,
                    "long_name": loinc_code.long_name,
                    "confidence": loinc_code.confidence
                }
        
        # Step 4: PHI Redaction (optional)
        redacted_text = ocr_result.raw_text
        redacted_entities = []
        
        if enable_phi_redaction:
            logger.info("Redacting PHI...")
            redacted_text, redacted_entities = phi_redactor.redact_text(ocr_result.raw_text)
        
        # Prepare response
        result = {
            "document_id": document_id,
            "document_type": document_type,
            "processing_time": ocr_result.processing_time,
            "ocr": {
                "raw_text": ocr_result.raw_text,
                "redacted_text": redacted_text,
                "total_text_blocks": len(ocr_result.structured_results),
                "average_confidence": ocr_result.metadata.get('average_confidence', 0)
            },
            "entities": {
                "medications": [
                    {
                        "name": m.name,
                        "generic_name": m.generic_name,
                        "dosage": m.dosage,
                        "frequency": m.frequency,
                        "duration": m.duration,
                        "confidence": m.confidence
                    } for m in entities['medications']
                ],
                "lab_tests": [
                    {
                        "test_name": lt.test_name,
                        "value": lt.value,
                        "unit": lt.unit,
                        "reference_range": lt.reference_range,
                        "is_abnormal": lt.is_abnormal,
                        "abnormal_reason": lt.abnormal_reason,
                        "loinc_code": loinc_mappings.get(lt.test_name, {}).get('code'),
                        "confidence": lt.confidence
                    } for lt in entities['lab_tests']
                ],
                "diagnoses": [
                    {
                        "name": d.name,
                        "icd10_code": icd10_mappings.get(d.name, {}).get('code'),
                        "description": icd10_mappings.get(d.name, {}).get('description'),
                        "confidence": d.confidence
                    } for d in entities['diagnoses']
                ],
                "procedures": entities['procedures'],
                "symptoms": entities['symptoms']
            },
            "medical_codes": {
                "icd10": icd10_mappings,
                "loinc": loinc_mappings
            },
            "phi_redaction": {
                "enabled": enable_phi_redaction,
                "redactions_count": len(redacted_entities),
                "redacted_types": list(set(e.entity_type for e in redacted_entities))
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # Save results
        output_path = settings.OUTPUT_DIR / f"{document_id}_processed.json"
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Document processed successfully: {document_id}")
        
        return result
    
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/claims/validate")
async def validate_claim(claim_data: Dict):
    """
    Validate insurance claim
    
    Args:
        claim_data: Claim information including entities and policy details
    
    Returns:
        Claim validation result
    """
    try:
        logger.info("Validating claim...")
        
        # Extract policy data if present
        policy_data = claim_data.get('policy_data')
        
        # Validate claim
        claim_result = claims_engine.validate_claim(claim_data, policy_data)
        
        # Fraud detection
        fraud_alerts, fraud_score = fraud_detector.analyze_claim(claim_data)
        
        result = {
            "claim_decision": claim_result.decision.value,
            "confidence": claim_result.confidence,
            "approved_amount": claim_result.approved_amount,
            "reasons": claim_result.reasons,
            "warnings": claim_result.warnings,
            "fraud_detection": {
                "fraud_score": fraud_score,
                "risk_level": fraud_detector._get_risk_level(fraud_score),
                "alerts": [
                    {
                        "type": alert.alert_type,
                        "severity": alert.severity,
                        "description": alert.description,
                        "confidence": alert.confidence,
                        "recommendation": alert.recommendation
                    } for alert in fraud_alerts
                ]
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return result
    
    except Exception as e:
        logger.error(f"Error validating claim: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/results/{document_id}")
async def get_results(document_id: str):
    """Get processed results for a document"""
    try:
        result_path = settings.OUTPUT_DIR / f"{document_id}_processed.json"
        
        if not result_path.exists():
            raise HTTPException(status_code=404, detail="Results not found")
        
        with open(result_path, 'r') as f:
            results = json.load(f)
        
        return results
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/download/{document_id}/json")
async def download_json(document_id: str):
    """Download processed results as JSON"""
    result_path = settings.OUTPUT_DIR / f"{document_id}_processed.json"
    
    if not result_path.exists():
        raise HTTPException(status_code=404, detail="Results not found")
    
    return FileResponse(
        result_path,
        media_type="application/json",
        filename=f"{document_id}_results.json"
    )


@app.get("/api/v1/icd10/search")
async def search_icd10(query: str, limit: int = 10):
    """Search ICD-10 codes"""
    try:
        results = code_mapper.search_icd10(query, limit)
        return {
            "query": query,
            "results": [
                {
                    "code": r.code,
                    "description": r.description,
                    "category": r.category,
                    "confidence": r.confidence
                } for r in results
            ]
        }
    except Exception as e:
        logger.error(f"Error searching ICD-10: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/loinc/search")
async def search_loinc(query: str, limit: int = 10):
    """Search LOINC codes"""
    try:
        results = code_mapper.search_loinc(query, limit)
        return {
            "query": query,
            "results": [
                {
                    "code": r.code,
                    "long_name": r.long_name,
                    "short_name": r.short_name,
                    "component": r.component,
                    "confidence": r.confidence
                } for r in results
            ]
        }
    except Exception as e:
        logger.error(f"Error searching LOINC: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
