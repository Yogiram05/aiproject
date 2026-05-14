"""
Unit Tests for Healthcare OCR System
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.nlp.entity_extractor import ClinicalEntityExtractor
from src.nlp.code_mapper import MedicalCodeMapper
from src.privacy.phi_redactor import PHIRedactor
from src.fraud.fraud_detector import FraudDetector
from src.claims.claims_engine import ClaimsAutomationEngine


class TestEntityExtractor:
    """Test Clinical Entity Extraction"""
    
    def test_medication_extraction(self):
        extractor = ClinicalEntityExtractor()
        text = "Patient prescribed Paracetamol 650mg twice daily for 5 days"
        
        entities = extractor.extract_entities(text)
        
        assert len(entities['medications']) > 0
        med = entities['medications'][0]
        assert 'paracetamol' in med.name.lower()
        assert med.dosage is not None
        assert med.frequency is not None
    
    def test_diagnosis_extraction(self):
        extractor = ClinicalEntityExtractor()
        text = "Diagnosis: Type 2 Diabetes Mellitus"
        
        entities = extractor.extract_entities(text)
        
        assert len(entities['diagnoses']) > 0
        assert any('diabetes' in d.name.lower() for d in entities['diagnoses'])


class TestCodeMapper:
    """Test Medical Code Mapping"""
    
    def test_icd10_mapping(self):
        mapper = MedicalCodeMapper()
        
        # Test diabetes mapping
        result = mapper.map_diagnosis_to_icd10("diabetes")
        assert result is not None
        assert result.code == "E11.9"
        
    def test_loinc_mapping(self):
        mapper = MedicalCodeMapper()
        
        # Test hemoglobin mapping
        result = mapper.map_lab_test_to_loinc("hemoglobin")
        assert result is not None
        assert result.code == "718-7"
    
    def test_fuzzy_matching(self):
        mapper = MedicalCodeMapper()
        
        # Test fuzzy match
        result = mapper.map_diagnosis_to_icd10("diabetic")
        assert result is not None
        assert "diabetes" in result.description.lower()


class TestPHIRedactor:
    """Test PHI Redaction"""
    
    def test_aadhaar_redaction(self):
        redactor = PHIRedactor()
        text = "Patient Aadhaar: 1234 5678 9012"
        
        redacted, entities = redactor.redact_text(text)
        
        assert "[AADHAAR-REDACTED]" in redacted
        assert len(entities) > 0
        assert entities[0].entity_type == "aadhaar"
    
    def test_phone_redaction(self):
        redactor = PHIRedactor()
        text = "Contact: +91 9876543210"
        
        redacted, entities = redactor.redact_text(text)
        
        assert "[PHONE-REDACTED]" in redacted
        assert any(e.entity_type == "phone" for e in entities)
    
    def test_email_redaction(self):
        redactor = PHIRedactor()
        text = "Email: patient@example.com"
        
        redacted, entities = redactor.redact_text(text)
        
        assert "[EMAIL-REDACTED]" in redacted
        assert any(e.entity_type == "email" for e in entities)


class TestFraudDetector:
    """Test Fraud Detection"""
    
    def test_dosage_anomaly_detection(self):
        detector = FraudDetector()
        
        claim_data = {
            "medications": [
                {
                    "name": "Paracetamol",
                    "dosage": "5000 mg",
                    "frequency": "twice daily"
                }
            ]
        }
        
        alerts, score = detector.analyze_claim(claim_data)
        
        # Should detect dosage exceeding safe limits
        assert len(alerts) > 0
        assert any(alert.alert_type == "dosage_anomaly" for alert in alerts)
    
    def test_normal_claim(self):
        detector = FraudDetector()
        
        claim_data = {
            "medications": [
                {
                    "name": "Paracetamol",
                    "dosage": "650 mg",
                    "frequency": "twice daily"
                }
            ],
            "total_amount": 500
        }
        
        alerts, score = detector.analyze_claim(claim_data)
        
        # Should have low fraud score
        assert score < 0.5


class TestClaimsEngine:
    """Test Claims Automation"""
    
    def test_eligible_claim(self):
        engine = ClaimsAutomationEngine()
        
        claim_data = {
            "diagnoses": ["fever"],
            "medications": [{"name": "Paracetamol"}],
            "total_amount": 1000,
            "has_prescription": True
        }
        
        result = engine.validate_claim(claim_data)
        
        # Basic claim should be eligible
        assert result.decision.value in ["eligible", "query"]
    
    def test_duplicate_claim_rejection(self):
        engine = ClaimsAutomationEngine()
        
        claim_data = {
            "is_duplicate": True,
            "total_amount": 1000
        }
        
        result = engine.validate_claim(claim_data)
        
        # Duplicate should be rejected
        assert result.decision.value == "reject"


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
