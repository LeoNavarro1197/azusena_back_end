import asyncio
import numpy as np
from database.faiss_db import FaissDB
from llm.ollama_model import OllamaModel
import whisper
from fastapi import UploadFile
import os
import re

class RAGService:
    def __init__(self, db: FaissDB, llm: OllamaModel):
        self.db = db
        self.llm = llm

    def _classify_query(self, query: str) -> str:
        """
        Clasifica el tipo de consulta para determinar el nivel de RAG necesario.
        
        Returns:
        - 'simple_greeting': Solo saludo simple
        - 'mixed_query': Saludo + solicitud de información
        - 'specific_query': Consulta específica sin saludo
        """
        query_lower = query.lower().strip()
        
        # Patrones de saludos simples (incluyendo variaciones con comas y sin acentos)
        simple_greetings = [
            r'^(hola|hello|hi|buenos días|buenas tardes|buenas noches|saludos)[,\s]*\.?$',
            r'^(hola|hello|hi)[,\s]*(azusena|sena)?[,\s]*\.?$',
            r'^(qué tal|cómo estás|como estas|cómo está|como esta)[,\s]*\.?\??$',
            r'^(buenas|buen día)[,\s]*\.?$',
            r'^(hola)[,\s]+(qué tal|cómo estás|como estas|cómo está|como esta)[,\s]*\.?\??$'
        ]
        
        # Patrones de palabras clave que indican solicitud de información específica
        info_keywords = [
            r'\b(información|datos|requisitos|proceso|procedimiento|trámite)\b',
            r'\b(sena|aprendiz|instructor|curso|programa|certificado)\b',
            r'\b(ley|norma|decreto|resolución|reglamento)\b',
            r'\b(afiliación|salud|pensión|riesgos|seguridad social)\b',
            r'\b(jubilación|retiro|beneficios|seguros)\b'
        ]
        
        # Verificar si es solo un saludo simple
        is_simple_greeting = any(re.match(pattern, query_lower) for pattern in simple_greetings)
        
        # Verificar si contiene solicitud de información específica
        has_info_request = any(re.search(pattern, query_lower) for pattern in info_keywords)
        
        if is_simple_greeting and not has_info_request:
            return 'simple_greeting'
        elif has_info_request:
            return 'mixed_query' if is_simple_greeting else 'specific_query'
        else:
            # Si no es un saludo simple reconocido, tratarlo como consulta específica
            return 'specific_query'

    def _filter_relevant_docs(self, docs: list, query: str, max_docs: int = 3) -> list:
        """
        Filtra documentos relevantes con mayor precisión semántica.
        """
        if not docs:
            return []
        
        # Palabras clave que indican documentos de comportamiento/saludos que queremos evitar para consultas técnicas
        behavior_keywords = [
            'saludo', 'cortesía', 'comportamiento', 'identidad', 'directrices',
            'greeting', 'courtesy', 'behavior', 'identity', 'guidelines',
            'presentación', 'introducción', 'bienvenida', 'filosofía pedagógica'
        ]
        
        # Palabras clave técnicas que indican contenido relevante
        technical_keywords = [
            'ley', 'artículo', 'decreto', 'resolución', 'procedimiento', 'requisito',
            'trámite', 'normativa', 'reglamento', 'código', 'estatuto', 'ordenanza',
            'sena', 'formación', 'aprendiz', 'instructor', 'programa', 'curso',
            'certificación', 'competencia', 'evaluación', 'titulación'
        ]
        
        filtered_docs = []
        query_lower = query.lower()
        
        # Determinar si la consulta busca información técnica específica
        is_technical_query = any(keyword in query_lower for keyword in technical_keywords)
        
        for doc in docs:
            doc_content = doc.get('content', '').lower() if isinstance(doc, dict) else doc.lower()
            doc_score = 0
            
            # Calcular relevancia del documento
            if is_technical_query:
                # Para consultas técnicas, priorizar documentos con contenido técnico
                technical_matches = sum(1 for keyword in technical_keywords if keyword in doc_content)
                behavior_matches = sum(1 for keyword in behavior_keywords if keyword in doc_content)
                
                # Penalizar documentos que son principalmente sobre comportamiento
                if behavior_matches > technical_matches and technical_matches == 0:
                    continue  # Saltar documentos puramente de comportamiento
                
                doc_score = technical_matches - (behavior_matches * 0.5)
            else:
                # Para consultas generales, permitir más flexibilidad
                doc_score = 1
            
            # Verificar relevancia directa con palabras de la consulta
            query_words = query_lower.split()
            content_matches = sum(1 for word in query_words if len(word) > 3 and word in doc_content)
            doc_score += content_matches
            
            if doc_score > 0:
                if isinstance(doc, dict):
                    doc['relevance_score'] = doc_score
                    filtered_docs.append(doc)
                else:
                    filtered_docs.append({'content': doc, 'relevance_score': doc_score})
        
        # Ordenar por relevancia y tomar los mejores
        filtered_docs.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        # Retornar en el formato original
        result = []
        for doc in filtered_docs[:max_docs]:
            if isinstance(doc, dict) and 'content' in doc:
                result.append(doc['content'])
            else:
                result.append(doc)
        
        return result

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
        Consulta documentos usando RAG con clasificación inteligente de consultas.
        """
        try:
            print(f"[RAG] Procesando consulta: {query}")
            
            # Clasificar el tipo de consulta
            query_type = self._classify_query(query)
            print(f"[RAG] Tipo de consulta detectado: {query_type}")
            
            # Para saludos simples, usar RAG mínimo o ninguno
            if query_type == 'simple_greeting':
                print(f"[RAG] Procesando saludo simple sin RAG extensivo")
                # Generar respuesta directa sin documentos adicionales
                full_response = ""
                async for chunk in self.llm.generate(prompt=query, relevant_docs=[]):
                    full_response += chunk
                return full_response
            
            # Para consultas específicas o mixtas, usar RAG completo
            print(f"[RAG] Generando embeddings para la consulta...")
            query_embedding = await self.llm.get_embeddings(query)
            
            if query_embedding is None:
                print(f"[RAG] Error: No se pudieron generar embeddings")
                return "Lo siento, no pude procesar tu consulta. Por favor, intenta de nuevo."
            
            # Convertir el embedding a un array de NumPy
            print(f"[RAG] Convirtiendo embedding a numpy array...")
            query_embedding_np = np.array(query_embedding).astype('float32')
            print(f"[RAG] Array numpy creado con shape: {query_embedding_np.shape}")
            
            print(f"[RAG] Buscando documentos similares...")
            # Ajustar el número de documentos según el tipo de consulta
            k = 3 if query_type == 'mixed_query' else 5
            similar_docs = self.db.search(query_embedding_np, k=k)
            
            if not similar_docs:
                print(f"[RAG] No se encontraron documentos similares")
                return "Lo siento, no encontré información relevante para tu consulta."
            
            # Filtrar documentos relevantes
            relevant_docs = self._filter_relevant_docs(similar_docs, query, max_docs=3)
            print(f"[RAG] Documentos filtrados: {len(relevant_docs)}")
            
            if not relevant_docs:
                print(f"[RAG] No se encontraron documentos relevantes después del filtrado")
                return "Lo siento, no encontré información específica para tu consulta."
            
            # Generar la respuesta usando el LLM
            print(f"[RAG] Generando respuesta con LLM...")
            full_response = ""
            async for chunk in self.llm.generate(prompt=query, relevant_docs=relevant_docs):
                full_response += chunk
            
            print(f"[RAG] Respuesta generada exitosamente: {len(full_response)} caracteres")
            return full_response

        except Exception as e:
            print(f"[RAG] Error en la consulta: {e}")
            print(f"[RAG] Tipo de error: {type(e)}")
            import traceback
            print(f"[RAG] Traceback completo: {traceback.format_exc()}")
            return "Lo siento, no pude procesar la consulta. Por favor, intenta de nuevo más tarde."
