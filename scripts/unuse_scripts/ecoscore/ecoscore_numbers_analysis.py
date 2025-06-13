import pandas as pd

# Cargar el archivo CSV
df = pd.read_csv("openfoodfacts_ecoscore_with_extracted_columns.csv")

# Definir qué significa "neutral o bueno" por columna
neutral_values_per_column = {
    'ecoscore_grade': ['not-applicable'],
    'origins_epi_score': [],  # 0.0 es malo
    'origins_epi_value': [],
    'origins_transportation_score': [0.0],  # 0.0 = sin penalización
    'origins_value': [],
    'origins_main_percent': [100.0],  # bueno
    'packaging_score': [],
    'packaging_value': [],
    'packaging_non_recyclable_materials': [0.0],  # bueno
    'production_value': [0.0]  # posiblemente neutro
}

# Crear diccionario de reporte
reporte = {}

for col in df.columns:
    total = len(df[col])
    missing = df[col].isnull().sum()

    # Valores neutros definidos para esta columna
    neutral_set = neutral_values_per_column.get(col, [])

    # Verificamos neutros sin duplicar conteo
    neutros = df[col].apply(lambda x: x in neutral_set if pd.notnull(x) else False).sum()

    reporte[col] = {
        "total": total,
        "faltantes": missing,
        "faltantes_pct": round((missing / total) * 100, 2),
        "neutros_o_buenos": neutros,
        "neutros_pct": round((neutros / total) * 100, 2)
    }

# Mostrar resultados
print("\nResumen de calidad de datos corregido:\n")
for columna, datos in reporte.items():
    print(f"{columna}:")
    print(f"  Total de datos: {datos['total']}")
    print(f"  Faltantes: {datos['faltantes']} ({datos['faltantes_pct']}%)")
    print(f"  Neutros o buenos: {datos['neutros_o_buenos']} ({datos['neutros_pct']}%)\n")
