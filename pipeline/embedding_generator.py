from vertexai.vision_models import Image as VertexImage, MultiModalEmbeddingModel
from vertexai import init
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv
from pathlib import Path
import requests
from io import BytesIO
from PIL import Image
import tempfile
# Load environment variables
dotenv_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=dotenv_path)
GCP_PROJECT = os.getenv("GCP_PROJECT")
GCP_REGION = os.getenv("GCP_REGION", "us-central1")

class EmbeddingGenerator:
    def __init__(self):
        print("\n" + "="*50)
        print("🚀 Initializing EmbeddingGenerator...")
        init(project=GCP_PROJECT, location=GCP_REGION)
        self.model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding@001")

    def _download_image(self, url: str) -> Optional[Image.Image]:
        """Download and validate image"""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return Image.open(BytesIO(response.content)).convert("RGB")
        except Exception as e:
            print(f"⚠️ Image download failed: {url} - {str(e)}")
            return None

    def generate_embeddings(self, recipes: List[Dict]) -> List[Dict]:
        """Generate multimodal embeddings for recipes with images"""
        for recipe in recipes:
            if not recipe.get("img_url"):
                continue
                
            try:
                # Download and prepare image
                pil_image = self._download_image(recipe["img_url"])
                if not pil_image:
                    continue

                with tempfile.NamedTemporaryFile(suffix=".jpg") as temp_img:
                    pil_image.save(temp_img.name)
                    
                    # Enhanced contextual text
                    contextual_text = (
                        f"{recipe['name']}, a {recipe['category']} dish from {recipe.get('area', 'unknown')}. "
                        f"Main ingredients: {', '.join(recipe['ingredients'])}. "
                    )
                    
                    # Generate embeddings
                    vertex_img = VertexImage.load_from_file(temp_img.name)
                    embeddings = self.model.get_embeddings(
                        image=vertex_img,
                        contextual_text=contextual_text,
                        dimension=512
                    )
                    
                    # Add to recipe
                    recipe.update({
                        "image_embedding": embeddings.image_embedding,
                        "text_embedding": embeddings.text_embedding
                    })
            except Exception as e:
                print(f"⚠️ Embedding failed for {recipe['name']}: {str(e)}")
        
        return recipes