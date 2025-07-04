import requests
import pandas as pd

# 🌍 Define relevant columns to fetch from API
important_columns = [
    "nutrient_levels_tags", "nutriments",
    "nutrition_grade_fr", 
    "ecoscore_data", "ecoscore_grade", "ecoscore_tags",
    "ingredients_analysis", "ingredients_analysis_tags", "ingredients_tags",
    "product_name", "brands_tags", "categories_tags", "code",
    "image_url"
]

fields_param = ",".join(important_columns)
results = []

# 📦 Fetch data from Open Food Facts API with improved filters
for page in range(1, 2): 
    url = (
        f"https://world.openfoodfacts.net/api/v2/search?"
        f"country=spain"
        f"&page={page}"
        f"&page_size=50"
        f"&sort_by=unique_scans_n"
        f"&lc=en"
        f"&fields={fields_param}"
        f"&tagtype_0=product_type"
        f"&tag_contains_0=contains"
        f"&tag_0=food"
        f"&tagtype_1=nutrition_grades"
        f"&tag_contains_1=exclude"
        f"&tag_1=unknown"
        f"&tagtype_2=status"
        f"&tag_contains_2=contains"
        f"&tag_2=validated"
        f"&tagtype_3=images"
        f"&tag_contains_3=contains"
        f"&tag_3=front"
    )
    print(f"Fetching page {page}...")  
    r = requests.get(url)
    data = r.json()
    products = data.get("products", [])
    results.extend(products)

# 🧹 Load into a DataFrame
df = pd.DataFrame(results)
print(f"✅ Saved {len(df)} products from Spain with improved quality filters")

# 💾 Save DataFrame to CSV
df.to_csv("spain_food_products.csv", index=False)
print("📁 Data saved to spain_food_products.csv")
