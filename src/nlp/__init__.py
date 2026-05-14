"""NLP Module Initialization"""
from .entity_extractor import (
    ClinicalEntityExtractor,
    MedicalEntity,
    Medication,
    LabTest,
    Diagnosis,
    extract_clinical_entities
)
from .code_mapper import MedicalCodeMapper, ICD10Code, LOINCCode, get_icd10_code, get_loinc_code

__all__ = [
    'ClinicalEntityExtractor',
    'MedicalEntity',
    'Medication',
    'LabTest',
    'Diagnosis',
    'extract_clinical_entities',
    'MedicalCodeMapper',
    'ICD10Code',
    'LOINCCode',
    'get_icd10_code',
    'get_loinc_code'
]
