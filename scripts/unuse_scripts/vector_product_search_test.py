import os
from dotenv import load_dotenv
from pymongo import MongoClient
import vertexai
from vertexai.language_models import TextEmbeddingModel, TextEmbeddingInput

# ---------- 1. Load environment variables ----------
load_dotenv()
MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME", "eco_footprint")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "products")
GCP_PROJECT = os.getenv("GCP_PROJECT")
GCP_REGION = os.getenv("GCP_REGION", "us-central1")
GCP_KEY_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GCP_KEY_PATH

# ---------- 2. Initialize Vertex AI ----------
vertexai.init(project=GCP_PROJECT, location=GCP_REGION)
embedding_model = TextEmbeddingModel.from_pretrained("gemini-embedding-001")

def get_query_embedding(text: str) -> list[float]:
    text_input = TextEmbeddingInput(text)
    embedding = embedding_model.get_embeddings([text_input], output_dimensionality=768)
    return embedding[0].values

def build_ann_query(query_embedding, k=10, num_candidates=100):
    return [
        {
            '$vectorSearch': {
                'index': 'vector_index',
                'path': 'embedding',
                'queryVector': query_embedding,
                'numCandidates': num_candidates,
                'limit': k
            }
        },
        {
            '$project': {
                "_id": 0,
                "product_name": 1,
                "brands_tags": 1,
                "categories_tags": 1,
                "score": {"$meta": "vectorSearchScore"}
            }
        }
    ]

def build_enn_query(query_embedding, k=10):
    return [
        {
            '$vectorSearch': {
                'index': 'vector_index',
                'path': 'embedding',
                'queryVector': query_embedding,
                'exact': True,
                'limit': k
            }
        },
        {
            '$project': {
                "_id": 0,
                "product_name": 1,
                "brands_tags": 1,
                "categories_tags": 1,
                "score": {"$meta": "vectorSearchScore"}
            }
        }
    ]

def search_products(query_text: str, k=10, num_candidates=100):
    query_embedding = get_query_embedding(query_text)
    client = MongoClient(MONGODB_URI)
    collection = client[DB_NAME][COLLECTION_NAME]

    # Run ANN
    ann_query = build_ann_query(query_embedding, k=k, num_candidates=num_candidates)
    ann_results = list(collection.aggregate(ann_query))

    # Run ENN
    enn_query = build_enn_query(query_embedding, k=k)
    enn_results = list(collection.aggregate(enn_query))

    return ann_results, enn_results

def jaccard_similarity(list1, list2):
    set1 = set(doc["product_name"] for doc in list1)
    set2 = set(doc["product_name"] for doc in list2)
    intersection = set1 & set2
    union = set1 | set2
    return len(intersection) / len(union) if union else 0.0

# ---------- 5. Run from CLI ----------
if __name__ == "__main__":
    query = input("🔎 ¿Qué tipo de producto estás buscando?: ")
    k = 10
    num_candidates = 100

    ann_results, enn_results = search_products(query, k=k, num_candidates=num_candidates)

    print("\n📦 ANN Resultados:")
    for i, doc in enumerate(ann_results, start=1):
        print(f"#{i}: {doc.get('product_name')} — Score: {doc.get('score', 0):.4f}")

    print("\n📦 ENN Resultados:")
    for i, doc in enumerate(enn_results, start=1):
        print(f"#{i}: {doc.get('product_name')} — Score: {doc.get('score', 0):.4f}")

    # Compare sets
    similarity = jaccard_similarity(ann_results, enn_results)
    print(f"\n🔁 Jaccard Similarity (ANN vs ENN): {similarity:.2%}")
