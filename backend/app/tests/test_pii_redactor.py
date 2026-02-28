"""Tests for PII Redaction Layer."""

import pytest
from app.utils.pii_redactor import PIIRedactor, pii_redactor


class TestAadhaarRedaction:
    """Test Aadhaar number redaction."""
    
    def test_aadhaar_with_spaces(self):
        redactor = PIIRedactor()
        text = "My Aadhaar is 1234 5678 9012"
        redacted, mapping = redactor.redact(text)
        
        assert "[AADHAAR_1]" in redacted
        assert "1234 5678 9012" not in redacted
        assert mapping["[AADHAAR_1]"] == "1234 5678 9012"
    
    def test_aadhaar_without_spaces(self):
        redactor = PIIRedactor()
        text = "Aadhaar: 123456789012"
        redacted, mapping = redactor.redact(text)
        
        assert "[AADHAAR_1]" in redacted
        assert "123456789012" not in redacted
    
    def test_multiple_aadhaar(self):
        redactor = PIIRedactor()
        text = "Aadhaar 1234 5678 9012 and 9876 5432 1098"
        redacted, mapping = redactor.redact(text)
        
        assert "[AADHAAR_1]" in redacted
        assert "[AADHAAR_2]" in redacted
        assert len(mapping) == 2


class TestPANRedaction:
    """Test PAN card redaction."""
    
    def test_valid_pan(self):
        redactor = PIIRedactor()
        text = "My PAN is ABCDE1234F"
        redacted, mapping = redactor.redact(text)
        
        assert "[PAN_1]" in redacted
        assert "ABCDE1234F" not in redacted
        assert mapping["[PAN_1]"] == "ABCDE1234F"
    
    def test_multiple_pan(self):
        redactor = PIIRedactor()
        text = "PAN: ABCDE1234F and XYZAB5678C"
        redacted, mapping = redactor.redact(text)
        
        assert "[PAN_1]" in redacted
        assert "[PAN_2]" in redacted


class TestMobileRedaction:
    """Test mobile number redaction."""
    
    def test_valid_mobile(self):
        redactor = PIIRedactor()
        text = "Call me at 9876543210"
        redacted, mapping = redactor.redact(text)
        
        assert "[MOBILE_1]" in redacted
        assert "9876543210" not in redacted
    
    def test_mobile_starting_with_6_to_9(self):
        redactor = PIIRedactor()
        text = "Numbers: 6123456789, 7123456789, 8123456789, 9123456789"
        redacted, mapping = redactor.redact(text)
        
        assert len(mapping) == 4
        assert all("[MOBILE_" in key for key in mapping.keys())


class TestEmailRedaction:
    """Test email redaction."""
    
    def test_simple_email(self):
        redactor = PIIRedactor()
        text = "Email: john.doe@example.com"
        redacted, mapping = redactor.redact(text)
        
        assert "[EMAIL_1]" in redacted
        assert "john.doe@example.com" not in redacted
    
    def test_multiple_emails(self):
        redactor = PIIRedactor()
        text = "Contact: user@test.com or admin@company.org"
        redacted, mapping = redactor.redact(text)
        
        assert "[EMAIL_1]" in redacted
        assert "[EMAIL_2]" in redacted


class TestNameRedaction:
    """Test name with title redaction."""
    
    def test_mr_name(self):
        redactor = PIIRedactor()
        text = "Complaint by Mr. John Doe"
        redacted, mapping = redactor.redact(text)
        
        assert "[NAME_1]" in redacted
        assert "Mr. John Doe" not in redacted
    
    def test_mrs_name(self):
        redactor = PIIRedactor()
        text = "Filed by Mrs. Jane Smith"
        redacted, mapping = redactor.redact(text)
        
        assert "[NAME_1]" in redacted
    
    def test_dr_name(self):
        redactor = PIIRedactor()
        text = "Dr. Rajesh Kumar filed complaint"
        redacted, mapping = redactor.redact(text)
        
        assert "[NAME_1]" in redacted


