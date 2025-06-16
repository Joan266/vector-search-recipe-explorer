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
        
        # Skip if ingredient is empty, None, or just whitespace
        if not ing or str(ing).strip() == "":
            continue
            
        # Clean the values
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
        "ingredients": ingredients,  # List of just ingredients
        "measures": measures,       # List of just measures
        "combined_ingredients": ", ".join(combined_ingredients),
        "img_url": meal.get("strMealThumb"),
        "tags": meal.get("strTags"),
        "youtube": meal.get("strYoutube"),
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

def main():
    mealdb_results = fetch_mealdb(limit=2500)
    
    # Save to CSV
    import csv
    with open("mealdb_recipes.csv", "w", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=mealdb_results[0].keys())
        writer.writeheader()
        writer.writerows(mealdb_results)
    
    print(f"Saved {len(mealdb_results)} rows to mealdb_recipes.csv")
    
    # For pandas analysis
    import pandas as pd
    df = pd.DataFrame(mealdb_results)
    
    # Analyze measures (units)
    all_measures = [measure for sublist in df['measures'] for measure in sublist]
    unique_measures = pd.Series(all_measures).value_counts()
    print("\nUnique measures/units:")
    print(unique_measures.head(20))  # Show top 20
    
    # Analyze ingredients
    all_ingredients = [ing for sublist in df['ingredients'] for ing in sublist]
    unique_ingredients = pd.Series(all_ingredients).value_counts()
    print("\nTop 20 most common ingredients:")
    print(unique_ingredients.head(20))

if __name__ == "__main__":
    main()