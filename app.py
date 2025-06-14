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

# Initialize Flask app
app = Flask(__name__, static_folder='./static')
CORS(app)  # Enable CORS for all routes

# ---------- 1. Load environment variables ----------
load_dotenv()
MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME", "eco_footprint")
COLLECTION_NAME = "mealdb_recipes"
GCP_PROJECT = os.getenv("GCP_PROJECT")
GCP_REGION = os.getenv("GCP_REGION", "us-central1")

# ---------- 2. Initialize Vertex AI ----------
vertexai.init(project=GCP_PROJECT, location=GCP_REGION)
model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding@001")

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

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

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

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)