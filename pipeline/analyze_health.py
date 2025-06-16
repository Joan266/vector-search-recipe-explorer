import json
import re
from typing import Dict, List
import google.generativeai as genai
from config import GEMINI_API_KEY

class HealthAnalyzer:
    def __init__(self):
        print("\n" + "="*50)
        print("🚀 Initializing HealthAnalyzer...")
        
        # Initialize Gemini client
        genai.configure(api_key=GEMINI_API_KEY)
        self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        print("✅ HealthAnalyzer initialized with Gemini client")

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
            
            # Parse the JSON response
            try:
                cleaned_text = re.sub(r'^```json|```$', '', response_text, flags=re.IGNORECASE).strip()
                health_data = json.loads(cleaned_text)
                
                if not all(key in health_data for key in ['health_score', 'health_description']):
                    raise ValueError("Response missing required fields")
                
                print("✅ Ingredients analysis successful")
                print(f"Health Score: {health_data['health_score']}")
                print(f"Health Description: {health_data['health_description'][:100]}...")
                
                return health_data
                
            except (json.JSONDecodeError, KeyError) as e:
                print(f"❌ Error parsing response: {str(e)}")
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

    def analyze_recipes(self, recipes: List[Dict]) -> List[Dict]:
        """Analyze a list of recipes and add health data"""
        analyzed_recipes = []
        total = len(recipes)
        
        for i, recipe in enumerate(recipes, 1):
            print(f"\n🍳 Processing recipe {i}/{total}: {recipe.get('name', 'Unnamed')}")
            
            if not recipe.get('ingredients'):
                print("❌ No ingredients found, skipping")
                continue
                
            health_data = self.analyze_ingredients(recipe['ingredients'])
            recipe['health_score'] = health_data.get("health_score", 0)
            recipe['health_description'] = health_data.get("health_description", 'Analysis failed')
            analyzed_recipes.append(recipe)
            
        return analyzed_recipes