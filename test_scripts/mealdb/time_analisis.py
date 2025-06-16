import os
import re
import json
import argparse
import logging
from typing import Dict, List, Optional
from dotenv import load_dotenv
import pymongo
from pymongo.collection import Collection
from pymongo.errors import PyMongoError
import google.generativeai as genai

# Load environment variables
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
        logging.FileHandler('recipe_time_analyzer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("RecipeTimeAnalyzer")

class RecipeTimeAnalyzer:
    def __init__(self):
        print("\n" + "="*50)
        print("🚀 Initializing RecipeTimeAnalyzer...")
        self.collection = self._get_mongo_collection()
        
        # Initialize Gemini client
        genai.configure(api_key=GEMINI_API_KEY)
        self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        print("✅ TimeAnalyzer initialized with Gemini client")

    def _get_mongo_collection(self) -> Collection:
        """Connect to MongoDB collection"""
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

    def analyze_instructions(self, instructions: str) -> Optional[Dict]:
        """Analyze recipe instructions for time and difficulty"""
        if not instructions:
            print("⚠️ No instructions provided")
            return None

        prompt = """You are an AI assistant specialized in analyzing recipe instructions to estimate cooking times and assess recipe difficulty. 

        **Input:** Recipe instructions
        **Output Requirements:** JSON format with:
        - active_cooking_time_minutes (number or "Not specified")
        - passive_time_minutes (number or "Not specified")
        - total_estimated_time_minutes (number)
        - confidence_level ("High"/"Medium"/"Low")
        - recipe_difficulty ("Very Easy"/"Easy"/"Medium"/"Hard"/"Very Hard")
        - difficulty_justification (1-2 sentences)
        - notes_assumptions (list of strings)

        Example Output:
        ```json
        {
          "active_cooking_time_minutes": 15,
          "passive_time_minutes": 65,
          "total_estimated_time_minutes": 80,
          "confidence_level": "Medium",
          "recipe_difficulty": "Easy",
          "difficulty_justification": "Simple steps with basic techniques and common ingredients.",
          "notes_assumptions": [
            "Assumed basic prep time for chopping",
            "Baking time taken as average"
          ]
        }
        ```

        Analyze these instructions:
        """ + instructions

        try:
            print("\n🔍 Analyzing instructions...")
            response = self.gemini_model.generate_content(prompt)
            
            # Handle different response formats
            if hasattr(response, 'text'):
                response_text = response.text
            elif hasattr(response, 'candidates') and response.candidates:
                response_text = response.candidates[0].content.parts[0].text
            else:
                raise ValueError("Unexpected response format from Gemini")

            # Clean and parse the JSON response
            try:
                # Remove markdown code blocks if present
                cleaned_text = re.sub(r'^```json|```$', '', response_text, flags=re.IGNORECASE).strip()
                analysis = json.loads(cleaned_text)
                
                # Validate required fields
                required_fields = [
                    'active_cooking_time_minutes',
                    'passive_time_minutes',
                    'total_estimated_time_minutes',
                    'confidence_level',
                    'recipe_difficulty',
                    'difficulty_justification',
                    'notes_assumptions'
                ]
                
                if not all(field in analysis for field in required_fields):
                    missing = [f for f in required_fields if f not in analysis]
                    raise ValueError(f"Missing required fields: {missing}")
                
                print("✅ Analysis successful")
                print(f"Total Time: {analysis.get('total_estimated_time_minutes')} minutes")
                print(f"Difficulty: {analysis.get('recipe_difficulty')}")
                
                return analysis
                
            except json.JSONDecodeError:
                print("❌ Error: Could not parse JSON response.")
                print(f"Raw response: {response_text[:200]}...")
                return None
            except KeyError as e:
                print(f"❌ Error: Missing key in JSON response: {e}")
                print(f"Raw response: {response_text[:200]}...")
                return None
                
        except Exception as e:
            print(f"❌ Analysis failed: {str(e)}")
            return None

    def process_recipe(self, recipe: Dict) -> bool:
        """Process a single recipe document"""
        print("\n" + "="*50)
        print(f"🍳 Processing recipe: {recipe.get('name', 'Unnamed')}")
        
        recipe_id = str(recipe.get("_id", ""))
        if not recipe_id:
            print("❌ Recipe missing ID, skipping")
            return False
            
        print(f"📌 Recipe ID: {recipe_id}")
        
        # Skip if already processed
        if recipe.get("time_analysis"):
            print("⏩ Already has time analysis, skipping")
            return False
            
        if "instructions" not in recipe or not recipe["instructions"]:
            print("❌ No instructions found, skipping")
            return False
            
        try:
            instructions = recipe["instructions"]
            print(f"\n📜 Instructions length: {len(instructions)} chars")
            
            analysis = self.analyze_instructions(instructions)
            if not analysis:
                print("⚠️ No analysis generated, skipping")
                return False
            
            print(f"\n💾 Updating MongoDB document with time analysis...")
            result = self.collection.update_one(
                {"_id": recipe["_id"]},
                {"$set": {
                    "time_analysis": analysis
                }}
            )
            print(f"✅ Updated recipe with time analysis")
            return result.modified_count > 0
                
        except Exception as e:
            print(f"🔥 Processing failed: {str(e)}")
            return False

    def run(self, test_mode: bool = False, limit: int = None):
        """Run the processing pipeline"""
        print("\n" + "="*50)
        print(f"🚀 Starting time analysis pipeline (test_mode={test_mode}, limit={limit})")
        
        try:
            query = {"instructions": {"$exists": True}, "time_analysis": {"$exists": False}}
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
    parser = argparse.ArgumentParser(description="Recipe Time Analysis Pipeline")
    parser.add_argument("--test", action="store_true", help="Test mode (processes one recipe)")
    parser.add_argument("--limit", type=int, help="Limit number of recipes to process")
    args = parser.parse_args()
    
    try:
        print("\n" + "="*50)
        print("🔧 Recipe Time Analysis Pipeline - Starting Up")
        print("="*50)
        
        # Verify environment variables
        required_vars = ["MONGODB_URI", "GEMINI_API_KEY"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
            return
        
        analyzer = RecipeTimeAnalyzer()
        analyzer.run(test_mode=args.test, limit=args.limit)
    except Exception as e:
        print("\n" + "="*50)
        print(f"💥 Critical error: {str(e)}")
        logger.critical(f"Pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()