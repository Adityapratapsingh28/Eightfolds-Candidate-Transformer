import re
from typing import Any, Dict, List
from src.models.candidate import CanonicalCandidate
from src.models.config import ProjectionConfig
from src.utils.exceptions import ProjectorError
from src.normalizers.phone import PhoneNormalizer
from src.normalizers.skills import SkillsNormalizer

class ProjectionEngine:
    """
    Applies custom projection configurations to the canonical profile output.
    """
    def _resolve_path(self, data: Any, parts: List[str]) -> Any:
        if not parts or data is None:
            return data

        current_part = parts[0]
        remaining_parts = parts[1:]

        # Handle array syntax: e.g. "emails[0]" or "skills[]"
        if "[" in current_part and "]" in current_part:
            match = re.match(r"^([^\[]+)\[(.*)\]$", current_part)
            if match:
                field_name = match.group(1)
                index_str = match.group(2)

                if isinstance(data, dict):
                    value = data.get(field_name)
                elif hasattr(data, field_name):
                    value = getattr(data, field_name)
                else:
                    return None

                if value is None:
                    return None

                if index_str == "":
                    # Map-all "[]": iterate remaining parts over the list
                    if isinstance(value, list):
                        return [self._resolve_path(item, remaining_parts) for item in value]
                    return None
                else:
                    # Index lookup "[index]"
                    try:
                        idx = int(index_str)
                        if isinstance(value, list) and 0 <= idx < len(value):
                            return self._resolve_path(value[idx], remaining_parts)
                        return None
                    except ValueError:
                        return None
            return None
        else:
            # Standard field key lookup
            if isinstance(data, dict):
                value = data.get(current_part)
            elif hasattr(data, current_part):
                value = getattr(data, current_part)
            else:
                return None
            
            return self._resolve_path(value, remaining_parts)

    def _apply_normalization(self, value: Any, rule: str) -> Any:
        if value is None:
            return None

        if isinstance(value, list):
            return [self._apply_normalization(item, rule) for item in value]

        if not isinstance(value, str):
            return value

        if rule == "E.164":
            return PhoneNormalizer.normalize(value)
        elif rule == "canonical":
            return SkillsNormalizer.normalize(value)
        
        return value

    def project(self, candidate: CanonicalCandidate, config: ProjectionConfig) -> Dict[str, Any]:
        # Immutability: convert to dictionary representation
        candidate_dict = candidate.model_dump()
        projected: Dict[str, Any] = {}

        for field in config.fields:
            # Pick path to fetch value from
            target_path = field.from_path if field.from_path else field.path
            parts = target_path.split(".")
            
            val = self._resolve_path(candidate_dict, parts)

            # Apply per-field normalization if specified
            if field.normalize and val is not None:
                val = self._apply_normalization(val, field.normalize)

            # Handle missing values
            # (Empty lists or empty strings can be considered missing depending on context,
            # but let's check None)
            is_missing = (val is None) or (isinstance(val, list) and len(val) == 0)

            if is_missing:
                if field.required:
                    raise ProjectorError(f"Required field '{field.path}' is missing.")
                
                # Apply missing value policy
                if config.on_missing == "error":
                    raise ProjectorError(f"Field '{field.path}' is missing.")
                elif config.on_missing == "null":
                    projected[field.path] = None
                # If "omit", do nothing (do not insert the key)
            else:
                projected[field.path] = val

        # Root level toggles
        if config.include_confidence:
            projected["overall_confidence"] = candidate.overall_confidence
        
        if config.include_provenance:
            projected["provenance"] = candidate_dict.get("provenance", [])

        return projected

