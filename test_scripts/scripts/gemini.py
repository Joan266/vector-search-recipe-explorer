import google.generativeai as genai
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def list_available_models():
    """List all available Gemini models"""
    try:
        # Configure the API
        genai.configure(api_key=GEMINI_API_KEY)
        
        # List all available models
        print("🔍 Checking available models...")
        models = genai.list_models()
        
        if not models:
            print("❌ No models available")
            return
        
        print("\n✅ Available Models:")
        print("=" * 50)
        for i, model in enumerate(models, 1):
            print(f"{i}. {model.name}")
            print(f"   - Description: {model.description}")
            print(f"   - Supported Methods: {', '.join(method for method in model.supported_generation_methods)}")
            print("-" * 50)
            
        return models
        
    except Exception as e:
        print(f"❌ Error checking models: {str(e)}")
        return None

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("🚀 Gemini Model Checker")
    print("=" * 50)
    
    if not GEMINI_API_KEY:
        print("❌ Please set GEMINI_API_KEY in your .env file")
    else:
        list_available_models()