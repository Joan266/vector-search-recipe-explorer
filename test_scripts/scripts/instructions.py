import pandas as pd
import re

def load_csv(filename="mealdb_recipes.csv"):
    df = pd.read_csv(filename)
    return df

def split_instructions(text):
    # Pattern explanation:
    # [A-Z][a-z]+ - Starts with capitalized word (only first letter uppercase)
    # .*? - Any characters (non-greedy)
    # \s\w+\. - Ends with space + word + dot
    # (?=\s|$) - Followed by either a space or end of string (positive lookahead)
    pattern = re.compile(r'([A-Z][a-z]+.*?\s\w+[.!](?=\s|$))')
    
    # Find all matches of the pattern
    sentences = pattern.findall(text)
    
    # Clean up sentences (remove leading/trailing whitespace)
    cleaned_sentences = [s.strip() for s in sentences if s.strip()]
    
    return cleaned_sentences

def process_instructions(df):
    # Add cleaned instruction sentences
    df['instruction_sentences'] = df['instructions'].apply(split_instructions)
    
    # Remove any empty strings that might have been created
    df['instruction_sentences'] = df['instruction_sentences'].apply(
        lambda x: [s for s in x if s.strip() and not s.isdigit()]
    )
    
    # Calculate length metrics
    df['original_length'] = df['instructions'].str.len()
    df['processed_length'] = df['instruction_sentences'].apply(lambda x: len(' '.join(x)))
    df['length_diff'] = df['original_length'] - df['processed_length']
    df['diff_percentage'] = (df['length_diff'] / df['original_length']) * 100
    
    return df

if __name__ == "__main__":
    # Load and process data
    recipe_df = load_csv()
    processed_df = process_instructions(recipe_df)
    
    # Create DataFrames for each output
    text_df = processed_df[['idMeal', 'instructions']]
    sentences_df = processed_df[['idMeal', 'instruction_sentences']]
    
    # Identify suspicious cases where significant text might have been lost
    # Using threshold of 20% difference or absolute difference of 100 characters
    threshold_percentage = 20
    threshold_absolute = 100
    suspicious_cases = processed_df[
        (processed_df['diff_percentage'] > threshold_percentage) | 
        (processed_df['length_diff'] > threshold_absolute)
    ]
    
    # Save to separate CSV files
    text_df.to_csv("instructions_text.csv", index=False)
    sentences_df.to_csv("instructions_sentences.csv", index=False)
    suspicious_cases[['idMeal', 'instructions', 'instruction_sentences']].to_csv("suspicious_cases.csv", index=False)
    
    print("Saved three files:")
    print("- instructions_text.csv (original text instructions)")
    print("- instructions_sentences.csv (processed sentences)")
    print(f"- suspicious_cases.csv ({len(suspicious_cases)} cases with significant differences)")
    
    # Show samples
    print("\nSample text instructions:")
    print(text_df.head(3).to_string())
    
    print("\nSample processed sentences:")
    print(sentences_df.head(3).to_string())
    
    if not suspicious_cases.empty:
        print("\nSample suspicious cases:")
        print(suspicious_cases[['idMeal', 'original_length', 'processed_length', 
                               'length_diff', 'diff_percentage']].head().to_string())
    else:
        print("\nNo suspicious cases found with the current thresholds.")