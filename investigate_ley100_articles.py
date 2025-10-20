#!/usr/bin/env python3
"""
Script para investigar artículos específicos de la Ley 100 en la base de conocimientos
"""

import pandas as pd
import re
from pathlib import Path

def search_ley100_articles():
    """Busca artículos específicos de la Ley 100 en la base de conocimientos"""
    
    # Cargar el archivo Excel
    excel_path = Path("data/Compilado_Preguntas_Azusena.xlsx")
    
    if not excel_path.exists():
        print(f"❌ No se encontró el archivo: {excel_path}")
        return
    
    print("📊 INVESTIGACIÓN DE ARTÍCULOS LEY 100")
    print("=" * 60)
    
    try:
        # Leer el archivo Excel
        df = pd.read_excel(excel_path)
        print(f"✅ Archivo cargado exitosamente: {len(df)} registros")
        print(f"📋 Columnas disponibles: {list(df.columns)}")
        print()
        
        # Buscar menciones de artículos específicos
        articles_to_search = ['186', '227', '106', '3', '182']
        
        for article_num in articles_to_search:
            print(f"🔍 BUSCANDO ARTÍCULO {article_num}")
            print("-" * 40)
            
            # Buscar en todas las columnas de texto
            found_records = []
            
            for col in df.columns:
                if df[col].dtype == 'object':  # Solo columnas de texto
                    # Buscar patrones como "artículo 186", "art. 186", "Art 186", etc.
                    pattern = rf'(?i)art[íi]?[culo]*\.?\s*{article_num}(?!\d)'
                    matches = df[df[col].astype(str).str.contains(pattern, na=False, regex=True)]
                    
                    if not matches.empty:
                        for idx, row in matches.iterrows():
                            found_records.append({
                                'index': idx,
                                'column': col,
                                'content': str(row[col])[:200] + "..." if len(str(row[col])) > 200 else str(row[col]),
                                'tema': row.get('tema', 'N/A'),
                                'subtema': row.get('subtema', 'N/A')
                            })
            
            if found_records:
                print(f"✅ Encontradas {len(found_records)} menciones del artículo {article_num}:")
                for i, record in enumerate(found_records, 1):
                    print(f"  {i}. Fila {record['index']} - Columna: {record['column']}")
                    print(f"     Tema: {record['tema']}")
                    print(f"     Subtema: {record['subtema']}")
                    print(f"     Contenido: {record['content']}")
                    print()
            else:
                print(f"❌ No se encontraron menciones del artículo {article_num}")
            
            print()
        
        # Buscar términos relacionados con "calidad"
        print("🔍 BUSCANDO TÉRMINOS RELACIONADOS CON CALIDAD")
        print("-" * 50)
        
        quality_terms = ['calidad', 'acreditación', 'auditoría', 'transparencia', 'normas']
        
        for term in quality_terms:
            print(f"🔎 Buscando: '{term}'")
            
            found_count = 0
            for col in df.columns:
                if df[col].dtype == 'object':
                    pattern = rf'(?i){term}'
                    matches = df[df[col].astype(str).str.contains(pattern, na=False, regex=True)]
                    found_count += len(matches)
            
            print(f"   Encontradas {found_count} menciones")
        
        print()
        
        # Buscar específicamente "Ley 100"
        print("🔍 BUSCANDO MENCIONES DE 'LEY 100'")
        print("-" * 40)
        
        ley100_pattern = r'(?i)ley\s*100'
        total_ley100 = 0
        
        for col in df.columns:
            if df[col].dtype == 'object':
                matches = df[df[col].astype(str).str.contains(ley100_pattern, na=False, regex=True)]
                if not matches.empty:
                    print(f"📄 Columna '{col}': {len(matches)} menciones")
                    total_ley100 += len(matches)
                    
                    # Mostrar algunos ejemplos
                    for idx, row in matches.head(3).iterrows():
                        content = str(row[col])[:150] + "..." if len(str(row[col])) > 150 else str(row[col])
                        print(f"   Ejemplo: {content}")
        
        print(f"📊 Total menciones de 'Ley 100': {total_ley100}")
        
    except Exception as e:
        print(f"❌ Error al procesar el archivo: {e}")

if __name__ == "__main__":
    search_ley100_articles()