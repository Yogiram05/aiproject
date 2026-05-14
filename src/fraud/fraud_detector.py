"""
Fraud Detection Module
Detects suspicious patterns in medical claims
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict
import logging


@dataclass
class FraudAlert:
    """Fraud detection alert"""
    alert_type: str
    severity: str  # low, medium, high, critical
    description: str
    confidence: float
    evidence: List[str]
    recommendation: str


class FraudDetector:
    """
    Detects fraud and anomalies in medical claims
    - Duplicate submissions
    - Dosage anomalies
    - Unusual billing patterns
    - Impossible medical scenarios
    """
    
    def __init__(self, fraud_threshold: float = 0.75):
        """
        Initialize Fraud Detector
        
        Args:
            fraud_threshold: Minimum confidence score to flag as fraudulent (0-1)
        """
        self.fraud_threshold = fraud_threshold
        self.logger = logging.getLogger(__name__)
        
        # Historical claims cache (in production, use database)
        self.claims_history = []
    
    def analyze_claim(
        self,
        claim_data: Dict,
        historical_claims: Optional[List[Dict]] = None
    ) -> Tuple[List[FraudAlert], float]:
        """
        Analyze claim for fraud patterns
        
        Args:
            claim_data: Current claim information
            historical_claims: Previous claims for comparison
            
        Returns:
            Tuple of (fraud alerts, overall fraud score)
        """
        alerts = []
        
        # Use provided history or internal cache
        if historical_claims:
            self.claims_history = historical_claims
        
        # Run fraud detection checks
        alerts.extend(self._check_duplicate_claims(claim_data))
        alerts.extend(self._check_dosage_anomalies(claim_data))
        alerts.extend(self._check_billing_patterns(claim_data))
        alerts.extend(self._check_impossible_scenarios(claim_data))
        alerts.extend(self._check_frequency_anomalies(claim_data))
        alerts.extend(self._check_prescription_fraud(claim_data))
        
        # Calculate overall fraud score
        fraud_score = self._calculate_fraud_score(alerts)
        
        return alerts, fraud_score
    
    def _check_duplicate_claims(self, claim_data: Dict) -> List[FraudAlert]:
        """Check for duplicate claim submissions"""
        alerts = []
        
        # Check against historical claims
        for historical_claim in self.claims_history:
            similarity = self._calculate_claim_similarity(claim_data, historical_claim)
            
            if similarity > 0.9:
                # Check time difference
                current_date = datetime.now()
                hist_date_str = historical_claim.get('date', current_date.isoformat())
                
                try:
                    hist_date = datetime.fromisoformat(hist_date_str)
                    days_diff = (current_date - hist_date).days
                    
                    if days_diff < 30:  # Same claim within 30 days
                        alerts.append(FraudAlert(
                            alert_type="duplicate_claim",
                            severity="high",
                            description=f"Potential duplicate claim detected (submitted {days_diff} days ago)",
                            confidence=similarity,
                            evidence=[
                                f"Similarity: {similarity * 100:.1f}%",
                                f"Previous submission: {hist_date.strftime('%Y-%m-%d')}"
                            ],
                            recommendation="Verify if this is a resubmission or duplicate claim"
                        ))
                except:
                    pass
        
        return alerts
    
    def _check_dosage_anomalies(self, claim_data: Dict) -> List[FraudAlert]:
        """Check for unsafe or unusual dosages"""
        alerts = []
        
        # Maximum safe dosages (mg per day)
        max_dosages = {
            'paracetamol': 4000,
            'acetaminophen': 4000,
            'ibuprofen': 3200,
            'aspirin': 4000,
            'metformin': 2550,
            'amlodipine': 10,
            'atorvastatin': 80,
        }
        
        medications = claim_data.get('medications', [])
        
        for med in medications:
            med_name = str(med.get('name', '')).lower()
            dosage_str = str(med.get('dosage', ''))
            
            # Extract numeric dosage
            import re
            dosage_match = re.search(r'(\d+\.?\d*)\s*mg', dosage_str, re.IGNORECASE)
            
            if dosage_match:
                dosage = float(dosage_match.group(1))
                
                # Check frequency to calculate daily dosage
                frequency = str(med.get('frequency', '')).lower()
                times_per_day = self._extract_frequency(frequency)
                daily_dosage = dosage * times_per_day
                
                # Check against limits
                for drug, max_dose in max_dosages.items():
                    if drug in med_name and daily_dosage > max_dose:
                        alerts.append(FraudAlert(
                            alert_type="dosage_anomaly",
                            severity="critical",
                            description=f"Dosage exceeds safe limits for {med_name}",
                            confidence=0.95,
                            evidence=[
                                f"Daily dosage: {daily_dosage} mg",
                                f"Maximum safe dosage: {max_dose} mg",
                                f"Excess: {daily_dosage - max_dose} mg"
                            ],
                            recommendation="Verify prescription authenticity and dosage"
                        ))
        
        return alerts
    
    def _check_billing_patterns(self, claim_data: Dict) -> List[FraudAlert]:
        """Check for unusual billing patterns"""
        alerts = []
        
        total_amount = claim_data.get('total_amount', 0)
        
        # Check for round numbers (potential overbilling)
        if total_amount > 0 and total_amount % 1000 == 0 and total_amount >= 5000:
            alerts.append(FraudAlert(
                alert_type="suspicious_billing",
                severity="medium",
                description="Bill amount is a perfect round number",
                confidence=0.65,
                evidence=[f"Amount: ₹{total_amount:,.2f}"],
                recommendation="Review itemized bill for accuracy"
            ))
        
        # Check for unusually high amounts
        medications = claim_data.get('medications', [])
        lab_tests = claim_data.get('lab_tests', [])
        
        # Estimate expected cost
        expected_cost = (len(medications) * 100) + (len(lab_tests) * 500)
        
        if total_amount > expected_cost * 5:  # 5x expected cost
            alerts.append(FraudAlert(
                alert_type="overbilling",
                severity="high",
                description="Bill amount significantly exceeds expected cost",
                confidence=0.80,
                evidence=[
                    f"Claimed: ₹{total_amount:,.2f}",
                    f"Expected: ₹{expected_cost:,.2f}",
                    f"Difference: ₹{total_amount - expected_cost:,.2f}"
                ],
                recommendation="Request itemized bill and verify costs"
            ))
        
        return alerts
    
    def _check_impossible_scenarios(self, claim_data: Dict) -> List[FraudAlert]:
        """Check for medically impossible scenarios"""
        alerts = []
        
        diagnoses = [str(d).lower() for d in claim_data.get('diagnoses', [])]
        medications = [str(m.get('name', '')).lower() for m in claim_data.get('medications', [])]
        
        # Check for conflicting diagnoses
        conflicting_pairs = [
            (['diabetes', 'diabetic'], ['hypoglycemia']),
            (['hypertension'], ['hypotension']),
        ]
        
        for condition_group1, condition_group2 in conflicting_pairs:
            has_condition1 = any(
                any(cond in diag for cond in condition_group1)
                for diag in diagnoses
            )
            has_condition2 = any(
                any(cond in diag for cond in condition_group2)
                for diag in diagnoses
            )
            
            if has_condition1 and has_condition2:
                alerts.append(FraudAlert(
                    alert_type="conflicting_diagnosis",
                    severity="medium",
                    description="Conflicting diagnoses detected",
                    confidence=0.70,
                    evidence=diagnoses,
                    recommendation="Verify diagnoses with healthcare provider"
                ))
        
        # Check for inappropriate medication-diagnosis combinations
        # Example: Insulin without diabetes diagnosis
        if any('insulin' in med for med in medications):
            if not any('diabetes' in diag for diag in diagnoses):
                alerts.append(FraudAlert(
                    alert_type="medication_diagnosis_mismatch",
                    severity="medium",
                    description="Insulin prescribed without diabetes diagnosis",
                    confidence=0.75,
                    evidence=["Insulin in medications", "No diabetes in diagnoses"],
                    recommendation="Verify prescription and diagnosis"
                ))
        
        return alerts
    
    def _check_frequency_anomalies(self, claim_data: Dict) -> List[FraudAlert]:
        """Check for unusual claim frequency"""
        alerts = []
        
        # Count recent claims in history
        current_date = datetime.now()
        recent_claims = 0
        
        for hist_claim in self.claims_history:
            hist_date_str = hist_claim.get('date', current_date.isoformat())
            try:
                hist_date = datetime.fromisoformat(hist_date_str)
                days_diff = (current_date - hist_date).days
                
                if days_diff <= 30:  # Last 30 days
                    recent_claims += 1
            except:
                pass
        
        # Flag if too many claims
        if recent_claims > 5:
            alerts.append(FraudAlert(
                alert_type="high_frequency",
                severity="medium",
                description=f"Unusually high claim frequency ({recent_claims} claims in 30 days)",
                confidence=0.70,
                evidence=[f"{recent_claims} claims in last 30 days"],
                recommendation="Review patient history and claim patterns"
            ))
        
        return alerts
    
    def _check_prescription_fraud(self, claim_data: Dict) -> List[FraudAlert]:
        """Check for prescription-related fraud"""
        alerts = []
        
        medications = claim_data.get('medications', [])
        has_prescription = claim_data.get('has_prescription', False)
        
        # Check if prescription is required but not provided
        prescription_required_meds = [
            'antibiotic', 'azithromycin', 'amoxicillin', 'ciprofloxacin',
            'insulin', 'metformin', 'controlled substance'
        ]
        
        for med in medications:
            med_name = str(med.get('name', '')).lower()
            
            if any(drug in med_name for drug in prescription_required_meds):
                if not has_prescription:
                    alerts.append(FraudAlert(
                        alert_type="missing_prescription",
                        severity="high",
                        description="Prescription-only medication without valid prescription",
                        confidence=0.85,
                        evidence=[f"Medication: {med_name}"],
                        recommendation="Request valid prescription document"
                    ))
        
        return alerts
    
    def _calculate_claim_similarity(
        self,
        claim1: Dict,
        claim2: Dict
    ) -> float:
        """Calculate similarity between two claims (0-1)"""
        similarity_score = 0.0
        weights = {
            'amount': 0.3,
            'medications': 0.3,
            'diagnoses': 0.2,
            'lab_tests': 0.2
        }
        
        # Amount similarity
        amount1 = claim1.get('total_amount', 0)
        amount2 = claim2.get('total_amount', 0)
        if amount1 and amount2:
            amount_diff = abs(amount1 - amount2) / max(amount1, amount2)
            similarity_score += weights['amount'] * (1 - amount_diff)
        
        # Medication similarity
        meds1 = set(str(m.get('name', '')).lower() for m in claim1.get('medications', []))
        meds2 = set(str(m.get('name', '')).lower() for m in claim2.get('medications', []))
        if meds1 or meds2:
            med_similarity = len(meds1 & meds2) / max(len(meds1 | meds2), 1)
            similarity_score += weights['medications'] * med_similarity
        
        return min(similarity_score, 1.0)
    
    def _extract_frequency(self, frequency_str: str) -> int:
        """Extract number of times per day from frequency string"""
        freq_lower = frequency_str.lower()
        
        if 'once' in freq_lower or 'od' in freq_lower or 'qd' in freq_lower:
            return 1
        elif 'twice' in freq_lower or 'bd' in freq_lower or 'bid' in freq_lower:
            return 2
        elif 'thrice' in freq_lower or 'td' in freq_lower or 'tid' in freq_lower:
            return 3
        elif 'qid' in freq_lower or 'four times' in freq_lower:
            return 4
        
        # Try to extract number
        import re
        match = re.search(r'(\d+)\s*times', freq_lower)
        if match:
            return int(match.group(1))
        
        return 1  # Default
    
    def _calculate_fraud_score(self, alerts: List[FraudAlert]) -> float:
        """Calculate overall fraud score based on alerts"""
        if not alerts:
            return 0.0
        
        severity_weights = {
            'low': 0.25,
            'medium': 0.50,
            'high': 0.75,
            'critical': 1.0
        }
        
        total_score = 0.0
        for alert in alerts:
            weight = severity_weights.get(alert.severity, 0.5)
            total_score += alert.confidence * weight
        
        # Normalize to 0-1 range
        return min(total_score / len(alerts), 1.0)
    
    def generate_fraud_report(
        self,
        alerts: List[FraudAlert],
        fraud_score: float
    ) -> str:
        """Generate fraud detection report"""
        report = []
        report.append("=" * 60)
        report.append("FRAUD DETECTION REPORT")
        report.append("=" * 60)
        report.append(f"Timestamp: {datetime.now().isoformat()}")
        report.append(f"Overall Fraud Score: {fraud_score * 100:.1f}%")
        report.append(f"Risk Level: {self._get_risk_level(fraud_score)}")
        report.append("")
        
        if alerts:
            report.append(f"Alerts Detected: {len(alerts)}")
            report.append("")
            
            # Group by severity
            by_severity = defaultdict(list)
            for alert in alerts:
                by_severity[alert.severity].append(alert)
            
            for severity in ['critical', 'high', 'medium', 'low']:
                if severity in by_severity:
                    report.append(f"{severity.upper()} SEVERITY ALERTS:")
                    for alert in by_severity[severity]:
                        report.append(f"  • {alert.description}")
                        report.append(f"    Confidence: {alert.confidence * 100:.1f}%")
                        report.append(f"    Recommendation: {alert.recommendation}")
                        report.append("")
        else:
            report.append("No fraud indicators detected.")
        
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def _get_risk_level(self, fraud_score: float) -> str:
        """Convert fraud score to risk level"""
        if fraud_score >= 0.8:
            return "CRITICAL"
        elif fraud_score >= 0.6:
            return "HIGH"
        elif fraud_score >= 0.4:
            return "MEDIUM"
        elif fraud_score >= 0.2:
            return "LOW"
        else:
            return "MINIMAL"


# Convenience function
def detect_fraud(claim_data: Dict) -> Tuple[List[FraudAlert], float]:
    """
    Quick function to detect fraud in a claim
    
    Args:
        claim_data: Claim information
        
    Returns:
        Tuple of (fraud alerts, fraud score)
    """
    detector = FraudDetector()
    return detector.analyze_claim(claim_data)
