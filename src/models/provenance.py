from pydantic import BaseModel

class ProvenanceEntry(BaseModel):
    field: str
    source: str
    method: str
