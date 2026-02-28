"""
BERT-NER model service for resume entity extraction.
Uses yashpwr/resume-ner-bert-v2 as a SUPPLEMENTARY signal.

The NER model has limited accuracy, so results are heavily
post-processed and filtered. Used alongside regex/keyword
matching for robust extraction.
"""
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
from typing import List, Dict, Optional
import re

from app.core.config import settings


class NERModelService:
    """Service for extracting entities from resume text using BERT-NER.
    
    NOTE: This model produces noisy output (broken subword tokens,
    dates leaking into entities). All results are cleaned and 
    filtered aggressively before use.
    """

    # Map NER entity labels to our internal field names
    ENTITY_MAP = {
        "Skills": "skills",
        "Designation": "designation",
        "Companies worked at": "companies",
        "Degree": "degree",
        "College Name": "college",
        "Graduation Year": "graduation_year",
        "Years of Experience": "experience_years",
        "Name": "name",
        "Email Address": "email",
        "Phone": "phone",
        "Location": "location",
    }

    def __init__(self):
        self.model_name = settings.NER_MODEL
        self.confidence_threshold = settings.NER_CONFIDENCE_THRESHOLD
        self._pipeline = None
        self._tokenizer = None
        self._load_model()

    def _load_model(self):
        """Load the BERT-NER model and tokenizer."""
        if self._pipeline is None:
            print(f"Loading BERT-NER model: {self.model_name}")
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            model = AutoModelForTokenClassification.from_pretrained(self.model_name)
            self._pipeline = pipeline(
                "token-classification",
                model=model,
                tokenizer=self._tokenizer,
                aggregation_strategy="simple",
                device=-1,  # CPU
            )
            print("✓ BERT-NER model loaded successfully")

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract entities from resume text with aggressive cleaning.

        Returns:
            Dict mapping entity type to list of CLEANED values.
        """
        chunks = self._chunk_text(text)
        all_entities: Dict[str, List[str]] = {}

        for chunk in chunks:
            try:
                results = self._pipeline(chunk)
            except Exception as e:
                print(f"NER inference error on chunk: {e}")
                continue

            for entity in results:
                score = entity.get("score", 0)
                if score < self.confidence_threshold:
                    continue

                entity_group = entity.get("entity_group", "")
                word = entity.get("word", "").strip()

                # Clean the entity text
                word = self._clean_entity_text(word)

                if not word or len(word) < 2:
                    continue

                # Map to our internal field name
                field = self.ENTITY_MAP.get(entity_group)
                if field is None:
                    continue

                # Additional validation per entity type
                if not self._validate_entity(field, word, score):
                    continue

                if field not in all_entities:
                    all_entities[field] = []

                # Deduplicate (case-insensitive)
                if not any(w.lower() == word.lower() for w in all_entities[field]):
                    all_entities[field].append(word)

        return all_entities

    def _chunk_text(self, text: str, max_chars: int = 1500, overlap: int = 200) -> List[str]:
        """Split long text into overlapping chunks."""
        if len(text) <= max_chars:
            return [text]

        chunks = []
        start = 0
        while start < len(text):
            end = start + max_chars
            if end < len(text):
                boundary = text.rfind('. ', start + max_chars // 2, end)
                if boundary == -1:
                    boundary = text.rfind(' ', start + max_chars // 2, end)
                if boundary != -1:
                    end = boundary + 1
            chunks.append(text[start:end].strip())
            start = end - overlap
        return chunks

    def _clean_entity_text(self, text: str) -> str:
        """Clean BERT tokenizer artifacts from entity text."""
        # Remove subword markers
        text = text.replace(" ##", "")
        text = text.replace("##", "")
        
        # Remove leading/trailing punctuation and whitespace
        text = text.strip(" .,;:-–—•|/\\()[]{}\"'")
        
        # Remove date fragments that leak into entities
        # e.g. "TechCorp Solutions Jan" -> "TechCorp Solutions"
        text = re.sub(r'\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s*\d{0,4}\s*$', '', text, flags=re.IGNORECASE)
        
        # Remove trailing date years
        text = re.sub(r'\s+\d{4}\s*$', '', text)
        
        # Remove trailing "at", "to", "from" that leak from context
        text = re.sub(r'\s+(?:at|to|from|in)\s*$', '', text, flags=re.IGNORECASE)

        # Collapse multiple spaces
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def _validate_entity(self, field: str, word: str, score: float) -> bool:
        """Validate that an entity is reasonable for its type."""
        
        # Skills: must be clean, not random text fragments
        if field == "skills":
            # Reject if it starts with lowercase (likely a fragment)
            if word[0].islower() and len(word) < 4:
                return False
            # Reject if it contains section headers or junk
            junk_patterns = [
                r'(?:ILLS|ills|anguages|rontend|ackend|atabases|ools)',  # broken section words
                r'(?:skills|experience|education|projects|summary)\s*:',  # section headers
                r'[\|\[\]\{\}]',  # brackets/pipes
                r'^\d+$',  # pure numbers
            ]
            for pat in junk_patterns:
                if re.search(pat, word, re.IGNORECASE):
                    return False
            # Require higher confidence for skills
            if score < 0.65:
                return False

        # Companies: must look like a company name
        if field == "companies":
            # Reject if contains framework/tech names
            tech_words = ['react', 'next.js', 'django', 'flask', 'fastapi', 'node.js',
                         'python', 'javascript', 'developer', 'engineer']
            if any(tw in word.lower() for tw in tech_words):
                return False
            # Must be at least 2 chars
            if len(word) < 3:
                return False
        
        # Designations: must look like a job title
        if field == "designation":
            if len(word) < 5:
                return False
            if score < 0.7:
                return False

        return True


# Singleton
_ner_service: Optional[NERModelService] = None


def get_ner_service() -> NERModelService:
    """Get singleton NER model service instance."""
    global _ner_service
    if _ner_service is None:
        _ner_service = NERModelService()
    return _ner_service
