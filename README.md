# Healthcare OCR & Clinical Document Intelligence System

## 🏥 AI-Powered Medical Document Processing & Claims Automation Platform

### Overview
A comprehensive end-to-end AI system for processing medical documents (prescriptions, lab reports, discharge summaries) with automatic extraction, structuring, and normalization of clinical information to accelerate health insurance claim processing.

---

## 🌟 Features

### 1. **Medical Document OCR Engine**
- Accurate OCR for handwritten + printed Indian medical documents
- Handles Hindi/English mix, doctor handwriting, stamps, and poor scans
- Supports multiple OCR engines: PaddleOCR, Tesseract, EasyOCR
- Advanced preprocessing for better accuracy

### 2. **Clinical Entity Extraction & Normalization**
- **Extracts:**
  - Diagnoses
  - Medications (name, dosage, frequency, duration)
  - Lab tests + values
  - Procedures
  - Symptoms

- **Medical Code Mapping:**
  - ICD-10-CM for diagnoses
  - LOINC for lab tests
  - Drug database integration
  - Abnormal lab value detection with reasoning

### 3. **Claims Automation Module**
- Rule-based policy coverage checks
- Automated claim scoring: Eligible / Query / Reject
- Confidence percentage calculation
- Structured JSON output for insurance systems
- 15+ Indian insurance rules implemented

### 4. **PHI Redaction & Compliance**
- Automatic detection and masking of:
  - Patient names
  - Aadhaar numbers
  - Phone numbers
  - Email addresses
  - PAN Card, Passport
  - Addresses
- Full audit logging
- Privacy compliance (HIPAA, GDPR, DPDP compatible)

### 5. **Fraud & Anomaly Detection**
- Duplicate claim detection
- Dosage limit validation
- Billing pattern analysis
- Medical impossibility checks
- Prescription fraud detection
- Claim frequency monitoring

### 6. **Web Dashboard**
- Modern, responsive UI
- Document upload (PDF/Image)
- Real-time processing
- Entity visualization
- Code mapping display
- Downloadable structured output (JSON)
- Claim decision reports

---

## 📁 Project Structure

```
healthcare-ocr-system/
├── main.py                      # FastAPI main application
├── config.py                    # Configuration management
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
│
├── src/
│   ├── ocr/
│   │   ├── __init__.py
│   │   └── medical_ocr.py      # OCR engine
│   │
│   ├── nlp/
│   │   ├── __init__.py
│   │   ├── entity_extractor.py  # Clinical entity extraction
│   │   └── code_mapper.py       # ICD-10, LOINC mapping
│   │
│   ├── claims/
│   │   ├── __init__.py
│   │   └── claims_engine.py     # Claims automation
│   │
│   ├── privacy/
│   │   ├── __init__.py
│   │   └── phi_redactor.py      # PHI redaction
│   │
│   ├── fraud/
│   │   ├── __init__.py
│   │   └── fraud_detector.py    # Fraud detection
│   │
│   └── utils/
│       ├── __init__.py
│       ├── document_processor.py
│       └── pdf_generator.py
│
├── frontend/
│   └── index.html               # Web dashboard
│
├── data/
│   ├── medical_codes/           # ICD-10, LOINC, SNOMED codes
│   └── rules/                   # Insurance rules
│
├── uploads/                     # Uploaded documents
├── outputs/                     # Processed results
├── models/                      # ML models
├── logs/                        # Application logs
│
└── tests/                       # Unit tests
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- pip package manager
- (Optional) CUDA for GPU acceleration

### Installation

1. **Clone/Navigate to the project:**
```bash
cd healthcare-ocr-system
```

2. **Create virtual environment:**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables:**
```bash
# Copy example env file
copy .env.example .env

# Edit .env with your settings
```

5. **Install Tesseract OCR (optional, for Tesseract backend):**
- **Windows:** Download from https://github.com/UB-Mannheim/tesseract/wiki
- **Linux:** `sudo apt-get install tesseract-ocr`
- **Mac:** `brew install tesseract`

---

## 🎯 Usage

### Starting the Server

```bash
python main.py
```

The server will start at: `http://localhost:8000`

### Web Dashboard

Open your browser and navigate to: `http://localhost:8000`

**Workflow:**
1. Upload a medical document (PDF/Image)
2. Select document type (or auto-detect)
3. Enable/disable PHI redaction and fraud detection
4. Click "Process Document"
5. View extracted entities, medical codes, and claim validation

### API Endpoints

#### 1. Health Check
```bash
GET /api/v1/health
```

#### 2. Upload Document
```bash
POST /api/v1/upload
Content-Type: multipart/form-data

Form Data:
- file: document file
- document_type: prescription | lab_report | discharge_summary
```

#### 3. Process Document
```bash
POST /api/v1/process/{document_id}?document_type=prescription&enable_phi_redaction=true&enable_fraud_detection=true
```

#### 4. Validate Claim
```bash
POST /api/v1/claims/validate
Content-Type: application/json

{
  "medications": [...],
  "diagnoses": [...],
  "lab_tests": [...],
  "total_amount": 5000,
  "policy_data": {...}
}
```

#### 5. Search ICD-10 Codes
```bash
GET /api/v1/icd10/search?query=diabetes&limit=10
```

#### 6. Search LOINC Codes
```bash
GET /api/v1/loinc/search?query=hemoglobin&limit=10
```

---

## 📊 Example Outputs

