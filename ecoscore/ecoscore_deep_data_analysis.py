import pandas as pd

# Cargar CSV
df = pd.read_csv("openfoodfacts_ecoscore_with_extracted_columns.csv")      

# Lista de valores que consideramos como 'desconocido'
unknown_values = {
    "", "unknown", "not-applicable", "en:unknown",
    "no_label", "origins_are_100_percent_unknown"
}

# Resultado final
result = []

for col in df.columns:
    total = len(df)
    
    # Contar valores NaN explícitos
    null_count = df[col].isna().sum()
    
    # Contar valores con etiquetas desconocidas (solo para columnas tipo texto)
    if df[col].dtype == "object":
        unknown_count = df[col].isin(unknown_values).sum()
    else:
        unknown_count = 0
    
    # Total de valores que consideramos desconocidos
    total_unknown = null_count + unknown_count
    unknown_pct = (total_unknown / total) * 100
    
    result.append({
        "column": col,
        "null_count": null_count,
        "unknown_tagged_count": unknown_count,
        "total_unknown": total_unknown,
        "unknown_pct": round(unknown_pct, 2)
    })

# Mostrar como DataFrame ordenado
result_df = pd.DataFrame(result).sort_values("unknown_pct", ascending=False)
print(result_df)
