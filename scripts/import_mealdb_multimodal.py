import requests
import time
import re
from vertexai.vision_models import Image as VertexImage, MultiModalEmbeddingModel
from PIL import Image
from io import BytesIO
import tempfile
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from typing import List, Dict, Optional
from pathlib import Path

# ---------- LOAD ENV ----------
dotenv_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=dotenv_path)

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "mealdb_recipes")
GCP_PROJECT = os.getenv("GCP_PROJECT")
GCP_REGION = os.getenv("GCP_REGION", "us-central1")
GCP_KEY_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

if GCP_KEY_PATH:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GCP_KEY_PATH

# ---------- Cooking Technique Constants ----------
COOKING_TECHNIQUES = [
    "grill", "bake", "fry", "simmer", "whisk", "roast", "steam", 
    "blend", "poach", "sear", "braise", "saute", "marinate", 
    "deep fry", "pan fry", "stir fry", "smoke", "broil", "grill"
]
PREP_KEYWORDS = [
    "chop", "dice", "mince", "slice", "grate", "peel", "mix",
    "knead", "whisk", "beat", "fold", "stir", "combine"
]

# ---------- Text Processing Helpers ----------
def extract_techniques(text: str) -> List[str]:
    """Extract cooking techniques from text"""
    if not text:
        return []
    
    text = text.lower()
    found_tech = set()
    
    # Check for exact matches
    for tech in COOKING_TECHNIQUES:
        if tech in text:
            found_tech.add(tech)
    
    # Check for verb forms (e.g., "grilled" -> "grill")
    for tech in COOKING_TECHNIQUES:
        if re.search(rf"\b{tech}(ed|ing|s)?\b", text):
            found_tech.add(tech)
    
    return list(found_tech)

def clean_instructions(instructions: str) -> str:
    """Remove noisy words from instructions"""
    if not instructions:
        return ""
    
    # Remove common procedural phrases
    stop_phrases = [
        "salt to taste", "pepper to taste", "serve hot", 
        "serve immediately", "as needed"
    ]
    
    cleaned = instructions
    for phrase in stop_phrases:
        cleaned = cleaned.replace(phrase, "")
    
    return cleaned[:500]  # Truncate to 500 chars

# ---------- MealDB API Functions ----------
def fetch_categories() -> List[str]:
    """Fetch all meal categories"""
    print("Fetching categories...")
    url = "https://www.themealdb.com/api/json/v1/1/categories.php"
    response = requests.get(url)
    data = response.json()
    return [cat["strCategory"] for cat in data["categories"]]

def fetch_meals_by_category(category: str) -> List[str]:
    """Fetch meal IDs for a category"""
    url = f"https://www.themealdb.com/api/json/v1/1/filter.php?c={category}"
    response = requests.get(url)
    data = response.json()
    meals = data.get("meals", [])
    return [meal["idMeal"] for meal in meals]

def fetch_meal_details(meal_id: str) -> Optional[Dict]:
    """Fetch full meal details"""
    url = f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={meal_id}"
    response = requests.get(url)
    data = response.json()
    meal = data.get("meals", [None])[0]
    if not meal:
        return None

    # Process ingredients
    ingredients = []
    for i in range(1, 21):
        ing = meal.get(f"strIngredient{i}", "").strip()
        meas = meal.get(f"strMeasure{i}", "").strip()
        if ing:
            ingredients.append(f"{meas} {ing}" if meas else ing)

    # Extract techniques from instructions
    techniques = extract_techniques(meal.get("strInstructions", ""))
    
    return {
        "meal_id": meal_id,
        "name": meal.get("strMeal"),
        "category": meal.get("strCategory"),
        "area": meal.get("strArea"),
        "instructions": clean_instructions(meal.get("strInstructions")),
        "ingredients": ingredients,
        "ingredients_text": ", ".join(ingredients),
        "techniques": techniques,
        "img_url": meal.get("strMealThumb"),
        "youtube_url": meal.get("strYoutube"),
        "tags": meal.get("strTags", "").split(",") if meal.get("strTags") else [],
        "source": "TheMealDB"
    }

