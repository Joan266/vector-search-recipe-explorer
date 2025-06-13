import pandas as pd

# Cargar el archivo ya limpiado
df = pd.read_csv("openfoodfacts_ecoscore_with_extracted_columns.csv")

summary = []

for col in df.columns:
    unique_vals = df[col].dropna().unique()
    num_unique = len(unique_vals)
    non_null_count = df[col].notnull().sum()
    null_percent = 100 * (1 - non_null_count / len(df))

    col_summary = {
        'column': col,
        'type': df[col].dtype,
        'non_null_%': round(100 - null_percent, 2),
        'unique_count': num_unique,
    }

    if df[col].dtype in ['float64', 'int64']:
        col_summary['min'] = df[col].min()
        col_summary['max'] = df[col].max()
    else:
        col_summary['sample_values'] = unique_vals[:5]  # ejemplo de valores únicos

    summary.append(col_summary)

# Mostrar como DataFrame ordenado por % completitud
summary_df = pd.DataFrame(summary).sort_values(by='non_null_%', ascending=False)

# Mostrar el resumen
pd.set_option('display.max_columns', None)
print(summary_df)
