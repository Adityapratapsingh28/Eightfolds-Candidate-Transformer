class CandidateTransformerError(Exception):
    """Base exception for all Candidate Transformer Engine errors."""
    pass

class ParserError(CandidateTransformerError):
    """Raised when a specific parser fails to process an input source."""
    pass

class ValidationError(CandidateTransformerError):
    """Raised when the transformed output fails schema validation."""
    pass

class ProjectorError(CandidateTransformerError):
    """Raised when the projection config is invalid or cannot be applied."""
    pass
