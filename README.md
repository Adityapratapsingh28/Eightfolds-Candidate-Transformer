# Candidate Transformation Engine

A high-performance, deterministic Python application designed to ingest heterogeneous candidate information from multiple independent sources, clean and normalize fields, merge conflicts, assign explainable confidence scores, track data provenance, and project canonical profiles based on dynamic runtime configurations.

## Features
- **Structured and Unstructured Data Parsing**: CSV, JSON, PDF, TXT.
- **Canonical Mapping Layer**: Abstracted data representation.
- **Field Normalization**: Phone numbers (E.164), Dates (YYYY-MM), country codes (ISO-3166), and canonical skills.
- **Merge & Conflict Resolution**: Merges multiple records for a single candidate into one canonical record.
- **Dynamic Projections**: Custom layout outputs configured at runtime.

## Installation
Ensure you have Python 3.11+ installed. Run the following:
```bash
pip install -r requirements.txt
```

## Running the Application
To run the CLI tool:
```bash
python -m src.cli.main --help
```
