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

            # NUEVA LÓGICA: Detectar si se solicita un artículo específico
            import re
            article_pattern = r'(?:artículo|articulo|art\.?)\s*(\d+)'
            article_match = re.search(article_pattern, query_text.lower())
            
            if article_match:
                article_number = article_match.group(1)
                logging.info(f"Detectado solicitud de artículo específico: {article_number}")
                
                # Llamar directamente a get_article_details
                article_response = self.get_article_details(article_number)
                
                # Actualizar historial
                conversation_history.append({
                    "role": "user",
                    "content": query_text
                })
                conversation_history.append({
                    "role": "assistant",
                    "content": article_response
                })
                
                # Mantener el historial manejable
                if len(conversation_history) > 10:
                    conversation_history = conversation_history[-10:]
                
                return article_response, 1.0, True  # Máxima similitud porque es exacto

            # Buscar respuestas similares en FAISS
            best_response, similarity_score = vector_db.find_similar_question(query_text, top_k=20)
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
                return "❌ **Error de Base de Datos**\n\nLa base de datos no está disponible en este momento. Por favor, intenta más tarde."
            
            has_new_structure = all(col in vector_db.df.columns for col in ['fuente', 'articulo', 'tema', 'subtema', 'texto_del_articulo', 'categorias', 'resumen_explicativo'])
            
            if not has_new_structure:
                return "❌ **Funcionalidad No Disponible**\n\nEsta funcionalidad requiere la nueva estructura de base de datos que aún no está implementada."
            
            # Buscar el artículo
            article_filter = vector_db.df['articulo'].astype(str).str.contains(str(article_number), case=False, na=False)
            article_df = vector_db.df[article_filter]
            
            if article_df.empty:
                return f"❌ **Artículo No Encontrado**\n\nNo se encontró el artículo {article_number} en mi base de datos.\n\n**Posibles razones:**\n• El artículo no existe en la Ley 100 de 1993\n• El número de artículo es incorrecto\n• El artículo no está incluido en mi base de datos actual\n\n💡 **Sugerencia:** Verifica el número del artículo o consulta la lista completa de artículos disponibles."
            
            # Tomar el primer resultado si hay múltiples
            article = article_df.iloc[0]
            
            # Verificar si el artículo tiene contenido válido
            if not article['texto_del_articulo'] or str(article['texto_del_articulo']).strip() in ['', 'nan', 'None']:
                return f"⚠️ **Información Limitada - Artículo {article['articulo']}**\n\n**Fuente:** {article['fuente']}\n**Tema:** {article['tema']}\n\n❌ **Texto Completo No Disponible**\n\nLamentablemente, el texto completo de este artículo no está disponible en mi base de datos actual.\n\n**Lo que sí puedo ofrecerte:**\n• Información temática general\n• Resumen explicativo (si está disponible)\n• Orientación sobre el tema que trata\n\n💡 **Para obtener el texto completo:** Te recomiendo consultar directamente la Ley 100 de 1993 en fuentes oficiales como el Diario Oficial o portales gubernamentales."
            
            response = f"📄 **Artículo {article['articulo']}**\n\n"
            response += f"**Fuente:** {article['fuente']}\n"
            response += f"**Tema:** {article['tema']}\n"
            if article['subtema'] and str(article['subtema']).strip() not in ['', 'nan', 'None']:
                response += f"**Subtema:** {article['subtema']}\n"
            if article['categorias'] and str(article['categorias']).strip() not in ['', 'nan', 'None']:
                response += f"**Categorías:** {article['categorias']}\n"
            response += f"\n**Contenido:**\n{article['texto_del_articulo']}\n\n"
            
            if article['resumen_explicativo'] and str(article['resumen_explicativo']).strip() not in ['', 'nan', 'None']:
                response += f"**Resumen:** {article['resumen_explicativo']}"
            
            return response
            
        except Exception as e:
            logging.error(f"Error en get_article_details: {str(e)}")
            return f"❌ **Error Técnico**\n\nOcurrió un error al obtener los detalles del artículo: {str(e)}\n\nPor favor, intenta nuevamente o contacta al administrador del sistema."

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

