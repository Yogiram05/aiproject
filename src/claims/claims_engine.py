"""
Claims Automation Module
Implements rule-based claim validation and eligibility scoring
"""

import yaml
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import logging


class ClaimDecision(Enum):
    """Claim decision types"""
    ELIGIBLE = "eligible"
    QUERY = "query"
    REJECT = "reject"


@dataclass
class ClaimRule:
    """Insurance claim validation rule"""
    rule_id: str
    name: str
    condition: str
    action: str
    message: str
    priority: int = 1


@dataclass
class ClaimResult:
    """Claim validation result"""
    decision: ClaimDecision
    confidence: float
    reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    approved_amount: Optional[float] = None
    rejected_items: List[str] = field(default_factory=list)
    required_documents: List[str] = field(default_factory=list)


class ClaimsAutomationEngine:
    """
    Automated Claims Processing Engine
    Validates claims against insurance policy rules
    """
    
    def __init__(self, rules_file: Optional[str] = None):
        """
        Initialize Claims Automation Engine
        
        Args:
            rules_file: Path to YAML file containing insurance rules
        """
        self.logger = logging.getLogger(__name__)
        self.rules = []
        
        if rules_file:
            self.load_rules_from_file(rules_file)
        else:
            self._load_default_rules()
    
    def _load_default_rules(self):
        """Load default Indian health insurance rules"""
        self.rules = [
            # Dengue testing rules
            ClaimRule(
                rule_id="DENGUE_001",
                name="Dengue NS1 Test Coverage",
                condition="dengue_ns1_test",
                action="require_fever_duration",
                message="Dengue NS1 test covered only if fever duration > 3 days",
                priority=1
            ),
            
            # Diabetes management
            ClaimRule(
                rule_id="DIABETES_001",
                name="HbA1c Test Frequency",
                condition="hba1c_test",
                action="check_frequency",
                message="HbA1c test covered once every 3 months for diabetic patients",
                priority=1
            ),
            
            # Pre-existing conditions
            ClaimRule(
                rule_id="PREEXIST_001",
                name="Pre-existing Waiting Period",
                condition="pre_existing_condition",
                action="check_waiting_period",
                message="Pre-existing conditions covered after 24-48 months waiting period",
                priority=1
            ),
            
            # Prescription rules
            ClaimRule(
                rule_id="PRESCR_001",
                name="Prescription Validity",
                condition="medication_claim",
                action="require_prescription",
                message="Prescription required for medication claims",
                priority=1
            ),
            
            # Hospitalization
            ClaimRule(
                rule_id="HOSP_001",
                name="Minimum Hospitalization Duration",
                condition="hospitalization",
                action="check_duration",
                message="Minimum 24 hours hospitalization required for claim",
                priority=1
            ),
            
            # Lab tests frequency
            ClaimRule(
                rule_id="LAB_001",
                name="Routine Lab Test Frequency",
                condition="routine_lab_tests",
                action="check_frequency",
                message="Routine lab tests covered once per year",
                priority=2
            ),
            
            # Duplicate claims
            ClaimRule(
                rule_id="DUP_001",
                name="Duplicate Claim Prevention",
                condition="duplicate_claim",
                action="reject",
                message="Duplicate claim detected",
                priority=1
            ),
            
            # Maximum dosage limits
            ClaimRule(
                rule_id="DOSAGE_001",
                name="Maximum Dosage Limit",
                condition="medication_dosage",
                action="check_limit",
                message="Dosage exceeds safe limits",
                priority=1
            ),
            
            # Age-based restrictions
            ClaimRule(
                rule_id="AGE_001",
                name="Age-based Coverage",
                condition="patient_age",
                action="check_age_limits",
                message="Treatment not covered for specified age group",
                priority=2
            ),
            
            # Sum insured limit
            ClaimRule(
                rule_id="LIMIT_001",
                name="Sum Insured Limit",
                condition="claim_amount",
                action="check_sum_insured",
                message="Claim amount exceeds sum insured limit",
                priority=1
            ),
        ]
    
    def load_rules_from_file(self, file_path: str):
        """Load rules from YAML file"""
        try:
            with open(file_path, 'r') as f:
                rules_data = yaml.safe_load(f)
            
            self.rules = []
            for rule_dict in rules_data.get('rules', []):
                self.rules.append(ClaimRule(**rule_dict))
            
            self.logger.info(f"Loaded {len(self.rules)} rules from {file_path}")
        except Exception as e:
            self.logger.error(f"Error loading rules: {str(e)}")
            self._load_default_rules()
    
    def validate_claim(
        self,
        claim_data: Dict,
        policy_data: Optional[Dict] = None
    ) -> ClaimResult:
        """
        Validate insurance claim
        
        Args:
            claim_data: Claim information including diagnoses, medications, tests
            policy_data: Insurance policy details
            
        Returns:
            ClaimResult with decision and details
        """
        result = ClaimResult(
            decision=ClaimDecision.ELIGIBLE,
            confidence=1.0
        )
        
        # Apply validation rules
        for rule in sorted(self.rules, key=lambda x: x.priority):
            rule_result = self._apply_rule(rule, claim_data, policy_data)
            
            if rule_result:
                result.reasons.append(rule_result)
        
        # Determine overall decision
        result.decision, result.confidence = self._determine_decision(result.reasons)
        
        # Calculate approved amount
        result.approved_amount = self._calculate_approved_amount(
            claim_data,
            result.decision,
            policy_data
        )
        
        return result
    
    def _apply_rule(
        self,
        rule: ClaimRule,
        claim_data: Dict,
        policy_data: Optional[Dict]
    ) -> Optional[str]:
        """Apply a single validation rule"""
        
        # Check for dengue test
        if rule.rule_id == "DENGUE_001":
            if self._has_dengue_test(claim_data):
                fever_duration = claim_data.get('fever_duration_days', 0)
                if fever_duration <= 3:
                    return f"QUERY: {rule.message}"
        
        # Check HbA1c frequency
        elif rule.rule_id == "DIABETES_001":
            if self._has_hba1c_test(claim_data):
                last_test_date = claim_data.get('last_hba1c_date')
                if last_test_date:
                    days_since = (datetime.now() - datetime.fromisoformat(last_test_date)).days
                    if days_since < 90:
                        return f"REJECT: {rule.message}"
        
        # Check for duplicate claims
        elif rule.rule_id == "DUP_001":
            if self._is_duplicate_claim(claim_data):
                return f"REJECT: {rule.message}"
        
        # Check prescription requirement
        elif rule.rule_id == "PRESCR_001":
            if claim_data.get('medications') and not claim_data.get('has_prescription'):
                return f"QUERY: {rule.message}"
        
        # Check hospitalization duration
        elif rule.rule_id == "HOSP_001":
            if claim_data.get('is_hospitalization'):
                duration = claim_data.get('hospitalization_hours', 0)
                if duration < 24:
                    return f"REJECT: {rule.message}"
        
        # Check sum insured limit
        elif rule.rule_id == "LIMIT_001":
            if policy_data:
                claim_amount = claim_data.get('total_amount', 0)
                sum_insured = policy_data.get('sum_insured', float('inf'))
                utilized = policy_data.get('utilized_amount', 0)
                
                if claim_amount + utilized > sum_insured:
                    return f"REJECT: {rule.message} (Available: {sum_insured - utilized})"
        
        # Check dosage limits
        elif rule.rule_id == "DOSAGE_001":
            if self._check_dosage_limits(claim_data):
                return f"QUERY: {rule.message}"
        
        return None
    
    def _has_dengue_test(self, claim_data: Dict) -> bool:
        """Check if claim includes dengue test"""
        lab_tests = claim_data.get('lab_tests', [])
        return any('dengue' in str(test).lower() for test in lab_tests)
    
    def _has_hba1c_test(self, claim_data: Dict) -> bool:
        """Check if claim includes HbA1c test"""
        lab_tests = claim_data.get('lab_tests', [])
        return any('hba1c' in str(test).lower() or 'a1c' in str(test).lower() for test in lab_tests)
    
    def _is_duplicate_claim(self, claim_data: Dict) -> bool:
        """Check for duplicate claims"""
        # In real implementation, check against database
        return claim_data.get('is_duplicate', False)
    
    def _check_dosage_limits(self, claim_data: Dict) -> bool:
        """Check if dosages exceed safe limits"""
        medications = claim_data.get('medications', [])
        
        # Sample dosage limits
        dosage_limits = {
            'paracetamol': 4000,  # mg per day
            'ibuprofen': 3200,
            'aspirin': 4000,
        }
        
        for med in medications:
            med_name = med.get('name', '').lower()
            dosage = self._extract_numeric_dosage(med.get('dosage', ''))
            
            for drug, limit in dosage_limits.items():
                if drug in med_name and dosage > limit:
                    return True
        
        return False
    
    def _extract_numeric_dosage(self, dosage_str: str) -> float:
        """Extract numeric dosage value"""
        import re
        match = re.search(r'(\d+\.?\d*)', str(dosage_str))
        return float(match.group(1)) if match else 0.0
    
    def _determine_decision(
        self,
        reasons: List[str]
    ) -> Tuple[ClaimDecision, float]:
        """Determine overall claim decision based on rule results"""
        
        if not reasons:
            return ClaimDecision.ELIGIBLE, 1.0
        
        # Count decision types
        rejects = sum(1 for r in reasons if r.startswith('REJECT'))
        queries = sum(1 for r in reasons if r.startswith('QUERY'))
        
        if rejects > 0:
            confidence = 1.0 - (queries * 0.1)
            return ClaimDecision.REJECT, max(confidence, 0.7)
        elif queries > 0:
            confidence = 0.8 - (queries * 0.1)
            return ClaimDecision.QUERY, max(confidence, 0.5)
        else:
            return ClaimDecision.ELIGIBLE, 1.0
    
    def _calculate_approved_amount(
        self,
        claim_data: Dict,
        decision: ClaimDecision,
        policy_data: Optional[Dict]
    ) -> Optional[float]:
        """Calculate approved claim amount"""
        
        total_amount = claim_data.get('total_amount', 0)
        
        if decision == ClaimDecision.REJECT:
            return 0.0
        elif decision == ClaimDecision.QUERY:
            # Approve partial amount pending clarification
            return total_amount * 0.5
        else:
            # Check co-payment
            if policy_data:
                copay_percent = policy_data.get('copay_percent', 0)
                return total_amount * (1 - copay_percent / 100)
            return total_amount
    
    def generate_claim_summary(
        self,
        claim_data: Dict,
        result: ClaimResult
    ) -> str:
        """Generate human-readable claim summary"""
        
        summary = []
        summary.append("=" * 60)
        summary.append("CLAIM PROCESSING SUMMARY")
        summary.append("=" * 60)
        summary.append("")
        
        # Decision
        summary.append(f"Decision: {result.decision.value.upper()}")
        summary.append(f"Confidence: {result.confidence * 100:.1f}%")
        summary.append("")
        
        # Approved Amount
        if result.approved_amount is not None:
            claimed = claim_data.get('total_amount', 0)
            summary.append(f"Claimed Amount: ₹{claimed:,.2f}")
            summary.append(f"Approved Amount: ₹{result.approved_amount:,.2f}")
            summary.append("")
        
        # Reasons
        if result.reasons:
            summary.append("Validation Results:")
            for i, reason in enumerate(result.reasons, 1):
                summary.append(f"{i}. {reason}")
            summary.append("")
        
        # Warnings
        if result.warnings:
            summary.append("Warnings:")
            for warning in result.warnings:
                summary.append(f"⚠ {warning}")
            summary.append("")
        
        # Required Documents
        if result.required_documents:
            summary.append("Required Documents:")
            for doc in result.required_documents:
                summary.append(f"📄 {doc}")
            summary.append("")
        
        summary.append("=" * 60)
        
        return "\n".join(summary)
    
    def export_result_json(self, result: ClaimResult) -> str:
        """Export claim result as JSON"""
        result_dict = {
            "decision": result.decision.value,
            "confidence": result.confidence,
            "approved_amount": result.approved_amount,
            "reasons": result.reasons,
            "warnings": result.warnings,
            "rejected_items": result.rejected_items,
            "required_documents": result.required_documents,
            "timestamp": datetime.now().isoformat()
        }
        
        return json.dumps(result_dict, indent=2)


# Convenience function
def process_claim(
    claim_data: Dict,
    policy_data: Optional[Dict] = None
) -> ClaimResult:
    """
    Quick function to process a claim
    
    Args:
        claim_data: Claim information
        policy_data: Policy details
        
    Returns:
        ClaimResult
    """
    engine = ClaimsAutomationEngine()
    return engine.validate_claim(claim_data, policy_data)
