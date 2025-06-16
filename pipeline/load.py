# pipeline/load.py
import csv
from pipeline.transform import clean_data

def save_to_csv(data, filename="mealdb_recipes.csv"):
    if not data:
        print("No data to save!")
        return
        
    # Clean the data before saving
    cleaned_data = clean_data(data)
    
    with open(filename, "w", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(cleaned_data)
    print(f"Saved {len(cleaned_data)} cleaned rows to {filename}")
    