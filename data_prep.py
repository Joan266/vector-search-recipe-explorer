import pandas as pd

# Cargar el dataset (ejemplo con OpenFoodFacts)
url = "https://static.openfoodfacts.org/data/en.openfoodfacts.org.products.csv"
df = pd.read_csv(url, sep='\t', nrows=200)  # Solo las primeras 200 filas

# Verificar:
print("✅ Resumen del DataFrame:")
print(df.head(3))  # Muestra las primeras 3 filas
print("\n📊 Total de filas:", len(df))
print("🔍 Columnas disponibles:", df.columns.tolist())