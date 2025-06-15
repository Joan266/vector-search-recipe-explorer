import os
import re
import argparse
import logging
import html
from typing import Dict, List, Optional
from dotenv import load_dotenv
from google.cloud import texttospeech, language_v1, storage
import pymongo
from pymongo.collection import Collection
from pymongo.errors import PyMongoError
import vertexai

# ---------- 1. Load environment variables ----------
load_dotenv()
MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME", "eco_footprint")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "mealdb_recipes")
GCP_PROJECT = os.getenv("GCP_PROJECT")
GCP_REGION = os.getenv("GCP_REGION", "us-central1")
BUCKET_NAME = os.getenv("BUCKET_NAME", "recipe-audio-bucket")

# ---------- 2. Initialize Vertex AI ----------
vertexai.init(project=GCP_PROJECT, location=GCP_REGION)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('recipe_processor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("RecipeAudioPipeline")

class RecipeAudioGenerator:
    def __init__(self):
        print("\n" + "="*50)
        print("🚀 Initializing RecipeAudioGenerator...")
        self.clients = self._initialize_clients()
        self.voice = texttospeech.VoiceSelectionParams(
            language_code="en-GB",
            name="en-GB-Wavenet-D",
            ssml_gender=texttospeech.SsmlVoiceGender.MALE
        )
        self.audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        print("✅ AudioGenerator initialized with British English voice")
        
    def _initialize_clients(self) -> Dict:
        """Initialize all required clients with bucket verification"""
        print("\n🛠️ Initializing clients...")
        clients = {}
        try:
            # Initialize other clients first
            clients["tts"] = texttospeech.TextToSpeechClient()
            clients["nlp"] = language_v1.LanguageServiceClient()
            clients["mongo"] = self._get_mongo_collection()
            
            # Initialize Storage client with bucket verification
            storage_client = storage.Client()
            clients["storage"] = storage_client
            
            # Verify bucket exists or create it
            bucket = storage_client.bucket(BUCKET_NAME)
            if not bucket.exists():
                print(f"🪣 Bucket '{BUCKET_NAME}' doesn't exist, creating...")
                try:
                    bucket = storage_client.create_bucket(BUCKET_NAME, location=GCP_REGION)
                    print(f"✅ Created bucket '{BUCKET_NAME}' in {GCP_REGION}")
                except Exception as e:
                    print(f"❌ Failed to create bucket: {str(e)}")
                    raise
            
            print("✅ All clients initialized successfully")
            return clients
        except Exception as e:
            print(f"❌ Client initialization failed: {str(e)}")
            raise

    def _get_mongo_collection(self) -> Collection:
        """Connect to MongoDB collection with debug prints"""
        print(f"\n🔗 Connecting to MongoDB at {MONGODB_URI.split('@')[-1]}...")
        try:
            client = pymongo.MongoClient(MONGODB_URI)
            db = client[DB_NAME]
            collection = db[COLLECTION_NAME]
            print(f"✅ Connected to collection: {DB_NAME}.{COLLECTION_NAME}")
            print(f"📊 Total recipes: {collection.count_documents({})}")
            return collection
        except PyMongoError as e:
            print(f"❌ MongoDB connection failed: {str(e)}")
            raise

    def normalize_instructions(self, text: str) -> str:
        """Normalize recipe instructions text with debug prints"""
        print("\n📝 Normalizing instructions...")
        if not text:
            print("⚠️ No instructions found")
            return ""
            
        original_length = len(text)
        print(f"  Original length: {original_length} chars")
        
        # Replace problematic characters and normalize whitespace
        text = re.sub(r'[\r\n]+', '. ', text)
        text = re.sub(r'\.{2,}', '.', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Capitalize first letter of each sentence
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s[0].upper() + s[1:] if s else s for s in sentences]
        normalized = ' '.join(sentences)
        
        print(f"  Normalized length: {len(normalized)} chars")
        print("  Sample normalized text:")
        print(f"  {normalized[:100]}{'...' if len(normalized)>100 else ''}")
        
        return normalized

    def split_instructions(self, normalized_text: str) -> List[str]:
        """Split instructions into individual steps with debug prints"""
        print("\n✂️ Splitting instructions into steps...")
        if not normalized_text:
            print("⚠️ No text to split")
            return []
            
        # Split on numbers (like "1.", "2.") or sentence boundaries
        steps = re.split(r'(?<=\d)\.\s+|(?<=[.!?])\s+(?=[A-Z])', normalized_text)
        steps = [step.strip() for step in steps if step.strip()]
        
        print(f"  Found {len(steps)} steps")
        for i, step in enumerate(steps[:3]):  # Print first 3 steps as sample
            print(f"    Step {i+1}: {step[:70]}{'...' if len(step)>70 else ''}")
        if len(steps) > 3:
            print(f"    (...and {len(steps)-3} more steps)")
            
        return steps

    def analyze_instruction(self, text: str) -> Dict:
        """Analyze instruction text for verbs and time phrases with debug prints"""
        print(f"\n🔍 Analyzing text: '{text[:50]}{'...' if len(text)>50 else ''}'")
        if not text:
            print("⚠️ No text to analyze")
            return {"action_verbs": [], "time_phrases": []}
            
        try:
            document = language_v1.Document(
                content=text,
                type_=language_v1.Document.Type.PLAIN_TEXT
            )
            
            print("  Calling Natural Language API...")
            response = self.clients["nlp"].analyze_syntax(
                request={"document": document}
            )
            
            # Extract verbs
            verbs = [
                token.text.content.lower()
                for token in response.tokens
                if token.part_of_speech.tag == language_v1.PartOfSpeech.Tag.VERB
            ]
            unique_verbs = list(set(verbs))  # Remove duplicates
            
            # Find time-related phrases
            time_phrases = re.findall(
                r'\b\d+\s*(?:minutes?|hours?|seconds?|days?|weeks?)\b|\b\d+[°º]?[CF]\b',
                text,
                flags=re.IGNORECASE
            )
            
            # Check for warnings
            warning_words = ["careful", "warning", "hot", "sharp", "danger"]
            contains_warning = any(word in text.lower() for word in warning_words)
            
            print("  Analysis results:")
            print(f"    Action verbs: {unique_verbs[:5]}{'...' if len(unique_verbs)>5 else ''}")
            print(f"    Time phrases: {time_phrases}")
            print(f"    Contains warning: {contains_warning}")
            
            return {
                "action_verbs": unique_verbs,
                "time_phrases": time_phrases,
                "contains_warning": contains_warning
            }
        except Exception as e:
            print(f"❌ Text analysis failed: {str(e)}")
            return {"action_verbs": [], "time_phrases": []}

    def transform_to_ssml(self, instruction: str, analysis: Dict) -> str:
        """Convert instruction text to SSML with enhancements and debug prints"""
        print("\n🎚️ Converting to SSML...")
        if not instruction:
            print("⚠️ No instruction to convert")
            return ""
            
        print("  Original instruction:")
        print(f"  {instruction[:100]}{'...' if len(instruction)>100 else ''}")
        
        # Start with basic SSML
        ssml = f"<speak>{instruction}</speak>"
        
        # Add emphasis on action verbs
        for verb in analysis.get("action_verbs", []):
            ssml = re.sub(
                rf'\b{re.escape(verb)}\b',
                f'<emphasis level="strong">{verb}</emphasis>',
                ssml,
                flags=re.IGNORECASE
            )
        
        # Add proper pauses for time phrases
        for phrase in analysis.get("time_phrases", []):
            ssml = ssml.replace(
                phrase,
                f'<say-as interpret-as="duration">{phrase}</say-as><break time="300ms"/>'
            )
        
        # Add warning prosody if needed
        if analysis.get("contains_warning"):
            ssml = ssml.replace("<speak>", '<speak><prosody rate="slow" pitch="high">')
            ssml = ssml.replace("</speak>", "</prosody></speak>")
        
        print("  Generated SSML:")
        print(f"  {ssml[:150]}{'...' if len(ssml)>150 else ''}")
        
        return ssml

    def generate_audio(self, ssml_text: str, recipe_id: str, step_index: int) -> Optional[str]:
        """Generate audio file from SSML and upload to GCS with debug prints"""
        print(f"\n🔊 Generating audio for step {step_index}...")
        if not ssml_text:
            print("⚠️ No SSML text to synthesize")
            return None
            
        try:
            print("  Synthesizing speech...")
            synthesis_input = texttospeech.SynthesisInput(ssml=ssml_text)
            response = self.clients["tts"].synthesize_speech(
                input=synthesis_input,
                voice=self.voice,
                audio_config=self.audio_config
            )
            
            print("  Uploading to Cloud Storage...")
            bucket = self.clients["storage"].bucket(BUCKET_NAME)
            filename = f"recipes/{recipe_id}/step_{step_index}.mp3"
            blob = bucket.blob(filename)
            
            blob.upload_from_string(response.audio_content, content_type="audio/mpeg")
            # Genera URL pública (funcionará si el bucket tiene allUsers:objectViewer)
            return f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"
        
        except Exception as e:
            logger.error(f"Audio generation failed: {str(e)}")
            return None

    def process_recipe(self, recipe: Dict) -> bool:
        """Process a single recipe document with comprehensive debug prints"""
        print("\n" + "="*50)
        print(f"🍳 Processing recipe: {recipe.get('name', 'Unnamed')}")
        
        recipe_id = str(recipe.get("_id", ""))
        if not recipe_id:
            print("❌ Recipe missing ID, skipping")
            return False
            
        print(f"📌 Recipe ID: {recipe_id}")
        
        # Skip if already processed
        if recipe.get("audio_steps"):
            print("⏩ Already has audio steps, skipping")
            return False
            
        if "instructions" not in recipe:
            print("❌ No instructions found, skipping")
            return False
            
        try:
            instructions = recipe["instructions"]
            print(f"\n📜 Original instructions ({len(instructions)} chars):")
            print(f"{instructions[:200]}{'...' if len(instructions)>200 else ''}")
            
            normalized = self.normalize_instructions(instructions)
            steps = self.split_instructions(normalized)
            
            audio_steps = []
            for i, step in enumerate(steps):
                print(f"\n🔧 Processing step {i+1}/{len(steps)}")
                analysis = self.analyze_instruction(step)
                ssml = self.transform_to_ssml(step, analysis)
                audio_url = self.generate_audio(ssml, recipe_id, i)
                
                if audio_url:
                    audio_steps.append({
                        "step_number": i,
                        "text": step,
                        "ssml": ssml,
                        "audio_url": audio_url,
                        "analysis": analysis
                    })
            
            if audio_steps:
                print(f"\n💾 Updating MongoDB document...")
                result = self.clients["mongo"].update_one(
                    {"_id": recipe["_id"]},
                    {"$set": {"audio_steps": audio_steps}}
                )
                print(f"✅ Updated recipe with {len(audio_steps)} audio steps")
                return result.modified_count > 0
                
            print("❌ No audio steps were generated")
            return False
        except Exception as e:
            print(f"🔥 Processing failed: {str(e)}")
            return False

    def run(self, test_mode: bool = False, limit: int = None):
        """Run the processing pipeline with debug prints"""
        print("\n" + "="*50)
        print(f"🚀 Starting pipeline (test_mode={test_mode}, limit={limit})")
        
        try:
            query = {"instructions": {"$exists": True}, "audio_steps": {"$exists": False}}
            print(f"🔍 MongoDB query: {query}")
            
            if test_mode:
                print("\n🧪 TEST MODE: Processing one random recipe")
                recipe = self.clients["mongo"].aggregate([
                    {"$match": query},
                    {"$sample": {"size": 1}}
                ]).next()
                self.process_recipe(recipe)
            else:
                print("\n🔎 Finding recipes to process...")
                cursor = self.clients["mongo"].find(query)
                if limit:
                    cursor.limit(limit)
                    print(f"  Limiting to {limit} recipes")
                    
                processed_count = 0
                total_to_process = self.clients["mongo"].count_documents(query)
                if limit and limit < total_to_process:
                    total_to_process = limit
                
                print(f"📊 Found {total_to_process} recipes to process")
                
                for i, recipe in enumerate(cursor, 1):
                    print(f"\n📦 Processing recipe {i}/{total_to_process}")
                    if self.process_recipe(recipe):
                        processed_count += 1
                
                print("\n" + "="*50)
                print(f"🎉 Pipeline complete! Processed {processed_count}/{total_to_process} recipes")
        except Exception as e:
            print("\n" + "="*50)
            print(f"❌ Pipeline failed: {str(e)}")
            raise

def main():
    parser = argparse.ArgumentParser(description="Recipe Audio Pipeline")
    parser.add_argument("--test", action="store_true", help="Test mode (processes one recipe)")
    parser.add_argument("--limit", type=int, help="Limit number of recipes to process")
    args = parser.parse_args()
    
    try:
        print("\n" + "="*50)
        print("🔧 Recipe Audio Pipeline - Starting Up")
        print("="*50)
        
        # Verify environment variables
        required_vars = ["MONGODB_URI", "GCP_PROJECT"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
            return
        
        processor = RecipeAudioGenerator()
        processor.run(test_mode=args.test, limit=args.limit)
    except Exception as e:
        print("\n" + "="*50)
        print(f"💥 Critical error: {str(e)}")
        logger.critical(f"Pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()