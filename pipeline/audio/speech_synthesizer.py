from google.cloud import texttospeech, storage
from typing import Optional,Dict
from config import GCP_PROJECT, GCP_REGION, BUCKET_NAME
import re
class SpeechSynthesizer:
    def __init__(self):
        self.tts_client = texttospeech.TextToSpeechClient()
        self.storage_client = storage.Client()
        self.voice = texttospeech.VoiceSelectionParams(
            language_code="en-GB",
            name="en-GB-Wavenet-D",
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
        )
        self.audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        bucket = self.storage_client.bucket(BUCKET_NAME)
        if not bucket.exists():
            bucket = self.storage_client.create_bucket(BUCKET_NAME, location=GCP_REGION)
    def _transform_to_ssml(self, instruction: str, analysis: Dict) -> str:
        """Convert instruction text to enhanced SSML"""
        if not instruction:
            return ""
            
        # Basic SSML wrapper
        ssml = f"<speak>{instruction}</speak>"
        
        # Add emphasis on action verbs
        for verb in analysis.get("action_verbs", []):
            ssml = re.sub(
                rf'\b{re.escape(verb)}\b',
                f'<emphasis level="strong">{verb}</emphasis>',
                ssml,
                flags=re.IGNORECASE
            )
        
        # Add pauses for time phrases
        for phrase in analysis.get("time_phrases", []):
            ssml = ssml.replace(
                phrase,
                f'<say-as interpret-as="duration">{phrase}</say-as><break time="300ms"/>'
            )
        
        # Add warning prosody if needed
        if analysis.get("contains_warning"):
            ssml = ssml.replace("<speak>", '<speak><prosody rate="slow" pitch="high">')
            ssml = ssml.replace("</speak>", "</prosody></speak>")
        
        return ssml
    def generate_audio(self, text: str, recipe_id: str, step_index: int, analysis: Dict) -> Optional[str]:
        """Generate audio file from SSML-enhanced text"""
        try:
            # Transform to SSML first
            ssml_text = self._transform_to_ssml(text, analysis)
            synthesis_input = texttospeech.SynthesisInput(ssml=ssml_text)
            response = self.tts_client.synthesize_speech(
                input=synthesis_input,
                voice=self.voice,
                audio_config=self.audio_config
            )
            
            bucket = self.storage_client.bucket(BUCKET_NAME)
            filename = f"recipes/{recipe_id}/step_{step_index}.mp3"
            blob = bucket.blob(filename)
            blob.upload_from_string(response.audio_content, content_type="audio/mpeg")
            return f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"
        except Exception as e:
            print(f"Audio generation failed: {e}")
            return None
            """Generate audio file and return public URL"""
            try:
                synthesis_input = texttospeech.SynthesisInput(ssml=text)
                response = self.tts_client.synthesize_speech(
                    input=synthesis_input,
                    voice=self.voice,
                    audio_config=self.audio_config
                )
                
                bucket = self.storage_client.bucket(BUCKET_NAME)
                filename = f"recipes/{recipe_id}/step_{step_index}.mp3"
                blob = bucket.blob(filename)
                blob.upload_from_string(response.audio_content, content_type="audio/mpeg")
                return f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"
            except Exception:
                return None