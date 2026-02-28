"""PII Redaction Layer for Nyaya-Flow.

Masks sensitive personal information before sending to AI agents.
"""

import re
from typing import Dict, Tuple


class PIIRedactor:
    """Redacts Personally Identifiable Information from text."""
    
    # Patterns for Indian PII
    PATTERNS = {
        "aadhaar": r'\b\d{4}\s?\d{4}\s?\d{4}\b',
        "pan": r'\b[A-Z]{5}\d{4}[A-Z]\b',
        "mobile": r'\b[6-9]\d{9}\b',
        "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "name": r'\b(?:Mr\.|Mrs\.|Ms\.|Dr\.)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',
        "address": r'\b\d+[,\s]+[A-Za-z\s]+(?:Street|Road|Lane|Avenue|Nagar|Colony)\b',
    }
    
    def __init__(self):
        self.redaction_map: Dict[str, str] = {}
    
    def redact(self, text: str) -> Tuple[str, Dict[str, str]]:
        """Redact PII from text.
        
        Args:
            text: Original text with PII
            
        Returns:
            Tuple of (redacted_text, redaction_map)
        """
        redacted = text
        self.redaction_map = {}
        
        for match in re.finditer(self.PATTERNS["aadhaar"], text):
            original = match.group()
            placeholder = f"[AADHAAR_{len(self.redaction_map) + 1}]"
            self.redaction_map[placeholder] = original
            redacted = redacted.replace(original, placeholder)
        
        for match in re.finditer(self.PATTERNS["pan"], text):
            original = match.group()
            placeholder = f"[PAN_{len(self.redaction_map) + 1}]"
            self.redaction_map[placeholder] = original
            redacted = redacted.replace(original, placeholder)
        
        for match in re.finditer(self.PATTERNS["mobile"], text):
            original = match.group()
            placeholder = f"[MOBILE_{len(self.redaction_map) + 1}]"
            self.redaction_map[placeholder] = original
            redacted = redacted.replace(original, placeholder)
        
        for match in re.finditer(self.PATTERNS["email"], text):
            original = match.group()
            placeholder = f"[EMAIL_{len(self.redaction_map) + 1}]"
            self.redaction_map[placeholder] = original
            redacted = redacted.replace(original, placeholder)
        
        for match in re.finditer(self.PATTERNS["name"], text):
            original = match.group()
            placeholder = f"[NAME_{len(self.redaction_map) + 1}]"
            self.redaction_map[placeholder] = original
            redacted = redacted.replace(original, placeholder)
        
        for match in re.finditer(self.PATTERNS["address"], text):
            original = match.group()
            placeholder = f"[ADDRESS_{len(self.redaction_map) + 1}]"
            self.redaction_map[placeholder] = original
            redacted = redacted.replace(original, placeholder)
        
        return redacted, self.redaction_map
    
    def restore(self, text: str, redaction_map: Dict[str, str]) -> str:
        """Restore original PII.
        
        Args:
            text: Redacted text
            redaction_map: Placeholder to original mapping
            
        Returns:
            Text with PII restored
        """
        restored = text
        for placeholder, original in redaction_map.items():
            restored = restored.replace(placeholder, original)
        return restored


pii_redactor = PIIRedactor()
