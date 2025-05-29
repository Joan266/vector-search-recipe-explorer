import ast
import json
import pandas as pd
from pymongo import MongoClient

# ---------- CONFIG ----------
CSV_PATH = "cleaned_output_no_empty_rows.csv"
MONGODB_URI = "mongodb+srv://<username>:<password>@<cluster-url>/?retryWrites=true&w=majority"
DB_NAME = "your_database"
COLLECTION_NAME = "products"
# ----------------------------

# Fields to parse specially
list_fields = [
    "brands_tags",
    "categories_tags",
    "ingredients_analysis",
    "ingredients_tags",
    "nutrient_levels_tags"
]

dict_fields = ["nutriments"]

float_fields = [
    "origins_epi_score",
    "origins_epi_value",
    "origins_transportation_score",
    "origins_value",
    "origins_main_percent",
    "packaging_score",
    "packaging_value",
    "packaging_non_recyclable_materials"
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

# Load CSV
df = pd.read_csv(CSV_PATH)

# Parse all rows
json_docs = []
for _, row in df.iterrows():
    parsed_doc = {}
    for col in df.columns:
        parsed_doc[col] = parse_field(row[col], col)
    json_docs.append(parsed_doc)

# Save locally as JSON (optional)
with open("mongo_ready_data.json", "w", encoding="utf-8") as f:
    json.dump(json_docs, f, ensure_ascii=False, indent=2)
print("📁 Saved to mongo_ready_data.json")

# ---------- MONGODB UPLOAD ----------
client = MongoClient(MONGODB_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# Drop collection before inserting (as requested)
collection.drop()
print(f"🗑️ Collection '{COLLECTION_NAME}' dropped.")

# Insert all documents
collection.insert_many(json_docs)
print(f"✅ Inserted {len(json_docs)} documents into '{COLLECTION_NAME}'.")

# Create indexes
collection.create_index("categories_tags")
collection.create_index("nutrition_grade_fr")
collection.create_index("product_name")
collection.create_index("code", unique=True)

print("🗂️ Indexes created on 'categories_tags', 'nutrition_grade_fr', 'product_name', and 'code'.")
