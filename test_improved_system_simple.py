#!/usr/bin/env python3
"""
Script simplificado para probar las mejoras implementadas en el sistema RAG de AzuSena.
"""

import requests
import json
import time
from datetime import datetime

# Configuración del servidor
SERVER_URL = "http://127.0.0.1:5000"

def send_query(query_text):
    """Envía una consulta al servidor y retorna la respuesta."""
    try:
        response = requests.post(
            f"{SERVER_URL}/query",
            json={"query": query_text},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error HTTP {response.status_code}: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión: {e}")
        return None

def main():
    """Función principal que ejecuta las pruebas."""
    print("🚀 Iniciando pruebas del sistema mejorado de AzuSena")
    print("=" * 60)
    
    # Pruebas específicas para validar las mejoras
    test_cases = [
        {
            "query": "¿Qué dice el artículo 186 sobre calidad?",
            "description": "Consulta específica sobre artículo existente",
            "expected": "Debe encontrar el artículo 186 y validar su existencia"
        },
        {
            "query": "¿Qué dicen los artículos 186 y 227 sobre calidad en la Ley 100?",
            "description": "Consulta sobre múltiples artículos (uno existe, otro no)",
            "expected": "Debe validar artículos y generar respuesta conservadora si es necesario"
        },
        {
            "query": "¿Cuáles son los artículos sobre calidad en salud?",
            "description": "Consulta general sobre calidad",
            "expected": "Debe mostrar artículos validados temáticamente"
        },
        {
            "query": "Información sobre acreditación de IPS",
            "description": "Consulta temática específica",
            "expected": "Debe mantener coherencia temática"
        },
        {
            "query": "¿Qué dice el artículo 999 de la Ley 100?",
            "description": "Consulta sobre artículo inexistente",
            "expected": "Debe detectar que el artículo no existe"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Prueba {i}: {test_case['description']} ---")
        print(f"Consulta: {test_case['query']}")
        print(f"Esperado: {test_case['expected']}")
        
        response = send_query(test_case['query'])
        
        if response:
            result = {
                "test_id": i,
                "query": test_case['query'],
                "description": test_case['description'],
                "expected": test_case['expected'],
                "response": response.get('response', ''),
                "similarity": response.get('similarity', 0),
                "used_kb": response.get('used_knowledge_base', False),
                "timestamp": datetime.now().isoformat()
            }
            
            results.append(result)
            
            print(f"✅ Respuesta obtenida:")
            print(f"   Similitud: {response.get('similarity', 0):.3f}")
            print(f"   Usó KB: {response.get('used_knowledge_base', False)}")
            print(f"   Respuesta: {response.get('response', '')[:150]}...")
            
            # Análisis básico de la respuesta
            response_text = response.get('response', '').lower()
            
            # Verificar si menciona artículos específicos
            import re
            articles_mentioned = re.findall(r'artículo\s*(\d+)', response_text)
            if articles_mentioned:
                print(f"   Artículos mencionados: {articles_mentioned}")
            
            # Verificar indicadores de respuesta conservadora
            conservative_indicators = [
                "basándome en mi base de datos",
                "información relevante:",
                "te gustaría obtener más detalles",
                "pregúntame directamente"
            ]
            
            is_conservative = any(indicator in response_text for indicator in conservative_indicators)
            if is_conservative:
                print(f"   🛡️ Respuesta conservadora detectada")
            
        else:
            print("❌ Error en la consulta")
        
        time.sleep(1)  # Pausa entre consultas
    
    # Guardar resultados
    report = {
        "test_summary": {
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(results),
            "successful_tests": len([r for r in results if r['response']])
        },
        "test_results": results,
        "analysis": {
            "avg_similarity": sum(r.get('similarity', 0) for r in results) / len(results) if results else 0,
            "kb_usage_rate": sum(1 for r in results if r.get('used_kb', False)) / len(results) if results else 0
        }
    }
    
    with open('improved_system_simple_results.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # Mostrar resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 60)
    print(f"Total de pruebas: {report['test_summary']['total_tests']}")
    print(f"Pruebas exitosas: {report['test_summary']['successful_tests']}")
    print(f"Similitud promedio: {report['analysis']['avg_similarity']:.3f}")
    print(f"Tasa de uso de KB: {report['analysis']['kb_usage_rate']:.1%}")
    
    print(f"\n✅ Resultados guardados en: improved_system_simple_results.json")
    print("\n🎉 Pruebas completadas!")

if __name__ == "__main__":
    main()