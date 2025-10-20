#!/usr/bin/env python3
"""
Script para probar la nueva funcionalidad de listado de primeros artículos
"""

import sys
import os

# Agregar el directorio raíz del proyecto al path
sys.path.insert(0, os.path.abspath('.'))

from app.query import QueryRAGSystem

def test_first_articles_query():
    """Prueba la consulta de primeros artículos"""
    
    # Inicializar el procesador de consultas
    query_processor = QueryRAGSystem()
    
    # Consulta de prueba
    test_query = "hola azusena. quiero que me muestres los diez primeros articulos con su texto de la ley 100 de 1993"
    
    print(f"🔍 CONSULTA DE PRUEBA:")
    print(f"   {test_query}")
    print(f"\n{'='*80}")
    
    try:
        # Ejecutar la consulta
        response, similarity, used_kb = query_processor.query_rag(test_query)
        
        print(f"📋 RESPUESTA:")
        print(f"   {response}")
        print(f"\n📊 MÉTRICAS:")
        print(f"   Similitud: {similarity:.3f}")
        print(f"   Base de conocimiento usada: {used_kb}")
        print(f"\n{'='*80}")
        
        # Verificar si se detectó correctamente como consulta de listado
        is_list_query = query_processor.is_article_list_query(test_query)
        print(f"🎯 DETECCIÓN:")
        print(f"   ¿Es consulta de listado?: {is_list_query}")
        
        if is_list_query and "ARTÍCULO 1" in response:
            print(f"   ✅ ÉXITO: Se detectó correctamente y devolvió artículos ordenados")
        elif is_list_query:
            print(f"   ⚠️  PARCIAL: Se detectó como listado pero la respuesta puede no ser la esperada")
        else:
            print(f"   ❌ FALLO: No se detectó como consulta de listado")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_first_articles_query()