import pytest
from unittest import mock
from pii_detector import detect_pii, redact_pii, init_model, validate_text

SAMPLE_EMAIL_TEXT = "Contact us at support@example.com or call 555-123-4567."
SAMPLE_PII_DATA = [
    {"type": "email", "start": 14, "end": 33, "value": "support@example.com"},
    {"type": "phone", "start": 41, "end": 53, "value": "555-123-4567"}
]
SAMPLE_NLP_RESPONSE = [
    {"entity": "EMAIL", "text": "support@example.com", "start": 14, "end": 33}
]

@pytest.fixture
def mock_nlp_response():
    return mock.MagicMock(return_value=SAMPLE_NLP_RESPONSE)

@pytest.fixture
def patch_external_nlp():
    with mock.patch("pii_detector.nlp_service.query") as mock_call:
        mock_call.return_value = SAMPLE_NLP_RESPONSE
        yield mock_call

class TestPiiDetectorPublicFunctions:
    @pytest.mark.parametrize("text,expected_count", [
        ("No PII here", 0),
        ("Email is test@test.com", 1),
        ("Phone 123-456-7890 and email a@b.com", 2)
    ])
    def test_detect_pii_regex_variations(self, text, expected_count):
        """Test detect_pii with regex patterns for standard formats."""
        with mock.patch("pii_detector.regex_detector.find") as mock_regex:
            mock_regex.return_value = SAMPLE_PII_DATA[:1] if "test@test.com" in text else (SAMPLE_PII_DATA[:1] if "a@b.com" in text else [])
            result = detect_pii(text, use_regex=True, use_nlp=False)
            assert len(result) == expected_count

    def test_detect_pii_with_nlp_model(self, patch_external_nlp):
        """Test detect_pii when NLP model is used."""
        with mock.patch("pii_detector.init_model"):
            result = detect_pii(SAMPLE_EMAIL_TEXT, use_nlp=True)
            patch_external_nlp.assert_called_once()
            assert len(result) == 1
            assert result[0]["type"] == "EMAIL"

    def test_detect_pii_invalid_input_handling(self):
        """Test detect_pii handles invalid input types gracefully."""
        with mock.patch("pii_detector.regex_detector.find"):
            with mock.patch("pii_detector.nlp_service.query"):
                result = detect_pii(12345, use_regex=True)
                assert result == []

class TestRedactionFunctions:
    def test_redact_pii_standard_formatting(self):
        """Test redact_pii replaces entities correctly with placeholder."""
        text = "Call 555-123-4567 now."
        entities = [{"type": "phone", "start": 5, "end": 17, "