# ---------- Image Processing ----------
def download_image(url: str) -> Optional[Image.Image]:
    """Download and validate image"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return Image.open(BytesIO(response.content)).convert("RGB")
    except Exception as e:
        print(f"Image download failed: {url} - {str(e)}")
        return None

# ---------- Embedding Generation ----------
def generate_embeddings(doc: Dict, mm_model) -> Dict:
    """Generate multimodal embeddings with enhanced context"""
    if not doc.get("img_url"):
        return doc
    
    pil_image = download_image(doc["img_url"])
    if not pil_image:
        return doc

    with tempfile.NamedTemporaryFile(suffix=".jpg") as temp_img:
        pil_image.save(temp_img.name)
        
        # Enhanced contextual text
        contextual_text = (
            f"{doc['name']}, a {doc['category']} dish from {doc.get('area', 'unknown')}. "
            f"Main ingredients: {', '.join(doc['ingredients'][:5])}. "
            f"Cooking techniques: {', '.join(doc.get('techniques', []))}. "
            f"Key steps: {doc['instructions'][:300]}"
        )
        
        try:
            vertex_img = VertexImage.load_from_file(temp_img.name)
            embeddings = mm_model.get_embeddings(
                image=vertex_img,
                contextual_text=contextual_text,
                dimension=1408
            )
            
            # Store all embedding types
            doc.update({
                "image_embedding": embeddings.image_embedding,
                "text_embedding": embeddings.text_embedding,
                "multimodal_embedding": embeddings.multimodal_embedding,
                "embedding_version": "v2.1"  # Track embedding schema
            })
        except Exception as e:
            print(f"Embedding generation failed for {doc['name']}: {str(e)}")
    
    return doc

# ---------- Main Pipeline ----------
def main(limit: int = 304):
    """Full data pipeline"""
    from vertexai import init
    init(project=GCP_PROJECT, location=GCP_REGION)
    
    # Initialize models
    print("🚀 Initializing multimodal embedding model...")
    mm_model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding@001")
    
    # Fetch data
    print("🍳 Fetching recipes from TheMealDB...")
    recipes = []
    seen_ids = set()
    
    for category in fetch_categories():
        print(f"Processing {category}...")
        for meal_id in fetch_meals_by_category(category):
            if meal_id in seen_ids:
                continue
                
            if details := fetch_meal_details(meal_id):
                recipes.append(details)
                seen_ids.add(meal_id)
                print(f"✓ {details['name']}")
                
                if len(recipes) >= limit:
                    break
            time.sleep(0.2)
        
        if len(recipes) >= limit:
            break
    
    # Generate embeddings
    print("\n🎨 Generating embeddings...")
    for i, recipe in enumerate(recipes):
        recipes[i] = generate_embeddings(recipe, mm_model)
        print(f"Embedded {i+1}/{len(recipes)}: {recipe['name']}")
    
    # MongoDB upload
    print("\n📦 Uploading to MongoDB...")
    client = MongoClient(MONGODB_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    
    # Clear existing data
    collection.drop()
    
    # Insert with error handling
    try:
        result = collection.insert_many(recipes)
        print(f"✅ Inserted {len(result.inserted_ids)} documents")
    except Exception as e:
        print(f"❌ Insert failed: {str(e)}")
        return
    
    # Create optimized indexes
    print("🔨 Creating indexes...")
    collection.create_index("meal_id", unique=True)
    collection.create_index([("name", "text")])
    collection.create_index("category")
    collection.create_index("area")
    collection.create_index("techniques")
    collection.create_index([("ingredients_text", "text")])
    
    # Vector search index (for Atlas)
    if "atlas" in MONGODB_URI.lower():
        collection.create_index([("multimodal_embedding", "vector")])
    
    print("✨ All done! Collection ready for vector searches.")

if __name__ == "__main__":
    main()