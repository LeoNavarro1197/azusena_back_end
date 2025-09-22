import asyncio
import numpy as np
from database.faiss_db import FaissDB
from llm.ollama_model import OllamaModel
import whisper
from fastapi import UploadFile
import os

class RAGService:
    def __init__(self, db: FaissDB, llm: OllamaModel):
        self.db = db
        self.llm = llm

    async def ingest_document(self, document: str):
        """
        Ingesta un documento en el índice de Faiss y lo almacena.
        """
        try:
            print(f"Obteniendo embedding para el documento...")
            embedding = await self.llm.get_embeddings(document)
            if not embedding:
                raise ValueError("No se pudo obtener el embedding para el documento.")
            
            # Convierte la lista de embeddings a un array de NumPy
            embedding_np = np.array(embedding).astype('float32')

            self.db.add_document(document, embedding_np)
            return {"message": "Documento ingestado con éxito."}
        except Exception as e:
            print(f"Error en la ingesta del documento: {e}")
            return {"message": f"Error en la ingesta del documento: {e}"}

    async def voice_to_text(self, path_audio_file):
        """
        convierte audio a texto usando el modelo de Whisper.
        se prueba con el "medium" por ser el más que tiene modelo con respuestas precisas más ligero.
        no obstante, se pueden elegir varios modelos qie son: "tiny" "base", "small", "medium" o "large"
        se empieza a ver una precisión funcional a partir me modelo "medium",
        los modelos "tiny" "base", "small", pueden ser una alternativa para entornos limitados, 
        pero muestran menor precisión.
        """
        voice_model = whisper.load_model("medium")
        audio_file = path_audio_file
        try:
            # Transcripción del audio
            print(f"Transcribiendo el archivo: {audio_file}...")
            #result = voice_model.transcribe(audio_file)
            result = await asyncio.to_thread(voice_model.transcribe, audio_file)
            # Imprime la transcripción
            print("\n--- Transcripción ---")
            print(result["text"])
            return result
        except FileNotFoundError:
            #print(f"Error: El archivo '{audio_file}' no fue encontrado. Por favor, asegúrate de que el archivo exista en la ruta especificada.")
            #return "no se pudo encontrar el archivo, por lo que no hay prompt de voz por parte del usuario"
            return None # Retorna None para manejar el error en el método principal
        except Exception as e:
            print(f"Ocurrió un error: {e}")
            #return "error desconocido con el archivo de audio, por lo que no hay prompt de voz por parte del usuario"
            return None
        
    async def process_voice_query(self, audio_file: UploadFile):
        """
        Recibe un archivo de audio, lo transcribe a texto y luego
        realiza una consulta RAG con el texto obtenido.
        """
        # Crear un archivo temporal para guardar el audio
        temp_file_path = f"temp_{audio_file.filename}"
        
        try:
            # 1. Guardar el archivo recibido en un archivo temporal
            with open(temp_file_path, "wb") as f:
                content = await audio_file.read()
                f.write(content)
            # 2. Transcribir el audio a texto
            transcription = await self.voice_to_text(temp_file_path)
            # 3. Validar si la transcripción fue exitosa
            if not transcription or "text" not in transcription or not transcription["text"]:
                return "Lo siento, no pude entender lo que dijiste. ¿Podrías repetirlo?"
            extracted_query_text = transcription["text"]
            print(f"Texto extraído del audio: '{extracted_query_text}'")
            # 4. Realizar la consulta RAG con el texto extraído
            response = await self.query_documents(extracted_query_text)
            return response

        except Exception as e:
            print(f"Error en el flujo de voz a texto y consulta: {e}")
            return "Lo siento, ocurrió un error inesperado al procesar tu solicitud."
        finally:
            # Asegúrate de eliminar el archivo temporal
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)



    async def query_documents(self, query: str):
        """
        Busca documentos relevantes y genera una respuesta con el LLM.
        """
        try:
            # Obtener el embedding de la consulta
            query_embedding = await self.llm.get_embeddings(query)
            if not query_embedding:
                return "Lo siento, no pude procesar la consulta. Por favor, intenta de nuevo más tarde."
            # Convertir el embedding a un array de NumPy
            query_embedding_np = np.array(query_embedding).astype('float32')
            # Buscar documentos relevantes
            relevant_docs = self.db.search(query_embedding_np, k=5)
            if not relevant_docs:
                return "Lo siento, no encontré información relevante en los documentos para responder a tu pregunta."
            # Generar la respuesta usando el LLM
            full_response = ""
            async for chunk in self.llm.generate(prompt=query, relevant_docs=relevant_docs):
                full_response += chunk
            return full_response

        except Exception as e:
            print(f"Error en la consulta: {e}")
            return "Lo siento, no pude procesar la consulta. Por favor, intenta de nuevo más tarde."
