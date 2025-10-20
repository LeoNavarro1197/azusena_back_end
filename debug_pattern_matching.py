#!/usr/bin/env python3
"""
Script para debuggear la detección de patrones
"""

import re

def test_pattern_matching():
    """Prueba los patrones de detección"""
    
    query = "hola azusena. quiero que me muestres los diez primeros articulos con su texto de la ley 100 de 1993"
    query_lower = query.lower()
    
    print(f"🔍 CONSULTA ORIGINAL:")
    print(f"   {query}")
    print(f"\n🔍 CONSULTA EN MINÚSCULAS:")
    print(f"   {query_lower}")
    print(f"\n{'='*80}")
    
    # Patrones originales
    original_patterns = [
        r'qu[eé]\s+art[ií]culos',
        r'cu[aá]les\s+art[ií]culos',
        r'lista\s+de\s+art[ií]culos',
        r'todos\s+los\s+art[ií]culos',
        r'art[ií]culos\s+sobre',
        r'art[ií]culos\s+relacionados',
        r'qu[eé]\s+normas',
        r'cu[aá]les\s+normas',
        r'dime\s+que\s+art[ií]culos',
        r'muestra\s+art[ií]culos',
        r'busca\s+art[ií]culos'
    ]
    
    # Nuevos patrones
    new_patterns = [
        r'primeros?\s+\d+\s+art[ií]culos',
        r'\d+\s+primeros?\s+art[ií]culos',
        r'art[ií]culos?\s+del?\s+\d+\s+al?\s+\d+',
        r'art[ií]culos?\s+\d+\s+al?\s+\d+',
        r'muestra\s+los?\s+\d+\s+primeros?\s+art[ií]culos',
        r'muestra\s+los?\s+primeros?\s+\d+\s+art[ií]culos',
        r'dame\s+los?\s+\d+\s+primeros?\s+art[ií]culos',
        r'dame\s+los?\s+primeros?\s+\d+\s+art[ií]culos',
        r'los?\s+\d+\s+primeros?\s+art[ií]culos',
        r'los?\s+primeros?\s+\d+\s+art[ií]culos'
    ]
    
    print("📋 PROBANDO PATRONES ORIGINALES:")
    for i, pattern in enumerate(original_patterns, 1):
        match = re.search(pattern, query_lower)
        status = "✅ COINCIDE" if match else "❌ NO COINCIDE"
        print(f"   {i:2d}. {pattern:<35} → {status}")
        if match:
            print(f"       Coincidencia: '{match.group()}'")
    
    print(f"\n📋 PROBANDO PATRONES NUEVOS:")
    for i, pattern in enumerate(new_patterns, 1):
        match = re.search(pattern, query_lower)
        status = "✅ COINCIDE" if match else "❌ NO COINCIDE"
        print(f"   {i:2d}. {pattern:<45} → {status}")
        if match:
            print(f"       Coincidencia: '{match.group()}'")
    
    # Probar patrones específicos que deberían funcionar
    print(f"\n🎯 PROBANDO PATRONES ESPECÍFICOS:")
    specific_patterns = [
        r'diez\s+primeros?\s+art[ií]culos',
        r'muestres?\s+los?\s+diez\s+primeros?\s+art[ií]culos',
        r'muestres?\s+los?\s+\d+\s+primeros?\s+art[ií]culos',
        r'que\s+me\s+muestres?\s+los?\s+\d+\s+primeros?\s+art[ií]culos'
    ]
    
    for i, pattern in enumerate(specific_patterns, 1):
        match = re.search(pattern, query_lower)
        status = "✅ COINCIDE" if match else "❌ NO COINCIDE"
        print(f"   {i:2d}. {pattern:<50} → {status}")
        if match:
            print(f"       Coincidencia: '{match.group()}'")

if __name__ == "__main__":
    test_pattern_matching()