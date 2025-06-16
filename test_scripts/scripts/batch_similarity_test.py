import os
import random
from dotenv import load_dotenv
from pymongo import MongoClient
from vertexai.language_models import TextEmbeddingModel, TextEmbeddingInput
import vertexai

# ---------------- 1. Environment Setup ----------------
load_dotenv()
MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME", "eco_footprint")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "products")
GCP_PROJECT = os.getenv("GCP_PROJECT")
GCP_REGION = os.getenv("GCP_REGION", "us-central1")
GCP_KEY_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GCP_KEY_PATH

# ---------------- 2. Vertex AI Init ----------------
vertexai.init(project=GCP_PROJECT, location=GCP_REGION)
embedding_model = TextEmbeddingModel.from_pretrained("gemini-embedding-001")

def get_query_embedding(text: str) -> list[float]:
    text_input = TextEmbeddingInput(text)
    embedding = embedding_model.get_embeddings([text_input], output_dimensionality=768)
    return embedding[0].values

# ---------------- 3. Jaccard Similarity ----------------
def jaccard_similarity(set1, set2):
    return len(set1 & set2) / len(set1 | set2) if set1 | set2 else 1.0

# ---------------- 4. Test Setup ----------------
client = MongoClient(MONGODB_URI)
collection = client[DB_NAME][COLLECTION_NAME]
k = 10
num_candidates = 100

# 100 example product-related queries
queries = [
    "low calorie soda", "organic apple juice", "gluten-free bread", "vegan snacks",
    "protein bars with chocolate", "sugar free energy drink", "whole grain cereal",
    "low sodium canned soup", "nut free granola", "coconut water", "healthy chips",
    "natural peanut butter", "high fiber pasta", "dairy free yogurt", "low fat milk",
    "organic orange juice", "sugar free chewing gum", "gluten-free cookies",
    "keto-friendly shakes", "non-dairy ice cream", "natural spring water",
    "vegan protein powder", "fruit and nut mix", "zero sugar soft drinks",
    "baby food organic", "plant-based meatballs", "unsweetened almond milk",
    "lactose free cheese", "low carb bread", "no sugar ketchup", "chia seed pudding",
    "vegan mayo", "sparkling mineral water", "protein cereal", "low fat cheese slices",
    "fiber-rich crackers", "nutritional yeast", "egg replacer", "soy milk",
    "light salad dressing", "organic trail mix", "unsweetened iced tea",
    "low sugar jelly", "vegan frozen meals", "healthy fruit snacks", "rice cakes",
    "non-gmo popcorn", "low calorie jam", "herbal tea blend", "vegan soup",
    "whole wheat pasta", "sugar-free chocolate", "oat milk", "turmeric latte",
    "vegan chocolate bar", "organic hummus", "gluten free pancake mix",
    "low sodium soy sauce", "sparkling coconut water", "vegan cheese", "baby cereal",
    "dried mango snack", "unsweetened applesauce", "nut-free protein bar",
    "vegan protein yogurt", "low-calorie crackers", "fruit juice with no sugar",
    "kombucha drink", "low carb tortilla", "fruit smoothie pouch", "chocolate soy milk",
    "vegan protein cookies", "no added sugar jam", "light peanut butter",
    "low calorie protein powder", "natural hazelnut spread", "low sodium tomato sauce",
    "gluten-free muffins", "organic granola", "vegan sour cream", "healthy oatmeal",
    "sugar-free hard candy", "vegan baby formula", "reduced sugar cereal",
    "flavored mineral water", "protein smoothie", "unsweetened coconut milk",
    "low sugar bbq sauce", "high protein yogurt", "green tea matcha drink",
    "almond based coffee creamer", "whole grain waffles", "oat-based snack bar",
    "vegetarian chili", "vegan meatless burger", "healthy snack mix", "low sugar cookies",
    "cocoa powder no sugar", "vegan pizza", "chia water", "low calorie granola bar",
    "vegetable juice mix", "organic peanut snack", "soy based yogurt", "protein oat bar"
]

# ---------------- 5. Main Comparison Loop ----------------
similarities = []
mismatches = []

for i, query in enumerate(queries, 1):
    print(f"🔍 [{i}/100] Query: {query}")
    query_embedding = get_query_embedding(query)

    # ANN
    ann_results = collection.aggregate([
        {
            '$vectorSearch': {
                'index': 'vector_index',
                'path': 'embedding',
                'queryVector': query_embedding,
                'numCandidates': num_candidates,
                'limit': k
            }
        },
        { '$project': {'_id': 1} }
    ])
    ann_ids = set(str(doc['_id']) for doc in ann_results)

    # ENN
    enn_results = collection.aggregate([
        {
            '$vectorSearch': {
                'index': 'vector_index',
                'path': 'embedding',
                'queryVector': query_embedding,
                'exact': True,
                'limit': k
            }
        },
        { '$project': {'_id': 1} }
    ])
    enn_ids = set(str(doc['_id']) for doc in enn_results)

    jac_sim = jaccard_similarity(ann_ids, enn_ids)
    similarities.append(jac_sim)

    if jac_sim < 1.0:
        mismatches.append((query, jac_sim, ann_ids ^ enn_ids))

# ---------------- 6. Final Report ----------------
print("\n📊 Jaccard Similarity Results:")
print(f"- Mean: {sum(similarities) / len(similarities):.4f}")
print(f"- Min: {min(similarities):.4f}")
print(f"- Max: {max(similarities):.4f}")

print(f"\n🔁 {len(mismatches)} queries had differences between ANN and ENN.")
for query, sim, diff in mismatches[:5]:  # Limit preview to first 5
    print(f"\n🔸 Query: {query}\nSimilarity: {sim:.4f}\nDiffering IDs: {list(diff)}")
