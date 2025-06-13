import requests
import time
# ---------- 1. Get all category names ----------
def fetch_categories():
    print("Fetching categories...")
    url = "https://www.themealdb.com/api/json/v1/1/categories.php"
    response = requests.get(url)
    data = response.json()
    return [cat["strCategory"] for cat in data["categories"]]

# ---------- 2. Get all meal IDs from each category ----------
def fetch_meals_by_category(category):
    url = f"https://www.themealdb.com/api/json/v1/1/filter.php?c={category}"
    response = requests.get(url)
    data = response.json()
    meals = data.get("meals", [])
    return [meal["idMeal"] for meal in meals]

# ---------- 3. Fetch full meal details by ID ----------
def fetch_meal_details(meal_id):
    url = f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={meal_id}"
    response = requests.get(url)
    data = response.json()
    meal = data.get("meals", [None])[0]
    if not meal:
        return None

    ingredients = []
    for i in range(1, 21):
        ing = meal.get(f"strIngredient{i}")
        meas = meal.get(f"strMeasure{i}")
        if ing and ing.strip():
            ingredients.append(f"{meas.strip()} {ing.strip()}")

    return {
        "name": meal.get("strMeal"),
        "category": meal.get("strCategory"),
        "area": meal.get("strArea"),
        "instructions": meal.get("strInstructions"),
        "ingredients": ", ".join(ingredients),
        "img_url": meal.get("strMealThumb"),
        "youtube_url": meal.get("strYoutube"),
        "tags": meal.get("strTags"),
    }

# ---------- 4. Combine and Save ----------
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
                continue  # Avoid duplicates
            seen_ids.add(meal_id)

            meal_details = fetch_meal_details(meal_id)
            if meal_details:
                results.append(meal_details)

            if len(results) >= limit:
                return results
            time.sleep(0.2)

    return results
# Replace the pandas code at the bottom of mealdb_access_API.py with:

def main():
    mealdb_results = fetch_mealdb(limit=2500)
    
    import csv
    with open("mealdb_recipes.csv", "w", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=mealdb_results[0].keys())
        writer.writeheader()
        writer.writerows(mealdb_results)
    
    print(f"Saved {len(mealdb_results)} rows to mealdb_recipes.csv")

if __name__ == "__main__":
    main()
