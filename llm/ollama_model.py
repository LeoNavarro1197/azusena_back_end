import aiohttp
import json
import asyncio

class OllamaModel:
    def __init__(self, model_name="mistral:7b"):
        self.model_name = model_name
        self.ollama_api_url = "http://localhost:11434/api/chat"
        self.session = None
        self.messages = [
            {
                "role": "system",
                "content": """Nombre: AzuSENA
                Rol: Asistente virtual del Servicio Nacional de Aprendizaje (SENA) de Colombia.
                
                Directrices de Comportamiento:
                    1. Identidad: Eres AzuSENA, asistente virtual del SENA.
                    
                    2. Respuesta Adaptativa: 
                        ◦ Para saludos simples (hola, buenos días, etc.): Responde ÚNICAMENTE con un saludo breve y cordial. NO agregues información adicional.
                        ◦ Para consultas específicas: Proporciona información detallada y relevante basada en tu base de datos.
                        ◦ Para consultas mixtas: Responde al saludo brevemente y enfócate en la información solicitada.
                    
                    3. Tono: Mantén un tono profesional pero amigable. Sé directo y útil.
                    
                    4. Fuentes de Información: Utiliza prioritariamente la base de datos de conocimiento proporcionada. Si no tienes información, comunícalo claramente.
                    
                    5. Precisión: Proporciona respuestas precisas. Evita especular o inventar información.
                    
                    6. Formato: Respuesta en formato Markdown cuando sea apropiado.
                        
                Restricciones:
                    • Para saludos simples, NO menciones tus capacidades, funciones o información del SENA a menos que se pregunte específicamente.
                    • No te inventes información.
                    • No proporciones opiniones personales."""
            }
        ]

    async def get_embeddings(self, text: str):
        if self.session is None or self.session.closed:
            # Crear sesión con timeout más largo para que funcione en equipos de menor poder de computo.
            # no obstante en casos de bajo poder de computo la inferencia sera más lenta
            timeout = aiohttp.ClientTimeout(total=1200)  # 20 minutos
            self.session = aiohttp.ClientSession(timeout=timeout)
        
        headers = {'Content-Type': 'application/json'}
        payload = {
            "model": self.model_name,
            "prompt": text
        }
        
        try:
            async with self.session.post("http://localhost:11434/api/embeddings", headers=headers, json=payload) as response:
                if response.status != 200:
                    print(f"Error en la llamada a la API de Ollama: {response.status}")
                    return []
                
                data = await response.json()
                return data.get('embedding', [])
        except asyncio.TimeoutError:
            print(f"Timeout al obtener embeddings de Ollama")
            return []
        except Exception as e:
            print(f"Error al obtener embeddings: {e}")
            return []

    async def generate(self, prompt: str, relevant_docs: list):
        if self.session is None or self.session.closed:
            # Crear sesión con timeout más largo
            timeout = aiohttp.ClientTimeout(total=300)  # 5 minutos
            self.session = aiohttp.ClientSession(timeout=timeout)

        # Añade los documentos relevantes al contenido del mensaje del sistema para RAG
        if relevant_docs:
            # Limitar el tamaño de cada documento y el número total
            processed_docs = []
            total_chars = 0
            max_total_chars = 2000  # Límite total de caracteres para contexto RAG
            
            for doc in relevant_docs[:3]:  # Máximo 3 documentos
                # Truncar cada documento a máximo 800 caracteres
                doc_content = doc[:800] if len(doc) > 800 else doc
                
                if total_chars + len(doc_content) <= max_total_chars:
                    processed_docs.append(doc_content)
                    total_chars += len(doc_content)
                else:
                    # Añadir solo la parte que cabe
                    remaining_chars = max_total_chars - total_chars
                    if remaining_chars > 100:  # Solo si queda espacio significativo
                        processed_docs.append(doc_content[:remaining_chars])
                    break
            
            rag_prompt = self.messages[0]['content'] + "\n\nContexto relevante:\n" + "\n\n".join(processed_docs)
        else:
            rag_prompt = self.messages[0]['content']
            
        self.messages[0]['content'] = rag_prompt

        # Agrega el nuevo mensaje del usuario al historial de la conversación
        user_message = {"role": "user", "content": prompt}
        self.messages.append(user_message)
        
        payload = {
            "model": self.model_name,
            "messages": self.messages, # Pasa todo el historial de la conversación
            "stream": True,
            "options": {
                "temperature": 0.24
            }
        }

        assistant_response = ""
        try:
            print(f"Enviando request a Ollama con modelo: {self.model_name}")
            async with self.session.post(self.ollama_api_url, json=payload) as response:
                if response.status != 200:
                    print(f"Error en la respuesta de Ollama: {response.status}")
                    yield "Error: No se pudo conectar al modelo Ollama."
                    return
                
                print("Recibiendo respuesta de Ollama...")
                async for chunk in response.content.iter_any():
                    if not chunk:
                        continue
                    try:
                        chunk_str = chunk.decode('utf-8')
                        json_data = json.loads(chunk_str)
                        if 'content' in json_data['message']:
                            content_chunk = json_data['message']['content']
                            assistant_response += content_chunk
                            yield content_chunk
                    except json.JSONDecodeError as e:
                        print(f"Error de decodificación JSON en la respuesta de Ollama: {e}")
                        continue
                        
        except asyncio.TimeoutError:
            print(f"Timeout al generar respuesta con Ollama - modelo: {self.model_name}")
            yield "Error: Timeout al generar respuesta. El modelo puede estar tardando demasiado."
        except aiohttp.ClientError as e:
            print(f"Error de conexión con el servidor de Ollama: {e}")
            yield "Error de conexión con el servidor de Ollama."
        except Exception as e:
            print(f"Error inesperado en generate: {e}")
            yield f"Error inesperado: {str(e)}"
        
        # Agrega la respuesta completa del asistente al historial de la conversación
        self.messages.append({"role": "assistant", "content": assistant_response})
        # Reinicia el prompt de RAG en el mensaje del sistema para la siguiente interacción
        self.messages[0]['content'] = self.messages[0]['content'].split("\n\n")[0]

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.session and not self.session.closed:
            await self.session.close()
