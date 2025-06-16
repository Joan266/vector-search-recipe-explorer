import json
import re
from typing import Dict, List, Optional
import google.generativeai as genai
from config import GEMINI_API_KEY

class TimeAnalyzer:
    def __init__(self):
        print("\n" + "="*50)
        print("🚀 Initializing TimeAnalyzer...")
        
        # Initialize Gemini client
        genai.configure(api_key=GEMINI_API_KEY)
        self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        print("✅ TimeAnalyzer initialized with Gemini client")

    def analyze_instructions(self, instructions: str) -> Optional[Dict]:
        """Analyze recipe instructions for time and difficulty"""
        if not instructions:
            print("⚠️ No instructions provided")
            return None

        prompt = """You are an AI assistant specialized in analyzing recipe instructions to estimate cooking times and assess recipe difficulty. 

        **Input:** Recipe instructions
        **Output Requirements:** JSON format with:
        - total_estimated_time_minutes (number)
        - recipe_difficulty ("Very Easy"/"Easy"/"Medium"/"Hard"/"Very Hard")

        Example Output:
        ```json
        {
          "total_estimated_time_minutes": 80,
          "recipe_difficulty": "Easy",
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
                cleaned_text = re.sub(r'^```json|```$', '', response_text, flags=re.IGNORECASE).strip()
                analysis = json.loads(cleaned_text)
                
                # Validate required fields
                required_fields = [
                    'total_estimated_time_minutes',
                    'recipe_difficulty',
                ]
                
                if not all(field in analysis for field in required_fields):
                    missing = [f for f in required_fields if f not in analysis]
                    raise ValueError(f"Missing required fields: {missing}")
                
                print("✅ Analysis successful")
                print(f"Total Time: {analysis.get('total_estimated_time_minutes')} minutes")
                print(f"Difficulty: {analysis.get('recipe_difficulty')}")
                
                return analysis
                
            except (json.JSONDecodeError, KeyError) as e:
                print(f"❌ Error parsing response: {str(e)}")
                return None
                
        except Exception as e:
            print(f"❌ Analysis failed: {str(e)}")
            return None

    def analyze_recipes(self, recipes: List[Dict]) -> List[Dict]:
        """Analyze a list of recipes and add time data"""
        analyzed_recipes = []
        total = len(recipes)
        
        for i, recipe in enumerate(recipes, 1):
            print(f"\n🍳 Processing recipe {i}/{total}: {recipe.get('name', 'Unnamed')}")
            
            if not recipe.get('instructions'):
                print("❌ No instructions found, skipping")
                continue
                
            time_data = self.analyze_instructions(recipe['instructions'])
            if time_data:
                recipe['time_analysis'] = time_data
                analyzed_recipes.append(recipe)
            
        return analyzed_recipes