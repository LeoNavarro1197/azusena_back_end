import logging
import emoji
from openai import OpenAI
from .config import Config
from app.models.vector_db import vector_db
import re
import traceback
import httpx

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

conversation_history = []

class QueryRAGSystem:
    def __init__(self):
        logging.info("Inicializando QueryRAGSystem")
        # Configuración básica del cliente OpenAI sin proxies
        client = httpx.Client()
        self.client = OpenAI(
            api_key=Config.OPENAI_API_KEY,
            http_client=client
        )
        self.min_similarity_score = 0.65
        logging.info(f"API Key configurada: {'Presente' if Config.OPENAI_API_KEY else 'No presente'}")

    def clean_text(self, texto: str) -> str:
        """Limpia y normaliza el texto."""
        # Eliminar emojis
        texto = emoji.replace_emoji(texto, "")
        # Eliminar caracteres especiales pero mantener acentos y ñ
        texto = re.sub(r'[^a-záéíóúñüA-ZÁÉÍÓÚÑÜ0-9\s.,¿?¡!]', '', texto)
        # Normalizar espacios
        texto = ' '.join(texto.split())
        return texto

    def query_rag(self, query_text: str) -> tuple:
        """Consulta el sistema RAG y devuelve la mejor respuesta disponible con información de similitud."""
        global conversation_history

        try:
            # Limpiar y normalizar la consulta
            query_text = self.clean_text(query_text)
            logging.info(f"Consulta normalizada: {query_text}")

            # Buscar respuestas similares en FAISS
            best_response, similarity_score = vector_db.find_similar_question(query_text)
            logging.info(f"Score de similitud: {similarity_score}")

            if similarity_score >= self.min_similarity_score:
                logging.info("Usando respuesta de la base de conocimiento")
                response = best_response
                used_kb = True
            else:
                logging.info("No se encontró una respuesta suficientemente similar, consultando OpenAI")
                context = self.get_context_from_history()
                response = self.query_openai(query_text, context)
                used_kb = False

            # Actualizar historial
            conversation_history.append({
                "role": "user",
                "content": query_text
            })
            conversation_history.append({
                "role": "assistant",
                "content": response
            })

            # Mantener el historial manejable
            if len(conversation_history) > 10:
                conversation_history = conversation_history[-10:]

            return response, similarity_score, used_kb  # Devolver respuesta, similitud y si usó KB

        except Exception as e:
            logging.error(f"Error en query_rag: {str(e)}")
            logging.error(f"Traceback completo: {traceback.format_exc()}")
            return f"Lo siento, hubo un problema al procesar tu consulta: {str(e)}", 0.0, False
    
    def search_by_theme(self, theme: str, subtema: str = None) -> str:
        """Busca artículos específicamente por tema y subtema."""
        try:
            # Verificar si tenemos nueva estructura
            if not hasattr(vector_db, 'df') or vector_db.df is None:
                return "La base de datos no está disponible."
            
            has_new_structure = all(col in vector_db.df.columns for col in ['fuente', 'articulo', 'tema', 'subtema', 'texto_del_articulo', 'categorias', 'resumen_explicativo'])
            
            if not has_new_structure:
                return "Esta funcionalidad requiere la nueva estructura de base de datos."
            
            # Filtrar por tema
            theme_filter = vector_db.df['tema'].str.contains(theme, case=False, na=False)
            filtered_df = vector_db.df[theme_filter]
            
            if subtema:
                subtema_filter = filtered_df['subtema'].str.contains(subtema, case=False, na=False)
                filtered_df = filtered_df[subtema_filter]
            
            if filtered_df.empty:
                return f"No se encontraron artículos para el tema '{theme}'{f' y subtema {subtema}' if subtema else ''}."
            
            # Generar respuesta estructurada
            response = f"📋 **Artículos sobre {theme.upper()}:**\n\n"
            
            for idx, row in filtered_df.head(10).iterrows():  # Limitar a 10 resultados
                article_num = row['articulo']
                source = row['fuente']
                summary = row['resumen_explicativo']
                subtema_info = row['subtema']
                
                response += f"• **Art. {article_num}** ({source})"
                if subtema_info and subtema_info.strip():
                    response += f" - *{subtema_info}*"
                response += f"\n  {summary}\n\n"
            
            if len(filtered_df) > 10:
                response += f"... y {len(filtered_df) - 10} artículo{'s' if len(filtered_df) - 10 > 1 else ''} más.\n\n"
            
            response += "¿Necesitas información más detallada de algún artículo específico?"
            
            return response
            
        except Exception as e:
            logging.error(f"Error en search_by_theme: {str(e)}")
            return f"Error al buscar por tema: {str(e)}"
    
    def get_article_details(self, article_number: str) -> str:
        """Obtiene los detalles completos de un artículo específico."""
        try:
            if not hasattr(vector_db, 'df') or vector_db.df is None:
                return "La base de datos no está disponible."
            
            has_new_structure = all(col in vector_db.df.columns for col in ['fuente', 'articulo', 'tema', 'subtema', 'texto_del_articulo', 'categorias', 'resumen_explicativo'])
            
            if not has_new_structure:
                return "Esta funcionalidad requiere la nueva estructura de base de datos."
            
            # Buscar el artículo
            article_filter = vector_db.df['articulo'].astype(str).str.contains(str(article_number), case=False, na=False)
            article_df = vector_db.df[article_filter]
            
            if article_df.empty:
                return f"No se encontró el artículo {article_number}."
            
            # Tomar el primer resultado si hay múltiples
            article = article_df.iloc[0]
            
            response = f"📄 **Artículo {article['articulo']}**\n\n"
            response += f"**Fuente:** {article['fuente']}\n"
            response += f"**Tema:** {article['tema']}\n"
            if article['subtema'] and article['subtema'].strip():
                response += f"**Subtema:** {article['subtema']}\n"
            if article['categorias'] and article['categorias'].strip():
                response += f"**Categorías:** {article['categorias']}\n"
            response += f"\n**Contenido:**\n{article['texto_del_articulo']}\n\n"
            response += f"**Resumen:** {article['resumen_explicativo']}"
            
            return response
            
        except Exception as e:
            logging.error(f"Error en get_article_details: {str(e)}")
            return f"Error al obtener detalles del artículo: {str(e)}"

    def get_context_from_history(self) -> str:
        """Obtiene contexto relevante del historial de conversación."""
        if not conversation_history:
            return ""
        
        # Tomar las últimas 3 interacciones
        recent_history = conversation_history[-6:]
        context = "\n".join([f"{'Usuario' if msg['role'] == 'user' else 'Asistente'}: {msg['content']}" 
                           for msg in recent_history])
        return context

    def query_openai(self, query_text: str, context: str = "") -> str:
        """Consulta OpenAI con contexto mejorado."""
        try:
            logging.info("Iniciando consulta a OpenAI")
            logging.info(f"API Key actual: {Config.OPENAI_API_KEY[:10]}...")

            system_prompt = """Nombre: AzuSENA
Rol: Asistente virtual del Servicio Nacional de Aprendizaje (SENA) de Colombia.
Función Principal: Proporcionar respuestas precisas y confiables sobre temas administrativos, jurídicos, y académicos del SENA (y en general del contexto jurídico, legal y normativo colombiano) a aprendices, instructores, y funcionarios del SENA (Servicio nacional de aprendizaje), institución educativa técnica y tecnológica colombiana, y sabe que el énfasis de los temas administrativos que requiere el SENA esta en el contexto colombiano, por lo que entiende que las preguntas administrativas que le hacen los usuarios son referidas al contexto colombiano, o sea que el usuario es colombiano, y por eso al pedirle una pregunta jurídica o administrativa, espera respuestas en base al contexto jurídico colombiano, por ejemplo si piden algo sobre leyes o normativas sobre salud o educación, sabe se necesita responder en base a leyes o normativas colombianas, por eso busca responder en base a leyes, normas, decretos o documentos jurídico de Colombia, que se aplique en Colombia y que regulen esos aspectos en Colombia, excepto si el usuario aclara que necesita algún dato jurídico de un contexto jurídico de otro país que no sea Colombia.

Directrices de Comportamiento:
1. Identidad: Siempre preséntate como AzuSENA, asistente virtual del SENA (la institución colombiana).
2. Fuentes de Información: Utiliza la una base de datos de conocimiento proporcionada a través de la técnica RAG, pero si tienes esa información en tu pre entrenamiento base, también puedes usar la información de tu pre entrenamiento base. Si la información solicitada no se encuentra en tu base de datos, o no la conoces, informa de manera clara que la información que presentas, no la estas extrayendo de tu base de datos, y que no tienes conocimientos sobre ese tema, sino de la información disponible por tu modelo base (no olvides en este aspecto de los datos de tu modelo base tener preferencia a datos referidos al contexto colombiano, dado que el usuario es colombiano).
3. Precisión y Confiabilidad: Asegúrate de que las respuestas sean precisas y de ser posible, si es posible, intenta que tus respuestas estén respaldadas por la información de tu base de datos, puedes dar información que no sea de la base, pero de ser posible ten en cuenta la relación que esa información tiene con temáticas académicas o administrativas del SENA, nunca te quedes sin dar respuesta, y si no sabes que responder, solo tienes que decirle al usuario que no tienes conocimientos sobre ese tema.
4. Respuesta Directa y Concisa: Responde a la pregunta del usuario de manera detallada, pero evitando información innecesaria, manteniendo una respuesta precisa que tenga la información requerida.
5. Tono: Mantén un tono formal pero amigable, profesional, y respetuoso. Sé amable y servicial.
6. Estructura de la Respuesta:
   • En la medida de lo posible puedes iniciar el primer mensaje de la conversación con una saludo apropiado y amigable.
   • Proporciona respuestas precisas con la información detallada.
   • Procura termina la respuesta con una frase que invite a la continuación de la conversación (ej. "¿Puedo ayudarte con algo más?", "Si tienes otra pregunta, no dudes en consultarme.").

Restricciones:
• No te inventes información, por lo que para evitar inventar información, solo tienes que decir no tienes conocimientos sobre ese tema pues no los encuentras en tu base de datos o en tus conocimientos de cultura general, también puedes decirle al usuario en tu respuesta que no posees información verificada o suficientemente contrastada sobre ese tema.
• No proporciones opiniones personales, juicios de valor o información no verificable, por eso si te piden algo que implique algún juicio de valor puedes informar al usuario que eres neutral en ese aspecto, que tienes como labor es dar información confiable.
• Puedes decir que modelo eres incluso decir que versión del modelo, pero asegúrate de incluir en ese dato que usas RAG y de decir que diferencia tiene el RAG de un LLM llamado AzuSENA del LLM original que eres(que pidria ser po ejemplo GPT, Mistral; Deepseek, llama o el o el modelo LLM que tu seas), y que el RAG fue añadido a tu modelo base por el equipo de desarrollo de SENNOVA."""

            messages = [
                {"role": "system", "content": system_prompt}
            ]

            if context:
                messages.append({
                    "role": "system",
                    "content": f"Contexto de la conversación previa:\n{context}"
                })

            messages.append({"role": "user", "content": query_text})

            logging.info("Enviando solicitud a OpenAI...")
            response = self.client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            logging.info("Respuesta recibida de OpenAI")

            return response.choices[0].message.content

        except Exception as e:
            logging.error(f"Error consultando OpenAI: {str(e)}")
            logging.error(f"Traceback completo: {traceback.format_exc()}")
            raise Exception(f"Error al consultar OpenAI: {str(e)}")

# Instancia global
query_rag_system = QueryRAGSystem()
