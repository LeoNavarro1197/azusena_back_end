import pandas as pd

# Cargar el archivo Excel
df = pd.read_excel('data/Compilado_Preguntas_Azusena.xlsx')

print("=== ANÁLISIS DEL CONTENIDO DE LA KB ===")
print(f"Total de filas en la KB: {len(df)}")
print(f"Columnas disponibles: {df.columns.tolist()}")

# Buscar contenido relacionado con salud
salud_keywords = ['salud', 'SGSSS', 'EPS', 'SISBEN', 'PQRS', 'referencia', 'contrarreferencia', 'médico', 'hospital', 'clínica', 'tratamiento', 'medicina']

salud_rows = df[
    df['tema'].str.contains('|'.join(salud_keywords), case=False, na=False) |
    df['subtema'].str.contains('|'.join(salud_keywords), case=False, na=False) |
    df['resumen_explicativo'].str.contains('|'.join(salud_keywords), case=False, na=False)
]

print(f"\n=== CONTENIDO RELACIONADO CON SALUD ===")
print(f"Filas relacionadas con salud: {len(salud_rows)}")

if len(salud_rows) > 0:
    print("\nTemas de salud encontrados:")
    for idx, row in salud_rows.head(10).iterrows():
        print(f"- Tema: {row['tema']}")
        print(f"  Subtema: {row['subtema']}")
        print(f"  Resumen: {row['resumen_explicativo'][:100]}...")
        print()
else:
    print("No se encontraron temas específicos de salud en la KB")

# Mostrar todos los temas únicos
print("\n=== TODOS LOS TEMAS EN LA KB ===")
print(df['tema'].value_counts().head(20))

# Buscar palabras clave específicas de las preguntas de salud
print("\n=== BÚSQUEDA DE PALABRAS CLAVE ESPECÍFICAS ===")
health_queries = [
    "afiliación", "SGSSS", "documentos", "EPS", "SISBEN", 
    "PQRS", "quejas", "reclamos", "referencia", "contrarreferencia"
]

# Verificar qué columnas existen
print(f"Columnas disponibles: {df.columns.tolist()}")

for keyword in health_queries:
    matches = df[
        df['tema'].str.contains(keyword, case=False, na=False) |
        df['subtema'].str.contains(keyword, case=False, na=False) |
        df['resumen_explicativo'].str.contains(keyword, case=False, na=False)
    ]
    print(f"'{keyword}': {len(matches)} coincidencias")