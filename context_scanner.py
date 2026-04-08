from typing import List, Dict, Optional, Tuple, Any, Union
import re
import os
import pandas as pd
import spacy
from tqdm import tqdm
from dataclasses import dataclass, field

@dataclass
class RedactionConfig:
    """Configuration for the redaction process."""
    context_window: int = 5
    min_entity_length: int = 2
    supported_formats: List[str] = field(default_factory=lambda: ['csv', 'json', 'txt'])
    entity_types: List[str] = field(default_factory=lambda: ['PERSON', 'ORG', 'GPE', 'PHONE', 'EMAIL'])

class ContextScanner:
    """
    Analyzes surrounding text to reduce false positives during PII detection.
    
    This scanner utilizes spaCy for NER, Pandas for data handling, and tqdm for progress tracking.
    It filters entities based on linguistic context to ensure high precision.
    """

    def __init__(self, config: Optional[RedactionConfig] = None, model_name: str = "en_core_web_sm"):
        """
        Initialize the ContextScanner with a spaCy model and configuration.
        
        Args:
            config: Configuration object for redaction rules. Defaults to defaults if None.
            model_name: The spaCy model name to load (e.g., en_core_web_sm).
        
        Raises:
            Exception: If the spaCy model fails to load or configuration is invalid.
        """
        self.config = config or RedactionConfig()
        self.nlp = None
        self._load_model(model_name)

    def _load_model(self, model_name: str) -> None:
        """
        Load the spaCy NLP model with error handling.
        
        Args:
            model_name: The name of the spaCy model to load.
        """
        try:
            self.nlp = spacy.load(model_name)
        except IOError:
            raise Exception(f"Failed to load spaCy model '{model_name}'. Please install the model first.")
        except Exception as e:
            raise Exception(f"Unexpected error loading spaCy model: {str(e)}")

    def _validate_format(self, filename: str) -> bool:
        """
        Validate if the file extension is supported by the scanner.
        
        Args:
            filename: The path or name of the file to check.
            
        Returns:
            bool: True if the format is supported, False otherwise.
        """
        if not filename:
            return False
        file_ext = os.path.splitext(filename)[1].lower().replace('.', '')
        return file_ext in self.config.supported_formats

    def _check_context(self, doc: spacy.tokens.Doc, entity: spacy.tokens.Span) -> bool:
        """
        Analyze surrounding tokens to verify if the entity is likely PII.
        
        Args:
            doc: The spaCy document object containing the token stream.
            entity: The detected entity span to validate.
            
        Returns:
            bool: True if the context confirms the entity, False if suspected false positive.
        """
        if not self.nlp or not entity:
            return False
            
        window = self.config.context_window
        start_index = max(0, entity.start - window)
        end_index = min(len(doc), entity.end + window)
        surrounding_tokens = doc[start_index:end_index]
        
        # Logic to reduce false positives based on context markers
        context_flags = {
            'code_syntax': False,
            'common_word': False,
            'function_call': False
        }
        
        # Check for code-like surrounding context
        for token in surrounding_tokens:
            if token.pos_ == 'PUNCT' and token.text in ['(', ')', '[', ']', '=']:
                context_flags['code_syntax'] = True
            # Check for function-like naming (lowercase identifier)
            if token.pos_ in ['PROPN', 'NOUN'] and token.text.islower():
                # Heuristic: If surrounding tokens suggest programming context
                context_flags['function_call'] = True
        
        # Heuristic: Common words misidentified as ORG/PERSON
        common_words = {'the', 'and', 'or', 'not', 'is', 'are', 'was', 'were', 'to', 'for', 'in', 'on', 'at', 'by'}
        if entity.text.lower() in common_words:
            context_flags['common_word'] = True
            
        # Reject if surrounded by code syntax markers which suggests it's an identifier/variable
        # rather than natural language PII.
        if context_flags['code_syntax']:
            return False
            
        # Reject if it looks like a common word used in code
        if context_flags['common_word']:
            return False
            
        # If entity length is too short (e.g., 'I', 'A') unless it's a clear entity
        if len(entity.text) < self.config.min_entity_length:
            return False
            
        return True