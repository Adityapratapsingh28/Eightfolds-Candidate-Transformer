from typing import List, Optional
from pydantic import BaseModel, Field

class FieldConfig(BaseModel):
    path: str
    from_path: Optional[str] = Field(None, alias="from")
    type: str
    required: bool = False
    normalize: Optional[str] = None

class ProjectionConfig(BaseModel):
    fields: List[FieldConfig] = Field(default_factory=list)
    include_confidence: bool = True
    include_provenance: bool = True
    on_missing: str = "null"  # "null", "omit", or "error"
