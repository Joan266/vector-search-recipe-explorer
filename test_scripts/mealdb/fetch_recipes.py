import requests
import csv

def fetch_categories():
    print("Fetching categories...")
    url = "https://www.themealdb.com/api/json/v1/1/categories.php"
    response = requests.get(url)
    data = response.json()
    return [cat["strCategory"] for cat in data["categories"]]

def fetch_meals_by_category(category):
    url = f"https://www.themealdb.com/api/json/v1/1/filter.php?c={category}"
    response = requests.get(url)
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
            "ingredients_text": ", ".join(ingredients),
            "img_url": meal.get("strMealThumb", ""),
            "source": meal.get("strSource", "")
        }
    except Exception as e:
        print(f"Error fetching details for meal {meal_id}: {e}")
        return None
def fetch_mealdb(limit=2500):
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

def clean_data(data):
    """Filter out rows with empty elements or short instructions"""
    cleaned_data = []
    for row in data:
        # Check for any empty values in required fields
        required_fields = ['name', 'category', 'area', 'instructions', 'ingredients_text']
        if any(not row.get(field) for field in required_fields):
            continue
        
        # Check if instructions are too short (less than 20 characters)
        if len(row.get('instructions', '')) < 20:
            continue
            
        # Check if ingredients list is empty
        if not row.get('ingredients'):
            continue
            
        cleaned_data.append(row)
    
    print(f"Filtered {len(data) - len(cleaned_data)} invalid rows")
    return cleaned_data

def save_to_csv(data, filename="mealdb_recipes.csv"):
    if not data:
        print("No data to save!")
        return
        
    # Clean the data before saving
    cleaned_data = clean_data(data)
    
    with open(filename, "w", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(cleaned_data)
    print(f"Saved {len(cleaned_data)} cleaned rows to {filename}")

if __name__ == "__main__":
    recipes = fetch_mealdb(limit=2500)
    save_to_csv(recipes)