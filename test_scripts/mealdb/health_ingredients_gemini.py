import os
import argparse
import logging
import json
import re
from typing import Dict, List
from dotenv import load_dotenv
import pymongo
from pymongo.collection import Collection
from pymongo.errors import PyMongoError
import google.generativeai as genai

# ---------- 1. Load environment variables ----------
load_dotenv()
MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME", "eco_footprint")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "mealdb_recipes")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('recipe_health_analyzer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("RecipeHealthAnalyzer")

class RecipeHealthAnalyzer:
    def __init__(self):
        print("\n" + "="*50)
        print("🚀 Initializing RecipeHealthAnalyzer...")
        self.collection = self._get_mongo_collection()
        
        # Initialize Gemini client
        genai.configure(api_key=GEMINI_API_KEY)
        self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        print("✅ HealthAnalyzer initialized with Gemini client")

    def _get_mongo_collection(self) -> Collection:
        """Connect to MongoDB collection with debug prints"""
        print(f"\n🔗 Connecting to MongoDB at {MONGODB_URI.split('@')[-1]}...")
        try:
            client = pymongo.MongoClient(MONGODB_URI)
            db = client[DB_NAME]
            collection = db[COLLECTION_NAME]
            print(f"✅ Connected to collection: {DB_NAME}.{COLLECTION_NAME}")
            print(f"📊 Total recipes: {collection.count_documents({})}")
            return collection
        except PyMongoError as e:
            print(f"❌ MongoDB connection failed: {str(e)}")
            raise

    def analyze_ingredients(self, ingredients: List[str]) -> Dict:
        """Analyze recipe ingredients and return health score and feedback"""
        print("\n🔍 Analyzing ingredients...")
        if not ingredients:
            print("⚠️ No ingredients found")
            return {
                "health_score": 0,
                "health_description": "No ingredients provided for analysis"
            }
            
        try:
            prompt = """You are a certified nutritionist and dietitian. Analyze these ingredients and provide:
1. A health score (1-5)
2. A professional health description (3-4 sentences)

Respond ONLY in this exact JSON format with no other text:
{
  "health_score": [1-5],
  "health_description": "Your analysis here"
}

Ingredients:\n""" + "\n".join([f"- {ingredient}" for ingredient in ingredients])
            
            print("  Sending to Gemini for analysis...")
            response = self.gemini_model.generate_content(prompt)
            
            # Handle different response formats
            if hasattr(response, 'text'):
                response_text = response.text
            elif hasattr(response, 'candidates') and response.candidates:
                response_text = response.candidates[0].content.parts[0].text
            else:
                raise ValueError("Unexpected response format from Gemini")
            
            print("  Raw response:", response_text[:200] + ("..." if len(response_text) > 200 else ""))
            
            # Parse the JSON response with improved error handling
            try:
                # Clean the response text first
                cleaned_text = re.sub(r'^```json|```$', '', response_text, flags=re.IGNORECASE).strip()
                health_data = json.loads(cleaned_text)
                
                # Validate the response structure
                if not all(key in health_data for key in ['health_score', 'health_description']):
                    raise ValueError("Response missing required fields")
                
                print("✅ Ingredients analysis successful")
                print(f"Health Score: {health_data['health_score']}")
                print(f"Health Description: {health_data['health_description'][:100]}...")
                
                return health_data
                
            except json.JSONDecodeError:
                print("❌ Error: Could not parse JSON response.")
                print(f"Raw response: {response_text[:200]}...")
                return {
                    "health_score": 0,
                    "health_description": "Analysis failed - invalid response format"
                }
            except KeyError as e:
                print(f"❌ Error: Missing key in JSON response: {e}")
                print(f"Raw response: {response_text[:200]}...")
                return {
                    "health_score": 0,
                    "health_description": f"Analysis failed - missing {e} in response"
                }
            except Exception as e:
                print(f"❌ Error parsing response: {str(e)}")
                print(f"Raw response: {response_text[:200]}...")
                return {
                    "health_score": 0,
                    "health_description": f"Analysis failed - {str(e)}"
                }
                
        except Exception as e:
            print(f"❌ Ingredients analysis failed: {str(e)}")
            return {
                "health_score": 0,
                "health_description": f"Analysis failed - {str(e)}"
            }

    def process_recipe(self, recipe: Dict) -> bool:
        """Process a single recipe document to analyze its ingredients"""
        print("\n" + "="*50)
        print(f"🍳 Processing recipe: {recipe.get('name', 'Unnamed')}")
        
        recipe_id = str(recipe.get("_id", ""))
        if not recipe_id:
            print("❌ Recipe missing ID, skipping")
            return False
            
        print(f"📌 Recipe ID: {recipe_id}")
        
        # Skip if already processed
        if recipe.get("health_analysis"):
            print("⏩ Already has health analysis, skipping")
            return False
            
        if "ingredients" not in recipe or not recipe["ingredients"]:
            print("❌ No ingredients found, skipping")
            return False
            
        try:
            ingredients = recipe["ingredients"]
            print(f"\n📜 Ingredients list ({len(ingredients)} items):")
            for i, ing in enumerate(ingredients[:5], 1):
                print(f"  {i}. {ing[:60]}{'...' if len(ing)>60 else ''}")
            if len(ingredients) > 5:
                print(f"  (...and {len(ingredients)-5} more ingredients)")
            
            analysis = self.analyze_ingredients(ingredients)
            
            print(f"\n💾 Updating MongoDB document with health analysis...")
            result = self.collection.update_one(
                {"_id": recipe["_id"]},
                {"$set": {
                    "health_analysis": analysis
                }}
            )
            print(f"✅ Updated recipe with health analysis")
            return result.modified_count > 0
                
        except Exception as e:
            print(f"🔥 Processing failed: {str(e)}")
            return False

    def run(self, test_mode: bool = False, limit: int = None):
        """Run the processing pipeline"""
        print("\n" + "="*50)
        print(f"🚀 Starting health analysis pipeline (test_mode={test_mode}, limit={limit})")
        
        try:
            query = {"ingredients": {"$exists": True}, "health_analysis": {"$exists": False}}
            print(f"🔍 MongoDB query: {query}")
            
            if test_mode:
                print("\n🧪 TEST MODE: Processing one random recipe")
                recipe = self.collection.aggregate([
                    {"$match": query},
                    {"$sample": {"size": 1}}
                ]).next()
                self.process_recipe(recipe)
            else:
                print("\n🔎 Finding recipes to process...")
                cursor = self.collection.find(query)
                if limit:
                    cursor.limit(limit)
                    print(f"  Limiting to {limit} recipes")
                    
                processed_count = 0
                total_to_process = self.collection.count_documents(query)
                if limit and limit < total_to_process:
                    total_to_process = limit
                
                print(f"📊 Found {total_to_process} recipes to analyze")
                
                for i, recipe in enumerate(cursor, 1):
                    print(f"\n📦 Processing recipe {i}/{total_to_process}")
                    if self.process_recipe(recipe):
                        processed_count += 1
                
                print("\n" + "="*50)
                print(f"🎉 Pipeline complete! Analyzed {processed_count}/{total_to_process} recipes")
        except Exception as e:
            print("\n" + "="*50)
            print(f"❌ Pipeline failed: {str(e)}")
            raise

def main():
    parser = argparse.ArgumentParser(description="Recipe Health Analysis Pipeline")
    parser.add_argument("--test", action="store_true", help="Test mode (processes one recipe)")
    parser.add_argument("--limit", type=int, help="Limit number of recipes to process")
    args = parser.parse_args()
    
    try:
        print("\n" + "="*50)
        print("🔧 Recipe Health Analysis Pipeline - Starting Up")
        print("="*50)
        
        # Verify environment variables
        required_vars = ["MONGODB_URI", "GEMINI_API_KEY"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
            return
        
        analyzer = RecipeHealthAnalyzer()
        analyzer.run(test_mode=args.test, limit=args.limit)
    except Exception as e:
        print("\n" + "="*50)
        print(f"💥 Critical error: {str(e)}")
        logger.critical(f"Pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()