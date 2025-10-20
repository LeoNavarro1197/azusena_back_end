import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.vector_db import vector_db

# Consultas de salud que probamos anteriormente
health_queries = [
    "¿Qué documentos necesito para afiliarme al SGSSS?",
    "¿Cómo puedo cambiar de EPS?",
    "¿Qué es el SISBEN y cómo me inscribo?",
    "¿Cómo presento una PQRS en salud?",
    "¿Qué es la referencia y contrarreferencia?",
    "¿Cuáles son mis derechos como usuario del sistema de salud?",
    "¿Cómo funciona la portabilidad en salud?",
    "¿Qué hacer si me niegan un servicio de salud?",
    "¿Cómo acceder a medicamentos no incluidos en el POS?"
]

print("=== ANÁLISIS DE UMBRALES DE SIMILITUD ===")
print("Probando consultas de salud con diferentes umbrales\n")

for i, query in enumerate(health_queries, 1):
    print(f"{i}. Query: {query}")
    
    # Obtener resultados con el método actual
    results = vector_db.get_top_results(query, top_k=5)
    
    if results:
        print(f"   ✓ Resultados encontrados: {len(results)}")
        best_result = results[0]
        print(f"   ✓ Mejor similitud: {best_result['similarity']:.4f}")
        print(f"   ✓ Tema: {best_result['data']['tema']}")
        print(f"   ✓ Subtema: {best_result['data']['subtema']}")
        
        # Verificar si pasaría los umbrales actuales
        passes_kb_threshold = best_result['similarity'] >= 0.65
        passes_context_threshold = best_result['similarity'] >= 0.3
        passes_vector_threshold = best_result['similarity'] >= 0.5
        
        print(f"   • Pasa umbral KB (0.65): {'SÍ' if passes_kb_threshold else 'NO'}")
        print(f"   • Pasa umbral contexto (0.3): {'SÍ' if passes_context_threshold else 'NO'}")
        print(f"   • Pasa umbral vector (0.5): {'SÍ' if passes_vector_threshold else 'NO'}")
    else:
        print("   ✗ No se encontraron resultados")
    
    print()

# Estadísticas generales
print("=== ESTADÍSTICAS GENERALES ===")
all_scores = []
kb_passes = 0
context_passes = 0
vector_passes = 0

for query in health_queries:
    results = vector_db.get_top_results(query, top_k=1)
    if results:
        score = results[0]['similarity']
        all_scores.append(score)
        if score >= 0.65: kb_passes += 1
        if score >= 0.3: context_passes += 1
        if score >= 0.5: vector_passes += 1

if all_scores:
    print(f"Promedio de similitud: {sum(all_scores)/len(all_scores):.4f}")
    print(f"Similitud máxima: {max(all_scores):.4f}")
    print(f"Similitud mínima: {min(all_scores):.4f}")
    print(f"Consultas que pasan umbral KB (0.65): {kb_passes}/{len(health_queries)} ({kb_passes/len(health_queries)*100:.1f}%)")
    print(f"Consultas que pasan umbral contexto (0.3): {context_passes}/{len(health_queries)} ({context_passes/len(health_queries)*100:.1f}%)")
    print(f"Consultas que pasan umbral vector (0.5): {vector_passes}/{len(health_queries)} ({vector_passes/len(health_queries)*100:.1f}%)")

print("\n=== RECOMENDACIONES ===")
if all_scores:
    avg_score = sum(all_scores)/len(all_scores)
    if avg_score < 0.65:
        print(f"• Reducir umbral KB de 0.65 a {avg_score:.2f} o menos")
    if vector_passes < len(health_queries):
        print(f"• Reducir umbral vector de 0.5 a {min(all_scores):.2f} o menos")
    print("• Los umbrales actuales son demasiado altos para las consultas de salud")
else:
    print("• No se encontraron resultados para ninguna consulta")