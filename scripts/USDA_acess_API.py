import requests
from dotenv import load_dotenv
import os
# ---------- 1. Cargar variables de entorno ----------
load_dotenv()
API_KEY = os.getenv("USDA_API_KEY")

def search_fooddata(query="chicken"):
    url = f"https://api.nal.usda.gov/fdc/v1/foods/search?query={query}&api_key={API_KEY}"
    response = requests.get(url)
    data = response.json()

    for item in data.get('foods', [])[:3]:
        print(f"Description: {item['description']}")
        print(f"FDC ID: {item['fdcId']}")
        print(f"Food Category: {item.get('foodCategory')}")
        print(f"Nutrients: {item.get('foodNutrients', [])[:3]}")
        print()

search_fooddata()
