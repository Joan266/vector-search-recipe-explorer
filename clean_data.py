import pandas as pd
import ast
import re
from unidecode import unidecode
import json

# --- Load raw dataset ---
df = pd.read_csv("openfoodfacts_spain_products.csv")

# --- Cleaning Helpers ---

def normalize_text(text):
    if pd.isnull(text):
        return ""
    return unidecode(str(text)).strip().lower()

def clean_brands(brand_str):
    if pd.isnull(brand_str):
        return []
    brand_str = unidecode(brand_str.strip().lower())
    return [b.strip() for b in brand_str.split(',') if b.strip() and not b.strip().isdigit()]

def clean_categories(cat_str):
    try:
        cat_list = ast.literal_eval(cat_str)
        return [normalize_text(c.split(':')[-1].replace('-', ' ')) for c in cat_list]
    except (ValueError, SyntaxError, TypeError):
        return []

def clean_product_name(name):
    if pd.isnull(name):
        return ""
    name = unidecode(str(name)).strip()
    name = re.sub(r'^["\']+|["\']+$', '', name)
    name = name.lower()
    return name

# --- Cleaning Steps ---

df["product_name"] = df["product_name"].apply(clean_product_name)
df["brands"] = df["brands"].apply(clean_brands)
df["brand"] = df["brands"].apply(lambda b: b[0] if b else "")
df["brand"] = df["brand"].apply(normalize_text)
df["categories_tags"] = df["categories_tags"].apply(clean_categories)

# --- Filter: remove low-quality or irrelevant entries ---

df = df[df["product_name"].str.len() >= 3]
df = df[~df["product_name"].str.match(r"^\d{6,}$")]  # product name is all digits
df = df[~df["product_name"].str.contains(r'[\u0600-\u06FF\u0590-\u05FF]', na=False)]  # Arabic/Hebrew
df = df[~df["brand"].str.match(r"^\d+$")]  # brand name is all digits
df = df[df["brand"].str.strip() != ""]
df = df[df["product_name"].str.strip() != ""]
df = df[df["categories_tags"].map(len) > 0]

# --- Normalize score fields ---

df["ecoscore_grade"] = (
    df["ecoscore_grade"]
    .replace({"not-applicable": "unknown"})
    .fillna("unknown")
)

df["nova_group"] = df["nova_group"].fillna(-1).replace(-1, None)

nutriscore_map = {
    -15: "a", -5: "a",
    -2: "b",  0: "b",
    3: "c",  10: "c",
    15: "d", 20: "d",
    25: "e", 40: "e"
}
df["nutriscore_grade"] = (
    df["nutriscore_grade"]
    .fillna(df["nutriscore_score"].map(nutriscore_map))
    .fillna("unknown")
)

# --- Quality scoring for deduplication ---

def record_quality(row):
    score = 0
    score += len(row["categories_tags"]) if isinstance(row["categories_tags"], list) else 0
    score += 1 if pd.notnull(row["image_url"]) and str(row["image_url"]).strip() != "" else 0
    score += 1 if row["nutriscore_grade"] != "unknown" else 0
    score += 1 if row["ecoscore_grade"] != "unknown" else 0
    score += 1 if pd.notnull(row["nova_group"]) else 0
    return score

df["quality_score"] = df.apply(record_quality, axis=1)
df = df.sort_values(by=["product_name", "brand", "quality_score"], ascending=[True, True, False])
df = df.drop_duplicates(subset=["product_name", "brand"], keep="first")
df = df.drop(columns=["quality_score"])

# --- Final adjustments for MongoDB compatibility ---

df["_id"] = df["code"].fillna(0).astype(int).astype(str)
df["vector"] = None
df["created_at"] = pd.Timestamp.now().isoformat()
df["origin"] = "openfoodfacts"
df["schema_version"] = 1
df["embedding_version"] = "openai-ada-v2"
df["scoring_version"] = "nutri-2024.1"

# --- Final column order ---

columns = [
    "_id", "product_name", "brand", "brands", "categories_tags", "image_url",
    "nutriscore_grade", "nutriscore_score", "ecoscore_grade", "nova_group",
    "vector", "created_at", "origin", "schema_version", "embedding_version", "scoring_version"
]
df = df[columns]

# --- Export ---

df.to_csv("cleaned_food_products.csv", index=False)
df.to_json("cleaned_food_products.json", orient="records", force_ascii=False, indent=2)

print("✅ Cleaning complete! Files saved as 'cleaned_food_products.csv' and 'cleaned_food_products.json'")
print(f"🧮 Final record count: {len(df)}")
