#!/usr/bin/env python3
"""
Script para probar la consistencia del sistema con consultas específicas sobre la Ley 100
"""

import requests
import json
import time

def test_query(query_text, test_name):
    """Envía una consulta al endpoint y retorna la respuesta formateada"""
    try:
        url = "http://127.0.0.1:5000/query"
        payload = {"query": query_text}
        
        print(f"🔍 {test_name}")
        print(f"📝 Consulta: {query_text}")
        print("-" * 60)
        
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ RESPUESTA:")
            print(f"📄 Contenido: {data.get('response', 'Sin respuesta')[:500]}...")
            print(f"📊 Similitud: {data.get('similarity', 0.0):.4f}")
            print(f"📚 Usó KB: {data.get('used_knowledge_base', False)}")
            print()
            
            return {
                'success': True,
                'response': data.get('response', ''),
                'similarity': data.get('similarity', 0.0),
                'used_kb': data.get('used_knowledge_base', False),
                'query': query_text,
                'test_name': test_name
            }
        else:
            error_msg = f"Error HTTP {response.status_code}: {response.text}"
            print(f"❌ ERROR: {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'query': query_text,
                'test_name': test_name
            }
            
    except Exception as e:
        error_msg = f"Error de conexión: {str(e)}"
        print(f"❌ ERROR: {error_msg}")
        return {
            'success': False,
            'error': error_msg,
            'query': query_text,
            'test_name': test_name
        }

def analyze_consistency(results):
    """Analiza la consistencia de las respuestas"""
    print("=" * 80)
    print("📊 ANÁLISIS DE CONSISTENCIA")
    print("=" * 80)
    
    successful_queries = [r for r in results if r['success']]
    failed_queries = [r for r in results if not r['success']]
    
    print(f"✅ Consultas exitosas: {len(successful_queries)}/{len(results)}")
    print(f"❌ Consultas fallidas: {len(failed_queries)}/{len(results)}")
    
    if successful_queries:
        kb_usage = [r for r in successful_queries if r['used_kb']]
        avg_similarity = sum(r['similarity'] for r in successful_queries) / len(successful_queries)
        
        print(f"📚 Consultas que usaron KB: {len(kb_usage)}/{len(successful_queries)}")
        print(f"📈 Similitud promedio: {avg_similarity:.4f}")
        print()
        
        # Analizar consistencia temática
        print("🔍 ANÁLISIS DE CONSISTENCIA TEMÁTICA:")
        print("-" * 50)
        
        # Buscar patrones problemáticos
        for result in successful_queries:
            response_text = result['response'].lower()
            query_text = result['query'].lower()
            
            # Verificar si la respuesta es relevante al tema solicitado
            if 'calidad' in query_text and 'calidad' not in response_text:
                print(f"⚠️  POSIBLE INCONSISTENCIA TEMÁTICA:")
                print(f"   Consulta: {result['query']}")
                print(f"   Problema: Pregunta sobre 'calidad' pero respuesta no menciona calidad")
                print()
            
            if 'artículo' in query_text:
                # Extraer números de artículos mencionados en la consulta
                import re
                query_articles = re.findall(r'artículo\s*(\d+)', query_text)
                response_articles = re.findall(r'artículo\s*(\d+)', response_text)
                
                if query_articles and response_articles:
                    if not any(art in response_articles for art in query_articles):
                        print(f"⚠️  POSIBLE INCONSISTENCIA DE ARTÍCULOS:")
                        print(f"   Consulta: {result['query']}")
                        print(f"   Artículos solicitados: {query_articles}")
                        print(f"   Artículos en respuesta: {response_articles}")
                        print()

def main():
    """Función principal para ejecutar las pruebas"""
    print("🧪 PRUEBAS DE CONSISTENCIA - LEY 100")
    print("=" * 60)
    
    # Definir consultas de prueba basadas en la conversación problemática
    test_queries = [
        {
            'query': 'cuales son los articulos que hablan sobre calidad en la ley 100 del 93',
            'name': 'Consulta Original - Artículos sobre Calidad'
        },
        {
            'query': 'que dice exactamente el articulo 186 de la ley 100',
            'name': 'Consulta Específica - Artículo 186'
        },
        {
            'query': 'que dice exactamente el articulo 227 de la ley 100',
            'name': 'Consulta Específica - Artículo 227'
        },
        {
            'query': 'articulo 106 ley 100 normas de publicidad',
            'name': 'Consulta Específica - Artículo 106'
        },
        {
            'query': 'articulo 3 ley 100 derecho seguridad social',
            'name': 'Consulta Específica - Artículo 3'
        },
        {
            'query': 'articulo 182 ley 100 ingresos EPS UPC',
            'name': 'Consulta Específica - Artículo 182'
        },
        {
            'query': 'sistema de acreditacion calidad IPS ley 100',
            'name': 'Consulta Temática - Acreditación y Calidad'
        },
        {
            'query': 'auditorias medicas transparencia calidad atencion salud ley 100',
            'name': 'Consulta Temática - Auditorías y Calidad'
        }
    ]
    
    results = []
    
    # Ejecutar las pruebas
    for i, test in enumerate(test_queries, 1):
        print(f"📋 PRUEBA {i}/{len(test_queries)}")
        result = test_query(test['query'], test['name'])
        results.append(result)
        
        # Pausa entre consultas para no sobrecargar el servidor
        if i < len(test_queries):
            time.sleep(2)
    
    # Analizar resultados
    analyze_consistency(results)
    
    # Guardar resultados para análisis posterior
    with open('ley100_consistency_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("💾 Resultados guardados en 'ley100_consistency_results.json'")

if __name__ == "__main__":
    main()