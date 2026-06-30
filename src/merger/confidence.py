from typing import List
from src.models.candidate import CanonicalCandidate

class ConfidenceEngine:
    """
    Computes overall profile confidence based on source quality, agreement, and completeness.
    """
    SOURCE_WEIGHTS = {
        "ats": 0.95,
        "csv": 0.90,
        "github": 0.85,
        "resume": 0.70,
        "notes": 0.55
    }

    def calculate(self, candidate: CanonicalCandidate, source_profiles: List[CanonicalCandidate] = None) -> float:
        if not source_profiles:
            # Fallback if no source profiles provided, check provenance
            sources = {prov.get("source") for prov in candidate.provenance if prov.get("source")}
        else:
            sources = {p.candidate_id.split("_")[0] for p in source_profiles}

        if not sources:
            return 0.0

        # Base confidence is the highest weight among the sources present
        base_confidence = max(self.SOURCE_WEIGHTS.get(src, 0.5) for src in sources)

        # Completeness bonus (up to +0.20)
        completeness_bonus = 0.0
        if candidate.emails:
            completeness_bonus += 0.05
        if candidate.phones:
            completeness_bonus += 0.05
        if candidate.skills:
            completeness_bonus += 0.05
        if candidate.experience:
            completeness_bonus += 0.05

        # Redundancy bonus (having more than one source validates identity, +0.05 per extra source)
        redundancy_bonus = 0.05 * (len(sources) - 1)

        total_confidence = base_confidence + completeness_bonus + redundancy_bonus

        return min(1.0, round(total_confidence, 2))

