import pytest
from unittest import mock
from context_scanner import ContextScanner, RedactionConfig
import spacy

# Fixtures for mocking spaCy and file operations

@pytest.fixture
def mock_nlp():
    """Mock the spaCy NLP object."""
    nlp_mock = mock.MagicMock()
    return nlp_mock

@pytest.fixture
def mock_doc():
    """Mock the spaCy document object."""
    doc_mock = mock.MagicMock()
    # Mock token objects
    token1 = mock.MagicMock()
    token1.text = "This"
    token1.pos_ = "PROPN"
    token1.islower.return_value = False
    token2 = mock.MagicMock()
    token2.text = "the"
    token2.pos_ = "NOUN"
    token2.islower.return_value = False
    
    # Mock the surrounding tokens result of slicing
    doc_mock.__getitem__.return_value = mock.MagicMock()
    doc_mock.__getitem__.return_value.__iter__.return_value = [token1, token2]
    doc_mock.__len__.return_value = 5
    doc_mock.start = 0
    doc_mock.end = 5
    return doc_mock

@pytest.fixture
def mock_entity():
    """Mock the spaCy entity span object."""
    entity_mock = mock.MagicMock()
    entity_mock.text = "John"
    entity_mock.start = 0
    entity_mock.end = 4
    return entity_mock

@pytest.fixture
def scanner_with_mock(mock_nlp):
    """Create a scanner instance with mocked model loading."""
    with mock.patch('context_scanner.spacy.load', return_value=mock_nlp):
        scanner = ContextScanner()
        scanner.nlp = mock_nlp
        yield scanner

@pytest.fixture
def scanner_default_config():
    """Create a scanner instance with default config."""
    with mock.patch('context_scanner.spacy.load', return_value=mock.MagicMock()):
        scanner = ContextScanner()
        yield scanner

class TestContextScannerInit:
    """Tests for ContextScanner.__init__ and _load_model logic."""

    @mock.patch('context_scanner.spacy.load')
    def test_init_default_config(self, mock_load, mock_nlp):
        """Test initialization with default config settings."""
        mock_load.return_value = mock_nlp
        scanner = ContextScanner()
        assert scanner.config.context_window == 5
        assert scanner.config.min_entity_length == 2
        assert scanner.config.supported_formats == ['csv', 'json', 'txt']

    @mock.patch('context_scanner.spacy.load')
    def test_init_custom_config(self, mock_load, mock_nlp):
        """Test initialization with custom configuration."""
        mock_load.return_value = mock_nlp
        custom_config = RedactionConfig(context_window=10, min_entity_length=3)
        scanner = ContextScanner(config=custom_config)
        assert scanner.config.context_window == 10
        assert scanner.config.min_entity_length == 3

    @mock.patch('context_scanner.spacy.load')
    def test_init_model_failure_ioerror(self, mock_load, mock_nlp):
        """Test initialization raises exception on IO load failure."""
        mock_load.side_effect = IOError("Model not found")
        with pytest.raises(Exception) as exc_info:
            ContextScanner()
        assert "Failed to load spaCy model" in str(exc_info.value)

    @mock.patch('context_scanner.spacy.load')
    def test_init_model_failure_generic(self, mock_load, mock_nlp):
        """Test initialization raises exception on generic load error."""
        mock_load.side_effect = ValueError("Config error")
        with pytest.raises(Exception) as exc_info:
            ContextScanner()
        assert "Unexpected error" in str(exc_info.value)

class TestLoadModel:
    """Tests for ContextScanner._load_model."""

    def test_load_model_success(self, mock_nlp):
        """Test successful model loading."""
        scanner = ContextScanner