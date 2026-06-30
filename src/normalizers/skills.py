class SkillsNormalizer:
    """
    Standardizes and canonicalizes skill names.
    """
    SKILLS_MAP = {
        "py": "Python", "python3": "Python", "python 3": "Python",
        "js": "JavaScript", "javascript": "JavaScript", "ecmascript": "JavaScript",
        "react": "React", "reactjs": "React", "react.js": "React",
        "vue": "Vue.js", "vuejs": "Vue.js", "vue.js": "Vue.js",
        "aws": "AWS", "amazon web services": "AWS",
        "ml": "Machine Learning", "machinelearning": "Machine Learning",
        "dl": "Deep Learning", "deeplearning": "Deep Learning",
        "k8s": "Kubernetes", "kubernetes": "Kubernetes",
        "docker": "Docker",
        "golang": "Go", "go lang": "Go", "go": "Go",
        "sql": "SQL", "postgres": "PostgreSQL", "postgresql": "PostgreSQL",
        "html": "HTML", "css": "CSS", "cpp": "C++", "c++": "C++",
        "rust": "Rust", "git": "Git"
    }

    @staticmethod
    def normalize(skill: str) -> str:
        if not skill:
            return ""
        
        skill_clean = skill.strip().lower()
        
        # Check canonical mapping
        canonical = SkillsNormalizer.SKILLS_MAP.get(skill_clean)
        if canonical:
            return canonical

        # Fallback to general formatting
        return skill.strip()

