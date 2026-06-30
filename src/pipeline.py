from typing import Dict, Any, Optional
from src.models.config import ProjectionConfig
from src.parsers.base import get_parser_for_source
from src.mapper.canonical_mapper import CanonicalMapper
from src.merger.resolver import ConflictResolver
from src.projector.projection import ProjectionEngine
from src.validator.schema_validator import SchemaValidator
from src.utils.exceptions import ParserError, ValidationError
from src.utils.logger import get_logger

logger = get_logger("Pipeline")

class CandidateTransformationPipeline:
    """
    Main orchestration class for the candidate transformation process.
    """
    def __init__(self):
        self.mapper = CanonicalMapper()
        self.resolver = ConflictResolver()
        self.projector = ProjectionEngine()
        self.validator = SchemaValidator()

    def run(
        self,
        config: ProjectionConfig,
        csv_path: Optional[str] = None,
        ats_path: Optional[str] = None,
        resume_path: Optional[str] = None,
        notes_path: Optional[str] = None,
        github_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Runs the full transformation pipeline on provided input sources.
        """
        sources_to_parse = [
            ("csv", csv_path),
            ("ats", ats_path),
            ("resume", resume_path),
            ("notes", notes_path),
            ("github", github_url)
        ]

        raw_payloads = []
        parsing_errors = []

        # Step 1: Ingest & Parse (SRP - BaseParser derivatives)
        for source_type, path in sources_to_parse:
            if not path:
                continue
            
            try:
                parser = get_parser_for_source(path)
                logger.info(f"Parsing {source_type} source: {path}")
                raw_data = parser.parse(path)
                raw_payloads.append((raw_data, source_type))
            except Exception as e:
                logger.warning(f"Failed to parse source {source_type} ({path}) - degrading gracefully: {e}")
                parsing_errors.append((source_type, path, e))

        # Check if all sources failed
        if not raw_payloads:
            raise ParserError(
                f"All provided input sources failed to parse. Errors: {parsing_errors}"
            )

        # Step 2: Canonical Mapping Layer (SRP - CanonicalMapper)
        mapped_profiles = []
        for raw_data, source_type in raw_payloads:
            try:
                mapped_profile = self.mapper.map_to_canonical(raw_data, source_type)
                mapped_profiles.append(mapped_profile)
            except Exception as e:
                logger.warning(f"Failed to map raw {source_type} data to canonical model: {e}")

        if not mapped_profiles:
            raise ParserError("No profiles were successfully mapped to the canonical schema.")

        # Step 3 & 4: Merge Engine & Normalizations (SRP - ConflictResolver / normalizers)
        try:
            logger.info(f"Merging {len(mapped_profiles)} candidate profiles...")
            merged_candidate = self.resolver.merge(mapped_profiles)
        except Exception as e:
            raise ParserError(f"Merge engine failed: {e}") from e

        # Step 5: Projection Engine (SRP - ProjectionEngine)
        try:
            logger.info("Projecting candidate output according to custom configuration...")
            projected_output = self.projector.project(merged_candidate, config)
        except Exception as e:
            raise ParserError(f"Projection engine failed: {e}") from e

        # Step 6: Schema Validator (SRP - SchemaValidator)
        try:
            logger.info("Validating projected output schema...")
            self.validator.validate_projected_output(projected_output, config)
        except ValidationError as e:
            logger.error(f"Output schema validation failed: {e}")
            raise e
        except Exception as e:
            raise ValidationError(f"Unexpected validation error: {e}") from e

        logger.info("Pipeline executed successfully. Canonical candidate transformed and verified.")
        return projected_output


