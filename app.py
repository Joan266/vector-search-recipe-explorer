import os
from dotenv import load_dotenv
from pymongo import MongoClient
import vertexai
from vertexai.vision_models import Image, MultiModalEmbeddingModel
from PIL import Image as PILImage
import requests
from io import BytesIO
import tempfile
from flask import Flask, request, jsonify, render_template, send_from_directory
import base64
from flask_cors import CORS
import traceback
import numpy as np
from typing import List, Dict, Optional
from bson import ObjectId
from google.cloud import texttospeech, language_v1, storage
import re
from bson.errors import InvalidId
app = Flask(__name__, static_folder='static', template_folder='templates')

CORS(app)  # Enable CORS for all routes

# ---------- 1. Load environment variables ----------
load_dotenv()
MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME", "eco_footprint")
COLLECTION_NAME = "mealdb_recipes"
GCP_PROJECT = os.getenv("GCP_PROJECT")
GCP_REGION = os.getenv("GCP_REGION", "us-central1")
BUCKET_NAME = os.getenv("BUCKET_NAME", "recipe-audio-bucket")
VOICE_CONFIG = texttospeech.VoiceSelectionParams(
    language_code="en-US",
    name="en-US-Standard-C",
    ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
)
AUDIO_CONFIG = texttospeech.AudioConfig(
    audio_encoding=texttospeech.AudioEncoding.MP3
)
# ---------- 2. Initialize Vertex AI ----------
vertexai.init(project=GCP_PROJECT, location=GCP_REGION)
model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding@001")
# Initialize clients (add this near your other initializations)
def initialize_clients():
    return {
        "nlp": language_v1.LanguageServiceClient(),
        "tts": texttospeech.TextToSpeechClient(),
        "storage": storage.Client()
    }
def download_image(url):
    """Download image from URL and return PIL Image object"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return PILImage.open(BytesIO(response.content))
    except Exception as e:
        print(f"Error downloading image: {e}")
        return None

def get_embeddings(image=None, text=None):
    """Get embeddings from Vertex AI's multimodal model"""
    vertex_image = None
    
    if image:
        # URL Handling
        if isinstance(image, str) and image.startswith(('http://', 'https://')):
            pil_image = download_image(image)
            if pil_image:
                with tempfile.NamedTemporaryFile(suffix=".jpg") as temp_img:
                    pil_image.save(temp_img.name, format="JPEG")
                    vertex_image = Image.load_from_file(temp_img.name)
        
        # Base64 Handling
        elif isinstance(image, str) and image.startswith('data:image'):
            try:
                header, encoded = image.split(",", 1)
                binary_data = base64.b64decode(encoded)
                
                with tempfile.NamedTemporaryFile(suffix=".jpg") as temp_img:
                    temp_img.write(binary_data)
                    temp_img.flush()  # Ensure all data is written
                    vertex_image = Image.load_from_file(temp_img.name)
            except Exception as e:
                print(f"Base64 image processing error: {str(e)}")
                return None
    
    try:
        embeddings = model.get_embeddings(
            image=vertex_image,
            contextual_text=text,
            dimension=512  # Must match your MongoDB index dimension
        )
        return {
            "image_embedding": embeddings.image_embedding if (image and embeddings.image_embedding) else None,
            "text_embedding": embeddings.text_embedding if text else None
        }
    except Exception as e:
        print(f"Vertex AI embedding error: {str(e)}")
        return None

def is_valid_result(result, image_weight, text_weight):
    """Determine if a search result meets quality thresholds"""
    MIN_COMBINED_SCORE = 0.25
    MIN_COMPONENT_SCORE = 0.15
    
    if result.get('combined_score', 0) < MIN_COMBINED_SCORE:
        return False
    
    if image_weight > 0 and 'img_score' in result and result['img_score'] < MIN_COMPONENT_SCORE:
        return False
        
    if text_weight > 0 and 'text_score' in result and result['text_score'] < MIN_COMPONENT_SCORE:
        return False
        
    return True

