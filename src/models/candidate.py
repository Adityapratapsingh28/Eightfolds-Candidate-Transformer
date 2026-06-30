from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class Location(BaseModel):
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None  # ISO-3166 alpha-2

class Links(BaseModel):
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None
    other: List[str] = Field(default_factory=list)

class Skill(BaseModel):
    name: str
    confidence: float
    sources: List[str]

class Experience(BaseModel):
    company: str
    title: str
    start: Optional[str] = None  # YYYY-MM
    end: Optional[str] = None    # YYYY-MM
    summary: Optional[str] = None

class Education(BaseModel):
    institution: str
    degree: Optional[str] = None
    field: Optional[str] = None
    end_year: Optional[int] = None

class CanonicalCandidate(BaseModel):
    candidate_id: str
    full_name: Optional[str] = None
    emails: List[str] = Field(default_factory=list)
    phones: List[str] = Field(default_factory=list)
    location: Optional[Location] = None
    links: Optional[Links] = None
    headline: Optional[str] = None
    years_experience: Optional[float] = None
    skills: List[Skill] = Field(default_factory=list)
    experience: List[Experience] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    provenance: List[Dict[str, Any]] = Field(default_factory=list)
    overall_confidence: float = 0.0
