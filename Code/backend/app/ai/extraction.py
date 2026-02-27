"""
AI-powered information extraction from resume text.
Handles skill extraction, experience detection, and domain classification.
"""
import re
from typing import List, Dict, Optional
import json

from app.ai.embeddings import get_embedding_service


# Predefined skill database (can be extended or loaded from DB)
SKILL_DATABASE = [
    # Programming Languages
    "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust", "Ruby", "PHP",
    "Swift", "Kotlin", "Scala", "R", "MATLAB", "SQL",
    
    # Web Technologies
    "React", "Angular", "Vue.js", "Node.js", "Express", "Django", "Flask", "FastAPI",
    "Spring Boot", "ASP.NET", "HTML", "CSS", "REST API", "GraphQL",
    
    # Databases
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "Cassandra",
    "Oracle", "SQL Server", "DynamoDB",
    
    # Cloud & DevOps
    "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Jenkins", "GitLab CI",
    "Terraform", "Ansible", "CI/CD",
    
    # Data Science & ML
    "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "Scikit-learn",
    "Pandas", "NumPy", "NLP", "Computer Vision", "Data Analysis",
    
    # Other
    "Git", "Linux", "Agile", "Scrum", "Microservices", "System Design"
]

# Domain keywords
DOMAIN_KEYWORDS = {
    "software_engineering": ["software", "development", "engineering", "programming", "coding"],
    "data_science": ["data science", "machine learning", "AI", "analytics", "statistics"],
    "devops": ["devops", "infrastructure", "cloud", "deployment", "automation"],
    "frontend": ["frontend", "UI", "UX", "web design", "react", "angular"],
    "backend": ["backend", "server", "API", "database", "microservices"],
    "mobile": ["mobile", "android", "iOS", "app development"],
    "security": ["security", "cybersecurity", "penetration testing", "encryption"]
}


class ExtractionService:
    """Service for extracting structured information from resume text"""
    
    def __init__(self):
        self.embedding_service = get_embedding_service()
    
    def extract_skills(self, text: str, use_embeddings: bool = True) -> List[str]:
        """
        Extract skills from resume text.
        
        Args:
            text: Resume text
            use_embeddings: Whether to use semantic matching
            
        Returns:
            List of extracted skills
        """
        skills = set()
        text_lower = text.lower()
        
        # Method 1: Keyword-based extraction
        for skill in SKILL_DATABASE:
            if skill.lower() in text_lower:
                skills.add(skill)
        
        # Method 2: Embedding-based similarity (optional)
        if use_embeddings and len(skills) < 5:
            # Extract potential skill phrases (2-3 word combinations)
            words = re.findall(r'\b[A-Za-z][A-Za-z\s]{1,20}\b', text)
            for phrase in words[:50]:  # Limit to first 50 phrases
                phrase = phrase.strip()
                if len(phrase) > 2:
                    similar = self.embedding_service.find_similar_skills(
                        phrase, SKILL_DATABASE, threshold=0.75
                    )
                    if similar:
                        skills.add(similar[0][0])
        
        return sorted(list(skills))
    
    def extract_experience(self, text: str) -> Dict[str, any]:
        """
        Extract experience information from resume text.
        
        Args:
            text: Resume text
            
        Returns:
            Dictionary with experience details
        """
        experience = {
            "years": None,
            "summary": ""
        }
        
        # Pattern 1: "X years of experience"
        years_pattern = r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:experience|exp)'
        match = re.search(years_pattern, text, re.IGNORECASE)
        if match:
            experience["years"] = int(match.group(1))
        
        # Pattern 2: Extract experience section
        exp_section_pattern = r'(?:experience|work history|employment)(.*?)(?:education|skills|projects|$)'
        match = re.search(exp_section_pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            experience["summary"] = match.group(1).strip()[:500]  # Limit to 500 chars
        
        return experience
    
    def detect_domain(self, text: str, skills: List[str]) -> str:
        """
        Detect professional domain from resume text and skills.
        
        Args:
            text: Resume text
            skills: Extracted skills
            
        Returns:
            Detected domain
        """
        text_lower = text.lower()
        domain_scores = {}
        
        # Score each domain based on keyword matches
        for domain, keywords in DOMAIN_KEYWORDS.items():
            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1
            
            # Bonus score from skills
            for skill in skills:
                skill_lower = skill.lower()
                for keyword in keywords:
                    if keyword in skill_lower or skill_lower in keyword:
                        score += 2
            
            domain_scores[domain] = score
        
        # Return domain with highest score
        if domain_scores:
            best_domain = max(domain_scores, key=domain_scores.get)
            if domain_scores[best_domain] > 0:
                return best_domain
        
        return "general"
    
    def extract_all(self, text: str) -> Dict[str, any]:
        """
        Extract all information from resume text.
        
        Args:
            text: Resume text
            
        Returns:
            Dictionary with all extracted information
        """
        # Extract skills
        skills = self.extract_skills(text)
        
        # Extract experience
        experience = self.extract_experience(text)
        
        # Detect domain
        domain = self.detect_domain(text, skills)
        
        return {
            "skills": skills,
            "experience": experience,
            "domain": domain,
            "raw_text_length": len(text)
        }


# Singleton instance
_extraction_service = None


def get_extraction_service() -> ExtractionService:
    """Get singleton extraction service instance"""
    global _extraction_service
    if _extraction_service is None:
        _extraction_service = ExtractionService()
    return _extraction_service