### 1. Extracted Entities
```json
{
  "medications": [
    {
      "name": "Paracetamol",
      "generic_name": "acetaminophen",
      "dosage": "650 mg",
      "frequency": "twice daily",
      "duration": "5 days",
      "confidence": 0.85
    }
  ],
  "lab_tests": [
    {
      "test_name": "Hemoglobin",
      "value": "12.5",
      "unit": "g/dL",
      "reference_range": "13.0-17.0",
      "is_abnormal": true,
      "abnormal_reason": "Below normal range (< 13.0)",
      "loinc_code": "718-7",
      "confidence": 0.80
    }
  ],
  "diagnoses": [
    {
      "name": "Diabetes Mellitus",
      "icd10_code": "E11.9",
      "description": "Type 2 diabetes mellitus",
      "confidence": 0.75
    }
  ]
}
```

### 2. Claim Validation Result
```json
{
  "claim_decision": "eligible",
  "confidence": 0.85,
  "approved_amount": 4750.00,
  "reasons": [],
  "fraud_detection": {
    "fraud_score": 0.12,
    "risk_level": "LOW",
    "alerts": []
  }
}
```

---

## 🔧 Configuration

### OCR Settings
```python
OCR_ENGINE = "paddleocr"  # Options: paddleocr, tesseract, easyocr
OCR_LANGUAGE = "en,hi"
OCR_CONFIDENCE_THRESHOLD = 0.6
```

### Privacy Settings
```python
ENABLE_PHI_REDACTION = True
AUDIT_LOG_ENABLED = True
```

### Fraud Detection
```python
FRAUD_THRESHOLD = 0.75
```

---

## 🧪 Testing

### Run Unit Tests
```bash
pytest tests/
```

### Test Individual Modules
```python
# Test OCR
from src.ocr import MedicalDocumentOCR
ocr = MedicalDocumentOCR()
result = ocr.process_document("sample.jpg", "prescription")
print(result.raw_text)

# Test Entity Extraction
from src.nlp import extract_clinical_entities
entities = extract_clinical_entities(text)

# Test Code Mapping
from src.nlp import get_icd10_code
code = get_icd10_code("diabetes")  # Returns "E11.9"

# Test PHI Redaction
from src.privacy import redact_phi
redacted = redact_phi(text)

# Test Fraud Detection
from src.fraud import detect_fraud
alerts, score = detect_fraud(claim_data)
```

---

## 📈 Performance Metrics

### Success Criteria
- ✅ ≥90% extraction accuracy on key fields
- ✅ ≥85% correct ICD-10 mapping
- ✅ 100% PHI redaction recall
- ✅ ≥88% claim classification accuracy
- ✅ Processing time: 2-5 seconds per document

---

## 🎓 For Students & Teams

### Team Roles (5-8 members)
1. **Project Lead** - Healthcare domain research
2. **OCR Specialist** - Handwriting + layout parsing
3. **Medical NLP Engineer** - Entity extraction + normalization
4. **Backend Developer** - Rule engine + API
5. **Frontend Developer** - Dashboard
6. **Data Curator** - Synthetic data + annotation
7. **Privacy Specialist** - Redaction + compliance
8. **QA Engineer** - Testing + accuracy evaluation

### Development Phases
1. **Phase 1 (Weeks 1-3):** OCR + basic extraction
2. **Phase 2 (Weeks 4-6):** Code mapping + entity normalization
3. **Phase 3 (Weeks 7-9):** Claims automation + fraud detection
4. **Phase 4 (Weeks 10-12):** Dashboard + integration
5. **Phase 5 (Weeks 13-14):** Testing + documentation
6. **Phase 6 (Weeks 15-16):** Demo preparation

---

## 🚧 Future Enhancements

- [ ] Deep learning models for entity extraction (BioBERT, ClinicalBERT)
- [ ] Multi-language support (Tamil, Telugu, Marathi, etc.)
- [ ] Real-time collaboration features
- [ ] Integration with hospital EMR systems
- [ ] Blockchain for audit trails
- [ ] Mobile app
- [ ] Voice input support
- [ ] Automated claim submission to insurers

---

## 📚 Additional Resources

### Medical Code References
- **ICD-10-CM:** https://www.cdc.gov/nchs/icd/icd10cm.htm
- **LOINC:** https://loinc.org/
- **SNOMED CT:** https://www.snomed.org/

### Indian Healthcare Context
- **IRDAI Guidelines:** https://www.irdai.gov.in/
- **ABDM (Ayushman Bharat Digital Mission):** https://abdm.gov.in/

---

## 🤝 Contributing

This is an educational project. Contributions are welcome!

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

---

## ⚖️ License

This project is for educational purposes. 

**Important:** 
- Do NOT use with real patient data without proper authorization
- Ensure HIPAA/GDPR/DPDP compliance before production use
- Obtain necessary certifications for healthcare systems

---

## 📞 Support

For questions or issues:
- Create an issue in the repository
- Contact: [Your contact information]

---

## 🎯 Target Companies

This project is valuable for:
- **HealthTech:** Practo, Tata 1mg, Portea, Netmeds
- **InsurTech:** Policybazaar, Acko, Plum, Digit Insurance
- **AI Healthcare:** Qure.ai, SigTuple, Navia Life Care
- **Hospitals:** Apollo, Fortis, Max Healthcare (EMR systems)

---

## ✨ Acknowledgments

- PaddleOCR for excellent OCR capabilities
- FastAPI for modern web framework
- The open-source medical NLP community
- Healthcare professionals for domain expertise

---

**Built with ❤️ for Healthcare Innovation**

**Version:** 1.0.0  
**Last Updated:** January 2026
