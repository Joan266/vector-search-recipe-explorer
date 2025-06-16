from typing import List, Dict

def clean_data(data: List[Dict]) -> List[Dict]:
    """Filter out rows with empty elements or short instructions"""
    cleaned_data = []
    for row in data:
        # Check for any empty values in required fields
        required_fields = ['name', 'category', 'area', 'instructions']
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

def extract_techniques(text: str) -> List[str]:
    # Your existing extract_techniques function
    pass

def clean_instructions(instructions: str) -> str:
    # Your existing clean_instructions function
    pass