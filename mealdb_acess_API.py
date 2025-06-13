import requests

def get_mealdb_sample():
    url = "https://www.themealdb.com/api/json/v1/1/search.php?s=chicken"
    response = requests.get(url)
    data = response.json()

    for meal in data.get('meals', [])[:3]:
        print(f"Meal Name: {meal['strMeal']}")
        print(f"Category: {meal['strCategory']}")
        print(f"Area: {meal['strArea']}")
        print("Ingredients:")
        for i in range(1, 21):
            ingredient = meal.get(f'strIngredient{i}')
            measure = meal.get(f'strMeasure{i}')
            if ingredient:
                print(f"  - {ingredient}: {measure}")
        print("Instructions:", meal['strInstructions'][:200], "...\n")

get_mealdb_sample()
