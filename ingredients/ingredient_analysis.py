import pandas as pd
import ast

# Load only the necessary columns
df = pd.read_csv("openfoodfacts_ingredients.csv")

def extract_en_items_from_dict(analysis_str):
    try:
        analysis_dict = ast.literal_eval(analysis_str)
        result_array = []
        for key, values in analysis_dict.items():
            result_array.append(key)
            result_array.extend(values)
        return [item for item in result_array if item.startswith('en:')]
    except Exception:
        return []

def extract_en_items_from_list(tag_str):
    try:
        tag_list = ast.literal_eval(tag_str)
        return [item for item in tag_list if item.startswith('en:')]
    except Exception:
        return []

def combine_en_tags(row):
    en_from_analysis = extract_en_items_from_dict(row['ingredients_analysis'])
    en_from_tags = extract_en_items_from_list(row['ingredients_analysis_tags'])
    # Combine and deduplicate
    return list(set(en_from_analysis + en_from_tags))

# Apply function
df['ingredients_analysis'] = df.apply(combine_en_tags, axis=1)

# Drop original columns
df = df.drop(columns=["ingredients_analysis_tags"])

# Save to CSV
df.to_csv("ingredient_analysis.csv", index=False)
