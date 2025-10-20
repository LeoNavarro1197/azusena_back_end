import os
import faiss
import pandas as pd
from sentence_transformers import SentenceTransformer
import logging
import numpy as np

# Configuración de logs detallados
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data"))
XLSX_FILE = os.path.join(DATA_DIR, "Compilado_Preguntas_Azusena.xlsx")
FAISS_INDEX_FILE = os.path.join(DATA_DIR, "index.faiss")

# Modelo de embeddings mejorado para español
EMBEDDING_MODEL = "paraphrase-multilingual-mpnet-base-v2"
model = SentenceTransformer(EMBEDDING_MODEL)

class VectorDB:
    def __init__(self):
        self.index = None
        self.questions = []
        self.df = None
        # Forzar recreación del índice
        if os.path.exists(FAISS_INDEX_FILE):
            try:
                os.remove(FAISS_INDEX_FILE)
                logging.info("Índice FAISS antiguo eliminado. Se creará uno nuevo.")
            except Exception as e:
                logging.warning(f"No se pudo eliminar el índice antiguo: {e}")
        self.load_or_create_index()

    def load_or_create_index(self):
        """Carga la base de datos FAISS o la crea desde el XLSX si no existe."""
        try:
            if os.path.exists(FAISS_INDEX_FILE):
                logging.info("Cargando índice FAISS existente...")
                self.index = faiss.read_index(FAISS_INDEX_FILE)
                self.load_questions()
            else:
                logging.info("Creando nuevo índice FAISS...")
                self.create_index_from_xlsx()
        except Exception as e:
            logging.error(f"Error al cargar/crear índice: {e}")
            logging.info("Intentando crear nuevo índice...")
            self.create_index_from_xlsx()

    def load_questions(self):
        """Carga los datos desde el XLSX usando la nueva estructura detallada."""
        if not os.path.exists(XLSX_FILE):
            raise FileNotFoundError(f"Archivo no encontrado: {XLSX_FILE}")

        self.df = pd.read_excel(XLSX_FILE)
        self.df.columns = [col.lower().strip().replace(' ', '_') for col in self.df.columns]
        
        # Verificar que tenga la nueva estructura requerida
        required_columns = ['fuente', 'articulo', 'tema', 'subtema', 'texto_del_articulo', 'categorias', 'resumen_explicativo']
        missing_columns = [col for col in required_columns if col not in self.df.columns]
        
        if missing_columns:
            raise ValueError(f"El archivo XLSX debe tener las siguientes columnas: {missing_columns}")
        
        # Crear texto completo enriquecido para embeddings
        self.df['texto_completo'] = (
            self.df['texto_del_articulo'] + " " + 
            self.df['resumen_explicativo'] + " " +
            "Palabras clave: " + self.df['categorias'] + " " +
            "Tema: " + self.df['tema'] + " " +
            "Subtema: " + self.df['subtema']
        )
        self.questions = self.df['texto_completo'].tolist()
        logging.info(f"Cargados {len(self.questions)} artículos del archivo XLSX con nueva estructura detallada")

    def create_index_from_xlsx(self):
        """Crea un nuevo índice FAISS basado en los artículos del XLSX usando la nueva estructura detallada."""
        logging.info("Iniciando creación de nuevo índice FAISS...")
        self.df = pd.read_excel(XLSX_FILE)

        # Normalizar nombres de columnas
        self.df.columns = [col.lower().strip().replace(' ', '_') for col in self.df.columns]
        
        # Verificar columnas requeridas para la nueva estructura
        required_columns = ['fuente', 'articulo', 'tema', 'subtema', 'texto_del_articulo', 'categorias', 'resumen_explicativo']
        missing_columns = [col for col in required_columns if col not in self.df.columns]
        
        if missing_columns:
            raise ValueError(f"El archivo XLSX debe tener las siguientes columnas: {missing_columns}")
        
        logging.info("Usando nueva estructura enriquecida...")
        
        # Limpiar y preparar datos
        for col in required_columns:
            self.df[col] = self.df[col].astype(str).fillna("")
            self.df[col] = self.df[col].str.strip()
        
        # Filtrar filas vacías
        self.df = self.df[self.df["texto_del_articulo"] != ""]
        
        # Crear texto enriquecido para embeddings (texto + resumen + categorías + tema + subtema)
        # Incluir categorías con mayor peso para mejorar la recuperación semántica
        self.df['texto_completo'] = (
            self.df['texto_del_articulo'] + " " + 
            self.df['resumen_explicativo'] + " " +
            "Palabras clave: " + self.df['categorias'] + " " +
            "Tema: " + self.df['tema'] + " " +
            "Subtema: " + self.df['subtema']
        )
        self.questions = self.df['texto_completo'].tolist()
        
        logging.info(f"Procesando {len(self.questions)} elementos para crear embeddings...")
        
        # Crear embeddings
        embeddings = model.encode(self.questions, convert_to_numpy=True, show_progress_bar=True)
        
        # Normalizar embeddings para mejorar la búsqueda de similitud
        faiss.normalize_L2(embeddings)
        
        # Crear índice FAISS optimizado
        dimension = embeddings.shape[1]
        logging.info(f"Creando índice FAISS con dimensión {dimension}")
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(embeddings)

        # Guardar el índice
        faiss.write_index(self.index, FAISS_INDEX_FILE)
        logging.info(f"Índice FAISS creado y guardado en {FAISS_INDEX_FILE}")

    def find_similar_question(self, query_text, top_k=5):
        """Encuentra artículos similares en FAISS y devuelve respuestas contextualizadas usando la nueva estructura."""
        if self.index is None or self.index.ntotal == 0:
            return "No hay datos en la base de conocimientos.", 0.0

        # Preprocesar la consulta
        query_text = query_text.strip()
        
        # Enriquecer la consulta con términos clave para mejorar la búsqueda semántica
        enhanced_query = self._enhance_query_with_keywords(query_text)
        
        # Crear embedding de la consulta enriquecida
        query_embedding = model.encode([enhanced_query], convert_to_numpy=True)
        faiss.normalize_L2(query_embedding)

        # Buscar artículos similares
        distances, indices = self.index.search(query_embedding, top_k)
        
        # Filtrar y ponderar resultados
        valid_results = []
        for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            # Aplicar ponderación semántica
            weighted_score = self._calculate_weighted_similarity(query_text, distance, self.df.iloc[idx])
            
            if weighted_score >= 0.4:  # Umbral reducido para incluir más artículos relevantes de salud
                valid_results.append({
                    'index': idx,
                    'similarity': float(weighted_score),
                    'original_similarity': float(distance),
                    'data': self.df.iloc[idx]
                })
        
        # Reordenar por similitud ponderada
        valid_results.sort(key=lambda x: x['similarity'], reverse=True)
        
        if not valid_results:
            logging.info("No se encontraron resultados por encima del umbral de similitud")
            return "No encontré información suficientemente relevante para tu consulta.", 0.0
        
        # Log detallado para debugging
        logging.info(f"Query: '{query_text}'")
        logging.info(f"Resultados válidos encontrados: {len(valid_results)}")
        
        # Generar respuesta contextualizada usando la nueva estructura
        response = self._generate_contextualized_response(valid_results, query_text)
        max_similarity = valid_results[0]['similarity'] if valid_results else 0.0
        
        return response, max_similarity
    
    def _enhance_query_with_keywords(self, query_text):
        """Enriquece la consulta con términos clave para mejorar la búsqueda semántica."""
        query_lower = query_text.lower()
        enhanced_terms = []
        
        # Mapeo de conceptos clave para mejorar la recuperación
        concept_mappings = {
            'objeto': ['finalidad', 'propósito', 'objetivo', 'meta'],
            'garantizar': ['asegurar', 'proteger', 'salvaguardar'],
            'derechos': ['derechos fundamentales', 'derechos irrenunciables'],
            'protección': ['amparo', 'cobertura', 'resguardo'],
            'contingencias': ['riesgos', 'eventualidades', 'situaciones'],
            'calidad de vida': ['bienestar', 'dignidad humana'],
            'principios': ['fundamentos', 'bases', 'criterios'],
            'cobertura': ['alcance', 'extensión', 'ámbito']
        }
        
        # Agregar términos relacionados si se encuentran conceptos clave
        for concept, related_terms in concept_mappings.items():
            if concept in query_lower:
                enhanced_terms.extend(related_terms)
        
        # Combinar consulta original con términos enriquecidos
        if enhanced_terms:
            return f"{query_text} {' '.join(enhanced_terms)}"
        return query_text
    
    def _calculate_weighted_similarity(self, query_text, original_similarity, article_data):
        """Calcula similitud ponderada basada en coincidencias conceptuales usando la nueva estructura."""
        query_lower = query_text.lower()
        
        # Obtener texto del artículo y categorías de la nueva estructura
        article_text = str(article_data.get('texto_del_articulo', '')).lower()
        categories = str(article_data.get('categorias', '')).lower()
        theme = str(article_data.get('tema', '')).lower()
        subtheme = str(article_data.get('subtema', '')).lower()
        
        # Ponderaciones para diferentes tipos de coincidencias
        weight_boost = 0.0
        
        # Boost por coincidencias conceptuales específicas
        concept_boosts = {
            'objeto': 0.15 if 'objeto' in query_lower and ('objeto' in categories or 'objeto' in subtheme) else 0,
            'garantizar': 0.1 if 'garantizar' in query_lower and 'garantizar' in article_text else 0,
            'derechos': 0.1 if 'derecho' in query_lower and 'derecho' in categories else 0,
            'protección': 0.1 if 'protec' in query_lower and 'protec' in article_text else 0,
            'contingencias': 0.1 if 'contingencia' in query_lower and 'contingencia' in article_text else 0,
            'principios': 0.1 if 'principio' in query_lower and 'principio' in categories else 0
        }
        
        weight_boost = sum(concept_boosts.values())
        
        # Boost por coincidencia exacta de tema/subtema
        if any(word in theme for word in query_lower.split()):
            weight_boost += 0.05
        if any(word in subtheme for word in query_lower.split()):
            weight_boost += 0.1
        
        # Aplicar ponderación (máximo boost de 0.3)
        final_similarity = min(original_similarity + min(weight_boost, 0.3), 1.0)
        
        return final_similarity
    
    def _generate_contextualized_response(self, results, query_text):
        """Genera una respuesta contextualizada basada en los resultados encontrados."""
        if not results:
            return "No encontré información específica sobre tu consulta."
        
        # Agrupar resultados por tema
        themes_groups = {}
        for result in results:
            data = result['data']
            theme = data.get('tema', 'Sin tema')
            
            if theme not in themes_groups:
                themes_groups[theme] = []
            themes_groups[theme].append(result)
        
        # NUEVA MEJORA: Validar coherencia temática antes de generar respuesta
        if not self._validate_response_coherence(query_text, themes_groups):
            logging.warning("Coherencia temática insuficiente, generando respuesta conservadora")
            return self._generate_conservative_response(results, query_text)
        
        # Si hay múltiples temas, generar respuesta de clarificación
        if len(themes_groups) > 1:
            return self._generate_clarification_response(themes_groups, query_text)
        
        # Si hay un solo tema, generar respuesta completa
        theme = list(themes_groups.keys())[0]
        return self._generate_complete_response(results, theme, query_text)

    def _validate_response_coherence(self, query_text, themes_groups):
        """Valida que los temas encontrados sean coherentes con la consulta."""
        query_lower = query_text.lower()
        
        # Términos clave para diferentes tipos de consultas
        quality_terms = ['calidad', 'estándares', 'acreditación', 'certificación']
        article_terms = ['artículo', 'art.', 'articulo']
        health_terms = ['salud', 'médico', 'atención', 'servicios']
        law_terms = ['ley 100', 'ley cien', 'normativa']
        
        # Verificar si la consulta es sobre calidad
        is_quality_query = any(term in query_lower for term in quality_terms)
        is_article_query = any(term in query_lower for term in article_terms)
        is_health_query = any(term in query_lower for term in health_terms)
        is_law_query = any(term in query_lower for term in law_terms)
        
        # Verificar coherencia de los temas encontrados
        relevant_themes_found = 0
        total_themes = len(themes_groups)
        
        for theme in themes_groups.keys():
            theme_lower = theme.lower()
            
            # Verificar si el tema es relevante para la consulta
            theme_relevant = False
            
            if is_quality_query and any(term in theme_lower for term in ['calidad', 'acreditación', 'estándares']):
                theme_relevant = True
            elif is_health_query and any(term in theme_lower for term in ['salud', 'atención', 'servicios']):
                theme_relevant = True
            elif is_law_query and any(term in theme_lower for term in ['ley', 'normativa', 'regulación']):
                theme_relevant = True
            elif is_article_query:  # Para consultas de artículos, ser más permisivo
                theme_relevant = True
            
            if theme_relevant:
                relevant_themes_found += 1
        
        # Considerar coherente si al menos el 60% de los temas son relevantes
        coherence_ratio = relevant_themes_found / total_themes if total_themes > 0 else 0
        is_coherent = coherence_ratio >= 0.6
        
        logging.info(f"Validación de coherencia: {relevant_themes_found}/{total_themes} temas relevantes (ratio: {coherence_ratio:.2f})")
        
        return is_coherent

    def _generate_conservative_response(self, results, query_text):
        """Genera una respuesta conservadora cuando hay problemas de coherencia."""
        if not results:
            return "No encontré información específica sobre tu consulta."
        
        # Tomar solo los resultados más relevantes (top 3)
        top_results = results[:3]
        
        response_parts = ["Basándome en mi base de datos, encontré la siguiente información relevante:\n"]
        
        for i, result in enumerate(top_results, 1):
            data = result['data']
            article = data.get('articulo', 'N/A')
            theme = data.get('tema', 'Sin tema')
            source = data.get('fuente', 'Sin fuente')
            similarity = result.get('similarity', 0)
            
            response_parts.append(f"{i}. **Artículo {article}** ({source})")
            response_parts.append(f"   - Tema: {theme}")
            response_parts.append(f"   - Relevancia: {similarity:.1%}\n")
        
        response_parts.append("¿Te gustaría obtener más detalles sobre algún artículo específico?")
        
        return "\n".join(response_parts)

    def _generate_clarification_response(self, themes_groups, query_text):
        """Genera una respuesta de clarificación cuando hay múltiples temas."""
        response_parts = ["Encontré información relacionada con varios temas. ¿Sobre cuál te gustaría saber más?\n"]
        
        # NUEVA MEJORA: Limitar a los temas más relevantes y validados
        sorted_themes = sorted(themes_groups.items(), 
                             key=lambda x: max(r['similarity'] for r in x[1]), 
                             reverse=True)
        
        # Mostrar solo los 3 temas más relevantes
        for i, (theme, results) in enumerate(sorted_themes[:3], 1):
            best_result = max(results, key=lambda x: x['similarity'])
            article_count = len(results)
            
            response_parts.append(f"{i}. **{theme}**")
            response_parts.append(f"   - {article_count} artículo(s) relacionado(s)")
            response_parts.append(f"   - Relevancia máxima: {best_result['similarity']:.1%}")
            
            # Mostrar algunos artículos de ejemplo
            example_articles = [r['data'].get('articulo', 'N/A') for r in results[:2]]
            response_parts.append(f"   - Ejemplos: Artículos {', '.join(example_articles)}\n")
        
        response_parts.append("Por favor, especifica sobre qué tema te gustaría obtener información detallada.")
        
        return "\n".join(response_parts)

    def _generate_complete_response(self, results, theme, query_text):
        """Genera una respuesta completa para un tema específico."""
        response_parts = [f"## 📋 **{theme}**\n"]
        
        # NUEVA MEJORA: Validar y filtrar artículos antes de mostrarlos
        validated_results = self._validate_articles_in_results(results)
        
        if not validated_results:
            return f"Encontré información sobre {theme}, pero necesito validar los datos. Por favor, pregúntame por un artículo específico."
        
        # Agrupar por subtema si existe
        subtemas = {}
        for result in validated_results:
            data = result['data']
            subtema = data.get('subtema', 'General')
            
            if subtema not in subtemas:
                subtemas[subtema] = []
            subtemas[subtema].append(result)
        
        # Mostrar información por subtema
        for subtema, subtema_results in subtemas.items():
            if subtema != 'General':
                response_parts.append(f"### 🔸 **{subtema}**")
            
            # Mostrar los artículos más relevantes (máximo 5 por subtema)
            for result in subtema_results[:5]:
                data = result['data']
                article = data.get('articulo', 'N/A')
                content = data.get('contenido', 'Sin contenido disponible')
                source = data.get('fuente', 'Sin fuente')
                similarity = result.get('similarity', 0)
                
                response_parts.append(f"**Artículo {article}** ({source}) - Relevancia: {similarity:.1%}")
                
                # Truncar contenido si es muy largo
                if len(content) > 300:
                    content = content[:300] + "..."
                
                response_parts.append(f"{content}\n")
        
        # Agregar sugerencia para más información
        response_parts.append("💡 **Sugerencia:** Para obtener información completa sobre un artículo específico, pregúntame directamente por su número.")
        
        return "\n".join(response_parts)

    def _validate_articles_in_results(self, results):
        """Valida que los artículos en los resultados existan realmente."""
        validated_results = []
        
        for result in results:
            data = result['data']
            article_num = data.get('articulo', '')
            
            if article_num and article_num.isdigit():
                # Verificar que el artículo tenga contenido válido
                content = data.get('contenido', '')
                theme = data.get('tema', '')
                
                if content and theme and len(content.strip()) > 10:
                    validated_results.append(result)
                else:
                    logging.warning(f"Artículo {article_num} descartado por contenido insuficiente")
            else:
                logging.warning(f"Artículo con número inválido descartado: {article_num}")
        
        logging.info(f"Validación de artículos: {len(validated_results)}/{len(results)} artículos válidos")
        return validated_results

    def get_article_details(self, article_number: str) -> tuple:
        """Obtiene los detalles de un artículo específico por su número."""
        try:
            if self.df is None:
                return "La base de datos no está disponible.", 0.0, False
            
            # Buscar el artículo específico
            article_filter = self.df['articulo'].astype(str) == str(article_number)
            matching_articles = self.df[article_filter]
            
            if matching_articles.empty:
                return f"No se encontró el artículo {article_number} en la base de datos.", 0.0, False
            
            # Tomar el primer resultado
            article = matching_articles.iloc[0]
            
            # Construir respuesta detallada
            response_parts = []
            response_parts.append(f"**Artículo {article_number}**")
            
            if article.get('fuente') and str(article.get('fuente')).strip() not in ['', 'nan', 'None', 'null']:
                response_parts.append(f"**Fuente:** {article.get('fuente')}")
            
            if article.get('tema') and str(article.get('tema')).strip() not in ['', 'nan', 'None', 'null']:
                response_parts.append(f"**Tema:** {article.get('tema')}")
            
            if article.get('subtema') and str(article.get('subtema')).strip() not in ['', 'nan', 'None', 'null']:
                response_parts.append(f"**Subtema:** {article.get('subtema')}")
            
            if article.get('texto_del_articulo') and str(article.get('texto_del_articulo')).strip() not in ['', 'nan', 'None', 'null']:
                response_parts.append(f"**Contenido:**\n{article.get('texto_del_articulo')}")
            else:
                response_parts.append("❌ **Texto Completo No Disponible**")
            
            if article.get('resumen_explicativo') and str(article.get('resumen_explicativo')).strip() not in ['', 'nan', 'None', 'null']:
                response_parts.append(f"**Resumen:** {article.get('resumen_explicativo')}")
            
            return "\n\n".join(response_parts), 1.0, True
            
        except Exception as e:
            logging.error(f"Error obteniendo detalles del artículo {article_number}: {e}")
            return f"Error al obtener información del artículo {article_number}.", 0.0, False

    def get_top_results(self, query_text, top_k=5):
        """Obtiene los resultados más relevantes para una consulta sin generar una respuesta formateada."""
        if self.index is None or self.index.ntotal == 0:
            return []

        # Preprocesar la consulta
        query_text = query_text.strip()
        
        # Enriquecer la consulta con términos clave para mejorar la búsqueda semántica
        enhanced_query = self._enhance_query_with_keywords(query_text)
        
        # Crear embedding de la consulta enriquecida
        query_embedding = model.encode([enhanced_query], convert_to_numpy=True)
        faiss.normalize_L2(query_embedding)

        # Buscar artículos similares
        distances, indices = self.index.search(query_embedding, top_k)
        
        # Filtrar y ponderar resultados
        valid_results = []
        for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            # Aplicar ponderación semántica
            weighted_score = self._calculate_weighted_similarity(query_text, distance, self.df.iloc[idx])
            
            if weighted_score >= 0.4:  # Umbral reducido para incluir más artículos relevantes de salud
                valid_results.append({
                    'index': idx,
                    'similarity': float(weighted_score),
                    'original_similarity': float(distance),
                    'data': self.df.iloc[idx]
                })
        
        # Reordenar por similitud ponderada
        valid_results.sort(key=lambda x: x['similarity'], reverse=True)
        
        logging.info(f"Resultados para consulta '{query_text}': {len(valid_results)} encontrados")
        return valid_results

# Crear instancia de la base de datos
vector_db = VectorDB()
