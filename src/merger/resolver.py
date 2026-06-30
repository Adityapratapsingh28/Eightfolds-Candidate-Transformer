from typing import List, Dict, Any, Set
from src.models.candidate import CanonicalCandidate, Location, Links, Skill, Experience, Education
from src.normalizers.phone import PhoneNormalizer
from src.normalizers.date import DateNormalizer
from src.normalizers.location import LocationNormalizer
from src.normalizers.skills import SkillsNormalizer
from src.normalizers.text import TextNormalizer
from src.merger.confidence import ConfidenceEngine

class ConflictResolver:
    """
    Merges a list of candidates into a single canonical record and resolves conflicts.
    """
    
    PRIORITIES = {"ats": 0, "csv": 1, "github": 2, "resume": 3, "notes": 4}
    SOURCE_CONFIDENCES = {"ats": 0.95, "csv": 0.90, "github": 0.85, "resume": 0.70, "notes": 0.55}

    def _get_source_priority(self, profile: CanonicalCandidate) -> int:
        prefix = profile.candidate_id.split("_")[0]
        return self.PRIORITIES.get(prefix, 10)

    def _get_source_name(self, profile: CanonicalCandidate) -> str:
        return profile.candidate_id.split("_")[0]

    def merge(self, profiles: List[CanonicalCandidate]) -> CanonicalCandidate:
        if not profiles:
            raise ValueError("Cannot merge empty list of profiles.")

        # Sort profiles by source priority (highest authority first)
        sorted_profiles = sorted(profiles, key=self._get_source_priority)

        # 1. Merge Single-value fields
        full_name = None
        headline = None
        
        # Provenance collection
        provenance: List[Dict[str, Any]] = []

        # Find full name from highest priority
        for p in sorted_profiles:
            if p.full_name:
                full_name = TextNormalizer.clean_text(p.full_name)
                # Find matching provenance
                for prov in p.provenance:
                    if prov.get("field") == "full_name":
                        provenance.append(prov)
                        break
                else:
                    provenance.append({"field": "full_name", "source": self._get_source_name(p), "method": "merge"})
                break

        # Find headline from highest priority
        for p in sorted_profiles:
            if p.headline:
                headline = TextNormalizer.clean_text(p.headline)
                for prov in p.provenance:
                    if prov.get("field") == "headline":
                        provenance.append(prov)
                        break
                else:
                    provenance.append({"field": "headline", "source": self._get_source_name(p), "method": "merge"})
                break

        # 2. Merge Location components
        city = None
        region = None
        country = None
        location_source = None

        for p in sorted_profiles:
            if p.location:
                if p.location.city and not city:
                    city = p.location.city
                    location_source = self._get_source_name(p)
                if p.location.region and not region:
                    region = p.location.region
                    location_source = self._get_source_name(p)
                if p.location.country and not country:
                    country = p.location.country
                    location_source = self._get_source_name(p)

        norm_location = None
        if city or region or country:
            raw_loc = {"city": city, "region": region, "country": country}
            norm_loc_dict = LocationNormalizer.normalize(raw_loc)
            norm_location = Location(**norm_loc_dict)
            provenance.append({"field": "location", "source": location_source or "merge", "method": "merge"})

        # 3. Merge Links
        linkedin = None
        github = None
        portfolio = None
        other_links: Set[str] = set()
        links_source = None

        for p in sorted_profiles:
            if p.links:
                if p.links.linkedin and not linkedin:
                    linkedin = p.links.linkedin
                    links_source = self._get_source_name(p)
                if p.links.github and not github:
                    github = p.links.github
                    links_source = self._get_source_name(p)
                if p.links.portfolio and not portfolio:
                    portfolio = p.links.portfolio
                    links_source = self._get_source_name(p)
                if p.links.other:
                    other_links.update(p.links.other)

        links = None
        if linkedin or github or portfolio or other_links:
            links = Links(
                linkedin=linkedin,
                github=github,
                portfolio=portfolio,
                other=sorted(list(other_links))
            )
            provenance.append({"field": "links", "source": links_source or "merge", "method": "merge"})

        # 4. Merge & Deduplicate emails and phones
        emails_set: Set[str] = set()
        phones_set: Set[str] = set()

        for p in sorted_profiles:
            for email in p.emails:
                clean_e = TextNormalizer.clean_email(email)
                if clean_e:
                    emails_set.add(clean_e)
            for phone in p.phones:
                clean_p = PhoneNormalizer.normalize(phone)
                if clean_p:
                    phones_set.add(clean_p)

        emails = sorted(list(emails_set))
        phones = sorted(list(phones_set))

        if emails: provenance.append({"field": "emails", "source": "multiple", "method": "deduplication"})
        if phones: provenance.append({"field": "phones", "source": "multiple", "method": "deduplication"})

        # 5. Merge & Deduplicate skills
        skills_grouped: Dict[str, List[Skill]] = {}
        for p in sorted_profiles:
            for skill in p.skills:
                norm_name = SkillsNormalizer.normalize(skill.name)
                if norm_name not in skills_grouped:
                    skills_grouped[norm_name] = []
                skills_grouped[norm_name].append(skill)

        skills: List[Skill] = []
        for norm_name, list_skills in skills_grouped.items():
            # Union of sources
            skill_sources: Set[str] = set()
            for s in list_skills:
                skill_sources.update(s.sources)
            
            # Highest base confidence based on sources
            base_conf = 0.0
            for src in skill_sources:
                base_conf = max(base_conf, self.SOURCE_CONFIDENCES.get(src, 0.5))

            # Redundancy bonus (+0.1 for each additional source)
            confidence = min(1.0, base_conf + 0.1 * (len(skill_sources) - 1))
            
            skills.append(Skill(
                name=norm_name,
                confidence=round(confidence, 2),
                sources=sorted(list(skill_sources))
            ))
        
        # Sort skills by confidence desc, then name asc
        skills = sorted(skills, key=lambda s: (-s.confidence, s.name))
        if skills: provenance.append({"field": "skills", "source": "multiple", "method": "skills_merging"})

        # 6. Merge & Deduplicate experience
        # Key: company_name + "|" + job_title (whitespace and lowercase normalized)
        exp_grouped: Dict[str, List[Experience]] = {}
        for p in sorted_profiles:
            for exp in p.experience:
                clean_company = TextNormalizer.clean_text(exp.company).lower()
                clean_title = TextNormalizer.clean_text(exp.title).lower()
                key = f"{clean_company}|{clean_title}"
                if key not in exp_grouped:
                    exp_grouped[key] = []
                exp_grouped[key].append(exp)

        experience: List[Experience] = []
        for key, exp_list in exp_grouped.items():
            # Pick earliest start date and latest end date
            start_dates = [exp.start for exp in exp_list if exp.start]
            end_dates = [exp.end for exp in exp_list if exp.end]
            
            norm_start_dates = sorted([DateNormalizer.normalize(d) for d in start_dates if d])
            norm_end_dates = sorted([DateNormalizer.normalize(d) for d in end_dates if d])
            
            start = norm_start_dates[0] if norm_start_dates else None
            
            # Handle Present end date prioritisation
            end = None
            if "Present" in norm_end_dates:
                end = "Present"
            elif norm_end_dates:
                end = norm_end_dates[-1]

            # Pick longest summary
            summary = ""
            for exp in exp_list:
                if exp.summary and len(exp.summary) > len(summary):
                    summary = exp.summary

            # Normalized company and title
            company = TextNormalizer.clean_text(exp_list[0].company)
            title = TextNormalizer.clean_text(exp_list[0].title)

            experience.append(Experience(
                company=company,
                title=title,
                start=start,
                end=end,
                summary=summary or None
            ))

        # Sort experience by start date descending
        def get_start_date_key(exp: Experience) -> str:
            return exp.start or "0000-00"
        experience = sorted(experience, key=get_start_date_key, reverse=True)
        if experience: provenance.append({"field": "experience", "source": "multiple", "method": "experience_merging"})

        # 7. Merge & Deduplicate education
        # Key: institution + "|" + degree (whitespace and lowercase normalized)
        edu_grouped: Dict[str, List[Education]] = {}
        for p in sorted_profiles:
            for edu in p.education:
                clean_inst = TextNormalizer.clean_text(edu.institution).lower()
                clean_degree = TextNormalizer.clean_text(edu.degree or "").lower()
                key = f"{clean_inst}|{clean_degree}"
                if key not in edu_grouped:
                    edu_grouped[key] = []
                edu_grouped[key].append(edu)

        education: List[Education] = []
        for key, edu_list in edu_grouped.items():
            end_years = [edu.end_year for edu in edu_list if edu.end_year]
            end_year = max(end_years) if end_years else None

            inst = TextNormalizer.clean_text(edu_list[0].institution)
            degree = TextNormalizer.clean_text(edu_list[0].degree) if edu_list[0].degree else None
            field = TextNormalizer.clean_text(edu_list[0].field) if edu_list[0].field else None

            education.append(Education(
                institution=inst,
                degree=degree,
                field=field,
                end_year=end_year
            ))

        # Sort education by end_year descending
        education = sorted(education, key=lambda e: e.end_year or 0, reverse=True)
        if education: provenance.append({"field": "education", "source": "multiple", "method": "education_merging"})

        # Assemble temporary Candidate model for calculating confidence
        candidate_id = f"merged_{full_name.lower().replace(' ', '_')}" if full_name else "merged_unknown"
        
        merged_candidate = CanonicalCandidate(
            candidate_id=candidate_id,
            full_name=full_name,
            emails=emails,
            phones=phones,
            location=norm_location,
            links=links,
            headline=headline,
            skills=skills,
            experience=experience,
            education=education,
            provenance=provenance,
            overall_confidence=0.0
        )

        # 8. Confidence calculation
        engine = ConfidenceEngine()
        merged_candidate.overall_confidence = engine.calculate(merged_candidate, profiles)

        return merged_candidate

