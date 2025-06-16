from flask import Flask, render_template, request, jsonify
from pymongo import MongoClient
from config import MONGODB_URI, DB_NAME, COLLECTION_NAME
import os
from bson import ObjectId
import vertexai
from vertexai.vision_models import Image, MultiModalEmbeddingModel
from PIL import Image as PILImage
import requests
from io import BytesIO
import tempfile
import base64
from flask_cors import CORS



app = Flask(__name__)
CORS(app) 
# Initialize Vertex AI
vertexai.init(project="your-gcp-project", location="us-central1")
model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding@001")

# MongoDB connection
client = MongoClient(MONGODB_URI)
db = client[DB_NAME]
recipes_collection = db[COLLECTION_NAME]

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
        # Base64 Handling
        if isinstance(image, str) and image.startswith('data:image'):
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
                        "img_url": 1,
                        "health_score": 1,
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
                        "img_url": 1,
                        "health_score": 1,
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
def index():
    """Homepage with recipe carousel"""
    featured_recipes = list(recipes_collection.aggregate([
        {'$sample': {'size': 10}},
        {'$project': {
            '_id': 1,
            'name': 1,
            'category': 1,
            'area': 1,
            'img_url': 1,
            'health_score': 1
        }}
    ]))
    return render_template('index.html', recipes=featured_recipes)

@app.route('/search', methods=['POST'])
def search():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid request format"}), 400
            
        query = data.get('query')
        image = data.get('image')
        
        if not query and not image:
            return jsonify({"error": "Please provide either text or image"}), 400
            
        results = hybrid_search(
            image=image,
            text=query,
            k=10,
            image_weight=0.5 if image else 0,
            text_weight=0.5 if query else 0
        )
        
        # Convert ObjectId to string for JSON serialization
        for recipe in results:
            recipe['_id'] = str(recipe['_id'])
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/recipe/<recipe_id>')
def recipe_detail(recipe_id):
    try:
        recipe = recipes_collection.find_one({'_id': ObjectId(recipe_id)})
        if not recipe:
            return "Recipe not found", 404
        
        # Ensure all expected fields exist
        recipe.setdefault('audio_steps', [])
        recipe.setdefault('time_analysis', {'total_estimated_time_minutes': 0, 'recipe_difficulty': 'Unknown'})
        
        # Convert ObjectId to string for template
        recipe['_id'] = str(recipe['_id'])
        
        return render_template('recipe.html', recipe=recipe)
    except Exception as e:
        return f"Error: {str(e)}", 400

if __name__ == '__main__':
    app.run(debug=True)