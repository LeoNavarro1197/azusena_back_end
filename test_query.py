#!/usr/bin/env python3
"""
Script de prueba para verificar las respuestas de AzuSENA
"""
import requests
import json

def test_query(query_text):
    """Prueba una consulta específica"""
    url = "http://127.0.0.1:5001/query"
    headers = {"Content-Type": "application/json"}
    data = {"query": query_text}
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            result = response.json()
            print(f"\n{'='*50}")
            print(f"CONSULTA: {query_text}")
            print(f"{'='*50}")
            print(f"RESPUESTA: {result.get('response', 'Sin respuesta')}")
            print(f"SIMILITUD: {result.get('similarity', 0.0)}")
            print(f"USÓ KB: {result.get('used_knowledge_base', False)}")
            print(f"{'='*50}")
            return result
        else:
            print(f"Error {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"Error al hacer la consulta: {e}")
        return None

def main():
    """Ejecuta las pruebas principales"""
    print("🔍 INICIANDO PRUEBAS EXHAUSTIVAS DE AZUSENA")
    
    # Pruebas básicas
    test_queries = [
        "hola azusena",
        "¿Cuál es el procedimiento para anular una factura en salud?",
        "que articulos hablan sobre calidad?",
        "buenos días",
        "¿Qué es el SENA?",
        "artículo 1",
        "lista de artículos sobre educación",
        "procedimiento de inscripción",
        "¿Cómo puedo contactar al SENA?",
        "normativa sobre aprendices"
    ]
    
    for query in test_queries:
        test_query(query)
    
    print("\n✅ PRUEBAS COMPLETADAS")

if __name__ == "__main__":
    main()