# Local AI Dataset Redactor

[![Python Version](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub stars](https://img.shields.io/github/stars/dev-org/local-ai-dataset-redactor.svg?style=social)](https://github.com/dev-org/local-ai-dataset-redactor)

**Local AI Dataset Redactor** is a privacy-focused CLI tool designed to redact Personally Identifiable Information (PII) from files and logs locally. Built for Data Engineers and AI Developers, it ensures safe AI training environments by preventing sensitive data leakage during model development and complies with regulations like GDPR and CCPA.

## Features

*   **Local Processing:** All data processing happens on your machine, ensuring no sensitive information is uploaded to external services.
*   **Multi-Format Support:** Recursively loads and processes JSON, CSV, LOG, and TXT files.
*   **Advanced PII Detection:** Utilizes `spaCy` NLP models combined with regex patterns for high-accuracy identification of PII.
*   **Contextual Analysis:** Analyzes surrounding text to significantly reduce false positives during detection.
*   **Secure Anonymization:** Safely replaces or hashes sensitive fields to ensure data utility while maintaining compliance.
*   **Versioned Backups:** Automatically creates timestamped backups before modification to prevent data loss.
*   **Audit Trails:** Generates detailed change logs and compliance summaries for internal audits.

## Installation

Ensure you have Python 3.8 or higher installed. The tool is available on PyPI and can be installed via `pip`.

```bash
pip install dev-dataset-redactor
```

Alternatively, install from source:

```bash
git clone https://github.com/dev-org/local-ai-dataset-redactor.git
cd local-ai-dataset-redactor
pip install -e .
```

## Quick Start

After installation, you can redact PII from a dataset with a single command. This example takes a raw JSON file and outputs a sanitized version.

```bash
dev-dataset-redactor \
    --input ./data/raw_training_data.json \
    --output ./data/sanitized_training_data.json \
    --pii-types name,email,phone \
    --mode strict
```

## Usage

The tool provides several options to customize the redaction process.

### Basic Usage

```bash
# Redact all default PII types
dev-dataset-redactor --input ./input.json --output ./output.json
```

### Verbose Logging and Dry Run

Run in verbose mode to see detailed detection logs, or use `--dry-run` to see what *would* change without modifying files.

```bash
dev-dataset-redactor \
    --input ./input.json \
    --output ./output.json \