import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.vector_db import vector_db

# Consultas basadas en el contenido real de la KB que encontramos
specific_kb_queries = [
    "afiliación EPS",
    "régimen de ahorro individual",
    "bonos pensionales",
    "pensiones",
    "administradoras de fondos",
    "garantía de calidad en servicios de salud",
    "implementación del SGSSS",
    "superintendencia",
    "financiamiento de actividades de salud pública"
]

print("=== PRUEBAS CON CONSULTAS ESPECÍFICAS DE LA KB ===")
print("Probando consultas que deberían tener alta similitud\n")

successful_queries = 0
total_queries = len(specific_kb_queries)

for i, query in enumerate(specific_kb_queries, 1):
    print(f"{i}. Query: '{query}'")
    
    # Obtener resultados
    results = vector_db.get_top_results(query, top_k=3)
    
    if results:
        print(f"   ✓ Resultados encontrados: {len(results)}")
        for j, result in enumerate(results[:2], 1):  # Mostrar top 2
            print(f"   {j}. Similitud: {result['similarity']:.4f}")
            print(f"      Tema: {result['data']['tema']}")
            print(f"      Subtema: {result['data']['subtema']}")
            print(f"      Resumen: {result['data']['resumen_explicativo'][:100]}...")
        
        best_score = results[0]['similarity']
        if best_score >= 0.65:
            print(f"   ✅ PASARÍA umbral KB (0.65)")
            successful_queries += 1
        else:
            print(f"   ❌ NO PASA umbral KB (0.65)")
    else:
        print("   ✗ No se encontraron resultados")
    
    print()

print("=== RESULTADOS FINALES ===")
print(f"Consultas exitosas con umbral actual: {successful_queries}/{total_queries} ({successful_queries/total_queries*100:.1f}%)")

# Ahora probemos con una consulta que sabemos que existe exactamente
print("\n=== PRUEBA CON CONSULTA EXACTA ===")
exact_query = "Régimen de Ahorro Individual con Solidaridad"
print(f"Query exacta: '{exact_query}'")

results = vector_db.get_top_results(exact_query, top_k=1)
if results:
    result = results[0]
    print(f"Similitud: {result['similarity']:.4f}")
    print(f"Tema: {result['data']['tema']}")
    print(f"¿Pasa umbral KB?: {'SÍ' if result['similarity'] >= 0.65 else 'NO'}")
else:
    print("No se encontraron resultados para la consulta exacta")

# Probar también el método find_similar_question directamente
print("\n=== PRUEBA CON find_similar_question ===")
response, similarity = vector_db.find_similar_question("afiliación EPS", top_k=1)
print(f"Respuesta: {response[:200]}...")
print(f"Similitud: {similarity}")
print(f"¿Usaría KB?: {'SÍ' if similarity >= 0.65 else 'NO'}")