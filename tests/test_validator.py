import pytest
import tempfile
import json
from src.validator.schema_validator import SchemaValidator
from src.models.config import ProjectionConfig
from src.utils.loader import load_config
from src.utils.exceptions import ValidationError

@pytest.fixture
def sample_config():
    config_dict = {
        "fields": [
            {"path": "full_name", "type": "string", "required": True},
            {"path": "email", "from": "emails[0]", "type": "string"},
            {"path": "skills", "from": "skills[].name", "type": "string[]"}
        ],
        "include_confidence": True,
        "include_provenance": True,
        "on_missing": "null"
    }
    return ProjectionConfig.model_validate(config_dict)

def test_validator_success(sample_config):
    validator = SchemaValidator()
    
    # Matching output format
    output = {
        "full_name": "Alice Smith",
        "email": "alice@example.com",
        "skills": ["Python", "JavaScript"],
        "overall_confidence": 0.85,
        "provenance": [
            {"field": "full_name", "source": "ats", "method": "json_path_mapping"}
        ]
    }
    
    assert validator.validate_projected_output(output, sample_config) is True

def test_validator_missing_required(sample_config):
    validator = SchemaValidator()
    
    # Missing required 'full_name'
    output = {
        "email": "alice@example.com",
        "skills": ["Python"]
    }
    
    with pytest.raises(ValidationError) as excinfo:
        validator.validate_projected_output(output, sample_config)
    assert "Schema validation failed" in str(excinfo.value)

def test_validator_type_mismatch(sample_config):
    validator = SchemaValidator()
    
    # 'skills' is supposed to be array of strings, not a single string
    output = {
        "full_name": "Alice Smith",
        "email": "alice@example.com",
        "skills": "Python"
    }
    
    with pytest.raises(ValidationError) as excinfo:
        validator.validate_projected_output(output, sample_config)
    assert "Schema validation failed" in str(excinfo.value)

def test_config_loader_invalid_json():
    with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".json") as tmp:
        tmp.write("invalid json string {")
        tmp_path = tmp.name
        
    with pytest.raises(ValidationError) as excinfo:
        load_config(tmp_path)
    assert "Invalid JSON format" in str(excinfo.value)

def test_config_loader_invalid_schema():
    invalid_config = {
        "fields": [
            # Type is required but missing here
            {"path": "full_name"}
        ]
    }
    with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".json") as tmp:
        json.dump(invalid_config, tmp)
        tmp_path = tmp.name
        
    with pytest.raises(ValidationError) as excinfo:
        load_config(tmp_path)
    assert "Configuration validation failed" in str(excinfo.value)
