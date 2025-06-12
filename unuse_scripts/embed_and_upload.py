import ast
import json
import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from vertexai.language_models import TextEmbeddingModel
import vertexai
from pymongo.errors import OperationFailure

# ---------- LOAD ENV ----------
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
GCP_PROJECT = os.getenv("GCP_PROJECT")
# ------------------------------


# Parse and embed
json_docs = []
for _, row in df.iterrows():
    parsed_doc = {}
    for col in df.columns:
        parsed_doc[col] = parse_field(row[col], col)
    parsed_doc["vector"] = generate_vector(parsed_doc)
    json_docs.append(parsed_doc)

# Save locally (optional)
with open("mongo_ready_data.json", "w", encoding="utf-8") as f:
    json.dump(json_docs, f, ensure_ascii=False, indent=2)
print("📁 Saved to mongo_ready_data.json")

# ---------- MongoDB Upload ----------
client = MongoClient(MONGODB_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

collection.drop()
print(f"🗑️ Collection '{COLLECTION_NAME}' dropped.")
collection.insert_many(json_docs)
print(f"✅ Inserted {len(json_docs)} documents into '{COLLECTION_NAME}'.")

# ---------- Index Creation ----------
collection.create_index("categories_tags")
collection.create_index("nutrition_grade_fr")
collection.create_index("product_name")
collection.create_index("code", unique=True)
print("🗂️ Created standard indexes.")
