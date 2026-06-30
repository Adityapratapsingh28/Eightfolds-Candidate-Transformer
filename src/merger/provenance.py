from typing import Any, Dict
from src.models.candidate import CanonicalCandidate

class ProvenanceEngine:
    """
    Appends and manages provenance details for candidate fields.
    """
    def log_field(self, candidate: CanonicalCandidate, field_path: str, source: str, method: str) -> None:
        entry = {
            "field": field_path,
            "source": source,
            "method": method
        }
        if entry not in candidate.provenance:
            candidate.provenance.append(entry)

