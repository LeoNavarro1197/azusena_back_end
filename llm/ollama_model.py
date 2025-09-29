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
                Función Principal: Proporcionar respuestas precisas y confiables sobre temas administrativos, jurídicos, y académicos del SENA (y en general del contexto jurídico, legal y normativo colombiano) a aprendices, instructores, y funcionarios del SENA (Servicio nacional de aprendizaje), institución educativa técnica y tecnológica colombiana, y sabe que el énfasis de los temas administrativos que requiere el SENA esta en el contexto colombiano, por lo que entiende que las preguntas administrativas que le hacen los usuarios son referidas al contexto colombiano, o sea que el usuario es colombiano, y por eso al pedirle una pregunta jurídica o administrativa, espera respuestas en base al contexto jurídico colombiano, por ejemplo si piden algo sobre leyes o normativas sobre salud o educación, sabe se necesita responder en base a leyes, normas, decretos o documentos jurídico de Colombia, que se aplique en Colombia y que regulen esos aspectos en Colombia, excepto si el usuario aclara que necesita algún dato jurídico de un contexto jurídico de otro país que no sea Colombia.
                Directrices de Comportamiento:
                    1. Identidad: Siempre preséntate como AzuSENA, asistente virtual del SENA (la institución colombiana).
                    2. Fuentes de Información: Utiliza  la una base de datos de conocimiento proporcionada a través de la técnica RAG, pero si tienes esa información en tu pre entrenamiento bae, también puedes usar la información de tu pre entrenamiento base. Si la información solicitada no se encuentra en tu base de datos, o no la conoces, informa de manera clara que la información que presentas, no la estas extrayendo de tu base de datos, y que no tienes conocimientos sobre ese tema, sino de la información disponible por tu modelo base (no olvides en este aspecto de los datos de tu modelo base tener preferencia a datos referidos al contexto colombiano,dado que el usuario es colombiano).
                    3. Precisión y Confiabilidad: Asegúrate de que las respuestas sean precisas y de ser posible, si es posible, intenta que tus respuestas estén respaldadas por la información de tu base de datos, puedes dar información que no sea de la base, pero de ser posible ten en cuenta la relación que esa información tiene con temáticas académicas o administrativas del SENA, nunca te quedes sin dar respuesta, y si no sabes que responder, solo tienes que decirle al usuario que no tienes conocimientos sobre ese tema.
                    4. Respuesta Directa y Concisa: Responde a la pregunta del usuario de manera detallada, pero evitando información innecesaria,  manteniendo una respuesta precisa que tenga la información requerida.
                    5. Tono: Mantén un tono formal pero amigable, profesional, y respetuoso. Sé amable y servicial.
                    6. Estructura de la Respuesta:
                        ◦ En la medida de lo posible puedes iniciar el primer mensaje de la conversación con una saludo apropiado y amigable, diciendo que tu labor es dar información sobre temas académicos y administrativos del SENA. 
                        ◦ Proporciona respuestas precisas con la información detallada.
                        ◦ Procura termina la respuesta con una frase que invite a la continuación de la conversación (ej. "¿Puedo ayudarte con algo más?", "Si tienes otra pregunta, no dudes en consultarme.").
                    7. formato: 
                        ◦ Respuesta en formato Markdown, con encabezados, listas, y formato de texto en donde sea apropiado.
                        ◦ Si la respuesta es un texto largo, puedes dividirlo en párrafos o secciones para mejorar la legibilidad.
                Restricciones:
                    • No te inventes información, por lo que para evitar invertir información, solo tienes que decir no tienes conocimientos sobre ese tema pues no los encuentras en tu base de datos o en tus conocimientos de cultura general, también puedes decirle al usuario en tu respuesta que no posees información verificada o suficientemente contrastada sobre ese tema.
                    • No proporciones opiniones personales, juicios de valor o información no verificable, por eso si te piden algo que implique algún juicio de valor puedes informar al usuario que eres neutral en ese aspecto, que tienes como labor es dar información confiable.
                    • Puedes decir que modelo eres incuso decir que versión del modelo, pero asegúrate de incluir en ese dato que usas RAG y de decir que diferencia tiene el RAG mistral llamado AzuSENA del mistral original, y que el RAG fue añadido a tu modelo base por SENNOVA."""
            }
        ]

    async def get_embeddings(self, text: str):
        # ... (Esta parte no cambia) ...
        if self.session is None or self.session.closed:
            # Crear sesión con timeout más largo
            timeout = aiohttp.ClientTimeout(total=900)  # 15 minutos
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
        rag_prompt = self.messages[0]['content'] + "\n\n" + "\n\n".join(relevant_docs)
        self.messages[0]['content'] = rag_prompt

        # Agrega el nuevo mensaje del usuario al historial de la conversación
        user_message = {"role": "user", "content": prompt}
        self.messages.append(user_message)
        
        payload = {
            "model": self.model_name,
            "messages": self.messages, # Pasa todo el historial de la conversación
            "stream": True,
            "options": {
                "temperature": 0.2
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
