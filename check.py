import pandas as pd
import ast  # for safely parsing strings representing lists/dicts

# Load original dataset
df = pd.read_csv('openfoodfacts_spain_products_v2.csv', low_memory=False)

def count_empty(cell):
    if pd.isnull(cell):
        return True
    if isinstance(cell, str) and cell.strip() == '[]':
        return True
    return False

# Calculate missing values frequency per column
missing_counts = df.applymap(count_empty).sum()
total_rows = len(df)
missing_freq = (missing_counts / total_rows) * 100

# Threshold for max % missing allowed (example 0%)
threshold = 10

# Filter columns with missing % <= threshold
usable_columns = missing_freq[missing_freq <= threshold].index.tolist()

print(f"Columns with missing values <= {threshold}%:")

unnecessary_cols = [
    "_id", "codes_tags", "complete", "countries", "countries_hierarchy", "countries_tags",
    "created_t", "creator", "editors_tags", "entry_dates_tags", "informers_tags", "lang",
    "languages", "languages_codes", "languages_tags", "last_edit_dates_tags", "last_modified_t",
    "lc", "popularity_key", "scans_n", "schema_version", "states", "states_hierarchy",
    "states_tags", "unique_scans_n", "update_key", "url","allergens_from_user","correctors_tags","data_sources","data_sources_tags","images","id",
    "image_front_small_url","image_front_thumb_url","image_front_url","image_small_url","image_thumb_url","images"
]

# Filter out unnecessary columns from usable_columns
usable_columns = [col for col in usable_columns if col not in unnecessary_cols]
print(usable_columns)

# Create new dataframe with only usable columns
df_filtered = df[usable_columns].copy()

# === Cleaning misc_tags: parse string list to python list ===
def parse_misc_tags(cell):
    if pd.isnull(cell) or cell.strip() == '[]':
        return []
    try:
        tags = ast.literal_eval(cell)
        if isinstance(tags, list):
            return tags
        return []
    except:
        return []

# === Generic cleaner to remove prefix like "en:" ===
def clean_tags(tag_list, prefix_to_remove="en:"):
    """
    Removes a specified prefix from each tag in a list of strings.
    Assumes input is already a list.
    """
    if not isinstance(tag_list, list):
        return []
    return [tag[len(prefix_to_remove):] if tag.startswith(prefix_to_remove) else tag for tag in tag_list]

# === Apply both steps ===
if 'misc_tags' in df_filtered.columns:
    df_filtered['misc_tags'] = df_filtered['misc_tags'].apply(parse_misc_tags)
    df_filtered['misc_tags'] = df_filtered['misc_tags'].apply(clean_tags)
# === Cleaning popularity_tags: keep only last tag ===
def last_popularity_tag(cell):
    if pd.isnull(cell) or cell.strip() == '[]':
        return None
    try:
        tags = ast.literal_eval(cell)
        if isinstance(tags, list) and len(tags) > 0:
            return tags[-1]
        return None
    except:
        return None

if 'popularity_tags' in df_filtered.columns:
    df_filtered['popularity_tags'] = df_filtered['popularity_tags'].apply(last_popularity_tag)

        
def clean_nutriments(cell):
    if pd.isnull(cell) or cell.strip() == '{}':
        return {}

    try:
        nutriments = ast.literal_eval(cell)
        if not isinstance(nutriments, dict):
            return {}

        cleaned = {}

        # Keep only keys ending with '_100g' and values > 0
        for k, v in nutriments.items():
            if k.endswith('_100g') and isinstance(v, (int, float)) and v > 0:
                cleaned[k] = v

        return cleaned

    except:
        return {}

if 'nutriments' in df_filtered.columns:
    df_filtered['nutriments'] = df_filtered['nutriments'].apply(clean_nutriments)

# Save new filtered and cleaned dataset
original_filename = 'openfoodfacts_spain_products_v2.csv'
new_filename = original_filename.replace('.csv', f'_threshold_{threshold}_cleaned.csv')
df_filtered.to_csv(new_filename, index=False)

print(f"File saved as: {new_filename}")
