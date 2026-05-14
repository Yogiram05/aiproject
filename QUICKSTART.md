# Healthcare OCR System - Quick Start Guide

## 🚀 Quick Start (5 Minutes)

### Step 1: Install Dependencies
```bash
# Navigate to project folder
cd healthcare-ocr-system

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### Step 2: Run the Server
```bash
python main.py
```

### Step 3: Open Dashboard
Open browser: http://localhost:8000

### Step 4: Process a Document
1. Drag and drop a medical document (or click to browse)
2. Select document type
3. Click "Process Document"
4. View results!

---

## 📝 Sample Test Data

### Sample Prescription Text
```
Dr. Rajesh Kumar
MBBS, MD (Medicine)
Reg. No: 12345

Date: 05-01-2026

Patient: Mr. Ramesh Sharma
Age: 45 years

Diagnosis: Type 2 Diabetes Mellitus, Hypertension

Medications:
1. Metformin 500mg - Twice daily after meals - 30 days
2. Amlodipine 5mg - Once daily - 30 days
3. Atorvastatin 10mg - Once daily at night - 30 days

Lab Tests Advised:
- HbA1c
- Lipid Profile
- Kidney Function Test

Follow-up: After 1 month
```

### Sample Lab Report Text
```
Apollo Diagnostics
Lab Report

Patient: Mrs. Priya Singh
Age: 38 years
Date: 05-01-2026

Complete Blood Count (CBC):
- Hemoglobin: 11.2 g/dL (Reference: 12.0-15.0)
- WBC: 8500 cells/μL (Reference: 4000-11000)
- Platelets: 250000 cells/μL (Reference: 150000-400000)

Diabetes Panel:
- Fasting Blood Sugar: 145 mg/dL (Reference: 70-100)
- HbA1c: 7.8% (Reference: <5.7%)

Lipid Profile:
- Total Cholesterol: 220 mg/dL (Reference: <200)
- HDL: 45 mg/dL (Reference: >40)
- LDL: 145 mg/dL (Reference: <100)
- Triglycerides: 180 mg/dL (Reference: <150)
```

---

## 🔧 Common Issues & Solutions

### Issue 1: ModuleNotFoundError
**Solution:** Make sure virtual environment is activated and all packages are installed
```bash
pip install -r requirements.txt
```

### Issue 2: OCR Not Working
**Solution:** Install PaddleOCR dependencies
```bash
pip install paddleocr paddlepaddle
```

### Issue 3: Port Already in Use
**Solution:** Change port in .env file
```
PORT=8001
```

### Issue 4: File Upload Error
**Solution:** Check file size (max 10MB) and format (PDF, PNG, JPG, JPEG, TIFF)

---

## 🎯 Quick API Test

### Using cURL:

#### 1. Health Check
```bash
curl http://localhost:8000/api/v1/health
```

#### 2. Search ICD-10
```bash
curl "http://localhost:8000/api/v1/icd10/search?query=diabetes"
```

#### 3. Search LOINC
```bash
curl "http://localhost:8000/api/v1/loinc/search?query=hemoglobin"
```

### Using Python:
```python
import requests

# Health check
response = requests.get("http://localhost:8000/api/v1/health")
print(response.json())

# Upload document
with open("prescription.jpg", "rb") as f:
    files = {"file": f}
    response = requests.post(
        "http://localhost:8000/api/v1/upload",
        files=files
    )
    doc_id = response.json()["document_id"]

# Process document
response = requests.post(
    f"http://localhost:8000/api/v1/process/{doc_id}",
    params={"document_type": "prescription"}
)
results = response.json()
print(results)
```

---

## 📚 Key Modules Usage

### 1. OCR Module
```python
from src.ocr import MedicalDocumentOCR

ocr = MedicalDocumentOCR(engine="paddleocr")
result = ocr.process_document("sample.jpg", "prescription")
print(result.raw_text)
```

### 2. Entity Extraction
```python
from src.nlp import ClinicalEntityExtractor

extractor = ClinicalEntityExtractor()
entities = extractor.extract_entities(text)

# Access medications
for med in entities['medications']:
    print(f"{med.name}: {med.dosage} {med.frequency}")
```

### 3. Code Mapping
```python
from src.nlp import MedicalCodeMapper

mapper = MedicalCodeMapper()
icd10 = mapper.map_diagnosis_to_icd10("diabetes")
print(f"ICD-10: {icd10.code}")  # E11.9
```

### 4. PHI Redaction
```python
from src.privacy import PHIRedactor

redactor = PHIRedactor()
redacted_text, entities = redactor.redact_text(text)
print(redacted_text)
```

### 5. Fraud Detection
```python
from src.fraud import FraudDetector

detector = FraudDetector()
alerts, score = detector.analyze_claim(claim_data)
print(f"Fraud Score: {score:.2f}")
```

### 6. Claims Validation
```python
from src.claims import ClaimsAutomationEngine

engine = ClaimsAutomationEngine()
result = engine.validate_claim(claim_data, policy_data)
print(f"Decision: {result.decision.value}")
print(f"Approved Amount: ₹{result.approved_amount}")
```

---

## 🎓 Learning Path

### Day 1: Setup & OCR
- Install dependencies
- Run OCR on sample documents
- Understand preprocessing

### Day 2: Entity Extraction
- Extract medications, diagnoses, lab tests
- Learn pattern matching
- Understand medical vocabularies

### Day 3: Code Mapping
- Map to ICD-10, LOINC
- Implement fuzzy matching
- Build medical code database

### Day 4: Claims & Fraud
- Implement insurance rules
- Build fraud detection
- Test with various scenarios

### Day 5: Integration & Dashboard
- Connect all modules
- Build REST API
- Create web interface

---

## 💡 Pro Tips

1. **Better OCR Results:**
   - Use high-resolution images (300 DPI)
   - Ensure good lighting
   - Flatten documents before scanning

2. **Improve Accuracy:**
   - Expand medical vocabularies
   - Add more ICD-10/LOINC codes
   - Fine-tune extraction patterns

3. **Performance:**
   - Use GPU for PaddleOCR
   - Batch process documents
   - Cache frequent queries

4. **Security:**
   - Always enable PHI redaction for real data
   - Use HTTPS in production
   - Implement authentication

---

## 📞 Need Help?

- Check README.md for detailed documentation
- Review test cases in tests/test_system.py
- Examine code comments in each module
- Create GitHub issue for bugs

---

**Happy Coding! 🚀**
