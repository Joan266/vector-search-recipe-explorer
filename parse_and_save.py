import ast
import json
import pandas as pd
from dotenv import load_dotenv
import os

# ---------- LOAD ENV ----------
load_dotenv()

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

    # Add product name twice for emphasis
    add("product_name", "product name")
    add("product_name", "product name")

    # Brand with prefix
    add("brands_tags", "brand")

    # Categories with prefix
    add("categories_tags", "categories")

    # Ingredients
    add("ingredients_tags", "ingredients")
    add("ingredients_analysis", "ingredient analysis")

    # Nutrient levels
    add("nutrient_levels_tags", "nutrient levels")

    # Grades
    add("nutrition_grade_fr", "nutrition grade")
    add("ecoscore_grade", "ecoscore grade")

    # Nutriments dict nicely formatted
    add("nutriments", "nutriments")

    # Origins fields with labels
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

    # Packaging fields with labels
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

# Load CSV
df = pd.read_csv("cleaned_output_no_empty_rows.csv")

# Parse CSV rows
parsed_docs = []
for _, row in df.iterrows():
    parsed_doc = {}
    for col in df.columns:
        parsed_doc[col] = parse_field(row[col], col)

    # Add the vector text field
    parsed_doc["vector_text"] = generate_vector(parsed_doc)

    parsed_docs.append(parsed_doc)

# Save parsed data as JSON
with open("parsed_docs.json", "w", encoding="utf-8") as f:
    json.dump(parsed_docs, f, ensure_ascii=False, indent=2)

print(f"✅ Parsed {len(parsed_docs)} documents and saved to parsed_docs.json")
