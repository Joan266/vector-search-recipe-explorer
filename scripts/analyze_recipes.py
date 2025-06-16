import pandas as pd
import ast
import re
from collections import Counter

def load_csv(filename="mealdb_recipes.csv"):
    df = pd.read_csv(filename)
    
    # Convert string representations of lists back to actual lists
    df['ingredients'] = df['ingredients'].apply(ast.literal_eval)
    df['measures'] = df['measures'].apply(ast.literal_eval)
    
    return df

def split_instructions(text):
    """Split instructions into sentences"""
    if pd.isna(text):
        return []
    
    # Split on periods followed by whitespace and capital letter
    sentences = re.split(r'\.\s+(?=[A-Z])', text)
    
    # Clean up sentences
    sentences = [s.strip() + '.' for s in sentences if s.strip()]
    
    # Handle special cases (numbered steps)
    if any(sentence[0].isdigit() for sentence in sentences):
        # If instructions are numbered steps, split on numbers
        sentences = re.split(r'\d+\.\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
    
    return sentences

def extract_units(measure):
    """Extract just the units from measures"""
    if not measure or pd.isna(measure):
        return ""
    
    # Remove numbers and special characters
    unit = re.sub(r'[\d½¼¾⅓⅔⅛⅜⅝⅞\/\.-]+', '', str(measure)).strip()
    
    # Common unit replacements
    unit_replacements = {
        'tbs': 'tablespoon',
        'tbsp': 'tablespoon',
        'tsp': 'teaspoon',
        'tb': 'tablespoon',
        'oz': 'ounce',
        'lb': 'pound',
        'ml': 'milliliter',
        'cl': 'centiliter',
        'l': 'liter',
        'g': 'gram',
        'kg': 'kilogram',
        'dl': 'deciliter',
        'pt': 'pint',
        'qt': 'quart',
        'gal': 'gallon',
        'doz': 'dozen'
    }
    
    # Standardize units
    for short, long in unit_replacements.items():
        if short in unit.lower():
            return long
    
    return unit if unit else "unit"

def analyze_data(df):
    # 1. Analyze Instructions
    print("\n=== INSTRUCTIONS ANALYSIS ===")
    df['instruction_sentences'] = df['instructions'].apply(split_instructions)
    
    # Count total sentences
    all_sentences = [sentence for sublist in df['instruction_sentences'] for sentence in sublist]
    print(f"\nTotal sentences across all recipes: {len(all_sentences)}")
    
    # Show sample of sentences
    print("\nSample sentences from instructions:")
    for i, sentence in enumerate(all_sentences[:10], 1):
        print(f"{i}. {sentence}")
    
    # 2. Analyze Ingredients
    print("\n=== INGREDIENTS ANALYSIS ===")
    all_ingredients = [ing for sublist in df['ingredients'] for ing in sublist]
    unique_ingredients = Counter(all_ingredients)
    
    print(f"\nTotal unique ingredients: {len(unique_ingredients)}")
    print("\nTop 20 most common ingredients:")
    for ingredient, count in unique_ingredients.most_common(20):
        print(f"{ingredient}: {count}")
    
    # 3. Analyze Measures (Units)
    print("\n=== MEASURES/UNITS ANALYSIS ===")
    all_measures = [measure for sublist in df['measures'] for measure in sublist]
    all_units = [extract_units(measure) for measure in all_measures]
    unique_units = Counter(all_units)
    
    print(f"\nTotal unique units: {len(unique_units)}")
    print("\nAll units and their counts:")
    for unit, count in unique_units.most_common():
        print(f"{unit}: {count}")
    
    # Return the transformed data for further use
    return {
        'instruction_sentences': df['instruction_sentences'].tolist(),
        'ingredients_list': df['ingredients'].tolist(),
        'units_list': all_units,
        'unique_ingredients': unique_ingredients,
        'unique_units': unique_units
    }

if __name__ == "__main__":
    recipe_df = load_csv()
    analysis_results = analyze_data(recipe_df)
    
    # You can access the results like:
    # analysis_results['unique_ingredients'] - Counter object of all ingredients
    # analysis_results['unique_units'] - Counter object of all units
    # analysis_results['instruction_sentences'] - List of split instructions