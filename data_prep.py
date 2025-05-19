import requests
import pandas as pd

results = []

for page in range(1, 101):  
    url = (
        f"https://world.openfoodfacts.net/api/v2/search?"
        f"country=spain"
        f"&page={page}"
        f"&page_size=100"
        f"&sort_by=unique_scans_n"
        f"&lc=en"
        f"&fields=code,product_name,brands,categories_tags,nova_group,nutriscore_grade,nutriscore_score,image_url,ecoscore_grade"
    )
    r = requests.get(url)
    data = r.json()
    products = data.get("products", [])
    results.extend(products)

df = pd.DataFrame(results)
df.to_csv("openfoodfacts_spain_products.csv", index=False)
print(f"✅ Saved {len(df)} products from Spain")

# 🔍 Print the list of columns
print("📋 Columns in the DataFrame:")
print(df.columns.tolist())
