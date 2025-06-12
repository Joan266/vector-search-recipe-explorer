from vertexai import init
from vertexai.vision_models import Image as VertexImage, MultiModalEmbeddingModel
import requests
from PIL import Image
from io import BytesIO
import tempfile
import json
import os
from dotenv import load_dotenv

# ---------- LOAD ENV ----------
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
GCP_PROJECT = os.getenv("GCP_PROJECT")
GCP_REGION = os.getenv("GCP_REGION", "us-central1")
GCP_KEY_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

if GCP_KEY_PATH:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GCP_KEY_PATH

# ✅ Initialize Vertex AI
init(project=GCP_PROJECT, location=GCP_REGION)

# ---------- Load parsed JSON ----------
with open("./parsed_docs.json", "r") as f:
    json_docs = json.load(f)

# ---------- Load MultiModal Model ----------
print("📷 Loading multimodal embedding model...")
mm_model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding@001")
print("✅ Multimodal model loaded!")

# ---------- Generate Image Embeddings ----------
def download_image(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return Image.open(BytesIO(response.content)).convert("RGB")
    except Exception as e:
        print(f"❌ Failed to download {url}: {e}")
        return None

print("🎨 Generating image + text embeddings...")

for doc in json_docs:
    image_url = doc.get("image_url")
    product_name = doc.get("product_name")
    
    if not image_url or not product_name:
        continue

    pil_image = download_image(image_url)
    if pil_image is None:
        continue

    with tempfile.NamedTemporaryFile(suffix=".jpg") as temp_img:
        pil_image.save(temp_img.name)

        try:
            vertex_img = VertexImage.load_from_file(temp_img.name)
            embeddings = mm_model.get_embeddings(
                image=vertex_img,
                contextual_text=product_name,
                dimension=1408
            )
            doc["image_embedding"] = embeddings.image_embedding
            doc["mm_text_embedding"] = embeddings.text_embedding
        except Exception as e:
            print(f"⚠️ Embedding failed for {image_url}: {e}")

# ---------- Save Output ----------
with open("parsed_docs_with_embeddings.json", "w") as f:
    json.dump(json_docs, f, indent=2)
