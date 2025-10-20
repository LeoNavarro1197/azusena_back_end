#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para probar consultas específicas sobre el sistema de salud colombiano
"""

import requests
import json
import time

def test_query(query_text):
    """Envía una consulta al endpoint y retorna la respuesta formateada"""
    try:
        url = "http://127.0.0.1:5000/query"
        payload = {"query": query_text}
        
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        return {
            'query': query_text,
            'response': data.get('response', 'Sin respuesta'),
            'similarity': data.get('similarity', 0.0),
            'used_kb': data.get('used_kb', False),
            'status': 'success'
        }
    except requests.exceptions.RequestException as e:
        return {
            'query': query_text,
            'response': f'Error de conexión: {str(e)}',
            'similarity': 0.0,
            'used_kb': False,
            'status': 'error'
        }
    except Exception as e:
        return {
            'query': query_text,
            'response': f'Error inesperado: {str(e)}',
            'similarity': 0.0,
            'used_kb': False,
            'status': 'error'
        }

def print_result(result):
    """Imprime el resultado de una consulta de forma formateada"""
    print("=" * 80)
    print(f"CONSULTA: {result['query']}")
    print("=" * 80)
    print(f"RESPUESTA: {result['response']}")
    print(f"SIMILITUD: {result['similarity']:.4f}")
    print(f"USÓ KB: {result['used_kb']}")
    print(f"STATUS: {result['status']}")
    print("=" * 80)
    print()

def main():
    """Función principal que ejecuta todas las pruebas"""
    print("🔍 INICIANDO PRUEBAS DE CONSULTAS SOBRE SISTEMA DE SALUD COLOMBIANO")
    print("=" * 80)
    
    # Lista de consultas sobre el sistema de salud
    queries = [
        "¿Qué documentos son necesarios para afiliar a un usuario al SGSSS?",
        "¿Cuál es el rol del SISBEN en la afiliación al sistema de salud?",
        "¿Qué es la movilidad entre regímenes en el SGSSS?",
        "¿Cómo se hace el traslado de EPS en Colombia?",
        "¿Qué derechos y deberes tienen los usuarios del sistema de salud?",
        "¿Qué pasos se deben seguir para resolver una queja de un usuario?",
        "¿Qué información debe contener una PQRS?",
        "¿Qué es la referencia y contrarreferencia en salud?",
        "¿Qué requisitos se deben cumplir para el acceso a servicios no POS?"
    ]
    
    results = []
    
    for i, query in enumerate(queries, 1):
        print(f"📋 Procesando consulta {i}/{len(queries)}...")
        result = test_query(query)
        results.append(result)
        print_result(result)
        
        # Pausa breve entre consultas para no sobrecargar el servidor
        if i < len(queries):
            time.sleep(1)
    
    # Generar diagnóstico
    print("\n" + "=" * 80)
    print("📊 DIAGNÓSTICO DE RESULTADOS")
    print("=" * 80)
    
    successful_queries = [r for r in results if r['status'] == 'success']
    error_queries = [r for r in results if r['status'] == 'error']
    kb_used_queries = [r for r in results if r['used_kb']]
    high_similarity = [r for r in results if r['similarity'] > 0.5]
    medium_similarity = [r for r in results if 0.3 <= r['similarity'] <= 0.5]
    low_similarity = [r for r in results if r['similarity'] < 0.3]
    
    print(f"✅ Consultas exitosas: {len(successful_queries)}/{len(queries)}")
    print(f"❌ Consultas con error: {len(error_queries)}/{len(queries)}")
    print(f"📚 Consultas que usaron KB: {len(kb_used_queries)}/{len(queries)}")
    print(f"🎯 Similitud alta (>0.5): {len(high_similarity)}/{len(queries)}")
    print(f"🎯 Similitud media (0.3-0.5): {len(medium_similarity)}/{len(queries)}")
    print(f"🎯 Similitud baja (<0.3): {len(low_similarity)}/{len(queries)}")
    
    if kb_used_queries:
        avg_similarity_kb = sum(r['similarity'] for r in kb_used_queries) / len(kb_used_queries)
        print(f"📈 Similitud promedio (con KB): {avg_similarity_kb:.4f}")
    
    if successful_queries:
        avg_similarity_all = sum(r['similarity'] for r in successful_queries) / len(successful_queries)
        print(f"📈 Similitud promedio (general): {avg_similarity_all:.4f}")
    
    print("\n🔍 ANÁLISIS DETALLADO:")
    
    if high_similarity:
        print(f"\n✅ CONSULTAS CON ALTA RELEVANCIA ({len(high_similarity)}):")
        for result in high_similarity:
            print(f"  • {result['query'][:60]}... (Similitud: {result['similarity']:.4f})")
    
    if medium_similarity:
        print(f"\n⚠️  CONSULTAS CON RELEVANCIA MEDIA ({len(medium_similarity)}):")
        for result in medium_similarity:
            print(f"  • {result['query'][:60]}... (Similitud: {result['similarity']:.4f})")
    
    if low_similarity:
        print(f"\n❌ CONSULTAS CON BAJA RELEVANCIA ({len(low_similarity)}):")
        for result in low_similarity:
            print(f"  • {result['query'][:60]}... (Similitud: {result['similarity']:.4f})")
    
    if error_queries:
        print(f"\n🚨 CONSULTAS CON ERRORES ({len(error_queries)}):")
        for result in error_queries:
            print(f"  • {result['query'][:60]}... (Error: {result['response'][:50]}...)")
    
    print("\n" + "=" * 80)
    print("✅ PRUEBAS DE SISTEMA DE SALUD COMPLETADAS")
    print("=" * 80)

if __name__ == "__main__":
    main()