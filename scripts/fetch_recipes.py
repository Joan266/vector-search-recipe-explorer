import requests
import time
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
    response = requests.get(url)
    data = response.json()
    meal = data.get("meals", [None])[0]
    if not meal:
        return None

    ingredients = []
    measures = []
    combined_ingredients = []
    
    for i in range(1, 21):
        ing = meal.get(f"strIngredient{i}")
        meas = meal.get(f"strMeasure{i}")
        
        if not ing or str(ing).strip() == "":
            continue
            
        ing = str(ing).strip()
        meas = str(meas).strip() if meas else ""
        
        ingredients.append(ing)
        measures.append(meas)
        combined_ingredients.append(f"{meas} {ing}" if meas else ing)

    return {
        "idMeal": meal_id,
        "name": meal.get("strMeal"),
        "category": meal.get("strCategory"),
        "area": meal.get("strArea"),
        "instructions": meal.get("strInstructions"),
        "ingredients": ingredients,
        "measures": measures,
        "combined_ingredients": ", ".join(combined_ingredients),
        "img_url": meal.get("strMealThumb"),
        "tags": meal.get("strTags"),
        "youtube": meal.get("strYoutube"),
    }

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
            time.sleep(0.2)

    return results

def save_to_csv(data, filename="mealdb_recipes.csv"):
    with open(filename, "w", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    print(f"Saved {len(data)} rows to {filename}")

if __name__ == "__main__":
    recipes = fetch_mealdb(limit=2500)
    save_to_csv(recipes)