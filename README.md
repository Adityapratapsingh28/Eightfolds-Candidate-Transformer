# Candidate Transformation Engine

A high-performance, strictly deterministic Python engine designed to ingest heterogeneous candidate information from multiple independent sources, clean and normalize fields, merge conflicts, assign explainable confidence scores, track data provenance, and project canonical profiles based on dynamic runtime configurations.

---

## 🏗️ Architecture Overview

The engine follows a modular, pipe-and-filter data-flow architecture where each stage has a single, isolated responsibility:

```
[Ingestion] -> [Parsing] -> [Canonical Mapping] -> [Normalization] -> [Merging] -> [Projection] -> [Validation] -> [JSON Output]
```

1. **Ingestion & Specific Parsing** (`src/parsers/`):
   Detects the source data type (CSV, JSON, PDF, TXT) and parses it into a raw structured format using dedicated tools (e.g. `pandas` for CSV, `PyMuPDF` for PDF).
2. **Canonical Mapping** (`src/mapper/`):
   Maps raw source fields into an internal intermediate canonical model (`CanonicalCandidate`) while logging data provenance metadata for every mapped field.
3. **Normalization Engine** (`src/normalizers/`):
   Applies pure validation and cleaning functions (e.g., standardizing phones to E.164, formatting dates to `YYYY-MM`, resolving country names to ISO-3166-1 codes, and resolving skill synonyms).
4. **Merge & Conflict Engine** (`src/merger/`):
   Fuses records from multiple matched profiles using a strict source authority priority hierarchy. Deduplicates experiences, educations, and skills, calculates skill confidence boosts, computes overall profile confidence, and aggregates provenance logs.
5. **Projection Engine** (`src/projector/`):
   Extracts, renames, and formats the internal model into a custom layout dictionary according to runtime JSON configurations without mutating the canonical record.
6. **Schema Validation** (`src/validator/`):
   Dynamically compiles a JSON Schema from the runtime config and validates the projected output against it, guaranteeing that the returned JSON profile matches specifications exactly.

---

## ⚙️ Installation & Setup

1. **Activate the Conda Environment**:
   ```bash
   conda activate candidate-transformer
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify the Installation**:
   Run the test suite using `pytest`:
   ```bash
   PYTHONPATH=. pytest
   ```

---

## 🚀 CLI Usage

The production command-line interface handles individual input flags for various source formats, a configuration selector, and an optional output file path.

```bash
python -m src.cli.main \
  --csv <csv_path> \
  --ats <ats_path> \
  --resume <pdf_path> \
  --notes <notes_path> \
  --github <github_url> \
  --config <config_path> \
  --output <output_path>
```

### Options
* `--csv`: Path to a structured Recruiter CSV file.
* `--ats`: Path to an ATS JSON file.
* `--resume`: Path to a candidate Resume PDF.
* `--notes`: Path to a Recruiter Notes text file.
* `--github`: URL to the candidate's GitHub profile.
* `--config`: Path to the output projection configuration JSON (required).
* `--output`: Optional path to write the transformed candidate JSON profile. Prints to `stdout` by default.

---

## ⚡ Demo & Verification

We have preloaded the project with a sample candidate dataset for testing:
* CSV: `sample_inputs/recruiter.csv`
* ATS JSON: `sample_inputs/ats.json`
* Resume PDF: `sample_inputs/resume.pdf`
* Notes text: `sample_inputs/notes.txt`

To run the pipeline on this dataset and output the transformed canonical profile:
```bash
python -m src.cli.main \
  --csv sample_inputs/recruiter.csv \
  --ats sample_inputs/ats.json \
  --resume sample_inputs/resume.pdf \
  --notes sample_inputs/notes.txt \
  --config config/default.json
```

---

## 💡 System Assumptions & Rules

### 1. Source Authority Priorities
When merging single-value fields (e.g. `full_name`, `headline`, `years_experience`), conflicts are resolved using a hierarchy of trust weights:
* **ATS JSON** (`ats`): `0.95` (Highest trust, directly from ATS)
* **Recruiter CSV** (`csv`): `0.90` (Structured data exported by recruiters)
* **GitHub Profile** (`github`): `0.85` (Developer self-reported profiles)
* **Candidate Resume** (`resume`): `0.70` (Extracted from resume text)
* **Recruiter Notes** (`notes`): `0.55` (Lowest trust, unstructured comments)

### 2. Skill Confidence Boosting Formula
Skills identified in multiple sources receive a confidence boost reflecting consensus redundancy:
$$C_{\text{skill}} = \min\left(1.0, \max(C_s) + 0.1 \times (N_{\text{agreed}} - 1)\right)$$
where $C_s$ represents the authority weights of the sources reporting the skill, and $N_{\text{agreed}}$ is the number of sources that match.

### 3. Candidate Matching Heuristics
Profiles are matched as the same candidate if they satisfy any of the following:
* Standardized, trimmed email address matches exactly.
* E.164 phone number matches exactly.
* Case-insensitive names match exactly AND they share a location or job experience records.

### 4. Normalization Rules
* **Phone**: Formatted to the E.164 standard (e.g. `+919140804752`) using `phonenumbers`.
* **Date**: Standardized to `YYYY-MM` (e.g. `2020-03`). Current roles are mapped to `"Present"`.
* **Country**: Converted to two-letter ISO-3166-1 Alpha-2 country codes (e.g. `"United States"` ➔ `"US"`, `"India"` ➔ `"IN"`).

---

## 🛠️ Design Decisions

1. **Zero LLM Dependencies**:
   Built strictly with deterministic algorithms, regex matching, dictionary vocabularies, and standards-compliant parsers to ensure reproducible results, zero latency penalties, and no cost overhead.
2. **Pydantic v2 Domain Models**:
   Used `pydantic` to define compile-time constraints and enforce schema typing on internal canonical objects.
3. **Dynamic JSON Schema Compilation**:
   Instead of using a static output schema, the validation layer parses the runtime configuration, compiles a dynamic draft-07 JSON Schema structure, and runs `jsonschema.validate` against the projected output to guarantee strict configuration-to-output compliance.
