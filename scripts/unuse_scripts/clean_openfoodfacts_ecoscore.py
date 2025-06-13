import pandas as pd
import ast
import re
from unidecode import unidecode
import json

df = pd.read_csv("openfoodfacts_ecoscore.csv")

def parse_ecoscore_data(text):
    try:
        # Limpieza previa para unicode y comillas
        text = unidecode(text).replace("'", '"').replace("None", "null")
        return json.loads(text) 
    except:
        return {}

df['ecoscore_data'] = df['ecoscore_data'].apply(parse_ecoscore_data)

# Extraer campos clave
df['co2_total'] = df['ecoscore_data'].apply(lambda x: x.get('agribalyse', {}).get('co2_total', None))
df['eco_score'] = df['ecoscore_data'].apply(lambda x: x.get('score', None))
df['packaging_materials'] = df['ecoscore_data'].apply(
    lambda x: [p['material'] for p in x.get('adjustments', {}).get('packaging', {}).get('packagings', [])]
)

# Normalizar grados ecorescore
grade_mapping = {'a': 'Excellent', 'b': 'Good', 'c': 'Average', 'd': 'Poor', 'e': 'Critical'}
df['ecoscore_grade'] = df['ecoscore_grade'].str.lower().map(grade_mapping).fillna('Not Applicable')

# Limpiar tags
df['ecoscore_tags'] = df['ecoscore_tags'].apply(
    lambda x: [tag.strip("'").lower() for tag in re.findall(r"'([^']*)'", x)]
)

# Feature: Porcentaje de materiales reciclables
def recyclability_score(packaging):
    recyclable_materials = {'en:glass', 'en:paper', 'en:cardboard'}
    return sum(1 for m in packaging if m in recyclable_materials) / len(packaging) if packaging else 0

df['recyclability'] = df['packaging_materials'].apply(recyclability_score)

# Feature: Nivel de procesamiento
df['processing_level'] = df['ecoscore_data'].apply(
    lambda x: x.get('agribalyse', {}).get('ef_processing', 0) > 0.05
).map({True: 'High', False: 'Low'})

df.to_csv("cleaned_openfoodfacts_ecoscore.csv", index=False)