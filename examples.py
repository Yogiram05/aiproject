"""
Example Usage - Healthcare OCR System
Demonstrates how to use each module
"""

from pathlib import Path
import json

# Import modules
from src.ocr import MedicalDocumentOCR
from src.nlp import ClinicalEntityExtractor, MedicalCodeMapper
from src.claims import ClaimsAutomationEngine
from src.privacy import PHIRedactor
from src.fraud import FraudDetector


def example_1_ocr():
    """Example 1: Extract text from medical document"""
    print("=" * 60)
    print("EXAMPLE 1: Medical Document OCR")
    print("=" * 60)
    
    # Initialize OCR engine
    ocr = MedicalDocumentOCR(engine="paddleocr")
    
    # Sample text (simulating OCR output)
    sample_text = """
    Dr. Rajesh Kumar, MBBS, MD
    Date: 05-01-2026
    
    Patient: Mr. Ramesh Sharma
    Age: 45 years
    
    Diagnosis: Type 2 Diabetes Mellitus
    
    Medications:
    1. Metformin 500mg - Twice daily after meals - 30 days
    2. Amlodipine 5mg - Once daily - 30 days
    
    Lab Tests:
    - HbA1c: 7.8% (Reference: <5.7%)
    - Fasting Blood Sugar: 145 mg/dL
    """
    
    print("Extracted Text:")
    print(sample_text)
    print()


def example_2_entity_extraction():
    """Example 2: Extract clinical entities"""
    print("=" * 60)
    print("EXAMPLE 2: Clinical Entity Extraction")
    print("=" * 60)
    
    text = """
    Diagnosis: Dengue Fever, Dehydration
    
    Medications:
    1. Paracetamol 650mg - Thrice daily - 5 days
    2. Dolo 650 - Twice daily - 3 days
    
    Lab Tests:
    - Hemoglobin: 11.2 g/dL (Reference: 13-17)
    - Platelet Count: 95000 cells/μL
    - Dengue NS1: Positive
    """
    
    # Extract entities
    extractor = ClinicalEntityExtractor()
    entities = extractor.extract_entities(text)
    
    # Display medications
    print("\nMedications Extracted:")
    for med in entities['medications']:
        print(f"  • {med.name}")
        print(f"    Dosage: {med.dosage}")
        print(f"    Frequency: {med.frequency}")
        print(f"    Duration: {med.duration}")
        print()
    
    # Display lab tests
    print("Lab Tests Extracted:")
    for test in entities['lab_tests']:
        print(f"  • {test.test_name}: {test.value} {test.unit or ''}")
        if test.is_abnormal:
            print(f"    ⚠ ABNORMAL: {test.abnormal_reason}")
        print()
    
    # Display diagnoses
    print("Diagnoses Extracted:")
    for diag in entities['diagnoses']:
        print(f"  • {diag.name}")
    print()


def example_3_code_mapping():
    """Example 3: Map to medical codes"""
    print("=" * 60)
    print("EXAMPLE 3: Medical Code Mapping")
    print("=" * 60)
    
    mapper = MedicalCodeMapper()
    
    # Map diagnoses to ICD-10
    diagnoses = ["Diabetes Mellitus", "Hypertension", "Dengue Fever"]
    
    print("\nICD-10 Code Mapping:")
    for diagnosis in diagnoses:
        icd10 = mapper.map_diagnosis_to_icd10(diagnosis)
        if icd10:
            print(f"  {diagnosis}")
            print(f"    → ICD-10: {icd10.code}")
            print(f"    → Description: {icd10.description}")
            print(f"    → Confidence: {icd10.confidence * 100:.1f}%")
            print()
    
    # Map lab tests to LOINC
    lab_tests = ["Hemoglobin", "HbA1c", "Cholesterol"]
    
    print("LOINC Code Mapping:")
    for test in lab_tests:
        loinc = mapper.map_lab_test_to_loinc(test)
        if loinc:
            print(f"  {test}")
            print(f"    → LOINC: {loinc.code}")
            print(f"    → Name: {loinc.long_name}")
            print()


def example_4_phi_redaction():
    """Example 4: Redact PHI"""
    print("=" * 60)
    print("EXAMPLE 4: PHI Redaction")
    print("=" * 60)
    
    text = """
    Patient Name: Mr. Ramesh Kumar Sharma
    Aadhaar: 1234 5678 9012
    Phone: +91 9876543210
    Email: ramesh.sharma@example.com
    Address: 123 MG Road, Bangalore 560001
    
    Diagnosis: Diabetes
    """
    
    print("Original Text:")
    print(text)
    print()
    
    # Redact PHI
    redactor = PHIRedactor()
    redacted_text, entities = redactor.redact_text(text)
    
    print("Redacted Text:")
    print(redacted_text)
    print()
    
    print(f"Total Redactions: {len(entities)}")
    print("\nRedacted Entities:")
    for entity in entities:
        print(f"  • {entity.entity_type.upper()}: {entity.original_text} → {entity.redacted_text}")
    print()


