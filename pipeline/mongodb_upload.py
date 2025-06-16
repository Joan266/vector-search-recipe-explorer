from pymongo import MongoClient
from pymongo.errors import OperationFailure
from pymongo.operations import SearchIndexModel
from config import MONGODB_URI, DB_NAME, COLLECTION_NAME
import time

class MongoDBUploader:
    def __init__(self):
        self.client = MongoClient(MONGODB_URI)
        self.db = self.client[DB_NAME]
        self.collection = self.db[COLLECTION_NAME]
    
    def upload_recipes(self, recipes):
        """
        Upload recipes to MongoDB with proper indexing
        """
        try:
            # Clear existing data
            self.collection.drop()
            
            # Insert new data
            if isinstance(recipes, dict):
                recipes = [recipes]  # convert single recipe to list
            result = self.collection.insert_many(recipes)
            
            # Create standard indexes
            self._create_standard_indexes()
            
            return {
                "success": True,
                "inserted_count": len(result.inserted_ids)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _create_standard_indexes(self):
        """Create standard indexes for query performance"""
        self.collection.create_index("meal_id", unique=True)
        self.collection.create_index([("name", "text")])
        self.collection.create_index("category")
        self.collection.create_index("area")
        self.collection.create_index("ingredients")
        self.collection.create_index("health_score")