def hybrid_search(image=None, text=None, k=5, image_weight=0.5, text_weight=0.5):
    """Perform proper hybrid search combining image and text results"""
    # Validate weights
    total_weight = image_weight + text_weight
    if total_weight <= 0:
        raise ValueError("Weights must sum to a positive value")
    
    # Normalize weights
    image_weight /= total_weight
    text_weight /= total_weight
    
    # Get embeddings
    embeddings = get_embeddings(image, text)
    if not embeddings or (not embeddings["image_embedding"] and not embeddings["text_embedding"]):
        raise ValueError("Failed to get valid embeddings")
    
    # Connect to MongoDB
    client = MongoClient(MONGODB_URI)
    collection = client[DB_NAME][COLLECTION_NAME]
    results = []
    
    # Perform image vector search if image embedding exists
    if embeddings["image_embedding"]:
        try:
            img_results = collection.aggregate([
                {
                    "$vectorSearch": {
                        "index": "recipe_img_vector_index",
                        "path": "image_embedding",
                        "queryVector": embeddings["image_embedding"],
                        "numCandidates": 100,
                        "limit": k * 3  # Get extra candidates for filtering
                    }
                },
                {
                    "$project": {
                        "_id": 1,
                        "name": 1,
                        "category": 1,
                        "area": 1,
                        "tags": 1,
                        "img_url": 1,
                        "ingredients": 1,
                        "instructions": 1,
                        "img_score": {"$meta": "vectorSearchScore"}
                    }
                }
            ])
            results.extend(list(img_results))
        except Exception as e:
            print(f"Image vector search failed: {str(e)}")
    
    # Perform text vector search if text embedding exists
    if embeddings["text_embedding"]:
        try:
            text_results = collection.aggregate([
                {
                    "$vectorSearch": {
                        "index": "recipe_text_vector_index",
                        "path": "text_embedding",
                        "queryVector": embeddings["text_embedding"],
                        "numCandidates": 100,
                        "limit": k * 3  # Get extra candidates for filtering
                    }
                },
                {
                    "$project": {
                        "_id": 1,
                        "name": 1,
                        "category": 1,
                        "area": 1,
                        "tags": 1,
                        "img_url": 1,
                        "ingredients": 1,
                        "instructions": 1,
                        "text_score": {"$meta": "vectorSearchScore"}
                    }
                }
            ])
            results.extend(list(text_results))
        except Exception as e:
            print(f"Text vector search failed: {str(e)}")
    
    # Combine and deduplicate results
    ranked_results = []
    seen_ids = set()
    
    for doc in results:
        doc_id = str(doc["_id"])
        if doc_id in seen_ids:
            # Merge scores for documents found in both searches
            existing = next(d for d in ranked_results if str(d["_id"]) == doc_id)
            if "img_score" in doc:
                existing["img_score"] = doc["img_score"]
            if "text_score" in doc:
                existing["text_score"] = doc["text_score"]
        else:
            seen_ids.add(doc_id)
            ranked_results.append(doc)
    
    # Calculate combined weighted score
    for doc in ranked_results:
        img_score = doc.get("img_score", 0)
        text_score = doc.get("text_score", 0)
        doc["combined_score"] = (image_weight * img_score) + (text_weight * text_score)
    
    # Sort by combined score
    ranked_results.sort(key=lambda x: x["combined_score"], reverse=True)
    
    # Apply score validation and return top k valid results
    valid_results = [r for r in ranked_results if is_valid_result(r, image_weight, text_weight)]
    return valid_results[:k]


def generate_audio_steps(recipe):
    """Generate audio instructions for a recipe if missing"""
    if 'audio_steps' in recipe and recipe['audio_steps']:
        return recipe['audio_steps']
    
    print(f"Generating audio for recipe: {recipe['name']}")
    # Audio generation logic from your script
    normalized = normalize_instructions(recipe['instructions'])
    steps = split_instructions(normalized)
    
    audio_steps = []
    for i, step in enumerate(steps):
        analysis = analyze_instruction(step)
        ssml = transform_to_ssml(step, analysis)
        audio_url = generate_audio(ssml, str(recipe['_id']), i)
        
        if audio_url:
            audio_steps.append({
                "step_number": i,
                "text": step,
                "audio_url": audio_url
            })
    
    # Update MongoDB
    client = MongoClient(MONGODB_URI)
    collection = client[DB_NAME][COLLECTION_NAME]
    collection.update_one(
        {"_id": recipe['_id']},
        {"$set": {"audio_steps": audio_steps}}
    )
    
    return audio_steps

def normalize_instructions(text: str) -> str:
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


def split_instructions(normalized_text: str) -> List[str]:
    """Split instructions into individual steps with debug prints"""
    print("\n✂️ Splitting instructions into steps...")
    if not normalized_text:
        print("⚠️ No text to split")
        return []
    
    # Improved splitting pattern that:
    # 1. Handles numbered steps (1., 2.) 
    # 2. Splits on sentence boundaries
    # 3. Removes trailing step numbers
    steps = re.split(r'(?<=\d)\.\s+|(?<=[.!?])\s+(?=[A-Z\d])', normalized_text)
    
    # Clean each step
    cleaned_steps = []
    for step in steps:
        if not step.strip():
            continue
            
        # Remove any leading numbers/dots/whitespace
        step = re.sub(r'^\d+\.?\s*', '', step.strip())
        
        # Remove any trailing partial words from bad splits
        step = re.sub(r'\s+\S+$', '', step) if len(step.split()) > 3 else step
        
        if step:
            cleaned_steps.append(step)
    
    print(f"  Found {len(cleaned_steps)} steps")
    for i, step in enumerate(cleaned_steps[:3]):  # Print first 3 steps as sample
        print(f"    Step {i+1}: {step[:70]}{'...' if len(step)>70 else ''}")
    if len(cleaned_steps) > 3:
        print(f"    (...and {len(cleaned_steps)-3} more steps)")
        
    return cleaned_steps

