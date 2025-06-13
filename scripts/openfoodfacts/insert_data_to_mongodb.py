import ast
import json
import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import vertexai
from vertexai.language_models import TextEmbeddingModel, TextEmbeddingInput

# ---------- LOAD ENV ----------
load_dotenv()
MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
GCP_PROJECT = os.getenv("GCP_PROJECT")
GCP_REGION = os.getenv("GCP_REGION", "us-central1")
GCP_KEY_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GCP_KEY_PATH

# ---------- Define parsing helpers ----------
list_fields = [
    "brands_tags", "categories_tags", "ingredients_analysis",
    "ingredients_tags", "nutrient_levels_tags"
]
dict_fields = ["nutriments"]
float_fields = [
    "origins_epi_score", "origins_epi_value", "origins_transportation_score", "origins_value",
    "origins_main_percent", "packaging_score", "packaging_value", "packaging_non_recyclable_materials"
]

def parse_field(val, field):
    if pd.isna(val):
        return None
    try:
        if field in list_fields:
            return ast.literal_eval(val)
        elif field in dict_fields:
            return ast.literal_eval(val.replace("’", "'").replace("‘", "'"))
        elif field in float_fields:
            return float(val)
        elif field == "code":
            return str(val)
        else:
            return val
    except Exception:
        return None if field in float_fields else val

def generate_vector(doc):
    parts = []

    def add(field, prefix=None):
        val = doc.get(field)
        if val is None:
            return
        if isinstance(val, list):
            text = ", ".join(val)
            if prefix:
                parts.append(f"{prefix}: {text}")
            else:
                parts.append(text)
        elif isinstance(val, dict):
            readable = ", ".join(f"{k.replace('_', ' ')} {v}" for k, v in val.items())
            if prefix:
                parts.append(f"{prefix}: {readable}")
            else:
                parts.append(readable)
        else:
            if prefix:
                parts.append(f"{prefix}: {val}")
            else:
                parts.append(str(val))

    add("product_name", "product name")
    add("brands_tags", "brand")
    add("categories_tags", "categories")
    add("ingredients_tags", "ingredients")
    add("ingredients_analysis", "ingredient analysis")
    add("nutrient_levels_tags", "nutrient levels")
    add("nutrition_grade_fr", "nutrition grade")
    add("ecoscore_grade", "ecoscore grade")
    add("nutriments", "nutriments")

    origins_fields = [
        "origins_epi_score", "origins_epi_value", "origins_transportation_score",
        "origins_value", "origins_main_percent"
    ]
    origins_text = " ".join(
        f"{field.replace('_', ' ')} {doc.get(field)}"
        for field in origins_fields if doc.get(field) is not None
    )
    if origins_text:
        parts.append(f"origins: {origins_text}")

    packaging_fields = [
        "packaging_score", "packaging_value", "packaging_non_recyclable_materials"
    ]
    packaging_text = " ".join(
        f"{field.replace('_', ' ')} {doc.get(field)}"
        for field in packaging_fields if doc.get(field) is not None
    )
    if packaging_text:
        parts.append(f"packaging: {packaging_text}")

    full_text = " | ".join(parts).lower().strip()
    return full_text if full_text else None

# ---------- Initialize Vertex AI ----------
print("🔌 Initializing Vertex AI...")
vertexai.init(project=GCP_PROJECT, location=GCP_REGION)

print("📦 Loading embedding model...")
embedding_model = TextEmbeddingModel.from_pretrained("gemini-embedding-001")
print("✅ Model loaded!")

# ---------- Load CSV ----------
df = pd.read_csv("cleaned_output_no_empty_rows.csv")

# ---------- Parse and generate vector_text ----------
json_docs = []
for _, row in df.iterrows():
    parsed_doc = {}
    for col in df.columns:
        parsed_doc[col] = parse_field(row[col], col)
    vector_text = generate_vector(parsed_doc)
    parsed_doc["vector_text"] = vector_text
    json_docs.append(parsed_doc)

print(f"📝 Parsed {len(json_docs)} documents with vector text.")

print("🧮 Generating embeddings for each document vector_text...")

for doc in json_docs:
    input_obj = TextEmbeddingInput(doc["vector_text"], "RETRIEVAL_DOCUMENT")
    embedding = embedding_model.get_embeddings([input_obj], output_dimensionality=768)
    doc["embedding"] = embedding[0].values

print("✅ Embeddings generated for all documents.")

# ---------- Connect to MongoDB ----------
print("🔗 Connecting to MongoDB...")
client = MongoClient(MONGODB_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# ---------- Insert into MongoDB ----------
print(f"🗑️ Dropping existing '{COLLECTION_NAME}' collection...")
collection.drop()

print(f"🚀 Inserting {len(json_docs)} documents into '{COLLECTION_NAME}'...")
collection.insert_many(json_docs)

# ---------- Create indexes ----------
print("🗂️ Creating indexes...")
collection.create_index("categories_tags")
collection.create_index("nutrition_grade_fr")
collection.create_index("product_name")
collection.create_index("code", unique=True)
print("✅ Indexes created.")

print("🎉 All done!")
