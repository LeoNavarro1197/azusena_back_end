import faiss
import numpy as np
import os
import csv
import pandas as pd

# clase que se encarga de definir la base de datos vectorial por medio del motor FAISS
class FaissDB:
    def __init__(self, index_path="faiss_index.bin", doc_path="faiss_index.txt"):
        self.dimension = 4096
        self.index_path = index_path
        self.doc_path = doc_path
        self.documents = []
        self.index = self._load_or_create_index()

    def _load_or_create_index(self):
        """Carga un índice Faiss existente o crea uno nuevo."""
        if os.path.exists(self.index_path) and os.path.exists(self.doc_path):
            try:
                # Carga el índice
                print("Índice de Faiss y documentos cargados con éxito desde 'faiss_index.bin'")
                index = faiss.read_index(self.index_path)
                
                # Carga los documentos
                self.documents = []
                with open(self.doc_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if row:
                            self.documents.append(row[0])

                return index
            except Exception as e:
                print(f"Error al cargar el índice o los documentos: {e}. Creando un nuevo índice.")
        
        # Crear un nuevo índice si no existe o hubo un error al cargar
        print("No se encontró un índice de Faiss existente. Se creará uno nuevo.")
        return faiss.IndexFlatL2(self.dimension)

    def add_document(self, document: str, embedding: np.ndarray):
        """Añade un documento y su embedding al índice."""
        # Redimensionar el embedding si es necesario para que sea bidimensional
        if embedding.ndim == 1:
            embedding = embedding.reshape(1, -1)
        
        # Comprobar las dimensiones del embedding antes de añadirlo
        if embedding.shape[1] != self.dimension:
            raise ValueError(f"La dimensión del embedding ({embedding.shape[1]}) no coincide con la del índice ({self.dimension}).")
        # añadir el embedding
        self.index.add(embedding)
        self.documents.append(document)
        print(f"Documento añadido con ID: {len(self.documents) - 1}")
        self._save_index()

    def search(self, query_embedding: np.ndarray, k: int = 5) -> list:
        """Busca los k documentos más similares a la consulta."""
        # Verificar si el índice está vacío
        if self.index.ntotal == 0:
            print("El índice de Faiss está vacío. Devolviendo una lista vacía de documentos.")
            return []

        # Redimensionar el embedding de la consulta si es necesario
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)

        # Realizar la búsqueda
        D, I = self.index.search(query_embedding, k)
        
        # Obtener los documentos relevantes basados en los índices encontrados
        relevant_docs = [self.documents[i] for i in I[0] if i < len(self.documents)]
        
        return relevant_docs

    def _save_index(self):
        """Guarda el índice y los documentos en archivos."""
        faiss.write_index(self.index, self.index_path)
        with open(self.doc_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for doc in self.documents:
                writer.writerow([doc])
        print(f"Índice de Faiss y documentos guardados en '{self.index_path}'")
