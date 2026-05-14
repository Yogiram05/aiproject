"""
Medical Code Mapper
Maps diagnoses to ICD-10, lab tests to LOINC, medications to standard codes
"""

import json
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from fuzzywuzzy import fuzz, process
import logging


@dataclass
class ICD10Code:
    """ICD-10 Code Information"""
    code: str
    description: str
    category: str
    confidence: float = 0.0


@dataclass
class LOINCCode:
    """LOINC Code Information"""
    code: str
    long_name: str
    short_name: str
    component: str
    confidence: float = 0.0


class MedicalCodeMapper:
    """
    Maps medical entities to standard medical codes
    - Diagnoses → ICD-10-CM
    - Lab Tests → LOINC
    - Medications → Standard Drug Codes
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._load_code_databases()
    
    def _load_code_databases(self):
        """Load medical code databases"""
        
        # ICD-10-CM codes (sample - expand this significantly)
        self.icd10_codes = {
            # Infectious diseases
            "dengue fever": ICD10Code("A97.9", "Dengue fever", "Infectious"),
            "dengue": ICD10Code("A97.9", "Dengue fever", "Infectious"),
            "malaria": ICD10Code("B54", "Unspecified malaria", "Infectious"),
            "typhoid": ICD10Code("A01.0", "Typhoid fever", "Infectious"),
            "tuberculosis": ICD10Code("A15.9", "Respiratory tuberculosis", "Infectious"),
            "tb": ICD10Code("A15.9", "Respiratory tuberculosis", "Infectious"),
            "covid-19": ICD10Code("U07.1", "COVID-19", "Infectious"),
            "covid": ICD10Code("U07.1", "COVID-19", "Infectious"),
            
            # Respiratory
            "upper respiratory tract infection": ICD10Code("J06.9", "Acute upper respiratory infection", "Respiratory"),
            "urti": ICD10Code("J06.9", "Acute upper respiratory infection", "Respiratory"),
            "pneumonia": ICD10Code("J18.9", "Pneumonia, unspecified", "Respiratory"),
            "asthma": ICD10Code("J45.909", "Unspecified asthma", "Respiratory"),
            "copd": ICD10Code("J44.9", "Chronic obstructive pulmonary disease", "Respiratory"),
            "bronchitis": ICD10Code("J40", "Bronchitis", "Respiratory"),
            
            # Metabolic
            "diabetes mellitus": ICD10Code("E11.9", "Type 2 diabetes mellitus", "Metabolic"),
            "diabetes": ICD10Code("E11.9", "Type 2 diabetes mellitus", "Metabolic"),
            "type 1 diabetes": ICD10Code("E10.9", "Type 1 diabetes mellitus", "Metabolic"),
            "type 2 diabetes": ICD10Code("E11.9", "Type 2 diabetes mellitus", "Metabolic"),
            
            # Cardiovascular
            "hypertension": ICD10Code("I10", "Essential (primary) hypertension", "Cardiovascular"),
            "essential hypertension": ICD10Code("I10", "Essential (primary) hypertension", "Cardiovascular"),
            "myocardial infarction": ICD10Code("I21.9", "Acute myocardial infarction", "Cardiovascular"),
            "heart attack": ICD10Code("I21.9", "Acute myocardial infarction", "Cardiovascular"),
            "angina": ICD10Code("I20.9", "Angina pectoris", "Cardiovascular"),
            
            # Gastrointestinal
            "gastroenteritis": ICD10Code("K52.9", "Gastroenteritis and colitis", "Gastrointestinal"),
            "gastritis": ICD10Code("K29.70", "Gastritis", "Gastrointestinal"),
            "peptic ulcer": ICD10Code("K27.9", "Peptic ulcer", "Gastrointestinal"),
            
            # Urinary
            "urinary tract infection": ICD10Code("N39.0", "Urinary tract infection", "Urinary"),
            "uti": ICD10Code("N39.0", "Urinary tract infection", "Urinary"),
            
            # General symptoms
            "fever": ICD10Code("R50.9", "Fever, unspecified", "Symptoms"),
            "headache": ICD10Code("R51", "Headache", "Symptoms"),
            "pain": ICD10Code("R52", "Pain, unspecified", "Symptoms"),
            "cough": ICD10Code("R05", "Cough", "Symptoms"),
            "fatigue": ICD10Code("R53.83", "Fatigue", "Symptoms"),
        }
        
        # LOINC codes for common lab tests (sample - expand this)
        self.loinc_codes = {
            "hemoglobin": LOINCCode("718-7", "Hemoglobin [Mass/volume] in Blood", "Hemoglobin", "Hematology"),
            "hb": LOINCCode("718-7", "Hemoglobin [Mass/volume] in Blood", "Hb", "Hematology"),
            "wbc": LOINCCode("6690-2", "Leukocytes [#/volume] in Blood", "WBC", "Hematology"),
            "white blood cell count": LOINCCode("6690-2", "Leukocytes [#/volume] in Blood", "WBC", "Hematology"),
            "rbc": LOINCCode("789-8", "Erythrocytes [#/volume] in Blood", "RBC", "Hematology"),
            "platelet count": LOINCCode("777-3", "Platelets [#/volume] in Blood", "Platelets", "Hematology"),
            "platelet": LOINCCode("777-3", "Platelets [#/volume] in Blood", "Platelets", "Hematology"),
            
            # Chemistry
            "glucose": LOINCCode("2345-7", "Glucose [Mass/volume] in Serum or Plasma", "Glucose", "Chemistry"),
            "fasting blood sugar": LOINCCode("1558-6", "Fasting glucose [Mass/volume] in Serum or Plasma", "FBS", "Chemistry"),
            "fbs": LOINCCode("1558-6", "Fasting glucose [Mass/volume] in Serum or Plasma", "FBS", "Chemistry"),
            "hba1c": LOINCCode("4548-4", "Hemoglobin A1c/Hemoglobin.total in Blood", "HbA1c", "Chemistry"),
            "cholesterol": LOINCCode("2093-3", "Cholesterol [Mass/volume] in Serum or Plasma", "Cholesterol", "Chemistry"),
            "total cholesterol": LOINCCode("2093-3", "Cholesterol [Mass/volume] in Serum or Plasma", "Total Chol", "Chemistry"),
            "hdl": LOINCCode("2085-9", "HDL Cholesterol [Mass/volume] in Serum or Plasma", "HDL", "Chemistry"),
            "ldl": LOINCCode("2089-1", "LDL Cholesterol [Mass/volume] in Serum or Plasma", "LDL", "Chemistry"),
            "triglycerides": LOINCCode("2571-8", "Triglyceride [Mass/volume] in Serum or Plasma", "Triglycerides", "Chemistry"),
            
            # Liver function
            "sgot": LOINCCode("1920-8", "Aspartate aminotransferase [Enzymatic activity/volume] in Serum or Plasma", "SGOT/AST", "Liver"),
            "sgpt": LOINCCode("1742-6", "Alanine aminotransferase [Enzymatic activity/volume] in Serum or Plasma", "SGPT/ALT", "Liver"),
            "alt": LOINCCode("1742-6", "Alanine aminotransferase [Enzymatic activity/volume] in Serum or Plasma", "ALT", "Liver"),
            "ast": LOINCCode("1920-8", "Aspartate aminotransferase [Enzymatic activity/volume] in Serum or Plasma", "AST", "Liver"),
            "bilirubin": LOINCCode("1975-2", "Bilirubin.total [Mass/volume] in Serum or Plasma", "Total Bilirubin", "Liver"),
            
            # Kidney function
            "creatinine": LOINCCode("2160-0", "Creatinine [Mass/volume] in Serum or Plasma", "Creatinine", "Kidney"),
            "urea": LOINCCode("3094-0", "Urea nitrogen [Mass/volume] in Serum or Plasma", "BUN", "Kidney"),
            
            # Thyroid
            "tsh": LOINCCode("3016-3", "Thyrotropin [Units/volume] in Serum or Plasma", "TSH", "Thyroid"),
            "t3": LOINCCode("3051-0", "Triiodothyronine (T3) [Mass/volume] in Serum or Plasma", "T3", "Thyroid"),
            "t4": LOINCCode("3053-6", "Thyroxine (T4) [Mass/volume] in Serum or Plasma", "T4", "Thyroid"),
            
            # Vitamins
            "vitamin d": LOINCCode("1989-3", "Vitamin D [Mass/volume] in Serum or Plasma", "Vitamin D", "Vitamins"),
            "vitamin b12": LOINCCode("2132-9", "Vitamin B12 [Mass/volume] in Serum or Plasma", "B12", "Vitamins"),
            
            # Inflammatory markers
            "crp": LOINCCode("1988-5", "C reactive protein [Mass/volume] in Serum or Plasma", "CRP", "Inflammatory"),
            "esr": LOINCCode("4537-7", "Erythrocyte sedimentation rate", "ESR", "Inflammatory"),
            
            # Infectious disease tests
            "dengue ns1": LOINCCode("75365-4", "Dengue virus NS1 Ag [Presence] in Serum", "Dengue NS1", "Infectious"),
            "malaria antigen": LOINCCode("32700-7", "Malaria Ag [Presence] in Blood", "Malaria Ag", "Infectious"),
        }
        
        # SNOMED CT codes (sample)
        self.snomed_codes = {}
        
        # Drug codes (sample)
        self.drug_codes = {}
    
    def map_diagnosis_to_icd10(
        self,
        diagnosis_name: str,
        fuzzy_threshold: int = 80
    ) -> Optional[ICD10Code]:
        """
        Map diagnosis to ICD-10 code
        
        Args:
            diagnosis_name: Diagnosis text
            fuzzy_threshold: Minimum fuzzy match score (0-100)
            
        Returns:
            ICD10Code if found, None otherwise
        """
        diagnosis_lower = diagnosis_name.lower().strip()
        
        # Direct match
        if diagnosis_lower in self.icd10_codes:
            code = self.icd10_codes[diagnosis_lower]
            code.confidence = 1.0
            return code
        
        # Fuzzy match
        best_match = process.extractOne(
            diagnosis_lower,
            self.icd10_codes.keys(),
            scorer=fuzz.token_set_ratio,
            score_cutoff=fuzzy_threshold
        )
        
        if best_match:
            matched_key, score = best_match[0], best_match[1]
            code = self.icd10_codes[matched_key]
            code.confidence = score / 100.0
            return code
        
        return None
    
    def map_lab_test_to_loinc(
        self,
        test_name: str,
        fuzzy_threshold: int = 80
    ) -> Optional[LOINCCode]:
        """
        Map lab test to LOINC code
        
        Args:
            test_name: Lab test name
            fuzzy_threshold: Minimum fuzzy match score (0-100)
            
        Returns:
            LOINCCode if found, None otherwise
        """
        test_lower = test_name.lower().strip()
        
        # Direct match
        if test_lower in self.loinc_codes:
            code = self.loinc_codes[test_lower]
            code.confidence = 1.0
            return code
        
        # Fuzzy match
        best_match = process.extractOne(
            test_lower,
            self.loinc_codes.keys(),
            scorer=fuzz.token_set_ratio,
            score_cutoff=fuzzy_threshold
        )
        
        if best_match:
            matched_key, score = best_match[0], best_match[1]
            code = self.loinc_codes[matched_key]
            code.confidence = score / 100.0
            return code
        
        return None
    
    def batch_map_diagnoses(
        self,
        diagnoses: List[str]
    ) -> Dict[str, Optional[ICD10Code]]:
        """Map multiple diagnoses to ICD-10 codes"""
        results = {}
        for diagnosis in diagnoses:
            results[diagnosis] = self.map_diagnosis_to_icd10(diagnosis)
        return results
    
    def batch_map_lab_tests(
        self,
        tests: List[str]
    ) -> Dict[str, Optional[LOINCCode]]:
        """Map multiple lab tests to LOINC codes"""
        results = {}
        for test in tests:
            results[test] = self.map_lab_test_to_loinc(test)
        return results
    
    def get_icd10_info(self, icd10_code: str) -> Optional[ICD10Code]:
        """Get ICD-10 code information by code"""
        for code_info in self.icd10_codes.values():
            if code_info.code == icd10_code:
                return code_info
        return None
    
    def get_loinc_info(self, loinc_code: str) -> Optional[LOINCCode]:
        """Get LOINC code information by code"""
        for code_info in self.loinc_codes.values():
            if code_info.code == loinc_code:
                return code_info
        return None
    
    def search_icd10(self, query: str, limit: int = 10) -> List[ICD10Code]:
        """Search ICD-10 codes by query"""
        matches = process.extract(
            query.lower(),
            self.icd10_codes.keys(),
            scorer=fuzz.token_set_ratio,
            limit=limit
        )
        
        results = []
        for match in matches:
            matched_key, score = match[0], match[1]
            code = self.icd10_codes[matched_key]
            code.confidence = score / 100.0
            results.append(code)
        
        return results
    
    def search_loinc(self, query: str, limit: int = 10) -> List[LOINCCode]:
        """Search LOINC codes by query"""
        matches = process.extract(
            query.lower(),
            self.loinc_codes.keys(),
            scorer=fuzz.token_set_ratio,
            limit=limit
        )
        
        results = []
        for match in matches:
            matched_key, score = match[0], match[1]
            code = self.loinc_codes[matched_key]
            code.confidence = score / 100.0
            results.append(code)
        
        return results


# Convenience functions
def get_icd10_code(diagnosis: str) -> Optional[str]:
    """Get ICD-10 code for a diagnosis"""
    mapper = MedicalCodeMapper()
    result = mapper.map_diagnosis_to_icd10(diagnosis)
    return result.code if result else None


def get_loinc_code(test_name: str) -> Optional[str]:
    """Get LOINC code for a lab test"""
    mapper = MedicalCodeMapper()
    result = mapper.map_lab_test_to_loinc(test_name)
    return result.code if result else None