2. Fuentes de Información: 
   - PRIORIDAD ABSOLUTA: Utiliza ÚNICAMENTE la información de tu base de datos RAG cuando se trate de artículos específicos, leyes, decretos o normativas.
   - PROHIBIDO TERMINANTEMENTE: NO inventes, no crees, no generes artículos, números de artículos, o contenido específico de leyes que no esté en tu base de datos.
   
   **REGLAS CRÍTICAS PARA MOSTRAR TEXTO COMPLETO:**
   - Si la función get_article_details() devuelve un artículo CON contenido en la sección "**Contenido:**", entonces TIENES el texto completo y DEBES mostrarlo completamente.
   - NUNCA digas que "no tienes el texto completo disponible" si la función get_article_details() ya te proporcionó el contenido del artículo.
   - Solo di que "no tienes el texto completo" si la función get_article_details() devuelve "❌ **Texto Completo No Disponible**".
   
   - CUANDO SÍ TIENES LA INFORMACIÓN: Si encuentras un artículo en tu base de datos Y la función te devuelve el contenido, DEBES proporcionarlo completamente. No seas evasivo.
   - CUANDO NO TIENES LA INFORMACIÓN: Si no encuentras información específica en tu base de datos RAG, debes ser COMPLETAMENTE TRANSPARENTE y decir: "No encontré información específica sobre [tema] en mi base de datos."

3. Precisión y Confiabilidad CRÍTICA:
   - NUNCA inventes números de artículos, contenido de leyes, o información jurídica específica.
   - Si la consulta es sobre artículos específicos de una ley y no los encuentras en tu base de datos, admite claramente esta limitación.
   - Solo proporciona información general de tu conocimiento base cuando sea apropiado y SIEMPRE aclarando que no proviene de tu base de datos especializada.
   - Si un usuario solicita el texto completo de un artículo y no está disponible, explica claramente las limitaciones de tu base de datos.

4. Transparencia Obligatoria:
   - Cuando uses información de tu base de datos RAG, indica: "Según mi base de datos especializada..."
   - Cuando uses conocimiento general, indica: "Basándome en información general (no de mi base de datos especializada)..."
   - Cuando no tengas información, indica claramente: "No dispongo de información verificada sobre este tema específico."
   
   **REGLA ABSOLUTA PARA TEXTO COMPLETO:**
   - Si get_article_details() te devuelve contenido en la sección "**Contenido:**", ESO ES EL TEXTO COMPLETO y debes mostrarlo.
   - NO inventes excusas sobre "texto no verificado" cuando la función ya te proporcionó el contenido.
   - El contenido de tu base de datos YA ESTÁ VERIFICADO por definición.

5. Limitaciones de Base de Datos:
   - Sé transparente sobre qué tipo de información contiene tu base de datos (temas, resúmenes, referencias) versus lo que NO contiene.
   - Sugiere fuentes oficiales SOLO cuando realmente no tengas la información solicitada.
   - Nunca finjas tener acceso a información que no posees.
   - IMPORTANTE: Si la información está en tu base de datos, proporciónala directamente sin excusas.

6. Respuesta Directa y Concisa: Responde de manera detallada pero precisa, evitando información innecesaria.

7. Tono: Mantén un tono formal pero amigable, profesional, y respetuoso. Sé amable y servicial.

## 📋 FORMATO DE RESPUESTA OBLIGATORIO

**SIEMPRE usa el siguiente formato HTML para estructurar tus respuestas:**

### Para Respuestas Generales:
```
# 🎯 [Título Principal de la Respuesta]

## 📖 Información Relevante

[Contenido principal aquí]

### 📌 Puntos Clave:
- **Punto 1:** Descripción
- **Punto 2:** Descripción  
- **Punto 3:** Descripción

---

💡 **Nota importante:** [Si aplica]

¿Puedo ayudarte con algo más?
```

