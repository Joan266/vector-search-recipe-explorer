import requests
import pandas as pd

# 🌍 Define relevant columns to fetch from API
important_columns = [
    "_keywords", "additives_n", "brands_tags", "categories_tags", "code",
    "ecoscore_data", "ecoscore_grade", "ecoscore_tags", "ingredients_analysis",
    "ingredients_analysis_tags", "ingredients_n",
    "ingredients_n_tags", "ingredients_non_nutritive_sweeteners_n",
    "ingredients_percent_analysis", "ingredients_sweeteners_n", "ingredients_tags",
    "ingredients_text", "ingredients_text_with_allergens", "ingredients_with_specified_percent_n",
    "ingredients_with_specified_percent_sum", "ingredients_with_unspecified_percent_n",
    "ingredients_with_unspecified_percent_sum", "ingredients_without_ciqual_codes_n",
    "ingredients_without_ecobalyse_ids_n", "known_ingredients_n", "last_updated_t",
    "nova_groups_tags", "nutrient_levels", "nutrient_levels_tags", "nutriments", "nutriscore",
    "nutriscore_data", "nutriscore_grade", "nutriscore_tags", "nutrition_data_per",
    "nutrition_data_prepared_per", "nutrition_grade_fr", "nutrition_grades", "nutrition_grades_tags",
    "nutrition_score_beverage", "packagings_materials", "product_name", "product_type"
]

fields_param = ",".join(important_columns)
results = []

# 📦 Fetch data from Open Food Facts API
for page in range(1, 10):  # You can increase the page range for more data
    url = (
        f"https://world.openfoodfacts.net/api/v2/search?"
        f"country=spain"
        f"&page={page}"
        f"&page_size=100"
        f"&sort_by=unique_scans_n"
        f"&lc=en"
        f"&fields={fields_param}"
    )
    r = requests.get(url)
    data = r.json()
    products = data.get("products", [])
    results.extend(products)

# 🧹 Load into a DataFrame
df = pd.DataFrame(results)
print(f"✅ Saved {len(df)} products from Spain")

# 🎯 Define thematic groups of columns
nutrition_columns = [
    "nutrient_levels", "nutrient_levels_tags", "nutriments",
    "nutrition_data_per", "nutrition_data_prepared_per",
    "nutrition_grade_fr", "nutrition_grades", "nutrition_grades_tags",
    "nutrition_score_beverage", "nova_groups_tags", "known_ingredients_n",
    "ingredients_n", "ingredients_text", "ingredients_text_with_allergens",
    "ingredients_sweeteners_n", "ingredients_non_nutritive_sweeteners_n"
]

eco_columns = [
    "ecoscore_data", "ecoscore_grade", "ecoscore_tags",
    "ingredients_without_ecobalyse_ids_n"
]

ingredients_columns = [
    "ingredients_analysis", "ingredients_analysis_tags",
    "ingredients_n_tags", "ingredients_percent_analysis", "ingredients_tags",
    "ingredients_with_specified_percent_n", "ingredients_with_specified_percent_sum",
    "ingredients_with_unspecified_percent_n", "ingredients_with_unspecified_percent_sum",
    "ingredients_without_ciqual_codes_n"
]

meta_columns = [
    "product_name", "brands_tags", "categories_tags", "code",
    "product_type", "last_updated_t", "_keywords"
]

# 🗂️ Create themed DataFrames
df_nutrition = df[nutrition_columns]
df_eco = df[eco_columns]
df_ingredients = df[ingredients_columns]
df_meta = df[meta_columns]

# 💾 Save to CSV files
df_nutrition.to_csv("openfoodfacts_nutrition.csv", index=False)
df_eco.to_csv("openfoodfacts_ecoscore.csv", index=False)
df_ingredients.to_csv("openfoodfacts_ingredients.csv", index=False)
df_meta.to_csv("openfoodfacts_metadata.csv", index=False)

print("📁 Thematic CSV files created:")
print(" - openfoodfacts_nutrition.csv")
print(" - openfoodfacts_ecoscore.csv")
print(" - openfoodfacts_ingredients.csv")
print(" - openfoodfacts_metadata.csv")
