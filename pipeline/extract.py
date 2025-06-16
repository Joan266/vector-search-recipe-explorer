# pipeline/extract.py
import requests
import csv
from typing import List, Dict, Optional

def fetch_categories() -> List[str]:
    print("Fetching categories...")
    url = "https://www.themealdb.com/api/json/v1/1/categories.php"
    response = requests.get(url)
    response.raise_for_status()  
    data = response.json()
    return [cat["strCategory"] for cat in data["categories"]]

def fetch_meals_by_category(category: str) -> List[str]:
    url = f"https://www.themealdb.com/api/json/v1/1/filter.php?c={category}"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    meals = data.get("meals", [])
    return [meal["idMeal"] for meal in meals]

def fetch_meal_details(meal_id):
    url = f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={meal_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Handle case where meal doesn't exist
        if not data.get("meals"):
            return None
            
        meal = data["meals"][0]
        
        # Process ingredients - handle both empty strings and null values
        ingredients = []
        for i in range(1, 21):
            # Handle both None and empty string cases
            ing = meal.get(f"strIngredient{i}")
            ing = str(ing).strip() if ing is not None else ""
            
            meas = meal.get(f"strMeasure{i}")
            meas = str(meas).strip() if meas is not None else ""
            
            if ing:  # Only add if ingredient exists
                ingredients.append(f"{meas} {ing}".strip() if meas else ing)

        # Clean instructions - remove excessive whitespace and newlines
        instructions = meal.get("strInstructions", "")
        if instructions:
            instructions = " ".join(instructions.split())
        
        # Handle tags - some are None, some are empty strings
        tags = meal.get("strTags")
        if tags:
            tags = [tag.strip() for tag in tags.split(",") if tag.strip()]
        else:
            tags = []

        return {
            "meal_id": meal_id,
            "name": meal.get("strMeal", ""),
            "category": meal.get("strCategory", ""),
            "area": meal.get("strArea", ""),
            "instructions": instructions,
            "ingredients": ingredients,
            "img_url": meal.get("strMealThumb", ""),
            "source": meal.get("strSource", "")
        }
    except Exception as e:
        print(f"Error fetching details for meal {meal_id}: {e}")
        return None
def fetch_mealdb(limit: int = 2500) -> List[Dict]:
    print("Fetching from TheMealDB by category...")
    results = []
    seen_ids = set()
    categories = fetch_categories()

    for category in categories:
        print(f"Processing category: {category}")
        meal_ids = fetch_meals_by_category(category)
        for meal_id in meal_ids:
            if meal_id in seen_ids:
                continue
            seen_ids.add(meal_id)

            meal_details = fetch_meal_details(meal_id)
            if meal_details:
                results.append(meal_details)

            if len(results) >= limit:
                return results

    return results

