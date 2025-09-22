import os
import sys
import pandas as pd
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
import asyncio

# Añade la raíz del proyecto al sys.path para permitir importaciones
# de módulos de otras carpetas como 'services' y 'database'.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importaciones directas de los componentes del proyecto
from services.rag_service import RAGService
from database.faiss_db import FaissDB
from llm.ollama_model import OllamaModel

# Configuración del script
DATA_DIR = "data_preprocessing/raw_data"
# La ruta al archivo de datos que quieres ingestar.
# Puedes usar un CSV, TXT o PDF.
DATA_FILE = "data_compilado.csv" 
# Si usas un CSV, especifica las columnas de texto relevantes.
# Si usas un TXT o PDF, esta lista puede estar vacía.
COLUMNS_TO_INGEST = ['fuente', 'articulo', 'tema', 'subtema', 'texto del articulo',
       'categorias', 'resumen explicativo']
# Configuración del fragmentador de texto
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

def get_file_path(filename: str) -> str:
    """Retorna la ruta completa del archivo de datos."""
    return os.path.join(os.getcwd(), DATA_DIR, filename)

def read_and_chunk_file(file_path: str, columns_to_ingest: List[str] = None) -> List[str]:
    """
    Lee un archivo (CSV, TXT, PDF) y lo divide en fragmentos de texto.
    """
    documents = []
    file_extension = os.path.splitext(file_path)[1].lower()
    
    try:
        if file_extension == '.csv':
            if not columns_to_ingest:
                print("Error: Se requiere una lista de columnas para ingestar datos desde un CSV.")
                return []
            df = pd.read_csv(file_path)
            # Concatena las columnas de texto relevantes
            for _, row in df.iterrows():
                concatenated_text = " ".join([str(row[col]) for col in columns_to_ingest if col in row])
                documents.append(concatenated_text)
        elif file_extension == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                documents.append(f.read())
        elif file_extension == '.pdf':
            # Usa PyMuPDF para extraer texto de PDFs
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            full_text = ""
            for page in doc:
                full_text += page.get_text()
            documents.append(full_text)
            doc.close()
        else:
            print(f"Formato de archivo no soportado: {file_extension}")
            return []

    except FileNotFoundError:
        print(f"Error: El archivo '{file_path}' no se encontró.")
        return []
    except Exception as e:
        print(f"Ocurrió un error al leer el archivo: {e}")
        return []
    
    # Fragmenta el texto de los documentos
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        is_separator_regex=False
    )
    
    chunks = text_splitter.split_text(" ".join(documents))
    print(f"Documento fragmentado en {len(chunks)} partes.")
    return chunks

async def main():
    """
    Función principal para orquestar el proceso de ingesta.
    """
    file_path = get_file_path(DATA_FILE)
    print(f"Iniciando la ingesta de documentos desde '{file_path}'...")
    
    # Lee y fragmenta los documentos
    try:
        documents_to_ingest = read_and_chunk_file(file_path, COLUMNS_TO_INGEST)
    except Exception as e:
        print(f"No se pudieron leer los documentos. Error: {e}")
        documents_to_ingest = []

    if not documents_to_ingest:
        print("No se encontraron documentos para ingestar. Por favor, revisa el archivo de datos.")
        return
        
    # Inicializa los servicios directamente
    llm_model = OllamaModel()
    faiss_db = FaissDB()
    rag_service = RAGService(ollama_model=llm_model, faiss_db=faiss_db)
    
    # Ingesta cada fragmento de documento
    for i, chunk in enumerate(documents_to_ingest):
        try:
            print(f"Ingestando fragmento {i+1}/{len(documents_to_ingest)}...")
            await rag_service.ingest_document(chunk)
        except Exception as e:
            print(f"Error al ingestar el fragmento {i+1}: {e}")

    print("Proceso de ingesta finalizado. El índice de Faiss ha sido guardado.")

if __name__ == "__main__":
    asyncio.run(main())
