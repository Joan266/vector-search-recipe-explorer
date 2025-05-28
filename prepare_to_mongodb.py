import pandas as pd
import ast
import re
from urllib.parse import urlparse
import json

def clean_list_string(val):
    if not isinstance(val, str) or not val.startswith('['):
        return []
    try:
        items = ast.literal_eval(val)
        cleaned_items = []
        for item in items:
            if isinstance(item, str) and item.startswith(('en:', 'xx:')):
                item_clean = re.sub(r'^(en:|xx:)', '', item)
                if re.fullmatch(r'[ -~]+', item_clean):  # ASCII only
                    cleaned_items.append(item_clean)
        return cleaned_items
    except Exception:
        return []

def clean_code(val):
    return str(val) if pd.notna(val) else None

def clean_url(val):
    if isinstance(val, str):
        parsed = urlparse(val)
        if all([parsed.scheme, parsed.netloc]):
            return val
    return None

def clean_nutriments(val):
    if not isinstance(val, str):
        return {}
    try:
        # Try to interpret stringified dict/list of key-value strings
        if val.startswith("[") or val.startswith("{"):
            parsed = ast.literal_eval(val)
            if isinstance(parsed, list):
                return {k.strip(): v.strip() for kv in parsed for k, v in [kv.split(":", 1)] if ":" in kv}
            elif isinstance(parsed, dict):
                return parsed
    except Exception:
        pass
    return {}

def clean_grade(val):
    if isinstance(val, str):
        val = val.strip().lower()
        return val if val not in ["not-applicable", "unknown"] else None
    return None

# Load CSV
df = pd.read_csv("spain_food_products_cleaned.csv")

# List-like fields to parse and clean
list_fields = [
    'brands_tags', 'categories_tags', 'ingredients_tags',
    'ingredients_percent_analysis', 'ingredients_analysis',
    'nutrient_levels_tags'
]
for col in list_fields:
    if col in df.columns:
        df[col] = df[col].apply(clean_list_string)

# Field type conversions and cleaning
if 'code' in df.columns:
    df['code'] = df['code'].apply(clean_code)


if 'image_url' in df.columns:
    df['image_url'] = df['image_url'].apply(clean_url)

if 'nutriments' in df.columns:
    df['nutriments'] = df['nutriments'].apply(clean_nutriments)

for grade_col in ['nutrition_grade_fr', 'ecoscore_grade']:
    if grade_col in df.columns:
        df[grade_col] = df[grade_col].apply(clean_grade)

# Replace 'not-applicable' and 'unknown' with None across all fields
df = df.replace({'not-applicable': None, 'unknown': None})

# Save cleaned file
df.to_csv("cleaned_output.csv", index=False)
