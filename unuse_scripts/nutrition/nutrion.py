import pandas as pd

# Read the original CSV
df = pd.read_csv("openfoodfacts_nutrition.csv")

# Select only the 'nutriments' column
nutriments_df = df[['nutriments']]

# Save to a new CSV
nutriments_df.to_csv("nutriments_only.csv", index=False)
