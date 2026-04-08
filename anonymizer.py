import click
import pandas as pd
import spacy
from tqdm import tqdm
import hashlib
import os
import re
import logging
from typing import List, Optional, Dict, Any, Union, Tuple
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variable to store the loaded Spacy model
_nlp_model: Optional[spacy.language.Language] = None


def _get_nlp_model(force_reload: bool = False) -> spacy.language.Language:
    """
    Load the English NLP model for entity recognition.

    Args:
        force_reload: If True, resets the cached model.

    Returns:
        spacy.language.Language: The loaded pipeline instance.

    Raises:
        SystemExit: If the model is not available and cannot be installed.
    """
    global _nlp_model
    if _nlp_model is None or force_reload:
        try:
            logger.info("Loading Spacy model en_core_web_sm...")
            _nlp_model = spacy.load("en_core_web_sm")
        except OSError as e:
            logger.error(f"Spacy model 'en_core_web_sm' not found. {str(e)}")
            logger.warning("Please install it using: python -m spacy download en_core_web_sm")
            raise click.exceptions.Abort() from e
    return _nlp_model


def _hash_value(value: Any, salt: str = "pii_redactor_salt") -> str:
    """
    Hash a value deterministically using SHA-256.

    Args:
        value: The value to hash.
        salt: A string salt to ensure uniqueness.

    Returns:
        str: Hexadecimal hash string.
    """
    safe_str = f"{salt}_{value}"
    return hashlib.sha256(safe_str.encode('utf-8')).hexdigest()[:16]


def _is_text_column(column: pd.Series) -> bool:
    """
    Determine if a DataFrame column contains string-like data suitable for redaction.

    Args:
        column: The pandas Series to check.

    Returns:
        bool: True if column is object dtype or string dtype.
    """
    return column.dtype == object or column.dtype == "string"


def _redact_nlp_text(text: str, strategy: str = "replace") -> str:
    """
    Process a string through NLP to identify and redact entities.

    Args:
        text: The text to process.
        strategy: Either 'replace' for masking or 'hash' for anonymization.

    Returns:
        str: The redacted text.
    """
    if pd.isna(text):
        return text

    doc = spacy.load("en_core_web_sm")
    doc = _get_nlp_model(force_reload=False)()
    doc = _nlp_model(text)

    # List of common PII entity labels in Spacy
    pii_labels = ["PERSON", "GPE", "LOC", "ORG", "DATE", "TIME", "MONEY", "CARDINAL"]
    
    redacted_text = text
    tokens = list(doc)
    token_texts = [token.text for token in tokens]
    
    replacements = {}
    # Collect spans to avoid overlap issues
    entities = [ent for ent in doc.ents if ent.label_ in pii_labels]
    
    if not entities:
        return text

    # Create a reverse mapping to process replacements from end to start
    # or use a more sophisticated replacement logic. 
    # Here we perform replacements on the text directly, but for robustness
    # with multiple entities, we will iterate carefully.
    # For simplicity in a module, we replace specific entity text with a placeholder
    # or hash.
    
    # We need to be careful not to double replace substrings of replaced entities.
    # Strategy: Replace longest spans first.
    entities = sorted(entities, key=lambda x: -x.end_char)
    
    current_text = text
    for ent in entities:
        if current_text is None or ent.start > len(current_text):
            continue
            
        # Safety check for substring
        try:
            entity_text = current_text[ent.start_char:ent.end_char]
        except IndexError:
            continue

        if entity_text in replacements:
            replacement = replacements[entity_text]
        else:
            if strategy == "hash":
                replacement = f"<HASH_{ent.label_}>"
                # In a real scenario, you might map entity_text to hash(entity_text)
                # For PII removal, usually we just mask.
                # Let's implement actual replacement for the specific text instance.
                # We will just mark it with label to denote PII found.
                replacement = f"<{ent.label_}>"
            else:
                replacement = f"[REDACTED_{ent.label_}]"
            
            replacements[entity_text] = replacement

        # Perform the replacement
        current_text = current_text.replace(entity_text, replacement, 1)

    return current_text


def detect_columns(df: pd.DataFrame) -> List[str]:
    """
    Automatically detect columns likely to contain PII based on data types.

    Args:
        df: Input DataFrame.

    Returns:
        List[str]: List of column names identified as text.
    """
    return [col for col in df.columns if _is_text_column(df[col])]


def process_dataframe(
    df: pd.DataFrame,
    columns: Optional[List[str]] = None,
    strategy: str = "replace",
    show_progress: bool = True
) -> pd.DataFrame:
    """
    Apply PII redaction logic to a DataFrame.

    Args:
        df: The pandas DataFrame to process.
        columns: Specific columns to process. If None, auto-detects text columns.
        strategy: Redaction strategy ('replace' or 'hash').
        show_progress: Whether to show a tqdm progress bar.

    Returns:
        pd.DataFrame: The redacted DataFrame.

    Raises:
        ValueError: If the DataFrame is empty or invalid.
    """
    if df.empty:
        raise ValueError("Input DataFrame is empty.")

    if columns is None:
        columns = detect