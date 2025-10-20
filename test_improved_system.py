#!/usr/bin/env python3
"""
Script para probar las mejoras implementadas en el sistema RAG de AzuSena.
Valida la coherencia temática, validación de artículos y respuestas conservadoras.
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

def test_article_validation():
    """Prueba la validación de artículos mencionados."""
    print("🔍 Probando validación de artículos...")
    
    test_cases = [
        {
            "query": "¿Qué dicen los artículos 186 y 227 sobre calidad en la Ley 100?",
            "description": "Consulta sobre artículos específicos de calidad",
            "expected_behavior": "Debe validar si los artículos existen"
        },
        {
            "query": "Explícame sobre el artículo 999 de la Ley 100",
            "description": "Consulta sobre artículo inexistente",
            "expected_behavior": "Debe detectar que el artículo no existe"
        },
        {
            "query": "¿Cuáles son los artículos sobre calidad en salud?",
            "description": "Consulta general sobre calidad",
            "expected_behavior": "Debe mostrar solo artículos validados"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Prueba {i}: {test_case['description']} ---")
        print(f"Consulta: {test_case['query']}")
        
        response = send_query(test_case['query'])
        
        if response:
            result = {
                "test_id": i,
                "query": test_case['query'],
                "description": test_case['description'],
                "expected_behavior": test_case['expected_behavior'],
                "response": response.get('response', ''),
                "similarity": response.get('similarity', 0),
                "used_kb": response.get('used_kb', False),
                "timestamp": datetime.now().isoformat()
            }
            
            results.append(result)
            
            print(f"Respuesta: {response.get('response', '')[:200]}...")
            print(f"Similitud: {response.get('similarity', 0):.3f}")
            print(f"Usó KB: {response.get('used_kb', False)}")
        else:
            print("❌ Error en la consulta")
        
        time.sleep(1)  # Pausa entre consultas
    
    return results

def test_thematic_consistency():
    """Prueba la consistencia temática de las respuestas."""
    print("\n🎯 Probando consistencia temática...")
    
    test_cases = [
        {
            "query": "¿Qué artículos hablan sobre calidad en la Ley 100?",
            "keywords": ["calidad", "ley 100"],
            "description": "Consulta sobre calidad - debe mantener coherencia temática"
        },
        {
            "query": "Información sobre acreditación de IPS",
            "keywords": ["acreditación", "ips"],
            "description": "Consulta sobre acreditación - debe ser coherente"
        },
        {
            "query": "¿Cómo funciona el sistema de auditorías médicas?",
            "keywords": ["auditoría", "médica", "sistema"],
            "description": "Consulta sobre auditorías - debe mantener el tema"
        },
        {
            "query": "Explícame sobre Azusena y la calidad",
            "keywords": ["azusena", "calidad"],
            "description": "Consulta mixta - debe manejar coherencia"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Prueba {i}: {test_case['description']} ---")
        print(f"Consulta: {test_case['query']}")
        
        response = send_query(test_case['query'])
        
        if response:
            response_text = response.get('response', '').lower()
            
            # Verificar presencia de palabras clave
            keywords_found = []
            for keyword in test_case['keywords']:
                if keyword.lower() in response_text:
                    keywords_found.append(keyword)
            
            consistency_score = len(keywords_found) / len(test_case['keywords'])
            
            result = {
                "test_id": i,
                "query": test_case['query'],
                "description": test_case['description'],
                "expected_keywords": test_case['keywords'],
                "keywords_found": keywords_found,
                "consistency_score": consistency_score,
                "response": response.get('response', ''),
                "similarity": response.get('similarity', 0),
                "used_kb": response.get('used_kb', False),
                "timestamp": datetime.now().isoformat()
            }
            
            results.append(result)
            
            print(f"Palabras clave esperadas: {test_case['keywords']}")
            print(f"Palabras clave encontradas: {keywords_found}")
            print(f"Puntuación de consistencia: {consistency_score:.2f}")
            print(f"Similitud: {response.get('similarity', 0):.3f}")
            print(f"Usó KB: {response.get('used_kb', False)}")
        else:
            print("❌ Error en la consulta")
        
        time.sleep(1)
    
    return results

def test_conservative_responses():
    """Prueba las respuestas conservadoras cuando hay problemas de coherencia."""
    print("\n🛡️ Probando respuestas conservadoras...")
    
    test_cases = [
        {
            "query": "¿Qué dice el artículo 123456 sobre calidad?",
            "description": "Artículo inexistente - debe generar respuesta conservadora",
            "expected_behavior": "Respuesta conservadora por artículo inválido"
        },
        {
            "query": "Información sobre temas muy diversos y artículos variados",
            "description": "Consulta muy amplia - puede generar respuesta conservadora",
            "expected_behavior": "Posible respuesta conservadora por falta de coherencia"
        },
        {
            "query": "Azusena calidad artículos diversos temas múltiples",
            "description": "Consulta confusa - debe manejar con respuesta conservadora",
            "expected_behavior": "Respuesta conservadora por consulta ambigua"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Prueba {i}: {test_case['description']} ---")
        print(f"Consulta: {test_case['query']}")
        
        response = send_query(test_case['query'])
        
        if response:
            response_text = response.get('response', '')
            
            # Detectar indicadores de respuesta conservadora
            conservative_indicators = [
                "basándome en mi base de datos",
                "información relevante:",
                "te gustaría obtener más detalles",
                "pregúntame directamente",
                "especifica qué aspecto",
                "información relacionada"
            ]
            
            is_conservative = any(indicator.lower() in response_text.lower() 
                                for indicator in conservative_indicators)
            
            result = {
                "test_id": i,
                "query": test_case['query'],
                "description": test_case['description'],
                "expected_behavior": test_case['expected_behavior'],
                "is_conservative": is_conservative,
                "response": response_text,
                "similarity": response.get('similarity', 0),
                "used_kb": response.get('used_kb', False),
                "timestamp": datetime.now().isoformat()
            }
            
            results.append(result)
            
            print(f"¿Es respuesta conservadora?: {is_conservative}")
            print(f"Respuesta: {response_text[:200]}...")
            print(f"Similitud: {response.get('similarity', 0):.3f}")
            print(f"Usó KB: {response.get('used_kb', False)}")
        else:
            print("❌ Error en la consulta")
        
        time.sleep(1)
    
    return results

def generate_report(article_results, consistency_results, conservative_results):
    """Genera un reporte completo de las pruebas."""
    report = {
        "test_summary": {
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(article_results) + len(consistency_results) + len(conservative_results),
            "article_validation_tests": len(article_results),
            "thematic_consistency_tests": len(consistency_results),
            "conservative_response_tests": len(conservative_results)
        },
        "article_validation_results": article_results,
        "thematic_consistency_results": consistency_results,
        "conservative_response_results": conservative_results,
        "analysis": {
            "avg_similarity_article_tests": sum(r.get('similarity', 0) for r in article_results) / len(article_results) if article_results else 0,
            "avg_consistency_score": sum(r.get('consistency_score', 0) for r in consistency_results) / len(consistency_results) if consistency_results else 0,
            "conservative_responses_detected": sum(1 for r in conservative_results if r.get('is_conservative', False)),
            "kb_usage_rate": sum(1 for r in article_results + consistency_results + conservative_results if r.get('used_kb', False)) / (len(article_results) + len(consistency_results) + len(conservative_results)) if (article_results or consistency_results or conservative_results) else 0
        }
    }
    
    return report

def main():
    """Función principal que ejecuta todas las pruebas."""
    print("🚀 Iniciando pruebas del sistema mejorado de AzuSena")
    print("=" * 60)
    
    # Verificar que el servidor esté funcionando
    try:
        response = requests.post(f"{SERVER_URL}/query", json={"query": "test"}, timeout=5)
        if response.status_code != 200:
            print("❌ El servidor no está respondiendo correctamente")
            return
    except:
        print("❌ No se puede conectar al servidor. Asegúrate de que esté ejecutándose.")
        return
    
    print("✅ Servidor conectado correctamente")
    
    # Ejecutar pruebas
    article_results = test_article_validation()
    consistency_results = test_thematic_consistency()
    conservative_results = test_conservative_responses()
    
    # Generar reporte
    report = generate_report(article_results, consistency_results, conservative_results)
    
    # Guardar resultados
    with open('improved_system_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # Mostrar resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 60)
    print(f"Total de pruebas ejecutadas: {report['test_summary']['total_tests']}")
    print(f"Similitud promedio (validación artículos): {report['analysis']['avg_similarity_article_tests']:.3f}")
    print(f"Puntuación promedio de consistencia: {report['analysis']['avg_consistency_score']:.3f}")
    print(f"Respuestas conservadoras detectadas: {report['analysis']['conservative_responses_detected']}/{len(conservative_results)}")
    print(f"Tasa de uso de base de conocimientos: {report['analysis']['kb_usage_rate']:.1%}")
    
    print(f"\n✅ Resultados guardados en: improved_system_test_results.json")
    print("\n🎉 Pruebas completadas exitosamente!")

if __name__ == "__main__":
    main()