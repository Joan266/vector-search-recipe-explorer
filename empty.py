import pandas as pd
import ast

# Load your CSV file
df = pd.read_csv("cleaned_output.csv")

# Remove the 'schema_version' column if it exists
if 'schema_version' in df.columns:
    df = df.drop(columns=['schema_version'])

# Function to evaluate if a field is empty
def is_empty(val):
    if pd.isna(val):  # Handles NaN
        return True
    try:
        val_eval = ast.literal_eval(val) if isinstance(val, str) else val
    except:
        val_eval = val
    return val_eval in ("", [], {}, None)

# Create boolean mask of empty values
empty_mask = df.applymap(is_empty)

# Drop rows with any empty values
df_cleaned = df[~empty_mask.any(axis=1)].copy()

# Calculate percentage of empties per column in the cleaned DataFrame (should be zero now)
empty_percentages = df_cleaned.applymap(is_empty).sum() / len(df_cleaned) * 100

print(f"Original dataset rows: {len(df)}")
print(f"Rows after dropping empty rows: {len(df_cleaned)}\n")

print("Percentage of empty/null values per column after cleaning:")
print(empty_percentages.sort_values(ascending=False))
