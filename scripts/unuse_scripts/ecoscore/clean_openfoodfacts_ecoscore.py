import pandas as pd
import ast

# Leer archivo original
df = pd.read_csv("openfoodfacts_ecoscore.csv")

def extract_ecoscore_data(ecoscore_str):
    try:
        data = ast.literal_eval(ecoscore_str)
    except:
        return pd.Series()

    adj = data.get('adjustments', {})
    origins = adj.get('origins_of_ingredients', {})
    packaging = adj.get('packaging', {})
    production = adj.get('production_system', {})

    agg_origins = origins.get('aggregated_origins', [{}])
    first_origin = agg_origins[0] if agg_origins else {}

    return pd.Series({
        'grade': data.get('grade'),
        # 'status': data.get('status'),  # OMITIDO
        # 'category_not_applicable': data.get('environmental_score_not_applicable_for_category'),  # QUITADO

        # ORIGINS
        'origins_epi_score': origins.get('epi_score'),
        'origins_epi_value': origins.get('epi_value'),
        'origins_transportation_score': origins.get('transportation_score'),
        'origins_value': origins.get('value'),
        # 'origins_warning': origins.get('warning'),  # quitado en análisis previo
        'origins_main_origin': first_origin.get('origin'),
        'origins_main_percent': first_origin.get('percent'),

        # PACKAGING
        'packaging_score': packaging.get('score'),
        'packaging_value': packaging.get('value'),
        'packaging_non_recyclable_materials': packaging.get('non_recyclable_and_non_biodegradable_materials'),

        # PRODUCTION SYSTEM
        'production_value': production.get('value'),
        # 'production_warning': production.get('warning'),  # quitado

        # MISSING INFO
        # 'missing_labels': missing.get('labels'),  # quitado
        # 'missing_origins': missing.get('origins'),  # quitado
    })

# Extraer nuevas columnas
ecoscore_extracted = df['ecoscore_data'].apply(extract_ecoscore_data)

# Eliminar columna original ecoscore_data del df original
df_cleaned = df.drop(columns=['ecoscore_data'])

# Añadir las columnas nuevas al df original sin la columna ecoscore_data
df_final = pd.concat([df_cleaned, ecoscore_extracted], axis=1)
df_final = df_final.drop(columns=['grade','ecoscore_tags','origins_main_origin','ingredients_without_ecobalyse_ids_n'])
# Guardar archivo con toda la data (menos ecoscore_data, con nuevas columnas)
df_final.to_csv("openfoodfacts_ecoscore_with_extracted_columns.csv", index=False)