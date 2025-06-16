# config.py (Production Version)
import os
from google.cloud import secretmanager

client = secretmanager.SecretManagerServiceClient()

def get_secret(secret_id):
    secret_name = f"projects/{os.environ['GCP_PROJECT']}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(name=secret_name)
    return response.payload.data.decode('UTF-8')

# Required configurations
MONGODB_URI = get_secret("mongodb-uri")
DB_NAME = os.getenv("DB_NAME", "eco_footprint")  # Non-sensitive defaults
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "mealdb_recipes")
BUCKET_NAME = os.getenv("BUCKET_NAME", "recipe-audio-bucket")

# API Keys (moved to Secret Manager)
GCP_PROJECT = os.environ["GCP_PROJECT"]  # From app.yaml
GCP_REGION = os.environ.get("GCP_REGION", "us-central1")