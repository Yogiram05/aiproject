"""
Clinical Entity Extraction & Normalization Module
Extracts medical entities: diagnoses, medications, lab tests, procedures
Uses medical NLP models and rule-based patterns
"""

import re
import json
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass
from datetime import datetime
import logging
from fuzzywuzzy import fuzz, process


@dataclass
class MedicalEntity:
    """Represents an extracted medical entity"""
    entity_type: str  # diagnosis, medication, lab_test, procedure, symptom
    text: str
    normalized_name: str
    confidence: float
    start_pos: int
    end_pos: int
    attributes: Dict = None
    
    def __post_init__(self):
        if self.attributes is None:
            self.attributes = {}


@dataclass
class Medication:
    """Medication entity with detailed attributes"""
    name: str
    generic_name: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    route: Optional[str] = None
    instructions: Optional[str] = None
    confidence: float = 0.0


@dataclass
class LabTest:
    """Lab test entity with results"""
    test_name: str
    value: Optional[str] = None
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    is_abnormal: bool = False
    abnormal_reason: Optional[str] = None
    loinc_code: Optional[str] = None
    confidence: float = 0.0


@dataclass
class Diagnosis:
    """Diagnosis entity"""
    name: str
    icd10_code: Optional[str] = None
    description: Optional[str] = None
    confidence: float = 0.0


