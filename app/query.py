import os
import logging
import traceback
import openai
import httpx
import emoji
import pandas as pd
from openai import OpenAI
from app.config import Config
from app.models.vector_db import vector_db
import re

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
        self.min_similarity_score = 0.55  # Reducido para incluir más consultas de salud
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

    def is_article_list_query(self, query_text):
        """Detecta si la consulta solicita una lista de artículos."""
        query_lower = query_text.lower()
        article_list_patterns = [
            r'qu[eé]\s+art[ií]culos',
            r'cu[aá]les\s+art[ií]culos',
            r'lista\s+de\s+art[ií]culos',
            r'todos\s+los\s+art[ií]culos',
            r'art[ií]culos\s+sobre',
            r'art[ií]culos\s+relacionados',
            r'qu[eé]\s+normas',
            r'cu[aá]les\s+normas',
            r'dime\s+que\s+art[ií]culos',
            r'muestra\s+art[ií]culos',
            r'busca\s+art[ií]culos',
            # Nuevos patrones para consultas por número/rango
            r'primeros?\s+\d+\s+art[ií]culos',
            r'\d+\s+primeros?\s+art[ií]culos',
            r'art[ií]culos?\s+del?\s+\d+\s+al?\s+\d+',
            r'art[ií]culos?\s+\d+\s+al?\s+\d+',
            r'muestra\s+los?\s+\d+\s+primeros?\s+art[ií]culos',
            r'muestra\s+los?\s+primeros?\s+\d+\s+art[ií]culos',
            r'dame\s+los?\s+\d+\s+primeros?\s+art[ií]culos',
            r'dame\s+los?\s+primeros?\s+\d+\s+art[ií]culos',
            r'los?\s+\d+\s+primeros?\s+art[ií]culos',
            r'los?\s+primeros?\s+\d+\s+art[ií]culos',
            # Patrones con números escritos en palabras
            r'diez\s+primeros?\s+art[ií]culos',
            r'cinco\s+primeros?\s+art[ií]culos',
            r'veinte\s+primeros?\s+art[ií]culos',
            r'muestres?\s+los?\s+diez\s+primeros?\s+art[ií]culos',
            r'muestres?\s+los?\s+cinco\s+primeros?\s+art[ií]culos',
            r'muestres?\s+los?\s+veinte\s+primeros?\s+art[ií]culos',
            r'que\s+me\s+muestres?\s+los?\s+diez\s+primeros?\s+art[ií]culos',
            r'que\s+me\s+muestres?\s+los?\s+cinco\s+primeros?\s+art[ií]culos'
        ]
        
        for pattern in article_list_patterns:
            if re.search(pattern, query_lower):
                return True
        return False

    def _generate_direct_response(self, results, query_text):
        """Genera una respuesta directa basada en los resultados más relevantes."""
        try:
            if not results:
                return f"No encontré información específica sobre '{query_text}' en mi base de datos."
            
            # Tomar el resultado más relevante
            best_result = results[0]['data']
            
            # Extraer información relevante
            article_num = best_result.get('articulo', 'N/A')
            source = best_result.get('fuente', 'N/A')
            theme = best_result.get('tema', 'N/A')
            subtheme = best_result.get('subtema', '')
            summary = best_result.get('resumen_explicativo', '')
            full_text = best_result.get('texto_del_articulo', '')
            
            # Construir respuesta directa y clara
            response = f"**{theme}**\n\n"
            
            # Añadir información del procedimiento/respuesta
            if summary and str(summary).strip() not in ['', 'nan', 'None', 'null']:
                response += f"{summary}\n\n"
            elif full_text and str(full_text).strip() not in ['', 'nan', 'None', 'null']:
                # Si no hay resumen pero sí texto completo, usar un extracto
                extract = full_text[:300] + "..." if len(full_text) > 300 else full_text
                response += f"{extract}\n\n"
            
            # Añadir referencia al artículo de forma más simple
            response += f"**Referencia:** Artículo {article_num} - {source}"
            if subtheme and str(subtheme).strip() not in ['', 'nan', 'None', 'null']:
                response += f" ({subtheme})"
            response += "\n\n"
            
            # Añadir información de artículos relacionados si hay más resultados
            if len(results) > 1:
                response += "**Artículos relacionados:**\n"
                for i in range(1, min(4, len(results))):
                    related = results[i]['data']
                    response += f"• Art. {related.get('articulo', 'N/A')} - {related.get('tema', 'N/A')}"
                    if related.get('subtema') and str(related.get('subtema')).strip() not in ['', 'nan', 'None', 'null']:
                        response += f" ({related.get('subtema')})"
                    response += "\n"
            
            logging.info("Generada respuesta directa estructurada con información legal")
            return response
            
        except Exception as e:
            logging.error(f"Error generando respuesta directa: {e}")
            return f"Encontré información sobre '{query_text}', pero hubo un error al procesarla. Por favor, intenta reformular tu pregunta."

    def _validate_article_mentions(self, response_text):
        """Valida que los artículos mencionados en la respuesta existan realmente en la base de datos."""
        import re
        
        # Extraer números de artículos mencionados
        article_numbers = re.findall(r'art[íi]culo\s*(\d+)', response_text.lower())
        
        if not article_numbers:
            return response_text, True  # No hay artículos que validar
        
        validated_articles = []
        invalid_articles = []
        
        for art_num in set(article_numbers):  # Eliminar duplicados
            try:
                # Verificar si el artículo existe
                article_response, similarity, used_kb = vector_db.get_article_details(art_num)
                
                if "❌ **Artículo No Encontrado**" in article_response:
                    invalid_articles.append(art_num)
                    logging.warning(f"Artículo {art_num} mencionado pero no existe en la base de datos")
                else:
                    validated_articles.append(art_num)
                    logging.info(f"Artículo {art_num} validado correctamente")
                    
            except Exception as e:
                logging.error(f"Error validando artículo {art_num}: {e}")
                invalid_articles.append(art_num)
        
        # Si hay artículos inválidos, modificar la respuesta
        if invalid_articles:
            logging.warning(f"Se encontraron artículos inválidos: {invalid_articles}")
            
            # Crear una respuesta más conservadora
            if validated_articles:
                response_text = f"Encontré información sobre calidad en la Ley 100 de 1993. Los artículos verificados que tratan este tema incluyen: {', '.join(validated_articles)}. Para obtener información específica sobre algún artículo, por favor pregúntame directamente por el número del artículo."
            else:
                response_text = "Encontré información relacionada con calidad en la Ley 100 de 1993, pero para brindarte información precisa sobre artículos específicos, por favor pregúntame por el número exacto del artículo que te interesa."
            
            return response_text, False
        
        return response_text, True

    def _validate_thematic_consistency(self, query_text, response_text):
        """Valida que la respuesta sea temáticamente consistente con la consulta."""
        query_lower = query_text.lower()
        response_lower = response_text.lower()
        
        # Definir términos clave y sus sinónimos
        key_terms = {
            'calidad': ['calidad', 'calidad de servicio', 'calidad de atención', 'estándares'],
            'artículo': ['artículo', 'art.', 'artículos'],
            'ley 100': ['ley 100', 'ley 100 de 1993', 'ley cien'],
            'salud': ['salud', 'servicios de salud', 'atención médica', 'sistema de salud'],
            'acreditación': ['acreditación', 'acreditar', 'certificación'],
            'auditoría': ['auditoría', 'auditorías', 'control', 'evaluación']
        }
        
        consistency_issues = []
        
        # Verificar consistencia temática principal
        for main_term, synonyms in key_terms.items():
            query_has_term = any(term in query_lower for term in synonyms)
            response_has_term = any(term in response_lower for term in synonyms)
            
            if query_has_term and not response_has_term:
                consistency_issues.append(f"Consulta menciona '{main_term}' pero respuesta no")
        
        # Si hay problemas de consistencia significativos, marcar como inconsistente
        if len(consistency_issues) > 1:  # Más de un problema temático
            logging.warning(f"Problemas de consistencia temática detectados: {consistency_issues}")
            return False, consistency_issues
        
        return True, []

    def _improve_response_coherence(self, query_text, response_text):
        """Mejora la coherencia de la respuesta basándose en la consulta."""
        
        # 1. Validar artículos mencionados
        response_text, articles_valid = self._validate_article_mentions(response_text)
        
        # 2. Validar consistencia temática
        is_consistent, issues = self._validate_thematic_consistency(query_text, response_text)
        
        # 3. Si hay problemas de consistencia, generar una respuesta más conservadora
        if not is_consistent or not articles_valid:
            logging.info("Generando respuesta más conservadora debido a problemas de consistencia")
            
            # Buscar información relevante de manera más específica
            top_results = vector_db.get_top_results(query_text, top_k=3)
            
            if top_results and top_results[0]['similarity'] >= 0.6:
                # Crear respuesta basada en resultados verificados
                verified_info = []
                for result in top_results:
                    data = result['data']
                    article_num = data.get('articulo', '')
                    theme = data.get('tema', '')
                    source = data.get('fuente', '')
                    
                    if article_num and theme and source:
                        verified_info.append(f"Artículo {article_num} ({source}): {theme}")
                
                if verified_info:
                    response_text = f"Basándome en mi base de datos verificada, encontré la siguiente información relevante:\n\n" + "\n".join(verified_info) + "\n\n¿Te gustaría obtener más detalles sobre algún artículo específico?"
                else:
                    response_text = "Encontré información relacionada con tu consulta, pero para brindarte datos precisos y verificados, por favor especifica qué aspecto particular te interesa conocer."
        
        return response_text

    def _list_articles_response(self, query_text: str, top_results: list):
        """Genera un listado de artículos coherente con la consulta, con resumen corto por artículo.
        Aplica filtros por concepto (tokens/sinónimos) y valida por tema/subtema/categorías.
        """
        try:
            import re
            q = query_text.lower()
            
            # NUEVA LÓGICA: Detectar consultas por número específico (ej: "primeros 10 artículos")
            number_patterns = [
                r'primeros?\s+(\d+)\s+art[ií]culos',
                r'(\d+)\s+primeros?\s+art[ií]culos',
                r'muestra\s+los?\s+(\d+)\s+primeros?\s+art[ií]culos',
                r'muestra\s+los?\s+primeros?\s+(\d+)\s+art[ií]culos',
                r'dame\s+los?\s+(\d+)\s+primeros?\s+art[ií]culos',
                r'dame\s+los?\s+primeros?\s+(\d+)\s+art[ií]culos',
                r'los?\s+(\d+)\s+primeros?\s+art[ií]culos',
                r'los?\s+primeros?\s+(\d+)\s+art[ií]culos'
            ]
            
            # Patrones con números en palabras
            word_number_patterns = {
                r'diez\s+primeros?\s+art[ií]culos': 10,
                r'cinco\s+primeros?\s+art[ií]culos': 5,
                r'veinte\s+primeros?\s+art[ií]culos': 20,
                r'muestres?\s+los?\s+diez\s+primeros?\s+art[ií]culos': 10,
                r'muestres?\s+los?\s+cinco\s+primeros?\s+art[ií]culos': 5,
                r'muestres?\s+los?\s+veinte\s+primeros?\s+art[ií]culos': 20,
                r'que\s+me\s+muestres?\s+los?\s+diez\s+primeros?\s+art[ií]culos': 10,
                r'que\s+me\s+muestres?\s+los?\s+cinco\s+primeros?\s+art[ií]culos': 5
            }
            
            requested_count = None
            
            # Primero probar patrones con números
            for pattern in number_patterns:
                match = re.search(pattern, q)
                if match:
                    requested_count = int(match.group(1))
                    logging.info(f"Detectada consulta por número específico: {requested_count} artículos")
                    break
            
            # Si no encontró, probar patrones con palabras
            if not requested_count:
                for pattern, count in word_number_patterns.items():
                    if re.search(pattern, q):
                        requested_count = count
                        logging.info(f"Detectada consulta por número en palabras: {requested_count} artículos")
                        break
            
            # Si es consulta por número específico, usar lógica diferente
            if requested_count:
                return self._list_articles_by_number(requested_count, query_text)
            
            # Construir tokens/sinónimos a partir de la consulta (lógica original)
            synonyms = []
            if any(term in q for term in ["peticion", "petición", "petici", "pqrs", "pqr", "queja", "reclamo", "reclamación", "reclamaciones"]):
                synonyms = [
                    r"\bpetici\w*",
                    r"\bderecho\s+de\s+petici\w*",
                    r"\bquej\w*",
                    r"\brecl\w*",
                    r"\bpqrs\b",
                    r"\bpqr\b"
                ]
            else:
                # Extraer palabras clave simples (remover stopwords comunes en español)
                stopwords = {
                    "que", "cuales", "cuáles", "sobre", "de", "del", "la", "el", "los", "las", "en", "y", "un", "una", "para", "por", "a", "qué", "articulo", "artículo", "art", "ley", "100", "1993"
                }
                tokens = [t for t in re.findall(r"[a-záéíóúñ]{3,}", q) if t not in stopwords]
                # Crear regex por token (usar raíz con \w*)
                synonyms = [fr"\b{re.escape(t)}\w*" for t in tokens]

            def matches_any(text: str) -> bool:
                s = str(text).lower()
                for rx in synonyms:
                    if re.search(rx, s):
                        return True
                return False

            # 1) Filtrar resultados semánticos por coincidencia de conceptos
            selected = []
            for res in (top_results or []):
                data = res.get('data', {})
                fields = [
                    data.get('tema', ''),
                    data.get('subtema', ''),
                    data.get('categorias', ''),
                    data.get('resumen_explicativo', ''),
                    data.get('texto_del_articulo', ''),
                ]
                if any(matches_any(f) for f in fields):
                    selected.append(res)

            # 2) Fallback: escanear el DataFrame si hay pocos seleccionados
            if len(selected) < 5 and hasattr(vector_db, 'df') and vector_db.df is not None:
                import pandas as pd
                df = vector_db.df
                cols = ['tema', 'subtema', 'categorias', 'resumen_explicativo', 'texto_del_articulo']
                mask = None
                for rx in synonyms:
                    part = None
                    for c in cols:
                        # str.contains puede fallar si columna no es string; convertir
                        col_series = df[c].astype(str)
                        m = col_series.str.contains(rx, case=False, na=False, regex=True)
                        part = m if part is None else (part | m)
                    mask = part if mask is None else (mask | part)
                if mask is not None:
                    fallback_df = df[mask].copy()
                    # Limitar tamaño y construir estructura similar a top_results
                    for _, row in fallback_df.head(20).iterrows():
                        selected.append({
                            'similarity': 0.5,
                            'data': {
                                'fuente': row.get('fuente', ''),
                                'articulo': str(row.get('articulo', '')).strip(),
                                'tema': row.get('tema', ''),
                                'subtema': row.get('subtema', ''),
                                'categorias': row.get('categorias', ''),
                                'resumen_explicativo': row.get('resumen_explicativo', ''),
                                'texto_del_articulo': row.get('texto_del_articulo', ''),
                            }
                        })

            # 3) Unificar por número de artículo y ordenar
            seen = set()
            unified = []
            for res in sorted(selected, key=lambda r: r.get('similarity', 0), reverse=True):
                art = str(res.get('data', {}).get('articulo', '')).strip()
                if not art or art in seen:
                    continue
                seen.add(art)
                unified.append(res)
                if len(unified) >= 10:  # limitar a 10 artículos
                    break

            if not unified:
                return ("No encontré artículos específicos coherentes con tu consulta en la Ley 100 de 1993. Si puedes precisar el término o tema, buscaré de nuevo.", 0.0, False)

            # 4) Generar respuesta con resumen corto
            response_lines = []
            response_lines.append("📋 Artículos relacionados encontrados (Ley 100 de 1993):")
            for res in unified:
                d = res['data']
                art = d.get('articulo', 'N/A')
                fuente = d.get('fuente', 'Ley 100 de 1993')
                tema = d.get('tema', '')
                subtema = d.get('subtema', '')
                resumen = d.get('resumen_explicativo', '')
                texto = d.get('texto_del_articulo', '')

                # Elegir resumen corto
                snippet = resumen if resumen and str(resumen).strip() not in ['', 'nan', 'None', 'null'] else texto
                snippet = str(snippet or '').strip()
                if len(snippet) > 220:
                    snippet = snippet[:220] + "..."
                if not snippet:
                    snippet = "(Sin resumen disponible)"

                line = f"• ARTÍCULO {art} — {fuente}"
                meta = []
                if tema and str(tema).strip():
                    meta.append(tema)
                if subtema and str(subtema).strip() not in ['', 'nan', 'None', 'null']:
                    meta.append(subtema)
                if meta:
                    line += f" | {' — '.join(meta)}"
                response_lines.append(line)
                response_lines.append(f"  {snippet}")

            response_text = "\n".join(response_lines)
            max_sim = max((r.get('similarity', 0.0) for r in unified), default=0.0)
            return response_text, max_sim, True

        except Exception as e:
            logging.error(f"Error generando listado de artículos: {e}")
            return f"Ocurrió un error al generar el listado: {str(e)}", 0.0, False

    def _list_articles_by_number(self, requested_count: int, query_text: str):
        """Genera un listado de artículos específicos por número (ej: primeros 10 artículos)."""
        try:
            # Verificar acceso a la base de datos
            if not hasattr(vector_db, 'df') or vector_db.df is None:
                return "❌ La base de datos no está disponible en este momento.", 0.0, False
            
            # Filtrar solo artículos de Ley 100 de 1993 (tolerando espacios no estándar)
            fuente_series = vector_db.df['fuente'].astype(str).str.replace('\u00A0', ' ', regex=False)
            ley100_mask = fuente_series.str.contains(r'(?i)ley\s*100\s*de\s*1993', regex=True)
            ley100_df = vector_db.df[ley100_mask]
            
            if ley100_df.empty:
                return "❌ No se encontraron artículos de la Ley 100 de 1993 en la base de datos.", 0.0, False
            
            # Convertir números de artículos a enteros para ordenar correctamente
            ley100_df = ley100_df.copy()
            ley100_df['articulo_num'] = pd.to_numeric(ley100_df['articulo'], errors='coerce')
            
            # Filtrar artículos válidos y ordenar por número
            valid_articles = ley100_df.dropna(subset=['articulo_num']).sort_values('articulo_num')
            
            # Limitar al número solicitado
            selected_articles = valid_articles.head(requested_count)
            
            if selected_articles.empty:
                return f"❌ No se encontraron artículos válidos para mostrar.", 0.0, False
            
            # Generar respuesta
            response_lines = [
                f"📋 **{len(selected_articles)} {'Primeros' if requested_count <= 20 else ''} Artículos de la Ley 100 de 1993:**\n"
            ]
            
            # Preferir texto completo si el usuario lo solicita
            query_lower = query_text.lower()
            prefer_full_text = any(term in query_lower for term in ['texto', 'texto completo', 'con su texto', 'con el texto'])
            
            for _, row in selected_articles.iterrows():
                art_num = int(row['articulo_num'])
                tema = row.get('tema', '')
                subtema = row.get('subtema', '')
                resumen = row.get('resumen_explicativo', '')
                texto = row.get('texto_del_articulo', '')
                
                # Elegir contenido según preferencia del usuario
                if prefer_full_text and texto and str(texto).strip() not in ['', 'nan', 'None', 'null']:
                    content = texto
                else:
                    content = resumen if resumen and str(resumen).strip() not in ['', 'nan', 'None', 'null'] else texto
                content = str(content or '').strip()
                
                # Truncar si es muy largo
                if len(content) > 300:
                    content = content[:300] + "..."
                if not content:
                    content = "(Contenido no disponible)"
                
                # Formatear línea del artículo
                line = f"• **ARTÍCULO {art_num}**"
                if tema and str(tema).strip():
                    line += f" — {tema}"
                if subtema and str(subtema).strip() not in ['', 'nan', 'None', 'null']:
                    line += f" ({subtema})"
                
                response_lines.append(line)
                response_lines.append(f"  {content}\n")
            
            response_text = "\n".join(response_lines)
            
            # Calcular similitud promedio (para consistencia con el sistema)
            similarity = 0.8  # Alta similitud ya que es una consulta específica exitosa
            
            logging.info(f"Generado listado de {len(selected_articles)} artículos por número específico")
            return response_text, similarity, True
            
        except Exception as e:
            logging.error(f"Error generando listado por número: {e}")
            return f"❌ Error al generar el listado: {str(e)}", 0.0, False

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
            match = re.search(article_pattern, query_text.lower())
            
            if match:
                article_number = match.group(1)
                logging.info(f"Solicitud de artículo específico detectada: {article_number}")
                return vector_db.get_article_details(article_number)

            # NUEVA LÓGICA: Detectar si es una consulta de lista de artículos
            if self.is_article_list_query(query_text):
                logging.info("Consulta de listado detectada; generando lista de artículos")
                top_results = vector_db.get_top_results(query_text, top_k=25)
                return self._list_articles_response(query_text, top_results)

            logging.info("Consulta específica detectada - generando respuesta con IA")
            # Para consultas específicas, usar OpenAI con contexto de la base de datos
            top_results = vector_db.get_top_results(query_text, top_k=5)
            if top_results and top_results[0]['similarity'] >= 0.3:  # Umbral más bajo para contexto
                # Crear contexto con la información relevante encontrada
                context_info = self._prepare_context_from_results(top_results)
                ai_response = self.query_openai_with_context(query_text, context_info)
                
                # NUEVA MEJORA: Validar y mejorar coherencia de la respuesta
                improved_response = self._improve_response_coherence(query_text, ai_response)
                
                return improved_response, top_results[0]['similarity'], True
            else:
                # Si no hay información relevante, usar OpenAI sin contexto específico
                logging.info("No se encontró información relevante, consultando OpenAI sin contexto específico")
                context = self.get_context_from_history()
                response = self.query_openai(query_text, context)
                return response, 0.0, False

            # Buscar preguntas similares en FAISS
            response, similarity_score = vector_db.find_similar_question(query_text)
            
            # NUEVA MEJORA: Validar coherencia también para respuestas de la base de conocimientos
            if similarity_score >= self.min_similarity_score:
                logging.info("Usando respuesta de la base de conocimiento")
                improved_response = self._improve_response_coherence(query_text, response)
                used_kb = True
                response = improved_response
            else:
                logging.info(f"Similitud baja ({similarity_score:.3f}), consultando OpenAI...")
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
            response += f"\n**Contenido:** {article['texto_del_articulo']}\n\n"
            
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

    def _prepare_context_from_results(self, results):
        """Prepara el contexto basado en los resultados de la búsqueda."""
        context_parts = []
        context_parts.append("INFORMACIÓN RELEVANTE DE LA BASE DE DATOS:")
        
        for i, result in enumerate(results[:3]):  # Usar solo los 3 más relevantes
            data = result['data']
            similarity = result['similarity']
            
            context_parts.append(f"\n--- Resultado {i+1} (Similitud: {similarity:.3f}) ---")
            context_parts.append(f"Artículo: {data.get('articulo', 'N/A')}")
            context_parts.append(f"Fuente: {data.get('fuente', 'N/A')}")
            context_parts.append(f"Tema: {data.get('tema', 'N/A')}")
            context_parts.append(f"Subtema: {data.get('subtema', 'N/A')}")
            
            # Incluir resumen si está disponible
            if data.get('resumen_explicativo') and str(data.get('resumen_explicativo')).strip() not in ['', 'nan', 'None', 'null']:
                context_parts.append(f"Resumen: {data.get('resumen_explicativo')}")
            
            # Incluir texto del artículo si está disponible
            if data.get('texto_del_articulo') and str(data.get('texto_del_articulo')).strip() not in ['', 'nan', 'None', 'null']:
                text = data.get('texto_del_articulo')
                # Limitar el texto para no sobrecargar el contexto
                if len(text) > 500:
                    text = text[:500] + "..."
                context_parts.append(f"Texto del artículo: {text}")
        
        return "\n".join(context_parts)

    def query_openai_with_context(self, query_text: str, context_info: str) -> str:
        """Consulta OpenAI con contexto específico de la base de datos."""
        try:
            logging.info("Iniciando consulta a OpenAI con contexto específico")
            
            # Verificar que la API key esté configurada
            if not Config.OPENAI_API_KEY or Config.OPENAI_API_KEY == "KEY_NO_DEFINIDA":
                logging.error("API Key de OpenAI no configurada")
                return "Lo siento, no puedo procesar tu consulta en este momento. La configuración de OpenAI no está disponible."
            
            import openai
            openai.api_key = Config.OPENAI_API_KEY
            
            system_prompt = """Eres AzuSENA, asistente virtual del SENA de Colombia.

INSTRUCCIONES CRÍTICAS:
1. Responde de manera natural y conversacional, como si fueras un experto humano
2. NO menciones que eres una IA o que estás consultando una base de datos
3. NO uses formatos de lista con viñetas o estructuras rígidas
4. Redacta respuestas fluidas y naturales basadas en la información proporcionada
5. Si la información no es suficiente para responder completamente, di que necesitas más detalles específicos

FORMATO DE RESPUESTA:
- Respuesta directa y natural
- Explicación clara del procedimiento o información solicitada
- Menciona las referencias legales de forma natural en el texto
- Termina preguntando si necesita más información específica

PROHIBIDO:
- Usar listas con viñetas (•)
- Usar formatos estructurados rígidos
- Mencionar "base de datos" o "sistema"
- Decir "según mi base de datos"
- Usar emojis excesivos"""

            user_prompt = f"""Pregunta del usuario: {query_text}

{context_info}

Responde de manera natural y conversacional basándote en la información proporcionada. Si la información es relevante, úsala para dar una respuesta completa. Si no es suficiente, explica qué información adicional necesitarías."""

            # Configurar cliente OpenAI
            client = OpenAI(api_key=Config.OPENAI_API_KEY)
            
            if not Config.OPENAI_API_KEY or Config.OPENAI_API_KEY == "KEY_NO_DEFINIDA":
                logging.error("API Key de OpenAI no configurada")
                return "Lo siento, el servicio de consulta no está disponible en este momento."

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=800,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content.strip()
            logging.info("Respuesta de OpenAI generada exitosamente")
            return ai_response
            
        except Exception as e:
            logging.error(f"Error consultando OpenAI con contexto: {str(e)}")
            return f"Lo siento, no pude procesar tu consulta en este momento. Por favor, intenta reformular tu pregunta o consulta más tarde."

    def query_openai(self, query_text: str, context: str = "") -> str:
        """Consulta OpenAI para respuestas generales sin contexto específico."""
        try:
            logging.info("Iniciando consulta a OpenAI sin contexto específico")
            
            # Verificar que la API key esté configurada
            if not Config.OPENAI_API_KEY:
                logging.error("API Key de OpenAI no configurada")
                return "Lo siento, no puedo procesar tu consulta en este momento. La configuración de OpenAI no está disponible."
            
            # Configurar cliente OpenAI
            client = OpenAI(api_key=Config.OPENAI_API_KEY)
            
            system_prompt = """Eres AzuSENA, asistente virtual del SENA de Colombia.

INSTRUCCIONES CRÍTICAS:
1. Responde de manera natural y conversacional
2. Proporciona información general sobre procedimientos administrativos colombianos
3. Si no tienes información específica, sé honesto al respecto
4. Sugiere consultar fuentes oficiales cuando sea apropiado
5. Mantén un tono profesional pero amigable

FORMATO DE RESPUESTA:
- Respuesta directa y natural
- Información general disponible
- Sugerencias de fuentes oficiales si es necesario
- Pregunta si necesita más ayuda específica

PROHIBIDO:
- Inventar información específica de leyes o artículos
- Dar información incorrecta
- Usar formatos excesivamente estructurados"""

            user_prompt = f"""Pregunta del usuario: {query_text}

{context if context else ""}

Responde de manera natural proporcionando la información general que tengas disponible. Si no tienes información específica, sugiere fuentes oficiales apropiadas."""

            response = client.chat.completions.create(
                 model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=600,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content.strip()
            logging.info("Respuesta de OpenAI generada exitosamente")
            return ai_response
            
        except Exception as e:
            logging.error(f"Error consultando OpenAI: {str(e)}")
            return f"Lo siento, no pude procesar tu consulta en este momento. Por favor, intenta más tarde o consulta directamente con las oficinas del SENA."

    def query_openai_with_context_full(self, query_text: str, context: str = "") -> str:
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
