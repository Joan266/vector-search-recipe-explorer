import csv
import json
import time
import re
from typing import List, Dict, Optional
from pathlib import Path
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# ---------- LOAD ENV ----------
dotenv_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=dotenv_path)

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "mealdb_recipes")

# ---------- Data Processing Functions ----------

def read_csv_to_dicts(filename: str) -> List[Dict]:
    """Read CSV file and return list of dictionaries"""
    with open(filename, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))

# ---------- MongoDB Functions ----------

def upload_to_mongodb(recipes: List[Dict], clear_existing: bool = True):
    """Upload recipes to MongoDB with proper indexing"""
    client = MongoClient(MONGODB_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    
    if clear_existing:
        collection.drop()
    
    try:
        # Insert in batches for better performance
        batch_size = 100
        inserted_count = 0
        for i in range(0, len(recipes), batch_size):
            batch = recipes[i:i + batch_size]
            result = collection.insert_many(batch)
            inserted_count += len(result.inserted_ids)
            print(f"Inserted batch {i//batch_size + 1}: {len(result.inserted_ids)} documents")
        
        print(f"✅ Total inserted: {inserted_count} documents")
        
        # Create indexes
        create_indexes(collection)
        
    except Exception as e:
        print(f"❌ Insert failed: {str(e)}")
        raise

def create_indexes(collection):
    """Create optimized indexes for querying"""
    print("🔨 Creating indexes...")
    collection.create_index("meal_id", unique=True)
    collection.create_index([("name", "text")])
    collection.create_index("category")
    collection.create_index("area")
    collection.create_index([("ingredients_text", "text")])
    collection.create_index("tags")
    collection.create_index([("instructions", "text")])
    print("✅ Indexes created")

# ---------- Main Pipeline ----------

def process_and_upload(csv_path: str = "mealdb_recipes.csv"):
    """Full processing and upload pipeline"""
    print("📖 Reading CSV file...")
    recipes = read_csv_to_dicts(csv_path)
    
    print("📦 Uploading to MongoDB...")
    upload_to_mongodb(recipes)
    
    print("🚀 All done!")

if __name__ == "__main__":
    process_and_upload()