def example_5_fraud_detection():
    """Example 5: Detect fraud"""
    print("=" * 60)
    print("EXAMPLE 5: Fraud Detection")
    print("=" * 60)
    
    # Example claim with high dosage
    claim_data = {
        "medications": [
            {
                "name": "Paracetamol",
                "dosage": "5000 mg",
                "frequency": "twice daily"
            }
        ],
        "total_amount": 50000,
        "diagnoses": ["Fever"]
    }
    
    # Detect fraud
    detector = FraudDetector()
    alerts, fraud_score = detector.analyze_claim(claim_data)
    
    print(f"\nFraud Score: {fraud_score * 100:.1f}%")
    print(f"Risk Level: {detector._get_risk_level(fraud_score)}")
    print()
    
    if alerts:
        print("Fraud Alerts:")
        for alert in alerts:
            print(f"  • [{alert.severity.upper()}] {alert.description}")
            print(f"    Recommendation: {alert.recommendation}")
            print()
    else:
        print("No fraud indicators detected.")
    print()


def example_6_claims_validation():
    """Example 6: Validate insurance claim"""
    print("=" * 60)
    print("EXAMPLE 6: Claims Validation")
    print("=" * 60)
    
    claim_data = {
        "diagnoses": ["Dengue Fever"],
        "medications": [
            {
                "name": "Paracetamol",
                "dosage": "650 mg",
                "frequency": "thrice daily"
            }
        ],
        "lab_tests": ["Dengue NS1", "CBC"],
        "fever_duration_days": 5,
        "total_amount": 5000,
        "has_prescription": True
    }
    
    policy_data = {
        "sum_insured": 500000,
        "utilized_amount": 50000,
        "copay_percent": 10
    }
    
    # Validate claim
    engine = ClaimsAutomationEngine()
    result = engine.validate_claim(claim_data, policy_data)
    
    print(f"\nClaim Decision: {result.decision.value.upper()}")
    print(f"Confidence: {result.confidence * 100:.1f}%")
    print(f"Claimed Amount: ₹{claim_data['total_amount']:,.2f}")
    print(f"Approved Amount: ₹{result.approved_amount:,.2f}")
    print()
    
    if result.reasons:
        print("Validation Results:")
        for reason in result.reasons:
            print(f"  • {reason}")
        print()


def example_7_complete_workflow():
    """Example 7: Complete end-to-end workflow"""
    print("=" * 60)
    print("EXAMPLE 7: Complete Workflow")
    print("=" * 60)
    
    # Sample prescription text
    text = """
    Dr. Kumar Medical Clinic
    Date: 05-01-2026
    
    Patient: Mr. Sharma
    Age: 45 years
    Contact: +91 9876543210
    
    Diagnosis: Type 2 Diabetes Mellitus
    
    Medications:
    1. Metformin 500mg - Twice daily - 30 days
    2. Amlodipine 5mg - Once daily - 30 days
    
    Lab Tests Advised:
    - HbA1c
    - Fasting Blood Sugar
    
    Total Consultation Fee: ₹800
    """
    
    print("Step 1: Extract Entities")
    extractor = ClinicalEntityExtractor()
    entities = extractor.extract_entities(text)
    print(f"  ✓ Found {len(entities['medications'])} medications")
    print(f"  ✓ Found {len(entities['diagnoses'])} diagnoses")
    print()
    
    print("Step 2: Map Medical Codes")
    mapper = MedicalCodeMapper()
    for diag in entities['diagnoses']:
        icd10 = mapper.map_diagnosis_to_icd10(diag.name)
        if icd10:
            print(f"  ✓ {diag.name} → ICD-10: {icd10.code}")
    print()
    
    print("Step 3: Redact PHI")
    redactor = PHIRedactor()
    redacted_text, phi_entities = redactor.redact_text(text)
    print(f"  ✓ Redacted {len(phi_entities)} PHI elements")
    print()
    
    print("Step 4: Validate Claim")
    claim_data = {
        "diagnoses": [d.name for d in entities['diagnoses']],
        "medications": [
            {
                "name": m.name,
                "dosage": m.dosage,
                "frequency": m.frequency
            }
            for m in entities['medications']
        ],
        "total_amount": 800,
        "has_prescription": True
    }
    
    engine = ClaimsAutomationEngine()
    result = engine.validate_claim(claim_data)
    print(f"  ✓ Claim Decision: {result.decision.value.upper()}")
    print(f"  ✓ Approved: ₹{result.approved_amount:,.2f}")
    print()
    
    print("Step 5: Fraud Detection")
    detector = FraudDetector()
    alerts, fraud_score = detector.analyze_claim(claim_data)
    print(f"  ✓ Fraud Score: {fraud_score * 100:.1f}%")
    print(f"  ✓ Risk Level: {detector._get_risk_level(fraud_score)}")
    print()
    
    print("✅ Workflow Complete!")
    print()


if __name__ == "__main__":
    print("\n🏥 HEALTHCARE OCR SYSTEM - EXAMPLES\n")
    
    # Run all examples
    example_1_ocr()
    example_2_entity_extraction()
    example_3_code_mapping()
    example_4_phi_redaction()
    example_5_fraud_detection()
    example_6_claims_validation()
    example_7_complete_workflow()
    
    print("\n" + "=" * 60)
    print("All examples completed successfully! ✨")
    print("=" * 60)