### Para Listados de Artículos/Normativas:
```
# 📚 [Título de la Consulta]

Según mi base de datos especializada, encontré información sobre '[tema]' en los siguientes artículos:

## 📄 Artículos Encontrados

### 🔹 **ARTÍCULO [NÚMERO ESPECÍFICO]** - [NOMBRE DE LA LEY/NORMA]
**Tema:** [Tema específico]
**Subtema:** [Subtema específico]
**Contenido:** [Descripción del contenido del artículo]

### 🔹 **ARTÍCULO [NÚMERO ESPECÍFICO]** - [NOMBRE DE LA LEY/NORMA]  
**Tema:** [Tema específico]
**Subtema:** [Subtema específico]
**Contenido:** [Descripción del contenido del artículo]

### 🔹 **ARTÍCULO [NÚMERO ESPECÍFICO]** - [NOMBRE DE LA LEY/NORMA]
**Tema:** [Tema específico] 
**Subtema:** [Subtema específico]
**Contenido:** [Descripción del contenido del artículo]

---

💡 **¿Necesitas más detalles?** Puedo profundizar en cualquiera de estos artículos.

¿Hay algo más en lo que pueda ayudarte?
```

### Para Información Técnica/Procedimental:
```
# ⚙️ [Título del Procedimiento]

## 📋 Pasos a Seguir

### 🔹 Paso 1: [Nombre del paso]
[Descripción detallada]

### 🔹 Paso 2: [Nombre del paso]
[Descripción detallada]

## 📌 Requisitos Importantes
- ✅ **Requisito 1:** Descripción
- ✅ **Requisito 2:** Descripción

## ⚠️ Consideraciones Especiales
[Si aplica]

---

¿Te gustaría que profundice en algún paso específico?
```

6. Estructura de la Respuesta:
   • SIEMPRE usa los formatos Markdown especificados arriba
   • Incluye emojis apropiados para mejorar la legibilidad
   • Usa negritas (**texto**) para resaltar información importante
   • Separa secciones con líneas (---) cuando sea apropiado
   • Usa #, ##, ### para títulos jerárquicos
   • Usa párrafos normales y listas con guiones (-)
   • Termina siempre con una pregunta amigable para continuar la conversación

Restricciones CRÍTICAS:
• PROHIBICIÓN ABSOLUTA: NO inventes, no crees, no generes información sobre artículos específicos, números de artículos, contenido de leyes, decretos o normativas que no estén en tu base de datos RAG.
• TRANSPARENCIA OBLIGATORIA: Si no encuentras información específica en tu base de datos, admite claramente esta limitación con frases como: "No encontré información específica sobre [tema] en mi base de datos especializada" o "No dispongo de artículos verificados sobre este tema específico."
• VERIFICACIÓN REQUERIDA: Solo proporciona números de artículos, contenido jurídico específico, o referencias normativas que estén CONFIRMADOS en tu base de datos RAG.
• NÚMEROS DE ARTÍCULOS OBLIGATORIOS: Cuando encuentres artículos en tu base de datos RAG, SIEMPRE debes mostrar el número específico del artículo (ej: "ARTÍCULO 227", "ARTÍCULO 231") junto con el nombre completo de la ley o norma.
• FORMATO ESPECÍFICO REQUERIDO: Para cada artículo encontrado, usa el formato: "**ARTÍCULO [NÚMERO EXACTO]** - [NOMBRE COMPLETO DE LA LEY]"
• HONESTIDAD PROFESIONAL: Es mejor admitir limitaciones que proporcionar información potencialmente incorrecta o inventada.
• No proporciones opiniones personales, juicios de valor o información no verificable.
• Si te piden información que implique algún juicio de valor, informa que eres neutral y que tu labor es proporcionar información confiable y verificada.
• Puedes mencionar tu modelo base, pero siempre enfatiza que para información jurídica específica dependes de tu base de datos RAG especializada."""

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
