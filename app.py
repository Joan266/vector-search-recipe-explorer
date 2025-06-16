import os
import logging
from flask import Flask, render_template, request, jsonify, send_from_directory
from pymongo import MongoClient, errors
from config import MONGODB_URI, DB_NAME, COLLECTION_NAME, GCP_PROJECT, GCP_REGION
from bson import ObjectId
import vertexai
from vertexai.vision_models import Image, MultiModalEmbeddingModel
from PIL import Image as PILImage
import requests
from io import BytesIO
import tempfile
import base64
from flask_cors import CORS
from google.cloud import logging as cloud_logging

# Initialize Cloud Logging
logging_client = cloud_logging.Client()
logging_client.setup_logging()

app = Flask(__name__)
CORS(app)

# Production Configuration
app.config.update(
    SECRET_KEY=os.environ.get('FLASK_SECRET_KEY', os.urandom(24)),
    JSONIFY_PRETTYPRINT_REGULAR=False,  # Disable in production
    MAX_CONTENT_LENGTH=16 * 1024 * 1024  # 16MB upload limit
)

# Initialize Vertex AI
vertexai.init(project=GCP_PROJECT, location=GCP_REGION)
model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding@001")

# MongoDB Connection with Pooling
try:
    client = MongoClient(
        MONGODB_URI,
        maxPoolSize=50,
        connectTimeoutMS=30000,
        socketTimeoutMS=30000,
        serverSelectionTimeoutMS=30000
    )
    client.admin.command('ping')  # Test connection
    db = client[DB_NAME]
    recipes_collection = db[COLLECTION_NAME]
except errors.ConnectionFailure as e:
    logging.critical(f"MongoDB connection failed: {str(e)}")
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

def hybrid_search(image=None, text=None, k=5, image_weight=0.5, text_weight=0.5):
    """Hybrid vector search with MongoDB"""
    try:
        total_weight = image_weight + text_weight
        if total_weight <= 0:
            raise ValueError("Invalid weights")
        
        embeddings = get_embeddings(image, text)
        if not embeddings:
            raise ValueError("Embedding generation failed")

        pipeline = []
        
        if embeddings["image_embedding"]:
            pipeline.append({
                "$vectorSearch": {
                    "index": "recipe_img_vector_index",
                    "path": "image_embedding",
                    "queryVector": embeddings["image_embedding"],
                    "numCandidates": 100,
                    "limit": k * 3
                }
            })

        if embeddings["text_embedding"]:
            pipeline.append({
                "$vectorSearch": {
                    "index": "recipe_text_vector_index",
                    "path": "text_embedding",
                    "queryVector": embeddings["text_embedding"],
                    "numCandidates": 100,
                    "limit": k * 3
                }
            })

        if not pipeline:
            return []

        pipeline.append({
            "$project": {
                "_id": 1,
                "name": 1,
                "category": 1,
                "area": 1,
                "img_url": 1,
                "health_score": 1,
                "img_score": {"$meta": "vectorSearchScore"},
                "text_score": {"$meta": "vectorSearchScore"}
            }
        })

        results = list(recipes_collection.aggregate(pipeline))
        
        # Score processing and deduplication
        seen_ids = set()
        final_results = []
        
        for doc in results:
            doc_id = str(doc["_id"])
            if doc_id not in seen_ids:
                seen_ids.add(doc_id)
                doc["combined_score"] = (
                    (image_weight * doc.get("img_score", 0)) + 
                    (text_weight * doc.get("text_score", 0))
                )
                final_results.append(doc)

        return sorted(
            [r for r in final_results if r["combined_score"] >= 0.25],
            key=lambda x: x["combined_score"],
            reverse=True
        )[:k]

    except Exception as e:
        logging.error(f"Search failed: {str(e)}")
        raise

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
        data = request.get_json()
        if not data:
            raise ValueError("Empty request")
            
        query = data.get('query', '').strip()
        image = data.get('image')
        
        if not query and not image:
            raise ValueError("No search criteria")
            
        results = hybrid_search(
            image=image,
            text=query,
            k=10,
            image_weight=0.5 if image else 0,
            text_weight=0.5 if query else 0
        )
        
        return jsonify([{**r, '_id': str(r['_id'])} for r in results])
        
    except Exception as e:
        logging.error(f"Search error: {str(e)}")
        return jsonify({"error": str(e)}), 400

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
    # Production entry point
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)