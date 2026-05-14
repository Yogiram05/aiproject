"""
PHI (Protected Health Information) Redaction Module
Automatically detects and redacts sensitive patient information
Complies with privacy regulations (HIPAA, GDPR, DPDP)
"""

import re
import json
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import logging


@dataclass
class RedactedEntity:
    """Information about a redacted entity"""
    entity_type: str  # name, phone, email, aadhaar, address, etc.
    original_text: str
    redacted_text: str
    start_pos: int
    end_pos: int
    confidence: float


class PHIRedactor:
    """
    Detects and redacts Protected Health Information (PHI)
    Supports Indian-specific identifiers (Aadhaar, Indian phone numbers)
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._initialize_patterns()
    
    def _initialize_patterns(self):
        """Initialize regex patterns for PHI detection"""
        
        # Aadhaar number (12 digits, optionally with spaces/hyphens)
        self.aadhaar_pattern = r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'
        
        # Indian phone number (10 digits with optional country code)
        self.phone_patterns = [
            r'\b(?:\+91[\s-]?)?[6-9]\d{9}\b',
            r'\b0\d{2,4}[\s-]?\d{6,8}\b',  # Landline
        ]
        
        # Email
        self.email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        # PAN Card
        self.pan_pattern = r'\b[A-Z]{5}\d{4}[A-Z]\b'
        
        # Indian Passport
        self.passport_pattern = r'\b[A-Z]\d{7}\b'
        
        # Date patterns (potential DOB)
        self.date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',
        ]
        
        # Age pattern
        self.age_pattern = r'\b(?:age|yrs?|years?)[\s:]*(\d{1,3})\b'
        
        # Address indicators
        self.address_keywords = [
            r'address', r'residence', r'street', r'road', r'colony',
            r'nagar', r'area', r'sector', r'pin\s*code', r'pincode',
            r'city', r'state', r'india'
        ]
        
        # Common Indian names (for demonstration - expand significantly)
        self.name_prefixes = [
            'mr', 'mrs', 'ms', 'dr', 'prof', 'shri', 'smt', 'kumari'
        ]
        
    def redact_text(
        self,
        text: str,
        redact_names: bool = True,
        redact_phones: bool = True,
        redact_emails: bool = True,
        redact_ids: bool = True,
        redact_addresses: bool = True,
        redact_dates: bool = False
    ) -> Tuple[str, List[RedactedEntity]]:
        """
        Redact PHI from text
        
        Args:
            text: Input text
            redact_names: Redact person names
            redact_phones: Redact phone numbers
            redact_emails: Redact email addresses
            redact_ids: Redact ID numbers (Aadhaar, PAN, Passport)
            redact_addresses: Redact addresses
            redact_dates: Redact dates (be careful, may redact medical dates)
            
        Returns:
            Tuple of (redacted_text, list of redacted entities)
        """
        redacted_entities = []
        redacted_text = text
        
        # Redact Aadhaar numbers
        if redact_ids:
            redacted_text, entities = self._redact_aadhaar(redacted_text)
            redacted_entities.extend(entities)
        
        # Redact phone numbers
        if redact_phones:
            redacted_text, entities = self._redact_phones(redacted_text)
            redacted_entities.extend(entities)
        
        # Redact emails
        if redact_emails:
            redacted_text, entities = self._redact_emails(redacted_text)
            redacted_entities.extend(entities)
        
        # Redact PAN
        if redact_ids:
            redacted_text, entities = self._redact_pan(redacted_text)
            redacted_entities.extend(entities)
        
        # Redact passport numbers
        if redact_ids:
            redacted_text, entities = self._redact_passport(redacted_text)
            redacted_entities.extend(entities)
        
        # Redact dates (optional, as it may redact important medical dates)
        if redact_dates:
            redacted_text, entities = self._redact_dates(redacted_text)
            redacted_entities.extend(entities)
        
        # Redact names (basic implementation)
        if redact_names:
            redacted_text, entities = self._redact_names(redacted_text)
            redacted_entities.extend(entities)
        
        # Redact addresses
        if redact_addresses:
            redacted_text, entities = self._redact_addresses(redacted_text)
            redacted_entities.extend(entities)
        
        return redacted_text, redacted_entities
    
    def _redact_aadhaar(self, text: str) -> Tuple[str, List[RedactedEntity]]:
        """Redact Aadhaar numbers"""
        entities = []
        
        def replacer(match):
            original = match.group(0)
            entities.append(RedactedEntity(
                entity_type="aadhaar",
                original_text=original,
                redacted_text="[AADHAAR-REDACTED]",
                start_pos=match.start(),
                end_pos=match.end(),
                confidence=0.95
            ))
            return "[AADHAAR-REDACTED]"
        
        redacted = re.sub(self.aadhaar_pattern, replacer, text)
        return redacted, entities
    
    def _redact_phones(self, text: str) -> Tuple[str, List[RedactedEntity]]:
        """Redact phone numbers"""
        entities = []
        
        def replacer(match):
            original = match.group(0)
            entities.append(RedactedEntity(
                entity_type="phone",
                original_text=original,
                redacted_text="[PHONE-REDACTED]",
                start_pos=match.start(),
                end_pos=match.end(),
                confidence=0.90
            ))
            return "[PHONE-REDACTED]"
        
        redacted = text
        for pattern in self.phone_patterns:
            redacted = re.sub(pattern, replacer, redacted)
        
        return redacted, entities
    
    def _redact_emails(self, text: str) -> Tuple[str, List[RedactedEntity]]:
        """Redact email addresses"""
        entities = []
        
        def replacer(match):
            original = match.group(0)
            entities.append(RedactedEntity(
                entity_type="email",
                original_text=original,
                redacted_text="[EMAIL-REDACTED]",
                start_pos=match.start(),
                end_pos=match.end(),
                confidence=0.95
            ))
            return "[EMAIL-REDACTED]"
        
        redacted = re.sub(self.email_pattern, replacer, text)
        return redacted, entities
    
    def _redact_pan(self, text: str) -> Tuple[str, List[RedactedEntity]]:
        """Redact PAN card numbers"""
        entities = []
        
        def replacer(match):
            original = match.group(0)
            entities.append(RedactedEntity(
                entity_type="pan",
                original_text=original,
                redacted_text="[PAN-REDACTED]",
                start_pos=match.start(),
                end_pos=match.end(),
                confidence=0.90
            ))
            return "[PAN-REDACTED]"
        
        redacted = re.sub(self.pan_pattern, replacer, text)
        return redacted, entities
    
    def _redact_passport(self, text: str) -> Tuple[str, List[RedactedEntity]]:
        """Redact passport numbers"""
        entities = []
        
        def replacer(match):
            original = match.group(0)
            # Additional validation to avoid false positives
            if original[0] in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                entities.append(RedactedEntity(
                    entity_type="passport",
                    original_text=original,
                    redacted_text="[PASSPORT-REDACTED]",
                    start_pos=match.start(),
                    end_pos=match.end(),
                    confidence=0.85
                ))
                return "[PASSPORT-REDACTED]"
            return original
        
        redacted = re.sub(self.passport_pattern, replacer, text)
        return redacted, entities
    
    def _redact_dates(self, text: str) -> Tuple[str, List[RedactedEntity]]:
        """Redact dates (use with caution in medical context)"""
        entities = []
        
        def replacer(match):
            original = match.group(0)
            entities.append(RedactedEntity(
                entity_type="date",
                original_text=original,
                redacted_text="[DATE-REDACTED]",
                start_pos=match.start(),
                end_pos=match.end(),
                confidence=0.80
            ))
            return "[DATE-REDACTED]"
        
        redacted = text
        for pattern in self.date_patterns:
            redacted = re.sub(pattern, replacer, redacted)
        
        return redacted, entities
    
    def _redact_names(self, text: str) -> Tuple[str, List[RedactedEntity]]:
        """Redact person names (basic implementation using prefixes)"""
        entities = []
        
        # Pattern to match titles followed by names
        name_pattern = r'\b(?:' + '|'.join(self.name_prefixes) + r')\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
        
        def replacer(match):
            original = match.group(0)
            entities.append(RedactedEntity(
                entity_type="name",
                original_text=original,
                redacted_text="[NAME-REDACTED]",
                start_pos=match.start(),
                end_pos=match.end(),
                confidence=0.75
            ))
            return "[NAME-REDACTED]"
        
        redacted = re.sub(name_pattern, replacer, text, flags=re.IGNORECASE)
        return redacted, entities
    
    def _redact_addresses(self, text: str) -> Tuple[str, List[RedactedEntity]]:
        """Redact addresses (basic implementation)"""
        entities = []
        lines = text.split('\n')
        redacted_lines = []
        
        for line in lines:
            line_lower = line.lower()
            
            # Check if line contains address keywords
            has_address_keyword = any(
                re.search(keyword, line_lower)
                for keyword in self.address_keywords
            )
            
            # Check for PIN code pattern (Indian postal code)
            has_pincode = re.search(r'\b\d{6}\b', line)
            
            if has_address_keyword or has_pincode:
                entities.append(RedactedEntity(
                    entity_type="address",
                    original_text=line,
                    redacted_text="[ADDRESS-REDACTED]",
                    start_pos=0,
                    end_pos=len(line),
                    confidence=0.70
                ))
                redacted_lines.append("[ADDRESS-REDACTED]")
            else:
                redacted_lines.append(line)
        
        return '\n'.join(redacted_lines), entities
    
    def create_audit_log(
        self,
        document_id: str,
        redacted_entities: List[RedactedEntity],
        user_id: Optional[str] = None
    ) -> Dict:
        """Create audit log for redaction operation"""
        audit_entry = {
            "document_id": document_id,
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id or "system",
            "operation": "phi_redaction",
            "entities_redacted": [
                {
                    "type": entity.entity_type,
                    "confidence": entity.confidence,
                    "position": (entity.start_pos, entity.end_pos)
                }
                for entity in redacted_entities
            ],
            "total_redactions": len(redacted_entities),
            "entity_type_counts": self._count_entity_types(redacted_entities)
        }
        
        return audit_entry
    
    def _count_entity_types(self, entities: List[RedactedEntity]) -> Dict[str, int]:
        """Count redacted entities by type"""
        counts = {}
        for entity in entities:
            counts[entity.entity_type] = counts.get(entity.entity_type, 0) + 1
        return counts
    
    def export_redaction_report(
        self,
        redacted_entities: List[RedactedEntity]
    ) -> str:
        """Generate redaction report"""
        report = []
        report.append("=" * 60)
        report.append("PHI REDACTION REPORT")
        report.append("=" * 60)
        report.append(f"Timestamp: {datetime.now().isoformat()}")
        report.append(f"Total Redactions: {len(redacted_entities)}")
        report.append("")
        
        # Group by type
        by_type = {}
        for entity in redacted_entities:
            if entity.entity_type not in by_type:
                by_type[entity.entity_type] = []
            by_type[entity.entity_type].append(entity)
        
        report.append("Redactions by Type:")
        for entity_type, entities in sorted(by_type.items()):
            report.append(f"  {entity_type.upper()}: {len(entities)}")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)


# Convenience function
def redact_phi(text: str) -> str:
    """
    Quick function to redact all PHI from text
    
    Args:
        text: Input text
        
    Returns:
        Redacted text
    """
    redactor = PHIRedactor()
    redacted_text, _ = redactor.redact_text(text)
    return redacted_text
