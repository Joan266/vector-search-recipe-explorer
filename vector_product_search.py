import os
from dotenv import load_dotenv
from pymongo import MongoClient
import vertexai
from vertexai.language_models import TextEmbeddingModel, TextEmbeddingInput

# ---------- 1. Cargar variables de entorno ----------
load_dotenv()
MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME", "eco_footprint")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "products")
GCP_PROJECT = os.getenv("GCP_PROJECT")
GCP_REGION = os.getenv("GCP_REGION", "us-central1")
GCP_KEY_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GCP_KEY_PATH

# ---------- 2. Inicializar Vertex AI ----------
vertexai.init(project=GCP_PROJECT, location=GCP_REGION)
embedding_model = TextEmbeddingModel.from_pretrained("gemini-embedding-001")

def get_query_embedding(text: str) -> list[float]:
    text_input = TextEmbeddingInput(text)  # quitar "RETRIEVAL_QUERY"
    embedding = embedding_model.get_embeddings([text_input], output_dimensionality=768)
    return embedding[0].values

def search_products(query_text: str, k: int = 5):
    query_embedding = get_query_embedding(query_text)
    print("Query embedding sample:", query_embedding[:5])  
    client = MongoClient(MONGODB_URI)
    collection = client[DB_NAME][COLLECTION_NAME]

    results = collection.aggregate([
         {
            '$vectorSearch': {
            'index': 'vector_index', 
            "path": "embedding",
            "queryVector": query_embedding,
            'numCandidates': 150, 
            'limit': k
            }
        },
        {
            "$project": {
                "product_name": 1,
                "brands_tags": 1,
                "categories_tags": 1,
            }
        }
    ])

    return list(results)

# ---------- 5. Ejecutar desde consola ----------
if __name__ == "__main__":
    query = input("🔎 ¿Qué tipo de producto estás buscando?: ")
    matches = search_products(query, k=5)
    print("\n📦 Resultados relevantes:")
    for i, doc in enumerate(matches, start=1):
        print(f"\n#{i}")
        print(f"Producto: {doc.get('product_name', 'Desconocido')}")
        print(f"Marca(s): {', '.join(doc.get('brands_tags', []))}")
        print(f"Categorías: {', '.join(doc.get('categories_tags', []))}")
        print(f"Score: {doc.get('score', 0):.4f}")
