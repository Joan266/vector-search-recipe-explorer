import pandas as pd
import ast
from unidecode import unidecode
import json

# Load the CSV file
df = pd.read_csv("openfoodfacts_spain_products.csv")

# Clean 'brands' column
def clean_brands(brand_str):
    if pd.isnull(brand_str):
        return []
    brand_str = unidecode(brand_str.strip().lower())
    return [b.strip() for b in brand_str.split(',')]

df['brands'] = df['brands'].apply(clean_brands)

# Clean 'categories_tags' column
def clean_categories(cat_str):
    try:
        cat_list = ast.literal_eval(cat_str)
        return [c.split(':')[-1].replace('-', ' ').strip().lower() for c in cat_list]
    except (ValueError, SyntaxError, TypeError):
        return []

df['categories_tags'] = df['categories_tags'].apply(clean_categories)

# Handle missing values
df["ecoscore_grade"] = (
    df["ecoscore_grade"]
    .replace({"not-applicable": "unknown"})
    .fillna("unknown")
)

df["nova_group"] = df["nova_group"].fillna(-1)

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

# Create search_text
df["search_text"] = (
    df["product_name"].fillna("") + " " +
    df["brands"].apply(lambda x: " ".join(x)) + " " +
    df["categories_tags"].apply(lambda x: " ".join(x)) + " " +
    "nutriscore_" + df["nutriscore_grade"] + " " +
    "ecoscore_" + df["ecoscore_grade"] + " " +
    "nova_" + df["nova_group"].astype(str)
).str.strip()

# Flag and drop unusable records
df["is_usable"] = (
    df["search_text"].str.strip() != ""
) & (df["nutriscore_grade"] != "unknown")

df = df[df["is_usable"]].reset_index(drop=True)

# Remove unnecessary column
if 'schema_version' in df.columns:
    df = df.drop(columns=['schema_version'])

# Save cleaned data
df.to_csv("cleaned_food_products.csv", index=False)
df.to_json("cleaned_food_products.json", orient="records", force_ascii=False)

print("✅ Cleaning complete! Saved to 'cleaned_food_products.csv' and 'cleaned_food_products.json'")

# Summary
total = len(df)
missing_nutri = (df["nutriscore_grade"] == "unknown").sum()
missing_eco = (df["ecoscore_grade"] == "unknown").sum()
unknown_nova = (df["nova_group"] == -1).sum()
empty_search = (df["search_text"].str.strip() == "").sum()

print("\n--- Data Quality Summary ---")
print(f"Total usable records: {total}")
print(f"Missing NutriScore grade: {missing_nutri}")
print(f"Missing EcoScore grade: {missing_eco}")
print(f"Unknown Nova Group: {unknown_nova}")
print(f"Empty search_text entries: {empty_search}")

# Show one sample
print("\nSample cleaned record:")
print(json.dumps(df.iloc[0].to_dict(), indent=2, ensure_ascii=False))