class ClinicalEntityExtractor:
    """
    Extract and normalize clinical entities from medical text
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Load medical vocabularies
        self._load_medical_vocabularies()
        
        # Initialize pattern matchers
        self._initialize_patterns()
    
    def _load_medical_vocabularies(self):
        """Load medical vocabularies and drug databases"""
        # Common Indian medications (sample - expand this)
        self.medications_db = {
            "paracetamol": {"generic": "acetaminophen", "class": "analgesic"},
            "dolo 650": {"generic": "paracetamol", "class": "analgesic"},
            "crocin": {"generic": "paracetamol", "class": "analgesic"},
            "azithromycin": {"generic": "azithromycin", "class": "antibiotic"},
            "amoxicillin": {"generic": "amoxicillin", "class": "antibiotic"},
            "metformin": {"generic": "metformin", "class": "antidiabetic"},
            "amlodipine": {"generic": "amlodipine", "class": "antihypertensive"},
            "atorvastatin": {"generic": "atorvastatin", "class": "statin"},
            "omeprazole": {"generic": "omeprazole", "class": "ppi"},
            "pantoprazole": {"generic": "pantoprazole", "class": "ppi"},
            "cetirizine": {"generic": "cetirizine", "class": "antihistamine"},
            "levocetrizine": {"generic": "levocetirizine", "class": "antihistamine"},
            "montelukast": {"generic": "montelukast", "class": "leukotriene inhibitor"},
            "salbutamol": {"generic": "albuterol", "class": "bronchodilator"},
        }
        
        # Common lab tests
        self.lab_tests_db = {
            "cbc": "Complete Blood Count",
            "hemoglobin": "Hemoglobin",
            "hb": "Hemoglobin",
            "wbc": "White Blood Cell Count",
            "rbc": "Red Blood Cell Count",
            "platelet": "Platelet Count",
            "esr": "Erythrocyte Sedimentation Rate",
            "crp": "C-Reactive Protein",
            "glucose": "Blood Glucose",
            "fbs": "Fasting Blood Sugar",
            "ppbs": "Post Prandial Blood Sugar",
            "hba1c": "Glycated Hemoglobin",
            "cholesterol": "Total Cholesterol",
            "hdl": "High-Density Lipoprotein",
            "ldl": "Low-Density Lipoprotein",
            "triglycerides": "Triglycerides",
            "sgot": "Serum Glutamic-Oxaloacetic Transaminase",
            "sgpt": "Serum Glutamic-Pyruvic Transaminase",
            "alt": "Alanine Aminotransferase",
            "ast": "Aspartate Aminotransferase",
            "bilirubin": "Bilirubin",
            "creatinine": "Creatinine",
            "urea": "Blood Urea",
            "uric acid": "Uric Acid",
            "tsh": "Thyroid Stimulating Hormone",
            "t3": "Triiodothyronine",
            "t4": "Thyroxine",
            "vitamin d": "Vitamin D",
            "vitamin b12": "Vitamin B12",
            "dengue ns1": "Dengue NS1 Antigen",
            "malaria": "Malaria Antigen",
        }
        
        # Common diagnoses
        self.diagnoses_db = {
            "diabetes": "Diabetes Mellitus",
            "hypertension": "Essential Hypertension",
            "fever": "Fever of Unknown Origin",
            "dengue": "Dengue Fever",
            "malaria": "Malaria",
            "typhoid": "Typhoid Fever",
            "upper respiratory tract infection": "URTI",
            "urti": "Upper Respiratory Tract Infection",
            "lower respiratory tract infection": "LRTI",
            "gastroenteritis": "Acute Gastroenteritis",
            "urinary tract infection": "UTI",
            "uti": "Urinary Tract Infection",
            "asthma": "Bronchial Asthma",
            "copd": "Chronic Obstructive Pulmonary Disease",
            "pneumonia": "Pneumonia",
            "tuberculosis": "Pulmonary Tuberculosis",
            "tb": "Tuberculosis",
            "covid": "COVID-19",
            "corona": "COVID-19",
        }
        
    def _initialize_patterns(self):
        """Initialize regex patterns for entity extraction"""
        
        # Dosage patterns
        self.dosage_patterns = [
            r'\b(\d+\.?\d*)\s*(mg|gm|g|ml|mcg|iu|units?)\b',
            r'\b(\d+)\s*tab(?:let)?s?\b',
            r'\b(\d+)\s*cap(?:sule)?s?\b',
        ]
        
        # Frequency patterns
        self.frequency_patterns = [
            r'\b(once|twice|thrice|od|bd|td|qd|bid|tid|qid)\s*(?:daily|a day|per day)?\b',
            r'\b(\d+)\s*times?\s*(?:a\s*)?day\b',
            r'\bevery\s*(\d+)\s*hours?\b',
            r'\b(morning|afternoon|evening|night|bedtime|hs)\b',
            r'\b(before|after)\s*(food|meal|breakfast|lunch|dinner)\b',
        ]
        
        # Duration patterns
        self.duration_patterns = [
            r'\bfor\s*(\d+)\s*(day|days|week|weeks|month|months)\b',
            r'\b(\d+)\s*(day|days|week|weeks|month|months)\s*course\b',
            r'\bcontinue\s*for\s*(\d+)\s*(day|days|week|weeks|month|months)\b',
        ]
        
        # Lab value patterns
        self.lab_value_patterns = [
            r'(\d+\.?\d*)\s*([a-z/%]+)\b',
            r':\s*(\d+\.?\d*)\s*([a-z/%]*)',
            r'=\s*(\d+\.?\d*)\s*([a-z/%]*)',
        ]
        
        # Reference range patterns
        self.reference_range_patterns = [
            r'(?:normal|reference)?\s*(?:range)?:?\s*(\d+\.?\d*)\s*-\s*(\d+\.?\d*)',
            r'\((\d+\.?\d*)\s*-\s*(\d+\.?\d*)\)',
        ]
    
    def extract_entities(self, text: str) -> Dict[str, List]:
        """
        Extract all medical entities from text
        
        Args:
            text: Medical document text
            
        Returns:
            Dictionary containing lists of extracted entities by type
        """
        text_lower = text.lower()
        
        entities = {
            "medications": self.extract_medications(text),
            "lab_tests": self.extract_lab_tests(text),
            "diagnoses": self.extract_diagnoses(text),
            "procedures": self.extract_procedures(text),
            "symptoms": self.extract_symptoms(text),
        }
        
        return entities
    
    def extract_medications(self, text: str) -> List[Medication]:
        """Extract medication information from text"""
        medications = []
        text_lower = text.lower()
        lines = text.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            
            # Check against medication database
            for med_name, med_info in self.medications_db.items():
                if med_name in line_lower:
                    # Extract dosage
                    dosage = self._extract_dosage(line)
                    
                    # Extract frequency
                    frequency = self._extract_frequency(line)
                    
                    # Extract duration
                    duration = self._extract_duration(line)
                    
                    medication = Medication(
                        name=med_name.title(),
                        generic_name=med_info.get("generic"),
                        dosage=dosage,
                        frequency=frequency,
                        duration=duration,
                        confidence=0.85
                    )
                    medications.append(medication)
        
        return medications
    
    def _extract_dosage(self, text: str) -> Optional[str]:
        """Extract dosage from text"""
        for pattern in self.dosage_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return None
    
    def _extract_frequency(self, text: str) -> Optional[str]:
        """Extract frequency from text"""
        for pattern in self.frequency_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return None
    
    def _extract_duration(self, text: str) -> Optional[str]:
        """Extract duration from text"""
        for pattern in self.duration_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return None
    
    def extract_lab_tests(self, text: str) -> List[LabTest]:
        """Extract lab test information from text"""
        lab_tests = []
        text_lower = text.lower()
        lines = text.split('\n')
        
        for line in lines:
            line_lower = line.lower()
            
            # Check against lab tests database
            for test_key, test_name in self.lab_tests_db.items():
                if test_key in line_lower:
                    # Extract value
                    value, unit = self._extract_lab_value(line)
                    
                    # Extract reference range
                    ref_range = self._extract_reference_range(line)
                    
                    # Check if abnormal
                    is_abnormal, reason = self._check_abnormal(test_key, value, ref_range)
                    
                    lab_test = LabTest(
                        test_name=test_name,
                        value=value,
                        unit=unit,
                        reference_range=ref_range,
                        is_abnormal=is_abnormal,
                        abnormal_reason=reason,
                        confidence=0.80
                    )
                    lab_tests.append(lab_test)
        
        return lab_tests
    
    def _extract_lab_value(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract lab test value and unit"""
        for pattern in self.lab_value_patterns:
            match = re.search(pattern, text)
            if match:
                value = match.group(1)
                unit = match.group(2) if len(match.groups()) > 1 else None
                return value, unit
        return None, None
    
    def _extract_reference_range(self, text: str) -> Optional[str]:
        """Extract reference range from text"""
        for pattern in self.reference_range_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return None
    
    def _check_abnormal(
        self,
        test_name: str,
        value: Optional[str],
        ref_range: Optional[str]
    ) -> Tuple[bool, Optional[str]]:
        """Check if lab value is abnormal"""
        if not value or not ref_range:
            return False, None
        
        try:
            # Extract numeric value
            numeric_value = float(re.search(r'\d+\.?\d*', value).group())
            
            # Extract range
            range_match = re.search(r'(\d+\.?\d*)\s*-\s*(\d+\.?\d*)', ref_range)
            if range_match:
                lower = float(range_match.group(1))
                upper = float(range_match.group(2))
                
                if numeric_value < lower:
                    return True, f"Below normal range (< {lower})"
                elif numeric_value > upper:
                    return True, f"Above normal range (> {upper})"
        except:
            pass
        
        return False, None
    
    def extract_diagnoses(self, text: str) -> List[Diagnosis]:
        """Extract diagnoses from text"""
        diagnoses = []
        text_lower = text.lower()
        
        # Look for diagnosis section
        diagnosis_section = re.search(
            r'(?:diagnosis|provisional diagnosis|final diagnosis|impression):\s*(.+?)(?:\n\n|\Z)',
            text_lower,
            re.DOTALL
        )
        
        if diagnosis_section:
            diagnosis_text = diagnosis_section.group(1)
        else:
            diagnosis_text = text_lower
        
        # Check against diagnoses database
        for diag_key, diag_name in self.diagnoses_db.items():
            if diag_key in diagnosis_text:
                diagnosis = Diagnosis(
                    name=diag_name,
                    confidence=0.75
                )
                diagnoses.append(diagnosis)
        
        return diagnoses
    
    def extract_procedures(self, text: str) -> List[str]:
        """Extract medical procedures from text"""
        procedures = []
        
        # Common procedures
        procedure_keywords = [
            "x-ray", "ultrasound", "ct scan", "mri", "ecg", "echo",
            "endoscopy", "colonoscopy", "biopsy", "surgery", "operation"
        ]
        
        text_lower = text.lower()
        for procedure in procedure_keywords:
            if procedure in text_lower:
                procedures.append(procedure.title())
        
        return procedures
    
    def extract_symptoms(self, text: str) -> List[str]:
        """Extract symptoms from text"""
        symptoms = []
        
        # Common symptoms
        symptom_keywords = [
            "fever", "cough", "cold", "headache", "pain", "nausea",
            "vomiting", "diarrhea", "fatigue", "weakness", "dizziness",
            "breathlessness", "chest pain", "abdominal pain"
        ]
        
        text_lower = text.lower()
        for symptom in symptom_keywords:
            if symptom in text_lower:
                symptoms.append(symptom.title())
        
        return symptoms
    
    def normalize_medication_name(self, med_name: str) -> str:
        """Normalize medication name to generic name"""
        med_lower = med_name.lower()
        
        # Direct match
        if med_lower in self.medications_db:
            return self.medications_db[med_lower].get("generic", med_name)
        
        # Fuzzy match
        best_match = process.extractOne(
            med_lower,
            self.medications_db.keys(),
            scorer=fuzz.ratio,
            score_cutoff=80
        )
        
        if best_match:
            return self.medications_db[best_match[0]].get("generic", med_name)
        
        return med_name
    
    def to_json(self, entities: Dict) -> str:
        """Convert extracted entities to JSON"""
        def convert_dataclass(obj):
            if hasattr(obj, '__dict__'):
                return obj.__dict__
            return str(obj)
        
        return json.dumps(entities, default=convert_dataclass, indent=2)


# Convenience function
def extract_clinical_entities(text: str) -> Dict:
    """
    Quick function to extract clinical entities from text
    
    Args:
        text: Medical document text
        
    Returns:
        Dictionary of extracted entities
    """
    extractor = ClinicalEntityExtractor()
    return extractor.extract_entities(text)
