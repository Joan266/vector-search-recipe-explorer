import pandas as pd
import ast
import re

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
    en_from_analysis = extract_en_items_from_dict(row.get('ingredients_analysis', '{}'))
    en_from_tags = extract_en_items_from_list(row.get('ingredients_analysis_tags', '[]'))
    return list(set(en_from_analysis + en_from_tags))

def clean_name(name):
    if not isinstance(name, str):
        return None
    name = name.strip().lower()
    name = re.sub(r'[^\x00-\x7F]+', '', name)  # Remove non-ASCII chars
    if re.fullmatch(r'\d+', name):  # Only digits
        return None
    if not name or name == '""':
        return None
    return name

def extract_key_value_with_unit(nutriments_str):
    try:
        nutriments = ast.literal_eval(nutriments_str)
        result = []
        for key, value in nutriments.items():
            if key.endswith("_value") and isinstance(value, (int, float)) and value > 0:
                base_key = key[:-6]  # remove '_value'
                unit_key = f"{base_key}_unit"
                unit = nutriments.get(unit_key)
                if unit is not None:
                    result.append(f"{base_key}: {value}{unit}")
        return result
    except Exception:
        return []

def extract_ecoscore_data(ecoscore_str):
    try:
        data = ast.literal_eval(ecoscore_str)
    except Exception:
        return pd.Series()

    adj = data.get('adjustments', {})
    origins = adj.get('origins_of_ingredients', {})
    packaging = adj.get('packaging', {})
    production = adj.get('production_system', {})

    agg_origins = origins.get('aggregated_origins', [{}])
    first_origin = agg_origins[0] if agg_origins else {}

    return pd.Series({
        'origins_epi_score': origins.get('epi_score'),
        'origins_epi_value': origins.get('epi_value'),
        'origins_transportation_score': origins.get('transportation_score'),
        'origins_value': origins.get('value'),
        'origins_main_percent': first_origin.get('percent'),
        'packaging_score': packaging.get('score'),
        'packaging_value': packaging.get('value'),
        'packaging_non_recyclable_materials': packaging.get('non_recyclable_and_non_biodegradable_materials'),
    })

def clean_openfoodfacts_data(input_csv, output_csv):
    df = pd.read_csv(input_csv)

    # 1. Process ingredients analysis columns
    if 'ingredients_analysis' in df.columns and 'ingredients_analysis_tags' in df.columns:
        df['ingredients_analysis'] = df.apply(combine_en_tags, axis=1)
        df = df.drop(columns=["ingredients_analysis_tags"], errors='ignore')

    # 2. Clean product_name column
    if 'product_name' in df.columns:
        df['product_name'] = df['product_name'].apply(clean_name)

    # 3. Process nutriments column
    if 'nutriments' in df.columns:
        df['nutriments'] = df['nutriments'].apply(extract_key_value_with_unit)

    # 4. Extract ecoscore data into new columns, drop original 'ecoscore_data' and other unwanted columns
    if 'ecoscore_data' in df.columns:
        ecoscore_extracted = df['ecoscore_data'].apply(extract_ecoscore_data)
        df = df.drop(columns=['ecoscore_data'])
        df = pd.concat([df, ecoscore_extracted], axis=1)

        # Drop unwanted columns if they exist
        drop_cols = ['grade', 'ecoscore_tags', 'origins_main_origin', 'ingredients_without_ecobalyse_ids_n']
        df = df.drop(columns=[col for col in drop_cols if col in df.columns])

    # Drop rows where product_name is None or NaN after cleaning
    if 'product_name' in df.columns:
        df = df[df['product_name'].notna()]

    # Save cleaned dataframe
    df.to_csv(output_csv, index=False)
    print(f"✅ Data cleaned and saved to {output_csv}")

if __name__ == "__main__":
    input_csv = "spain_food_products.csv"  # Your input CSV with all raw data
    output_csv = "spain_food_products_cleaned.csv"
    clean_openfoodfacts_data(input_csv, output_csv)
