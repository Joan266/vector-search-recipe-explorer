import pandas as pd
import ast
import re

def load_csv(filename="mealdb_recipes.csv"):
    df = pd.read_csv(filename)
    
    # Convert string representations of lists back to actual lists
    df['ingredients'] = df['ingredients'].apply(ast.literal_eval)
    df['measures'] = df['measures'].apply(ast.literal_eval)
    
    return df

def split_instructions(text):
    """Split instructions into sentences, handling numbered steps and \r\n newlines"""
    if pd.isna(text) or not text.strip():
        return []
    
    # Normalize line endings and clean up text
    text = text.replace('\r\n', '\n').strip()
    
    # Check if text uses numbered steps (e.g., "1. Prepare...", "2. Sear...")
    if re.search(r'^\d+\.\s+', text, re.MULTILINE):
        # Split on numbered steps
        steps = re.split(r'\n\s*\d+\.\s+', text)
        # The first element might be empty or intro text
        if steps and not steps[0].strip():
            steps = steps[1:]
        return [step.strip() for step in steps if step.strip()]
    else:
        # Regular sentence splitting
        sentences = re.split(r'\.\s+(?=[A-Z])|\n+', text)
        return [s.strip() + ('.' if not s.endswith('.') else '') 
                for s in sentences if s.strip()]
def extract_units(measure):
    """Extract and standardize just the units from measures"""
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
        'doz': 'dozen',
        'cup': 'cup',
        'cups': 'cup',
        'pinch': 'pinch',
        'handful': 'handful'
    }
    
    # Standardize units
    for short, long in unit_replacements.items():
        if short in unit.lower():
            return long
    
    return unit if unit else "unit"

def standardize_measures(measures):
    """Apply extract_units to each measure in a list"""
    return [extract_units(measure) for measure in measures]

def analyze_data(df):
    # 1. Add instruction sentences as a new column
    df['instruction_sentences'] = df['instructions'].apply(split_instructions)
    
    # 2. Standardize measures in place (modify the measures column)
    df['standardized_measures'] = df['measures'].apply(
        lambda x: [extract_units(measure) for measure in x]
    )
    
    return df

if __name__ == "__main__":
    # Load and transform the data
    recipe_df = load_csv()
    analyzed_df = analyze_data(recipe_df)
    
    # Save the enhanced DataFrame
    analyzed_df.to_csv("enhanced_recipes.csv", index=False)
    print("Saved enhanced data to enhanced_recipes.csv")
    
    # Show sample of the enhanced data
    print("\nSample of enhanced data:")
    print(analyzed_df[['name', 'instruction_sentences', 'ingredients', 'standardized_measures']].head(3))