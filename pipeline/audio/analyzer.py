from typing import Dict
from google.cloud import language_v1
import re
class InstructionAnalyzer:
    def __init__(self):
        self.client = language_v1.LanguageServiceClient()

    def analyze(self, text: str) -> Dict:
        """Analyze instruction text for verbs and time phrases"""
        if not text:
            return {"action_verbs": [], "time_phrases": []}
            
        try:
            document = language_v1.Document(
                content=text,
                type_=language_v1.Document.Type.PLAIN_TEXT
            )
            response = self.client.analyze_syntax(request={"document": document})
            
            verbs = [
                token.text.content.lower()
                for token in response.tokens
                if token.part_of_speech.tag == language_v1.PartOfSpeech.Tag.VERB
            ]
            
            time_phrases = re.findall(
                r'\b\d+\s*(?:minutes?|hours?|seconds?|days?|weeks?)\b|\b\d+[°º]?[CF]\b',
                text,
                flags=re.IGNORECASE
            )
            
            return {
                "action_verbs": list(set(verbs)),
                "time_phrases": time_phrases,
                "contains_warning": any(w in text.lower() 
                                      for w in ["careful", "warning", "hot", "sharp", "danger"])
            }
        except Exception:
            return {"action_verbs": [], "time_phrases": []}