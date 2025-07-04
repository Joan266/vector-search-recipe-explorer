# config.py (Development Version)
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_required_env(key: str, default=None):
    """Get required environment variable or raise error if missing"""
    value = os.getenv(key, default)
    if value is None:
        raise ValueError(f"Required environment variable '{key}' is not set. Please check your .env file.")
    return value

# Required configurations
MONGODB_URI = get_required_env("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME", "eco_footprint")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "mealdb_recipes")
BUCKET_NAME = os.getenv("BUCKET_NAME", "recipe-audio-bucket")

# API Keys
GCP_PROJECT = get_required_env("GCP_PROJECT")
GCP_REGION = os.getenv("GCP_REGION", "us-central1")
GEMINI_API_KEY = get_required_env("GEMINI_API_KEY")

# Flask Configuration
FLASK_ENV = os.getenv("FLASK_ENV", "development")
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")

# Google Cloud Authentication
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if GOOGLE_APPLICATION_CREDENTIALS:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_APPLICATION_CREDENTIALS

print("✅ Configuration loaded successfully")
print(f"📊 Database: {DB_NAME}.{COLLECTION_NAME}")
print(f"🌍 GCP Project: {GCP_PROJECT} ({GCP_REGION})")
print(f"🔧 Environment: {FLASK_ENV}")