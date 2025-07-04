import os
import logging
from flask import Flask, render_template, request, jsonify, send_from_directory
from pymongo import MongoClient, errors
from config import MONGODB_URI, DB_NAME, COLLECTION_NAME, GCP_PROJECT, GCP_REGION, FLASK_ENV, FLASK_SECRET_KEY
from bson import ObjectId
import vertexai
from vertexai.vision_models import Image, MultiModalEmbeddingModel
from PIL import Image as PILImage
import requests
from io import BytesIO
import tempfile
import base64
from flask_cors import CORS

# Configure logging based on environment
if FLASK_ENV == "development":
    logging.basicConfig(level=logging.DEBUG)
else:
    from google.cloud import logging as cloud_logging
    logging_client = cloud_logging.Client()
    logging_client.setup_logging()

app = Flask(__name__)
CORS(app)

# Configuration
app.config.update(
    SECRET_KEY=FLASK_SECRET_KEY,
    JSONIFY_PRETTYPRINT_REGULAR=FLASK_ENV == "development",  # Pretty print in dev
    MAX_CONTENT_LENGTH=16 * 1024 * 1024  # 16MB upload limit
)

# Initialize Vertex AI
try:
    vertexai.init(project=GCP_PROJECT, location=GCP_REGION)
    model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding@001")
    print("✅ Vertex AI initialized successfully")
except Exception as e:
    logging.error(f"❌ Vertex AI initialization failed: {str(e)}")
    model = None

# MongoDB Connection with error handling
try:
    client = MongoClient(
        MONGODB_URI,
        maxPoolSize=50 if FLASK_ENV != "development" else 10,
        connectTimeoutMS=30000,
        socketTimeoutMS=30000,
        serverSelectionTimeoutMS=30000
    )
    client.admin.command('ping')  # Test connection
    db = client[DB_NAME]
    recipes_collection = db[COLLECTION_NAME]
    print(f"✅ MongoDB connected successfully to {DB_NAME}.{COLLECTION_NAME}")
except errors.ConnectionFailure as e:
    logging.critical(f"❌ MongoDB connection failed: {str(e)}")
    print("Please check your MONGODB_URI in the .env file")
    raise

def download_image(url):
    """Download image from URL with timeout and error handling"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return PILImage.open(BytesIO(response.content))
    except Exception as e:
        logging.error(f"Image download failed: {str(e)}")
        return None

def get_embeddings(image=None, text=None):
    """Generate embeddings with Vertex AI"""
    if not model:
        logging.error("Vertex AI model not available")
        return None
        
    vertex_image = None
    
    if image and isinstance(image, str) and image.startswith('data:image'):
        try:
            header, encoded = image.split(",", 1)
            binary_data = base64.b64decode(encoded)
            
            with tempfile.NamedTemporaryFile(suffix=".jpg") as temp_img:
                temp_img.write(binary_data)
                temp_img.flush()
                vertex_image = Image.load_from_file(temp_img.name)
        except Exception as e:
            logging.error(f"Image processing error: {str(e)}")
            return None
    
    try:
        embeddings = model.get_embeddings(
            image=vertex_image,
            contextual_text=text,
            dimension=512
        )
        return {
            "image_embedding": embeddings.image_embedding if (image and embeddings.image_embedding) else None,
            "text_embedding": embeddings.text_embedding if text else None
        }
    except Exception as e:
        logging.error(f"Vertex AI error: {str(e)}")
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

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(os.path.join(app.root_path, 'static'), filename)

@app.route('/')
def index():
    """Homepage with recipe carousel"""
    try:
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
    except Exception as e:
        logging.error(f"Homepage error: {str(e)}")
        return render_template('error.html'), 500

@app.route('/search', methods=['POST'])
def search():
    try:
        # Ensure we have JSON data
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400
            
        data = request.get_json()
        query = data.get('query', '').strip()
        image = data.get('image')
        
        if not query and not image:
            return jsonify({"error": "Please provide either text or image"}), 400
            
        results = hybrid_search(
            image=image,
            text=query,
            k=10,
            image_weight=0.7 if image else 0,
            text_weight=0.3 if query else 0
        )
        
        return jsonify([{**r, '_id': str(r['_id'])} for r in results])
        
    except Exception as e:
        logging.error(f"Search error: {str(e)}")
        return jsonify({"error": "Search failed", "details": str(e)}), 500
        
@app.route('/recipe/<recipe_id>')
def recipe_detail(recipe_id):
    try:
        recipe = recipes_collection.find_one({'_id': ObjectId(recipe_id)})
        if not recipe:
            return render_template('404.html'), 404
            
        recipe['_id'] = str(recipe['_id'])
        recipe.setdefault('audio_steps', [])
        recipe.setdefault('time_analysis', {
            'total_estimated_time_minutes': 0,
            'recipe_difficulty': 'Unknown'
        })
        
        return render_template('recipe.html', recipe=recipe)
    except Exception as e:
        logging.error(f"Recipe detail error: {str(e)}")
        return render_template('error.html'), 400

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    logging.critical(f"Server error: {str(e)}")
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Development server
    port = int(os.environ.get("PORT", 5000))
    debug = FLASK_ENV == "development"
    app.run(host='0.0.0.0', port=port, debug=debug)