def analyze_instruction(text: str) -> Dict:
    """Analyze instruction text for verbs and time phrases with debug prints"""
    print(f"\n🔍 Analyzing text: '{text[:50]}{'...' if len(text)>50 else ''}'")
    if not text:
        print("⚠️ No text to analyze")
        return {"action_verbs": [], "time_phrases": []}
        
    try:
        clients = initialize_clients()
        document = language_v1.Document(
            content=text,
            type_=language_v1.Document.Type.PLAIN_TEXT
        )
        response = clients["nlp"].analyze_syntax(request={"document": document})
            
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

def transform_to_ssml(instruction: str, analysis: Dict) -> str:
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

def generate_audio(ssml_text: str, recipe_id: str, step_index: int) -> Optional[str]:
    clients = initialize_clients()
    try:
        synthesis_input = texttospeech.SynthesisInput(ssml=ssml_text)
        response = clients["tts"].synthesize_speech(
            input=synthesis_input,
            voice=VOICE_CONFIG,
            audio_config=AUDIO_CONFIG
        )
        
        bucket = clients["storage"].bucket(BUCKET_NAME)
        filename = f"recipes/{recipe_id}/step_{step_index}.mp3"
        blob = bucket.blob(filename)
        blob.upload_from_string(response.audio_content, content_type="audio/mpeg")
        return f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"
    except Exception as e:
        print(f"Audio generation failed: {str(e)}")
        return None

@app.route("/recipe/<recipe_id>")
def recipe_detail(recipe_id):
    try:
        object_id = ObjectId(recipe_id)
    except InvalidId:
        return "Invalid recipe ID format", 400

    try:
        client = MongoClient(MONGODB_URI)
        collection = client[DB_NAME][COLLECTION_NAME]
        recipe = collection.find_one({"_id": object_id})
        
        if not recipe:
            return "Recipe not found", 404
        
        # Generate audio steps BEFORE removing _id
        recipe['audio_steps'] = generate_audio_steps(recipe)
        
        # Now convert for the template
        recipe['id'] = str(recipe['_id'])
        del recipe['_id']
        
        return render_template('recipe_detail.html', recipe=recipe)
        
    except Exception as e:
        traceback.print_exc()
        return f"Error: {str(e)}", 500

@app.route('/')
def serve_index():
    return render_template('index.html')

@app.route("/api/recipes/search", methods=["POST"])
def search_recipes():
    data = request.json
    ingredients = data.get("ingredients")
    image = data.get("image")  
    
    try:
        results = hybrid_search(
            image=image,
            text=ingredients,
            k=5,
            image_weight=0.5,
            text_weight=0.5
        )
        
        # Ensure we always return an array, even if empty
        formatted_results = []
        for recipe in results:
            recipe_data = {
                "id": str(recipe.get("_id", "")),
                "name": recipe.get("name", "Unknown Recipe"),
                "image": recipe.get("img_url", ""),
                "ingredients": recipe.get("ingredients", []),
                "instructions": recipe.get("instructions", "No instructions available"),
                "category": recipe.get("category", ""),
                "area": recipe.get("area", ""),
                "tags": recipe.get("tags", []),
                "prepTime": recipe.get("prepTime", "N/A"),
                "cookTime": recipe.get("cookTime", "N/A"),
                "nutritionScore": recipe.get("nutritionScore", 0),
                "healthClass": recipe.get("healthClass", "unknown"),
                "score": recipe.get("combined_score", 0)
            }
            formatted_results.append(recipe_data)
            
        # Return results array directly (not nested in another object)
        return jsonify(formatted_results)
        
    except Exception as e:
        print(f"[ERROR] Search failed: {str(e)}")
        traceback.print_exc()
        # Return empty array on error
        return jsonify([])
@app.route("/recipe/<recipe_id>/audio")
def recipe_audio(recipe_id):
    try:
        object_id = ObjectId(recipe_id)
    except InvalidId:
        return "Invalid recipe ID format", 400

    try:
        client = MongoClient(MONGODB_URI)
        collection = client[DB_NAME][COLLECTION_NAME]
        recipe = collection.find_one({"_id": object_id})
        
        if not recipe:
            return "Recipe not found", 404
        
        # Generate audio steps if needed
        recipe['audio_steps'] = generate_audio_steps(recipe)
        
        # Convert for the template
        recipe['id'] = str(recipe['_id'])
        del recipe['_id']
        
        return render_template('audio_instructions.html', recipe=recipe)
        
    except Exception as e:
        traceback.print_exc()
        return f"Error: {str(e)}", 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)