#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import pandas as pd
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.vector_db import VectorDB

def check_database():
    """Verificar qué artículos hay en la base de datos"""
    try:
        # Inicializar VectorDB
        vector_db = VectorDB()
        
        # Obtener todos los documentos del DataFrame
        all_docs = vector_db.df.to_dict('records')
        
        print(f"📊 TOTAL DE DOCUMENTOS: {len(all_docs)}")
        print("\n" + "="*80)
        
        # Mostrar las columnas disponibles
        print(f"📋 COLUMNAS DISPONIBLES: {list(vector_db.df.columns)}")
        
        # Mostrar algunos ejemplos de documentos
        print(f"\n🔍 PRIMEROS 3 DOCUMENTOS:")
        for i, doc in enumerate(all_docs[:3]):
            print(f"\n{i+1}. Documento:")
            for key, value in doc.items():
                if pd.notna(value):
                    print(f"   {key}: {str(value)[:100]}...")
        
        # Filtrar por Ley 100 de 1993 usando diferentes campos
        ley_100_docs = []
        for doc in all_docs:
            doc_text = ' '.join([str(v).lower() for v in doc.values() if pd.notna(v)])
            if 'ley 100' in doc_text or '100 de 1993' in doc_text:
                ley_100_docs.append(doc)
        
        print(f"📋 DOCUMENTOS DE LEY 100: {len(ley_100_docs)}")
        
        if ley_100_docs:
            print("\n🔍 PRIMEROS 5 DOCUMENTOS DE LEY 100:")
            for i, doc in enumerate(ley_100_docs[:5]):
                print(f"\n{i+1}. Artículo: {doc.get('article_number', 'N/A')}")
                print(f"   Fuente: {doc.get('source', 'N/A')}")
                print(f"   Título: {doc.get('title', 'N/A')[:100]}...")
                print(f"   Contenido: {doc.get('content', 'N/A')[:150]}...")
        
        # Verificar diferentes variaciones del nombre
        variations = ['ley 100', 'ley100', '100 de 1993', 'ley 100 de 1993']
        print(f"\n🔍 BÚSQUEDA POR VARIACIONES:")
        for variation in variations:
            matching_docs = [doc for doc in all_docs if variation in doc.get('source', '').lower()]
            print(f"   '{variation}': {len(matching_docs)} documentos")
            
        # Mostrar todas las fuentes únicas
        sources = set(doc.get('source', 'Sin fuente') for doc in all_docs)
        print(f"\n📚 FUENTES DISPONIBLES ({len(sources)}):")
        for source in sorted(sources):
            count = len([doc for doc in all_docs if doc.get('source') == source])
            print(f"   - {source}: {count} documentos")
            
    except Exception as e:
        print(f"❌ Error al verificar la base de datos: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_database()