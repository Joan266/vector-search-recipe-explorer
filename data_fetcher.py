import requests
import pandas as pd

# 🌍 Define relevant columns to fetch from API
important_columns = [
    "nutrient_levels_tags", "nutriments",
    "nutrition_grade_fr", 
    "ecoscore_data", "ecoscore_grade", "ecoscore_tags",
    "ingredients_analysis", "ingredients_analysis_tags", "ingredients_tags",
    "product_name", "brands_tags", "categories_tags", "code"
    ,"image_url"
]

fields_param = ",".join(important_columns)
results = []

# 📦 Fetch data from Open Food Facts API
for page in range(1, 51): 
    url = (
        f"https://world.openfoodfacts.net/api/v2/search?"
        f"country=spain"
        f"&page={page}"
        f"&page_size=100"
        f"&sort_by=unique_scans_n"
        f"&lc=en"
        f"&fields={fields_param}"
        f"&tagtype_0=product_type"
        f"&tag_contains_0=contains"
        f"&tag_0=food"
    )
    r = requests.get(url)
    data = r.json()
    products = data.get("products", [])
    results.extend(products)

# 🧹 Load into a DataFrame
df = pd.DataFrame(results)
print(f"✅ Saved {len(df)} products from Spain")

# 💾 Save DataFrame to CSV
df.to_csv("spain_food_products.csv", index=False)
print("📁 Data saved to spain_food_products.csv")