class TestAddressRedaction:
    """Test address redaction."""
    
    def test_street_address(self):
        redactor = PIIRedactor()
        text = "Address: 123 Main Street"
        redacted, mapping = redactor.redact(text)
        
        assert "[ADDRESS_1]" in redacted
        assert "123 Main Street" not in redacted
    
    def test_nagar_address(self):
        redactor = PIIRedactor()
        text = "Lives at 45 Gandhi Nagar"
        redacted, mapping = redactor.redact(text)
        
        assert "[ADDRESS_1]" in redacted


class TestRestore:
    """Test PII restoration."""
    
    def test_restore_single_item(self):
        redactor = PIIRedactor()
        original = "My PAN is ABCDE1234F"
        redacted, mapping = redactor.redact(original)
        restored = redactor.restore(redacted, mapping)
        
        assert restored == original
    
    def test_restore_multiple_items(self):
        redactor = PIIRedactor()
        original = "Contact Mr. John Doe at 9876543210 or john@example.com"
        redacted, mapping = redactor.redact(original)
        restored = redactor.restore(redacted, mapping)
        
        assert restored == original
    
    def test_restore_complex_text(self):
        redactor = PIIRedactor()
        original = "Mr. John Doe (PAN: ABCDE1234F, Aadhaar: 1234 5678 9012) at 9876543210"
        redacted, mapping = redactor.redact(original)
        restored = redactor.restore(redacted, mapping)
        
        assert restored == original


class TestComplexScenarios:
    """Test complex real-world scenarios."""
    
    def test_legal_grievance(self):
        redactor = PIIRedactor()
        text = """I, Mr. Rajesh Kumar, holder of PAN ABCDE1234F and Aadhaar 1234 5678 9012,
        residing at 123 MG Road, Kochi, contact 9876543210, email rajesh@example.com,
        wish to file a complaint."""
        
        redacted, mapping = redactor.redact(text)
        
        assert "[NAME_" in redacted
        assert "[PAN_" in redacted
        assert "[AADHAAR_" in redacted
        assert "[ADDRESS_" in redacted
        assert "[MOBILE_" in redacted
        assert "[EMAIL_" in redacted
        assert len(mapping) == 6
    
    def test_no_pii(self):
        redactor = PIIRedactor()
        text = "This is a simple complaint about a defective product."
        redacted, mapping = redactor.redact(text)
        
        assert redacted == text
        assert len(mapping) == 0
    
    def test_partial_pii(self):
        redactor = PIIRedactor()
        text = "Contact at 9876543210 for details"
        redacted, mapping = redactor.redact(text)
        
        assert "[MOBILE_1]" in redacted
        assert len(mapping) == 1


class TestGlobalInstance:
    """Test global pii_redactor instance."""
    
    def test_global_instance_works(self):
        text = "PAN: ABCDE1234F"
        redacted, mapping = pii_redactor.redact(text)
        
        assert "[PAN_1]" in redacted
        assert len(mapping) == 1
    
    def test_global_instance_restore(self):
        original = "Aadhaar: 1234 5678 9012"
        redacted, mapping = pii_redactor.redact(original)
        restored = pii_redactor.restore(redacted, mapping)
        
        assert restored == original


class TestEdgeCases:
    """Test edge cases."""
    
    def test_empty_string(self):
        redactor = PIIRedactor()
        redacted, mapping = redactor.redact("")
        
        assert redacted == ""
        assert len(mapping) == 0
    
    def test_only_whitespace(self):
        redactor = PIIRedactor()
        redacted, mapping = redactor.redact("   \n\t  ")
        
        assert len(mapping) == 0
    
    def test_special_characters(self):
        redactor = PIIRedactor()
        text = "PAN: ABCDE1234F! Email: test@example.com?"
        redacted, mapping = redactor.redact(text)
        
        assert "[PAN_" in redacted
        assert "[EMAIL_" in redacted
    
    def test_case_sensitivity(self):
        redactor = PIIRedactor()
        text = "pan: ABCDE1234F"  # lowercase 'pan'
        redacted, mapping = redactor.redact(text)
        
        assert "[PAN_1]" in redacted
