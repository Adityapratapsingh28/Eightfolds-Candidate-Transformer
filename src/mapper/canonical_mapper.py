import re
from typing import Any, Dict, List, Optional
from src.models.candidate import CanonicalCandidate, Location, Links, Skill, Experience, Education
from src.utils.exceptions import ParserError

class CanonicalMapper:
    """
    Maps heterogeneous parser output dicts into CanonicalCandidate models.
    """
    
    # Vocabulary list for matching skills in unstructured texts
    SKILLS_VOCABULARY = [
        "Python", "Java", "C++", "JavaScript", "HTML", "CSS", "AWS", 
        "Docker", "Kubernetes", "SQL", "Machine Learning", "Deep Learning", 
        "React", "Pandas", "NumPy", "Git", "Go", "Rust"
    ]

    def map_to_canonical(self, raw_payload: Dict[str, Any], source_type: str) -> CanonicalCandidate:
        """
        Takes raw parser payload and transforms it to a CanonicalCandidate.
        """
        raw_content = raw_payload.get("raw_content")
        source_path = raw_payload.get("source_path", "unknown")
        
        if raw_content is None:
            raise ParserError(f"No raw content found in payload for mapping.")

        if source_type == "csv":
            return self._map_csv(raw_content, source_path)
        elif source_type == "ats":
            return self._map_ats(raw_content, source_path)
        elif source_type == "resume":
            return self._map_resume(raw_content, source_path)
        elif source_type == "notes":
            return self._map_notes(raw_content, source_path)
        elif source_type == "github":
            return self._map_github(raw_content, source_path)
        else:
            raise ParserError(f"Unsupported source type for mapping: {source_type}")

    def _create_provenance_entry(self, field: str, source: str, method: str) -> Dict[str, str]:
        return {
            "field": field,
            "source": source,
            "method": method
        }

    def _map_csv(self, raw_content: Any, source_path: str) -> CanonicalCandidate:
        # Check if list and get first record
        record = {}
        if isinstance(raw_content, list) and len(raw_content) > 0:
            record = raw_content[0]
        elif isinstance(raw_content, dict):
            record = raw_content

        full_name = record.get("name")
        emails = [record.get("email")] if record.get("email") else []
        phones = [record.get("phone")] if record.get("phone") else []

        experience = []
        if record.get("current_company") or record.get("title"):
            experience.append(Experience(
                company=record.get("current_company") or "Unknown",
                title=record.get("title") or "Unknown",
                summary="Current position (CSV)"
            ))

        provenance = []
        if full_name: provenance.append(self._create_provenance_entry("full_name", "csv", "direct_mapping"))
        if emails: provenance.append(self._create_provenance_entry("emails", "csv", "direct_mapping"))
        if phones: provenance.append(self._create_provenance_entry("phones", "csv", "direct_mapping"))
        if experience: provenance.append(self._create_provenance_entry("experience", "csv", "direct_mapping"))

        # Generate a candidate ID from name or email
        candidate_id = f"csv_{full_name.lower().replace(' ', '_')}" if full_name else "csv_unknown"

        return CanonicalCandidate(
            candidate_id=candidate_id,
            full_name=full_name,
            emails=emails,
            phones=phones,
            experience=experience,
            provenance=provenance,
            overall_confidence=1.0  # Structured direct mapping gets high confidence
        )

    def _map_ats(self, raw_content: Dict[str, Any], source_path: str) -> CanonicalCandidate:
        candidate_info = raw_content.get("candidate", {})
        first_name = candidate_info.get("first_name", "")
        last_name = candidate_info.get("last_name", "")
        full_name = f"{first_name} {last_name}".strip() or None

        contact = candidate_info.get("contact", {})
        emails = [contact.get("email_address")] if contact.get("email_address") else []
        phones = [contact.get("phone_number")] if contact.get("phone_number") else []

        experience_list = []
        for pos in candidate_info.get("positions", []):
            experience_list.append(Experience(
                company=pos.get("company_name") or "Unknown",
                title=pos.get("job_title") or "Unknown",
                start=pos.get("start_date"),
                end=pos.get("end_date"),
                summary=pos.get("description")
            ))

        education_list = []
        for edu in candidate_info.get("education_records", []):
            education_list.append(Education(
                institution=edu.get("school") or "Unknown",
                degree=edu.get("degree_name"),
                field=edu.get("major"),
                end_year=edu.get("graduation_year")
            ))

        provenance = []
        if full_name: provenance.append(self._create_provenance_entry("full_name", "ats", "json_path_mapping"))
        if emails: provenance.append(self._create_provenance_entry("emails", "ats", "json_path_mapping"))
        if phones: provenance.append(self._create_provenance_entry("phones", "ats", "json_path_mapping"))
        if experience_list: provenance.append(self._create_provenance_entry("experience", "ats", "json_path_mapping"))
        if education_list: provenance.append(self._create_provenance_entry("education", "ats", "json_path_mapping"))

        candidate_id = f"ats_{full_name.lower().replace(' ', '_')}" if full_name else "ats_unknown"

        return CanonicalCandidate(
            candidate_id=candidate_id,
            full_name=full_name,
            emails=emails,
            phones=phones,
            experience=experience_list,
            education=education_list,
            provenance=provenance,
            overall_confidence=0.9
        )

    def _map_resume(self, raw_content: Dict[str, Any], source_path: str) -> CanonicalCandidate:
        text = raw_content.get("raw_text", "")
        
        # Regex extraction
        emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
        phones = re.findall(r"\+?\d{1,4}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}", text)
        # Filter phone candidates that are too short to be real phones (like year dates)
        phones = [p.strip() for p in phones if len(re.sub(r"\D", "", p)) >= 7]

        # Extract name: first non-empty line with 2-4 words
        full_name = None
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        for line in lines[:5]:
            words = line.split()
            if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words if w.isalpha()):
                full_name = line
                break

        # If not found, use the first line
        if not full_name and lines:
            full_name = lines[0]

        # Skill matching
        skills_matched = []
        for skill in self.SKILLS_VOCABULARY:
            if re.search(r"\b" + re.escape(skill) + r"\b", text, re.IGNORECASE):
                skills_matched.append(Skill(name=skill, confidence=0.7, sources=["resume"]))

        provenance = []
        if full_name: provenance.append(self._create_provenance_entry("full_name", "resume", "heuristics"))
        if emails: provenance.append(self._create_provenance_entry("emails", "resume", "regex_extraction"))
        if phones: provenance.append(self._create_provenance_entry("phones", "resume", "regex_extraction"))
        if skills_matched: provenance.append(self._create_provenance_entry("skills", "resume", "vocabulary_matching"))

        candidate_id = f"resume_{full_name.lower().replace(' ', '_')}" if full_name else "resume_unknown"

        return CanonicalCandidate(
            candidate_id=candidate_id,
            full_name=full_name,
            emails=emails,
            phones=phones,
            skills=skills_matched,
            provenance=provenance,
            overall_confidence=0.7
        )

    def _map_notes(self, raw_content: Dict[str, Any], source_path: str) -> CanonicalCandidate:
        text = raw_content.get("raw_text", "")
        
        # Regex extraction
        emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
        phones = re.findall(r"\+?\d{1,4}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}", text)
        phones = [p.strip() for p in phones if len(re.sub(r"\D", "", p)) >= 7]

        # Extract name: Look for Name: [Name] or Candidate: [Name]
        full_name = None
        match = re.search(r"(?:Candidate|Name)\s*:\s*([A-Z][a-z]+(?:[ \t]+[A-Z][a-z]+)*)", text, re.IGNORECASE)
        if match:
            full_name = match.group(1).strip()
        else:
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            if lines:
                full_name = lines[0]

        skills_matched = []
        for skill in self.SKILLS_VOCABULARY:
            if re.search(r"\b" + re.escape(skill) + r"\b", text, re.IGNORECASE):
                skills_matched.append(Skill(name=skill, confidence=0.7, sources=["notes"]))

        provenance = []
        if full_name: provenance.append(self._create_provenance_entry("full_name", "notes", "regex_extraction"))
        if emails: provenance.append(self._create_provenance_entry("emails", "notes", "regex_extraction"))
        if phones: provenance.append(self._create_provenance_entry("phones", "notes", "regex_extraction"))
        if skills_matched: provenance.append(self._create_provenance_entry("skills", "notes", "vocabulary_matching"))

        candidate_id = f"notes_{full_name.lower().replace(' ', '_')}" if full_name else "notes_unknown"

        return CanonicalCandidate(
            candidate_id=candidate_id,
            full_name=full_name,
            emails=emails,
            phones=phones,
            skills=skills_matched,
            provenance=provenance,
            overall_confidence=0.6
        )

    def _map_github(self, raw_content: Dict[str, Any], source_path: str) -> CanonicalCandidate:
        user_info = raw_content.get("user", {})
        repos = raw_content.get("repos", [])

        full_name = user_info.get("name") or user_info.get("login")
        emails = [user_info.get("email")] if user_info.get("email") else []
        headline = user_info.get("bio")

        # Links mapping
        links = Links(
            github=user_info.get("html_url"),
            other=[]
        )

        # Location mapping (non-normalized, just split text if possible)
        location_raw = user_info.get("location")
        location = None
        if location_raw:
            parts = [p.strip() for p in location_raw.split(",")]
            city = parts[0] if len(parts) > 0 else None
            region = parts[1] if len(parts) > 1 else None
            location = Location(city=city, region=region, country=None)

        # Repos language extraction
        languages = set()
        for repo in repos:
            lang = repo.get("language")
            if lang:
                languages.add(lang)

        skills = []
        for lang in languages:
            skills.append(Skill(name=lang, confidence=0.8, sources=["github"]))

        provenance = []
        if full_name: provenance.append(self._create_provenance_entry("full_name", "github", "api_enrichment"))
        if emails: provenance.append(self._create_provenance_entry("emails", "github", "api_enrichment"))
        if headline: provenance.append(self._create_provenance_entry("headline", "github", "api_enrichment"))
        if links.github: provenance.append(self._create_provenance_entry("links", "github", "api_enrichment"))
        if location: provenance.append(self._create_provenance_entry("location", "github", "api_enrichment"))
        if skills: provenance.append(self._create_provenance_entry("skills", "github", "api_enrichment"))

        candidate_id = f"github_{full_name.lower().replace(' ', '_')}" if full_name else "github_unknown"

        return CanonicalCandidate(
            candidate_id=candidate_id,
            full_name=full_name,
            emails=emails,
            headline=headline,
            links=links,
            location=location,
            skills=skills,
            provenance=provenance,
            overall_confidence=0.8
        )

