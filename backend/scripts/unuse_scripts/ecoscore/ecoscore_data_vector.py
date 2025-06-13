import pandas as pd
from sklearn.preprocessing import MinMaxScaler

# Cargar datos
df = pd.read_csv("openfoodfacts_ecoscore_with_extracted_columns.csv")

# Mapear ecoscore_grade a números
grade_map = {
    'A': 4,
    'B': 3,
    'C': 2,
    'D': 1,
    'not-applicable': 0
}
df['ecoscore_grade_num'] = df['ecoscore_grade'].map(grade_map).fillna(0)

# Columnas seleccionadas para el vector
cols_vector = [
    'ecoscore_grade_num',
    'origins_epi_score',
    'origins_transportation_score',
    'origins_main_percent',
    'packaging_score',
    'packaging_non_recyclable_materials',
    'production_value'
]

# Rellenar valores faltantes con la mediana para cada columna
for col in cols_vector:
    df[col].fillna(df[col].median(), inplace=True)

# Escalar los valores con MinMaxScaler para rango [0,1]
scaler = MinMaxScaler()
df_scaled = scaler.fit_transform(df[cols_vector])

# Cada fila de df_scaled es un vector numérico listo para usar en búsqueda vectorial
# Ejemplo: vector del primer producto
print(df_scaled[0])

# Opcional: Guardar los vectores normalizados junto al dataframe original
df_vectors = pd.DataFrame(df_scaled, columns=[f"{c}_scaled" for c in cols_vector])
df_final = pd.concat([df, df_vectors], axis=1)

# Guardar resultado en CSV si quieres
df_final.to_csv("productos_vectores.csv", index=False)
