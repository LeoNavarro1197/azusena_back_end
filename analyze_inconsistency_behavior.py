#!/usr/bin/env python3
"""
Script para analizar el comportamiento inconsistente del sistema RAG
Simula el problema reportado por Azusena
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.vector_db import vector_db
from app.query import query_rag_system
import json
import logging

# Configurar logging para ver detalles
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def analyze_query_behavior(query_text, description):
    """Analiza el comportamiento detallado de una consulta"""
    print(f"\n{'='*80}")
    print(f"🔍 ANÁLISIS: {description}")
    print(f"📝 CONSULTA: {query_text}")
    print(f"{'='*80}")
    
    # 1. Análisis de búsqueda vectorial directa
    print("\n1️⃣ BÚSQUEDA VECTORIAL DIRECTA:")
    print("-" * 50)
    
    try:
        # Obtener resultados directos de FAISS
        top_results = vector_db.get_top_results(query_text, top_k=10)
        
        if top_results:
            print(f"✅ Se encontraron {len(top_results)} resultados")
            for i, result in enumerate(top_results[:5], 1):
                data = result['data']
                similarity = result['similarity']
                print(f"   {i}. Art. {data.get('articulo', 'N/A')} - Similitud: {similarity:.4f}")
                print(f"      Tema: {data.get('tema', 'N/A')}")
                print(f"      Subtema: {data.get('subtema', 'N/A')}")
                print(f"      Fuente: {data.get('fuente', 'N/A')}")
                print()
        else:
            print("❌ No se encontraron resultados")
    except Exception as e:
        print(f"❌ Error en búsqueda vectorial: {e}")
    
    # 2. Análisis del sistema RAG completo
    print("\n2️⃣ SISTEMA RAG COMPLETO:")
    print("-" * 50)
    
    try:
        response, similarity, used_kb = query_rag_system.query_rag(query_text)
        print(f"✅ Respuesta generada:")
        print(f"   📊 Similitud: {similarity:.4f}")
        print(f"   📚 Usó KB: {used_kb}")
        print(f"   📄 Respuesta (primeros 300 chars): {response[:300]}...")
        
        # Analizar la respuesta para detectar inconsistencias
        analyze_response_consistency(query_text, response)
        
    except Exception as e:
        print(f"❌ Error en sistema RAG: {e}")
    
    # 3. Análisis de artículos específicos mencionados
    print("\n3️⃣ VERIFICACIÓN DE ARTÍCULOS MENCIONADOS:")
    print("-" * 50)
    
    # Extraer números de artículos de la respuesta
    import re
    if 'response' in locals():
        article_numbers = re.findall(r'art[íi]culo\s*(\d+)', response.lower())
        if article_numbers:
            print(f"📋 Artículos mencionados en la respuesta: {article_numbers}")
            for art_num in set(article_numbers):  # Eliminar duplicados
                verify_article_existence(art_num)
        else:
            print("ℹ️  No se mencionaron artículos específicos en la respuesta")

def analyze_response_consistency(query_text, response):
    """Analiza la consistencia de la respuesta con respecto a la consulta"""
    print("\n   🔍 ANÁLISIS DE CONSISTENCIA:")
    
    query_lower = query_text.lower()
    response_lower = response.lower()
    
    # Verificar consistencia temática
    if 'calidad' in query_lower:
        if 'calidad' in response_lower:
            print("   ✅ Consistencia temática: La respuesta menciona 'calidad'")
        else:
            print("   ⚠️  INCONSISTENCIA: Consulta sobre 'calidad' pero respuesta no la menciona")
    
    # Verificar artículos mencionados
    import re
    query_articles = re.findall(r'art[íi]culo\s*(\d+)', query_lower)
    response_articles = re.findall(r'art[íi]culo\s*(\d+)', response_lower)
    
    if query_articles:
        print(f"   📋 Artículos en consulta: {query_articles}")
        print(f"   📋 Artículos en respuesta: {response_articles}")
        
        # Verificar si los artículos de la consulta aparecen en la respuesta
        for art in query_articles:
            if art in response_articles:
                print(f"   ✅ Artículo {art} mencionado correctamente")
            else:
                print(f"   ⚠️  INCONSISTENCIA: Artículo {art} solicitado pero no mencionado en respuesta")

def verify_article_existence(article_number):
    """Verifica si un artículo específico existe en la base de datos"""
    try:
        response, similarity, used_kb = vector_db.get_article_details(article_number)
        
        if "❌ **Artículo No Encontrado**" in response:
            print(f"   ❌ Artículo {article_number}: NO EXISTE en la base de datos")
        else:
            print(f"   ✅ Artículo {article_number}: EXISTE en la base de datos")
            # Extraer información básica
            lines = response.split('\n')
            for line in lines:
                if line.startswith('**Fuente:**'):
                    print(f"      Fuente: {line.replace('**Fuente:**', '').strip()}")
                elif line.startswith('**Tema:**'):
                    print(f"      Tema: {line.replace('**Tema:**', '').strip()}")
                    break
    except Exception as e:
        print(f"   ❌ Error verificando artículo {article_number}: {e}")

def simulate_azusena_conversation():
    """Simula la conversación problemática reportada con Azusena"""
    print("\n" + "="*100)
    print("🤖 SIMULACIÓN DE CONVERSACIÓN PROBLEMÁTICA CON AZUSENA")
    print("="*100)
    
    # Primera consulta (la original)
    analyze_query_behavior(
        "cuales son los articulos que hablan sobre calidad en la ley 100 del 93",
        "Consulta Original de Azusena"
    )
    
    # Segunda consulta (seguimiento problemático)
    analyze_query_behavior(
        "dame mas detalles sobre esos articulos",
        "Consulta de Seguimiento Problemática"
    )
    
    # Consultas específicas para verificar artículos mencionados
    analyze_query_behavior(
        "que dice exactamente el articulo 186 de la ley 100",
        "Verificación Artículo 186"
    )
    
    analyze_query_behavior(
        "que dice exactamente el articulo 227 de la ley 100",
        "Verificación Artículo 227"
    )

def analyze_context_switching():
    """Analiza por qué el sistema cambia de contexto"""
    print("\n" + "="*100)
    print("🔄 ANÁLISIS DE CAMBIO DE CONTEXTO")
    print("="*100)
    
    # Simular consultas secuenciales para ver cómo cambia el contexto
    queries = [
        "cuales son los articulos sobre calidad en la ley 100",
        "dame mas informacion sobre esos articulos",
        "que dice el articulo 186",
        "y el articulo 227",
        "explicame sobre calidad en salud ley 100"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n🔢 CONSULTA SECUENCIAL {i}:")
        print(f"📝 {query}")
        
        try:
            response, similarity, used_kb = query_rag_system.query_rag(query)
            print(f"📊 Similitud: {similarity:.4f} | KB: {used_kb}")
            print(f"📄 Respuesta: {response[:200]}...")
            
            # Extraer artículos mencionados
            import re
            articles = re.findall(r'art[íi]culo\s*(\d+)', response.lower())
            if articles:
                print(f"📋 Artículos mencionados: {articles}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 80)

def main():
    """Función principal"""
    print("🧪 ANÁLISIS DETALLADO DEL COMPORTAMIENTO INCONSISTENTE")
    print("="*80)
    
    # 1. Simular la conversación problemática
    simulate_azusena_conversation()
    
    # 2. Analizar cambio de contexto
    analyze_context_switching()
    
    # 3. Generar reporte de hallazgos
    print("\n" + "="*100)
    print("📊 RESUMEN DE HALLAZGOS")
    print("="*100)
    
    print("""
    🔍 PROBLEMAS IDENTIFICADOS:
    
    1. INCONSISTENCIA EN ARTÍCULOS MENCIONADOS:
       - El sistema puede mencionar artículos que no existen en la base de datos
       - Cambio de artículos entre consultas relacionadas
    
    2. PÉRDIDA DE CONTEXTO:
       - Las consultas de seguimiento no mantienen el contexto de la consulta anterior
       - El sistema trata cada consulta como independiente
    
    3. FALTA DE VALIDACIÓN:
       - No hay verificación de que los artículos mencionados existan realmente
       - No hay validación de consistencia temática
    
    4. PROBLEMAS DE RECUPERACIÓN:
       - Los umbrales de similitud pueden estar causando recuperación incorrecta
       - La ponderación de similitud puede estar priorizando resultados irrelevantes
    
    💡 RECOMENDACIONES:
    
    1. Implementar validación de artículos antes de mencionarlos
    2. Mejorar el manejo de contexto conversacional
    3. Añadir verificación de consistencia temática
    4. Revisar y ajustar umbrales de similitud
    5. Implementar logging detallado para debugging
    """)

if __name__ == "__main__":
    main()