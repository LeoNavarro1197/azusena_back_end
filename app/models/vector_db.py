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
            
            if weighted_score >= 0.65:  # Umbral ajustado para mejor precisión
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
        return self._generate_contextualized_response(valid_results, query_text)
    
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
        """Genera respuesta contextualizada agrupando por temas."""
        # Agrupar resultados por tema
        themes_groups = {}
        for result in results:
            data = result['data']
            theme = data['tema']
            if theme not in themes_groups:
                themes_groups[theme] = []
            themes_groups[theme].append(result)
        
        # Si hay múltiples temas, generar respuesta clarificadora
        if len(themes_groups) > 1:
            return self._generate_clarification_response(themes_groups, query_text)
        else:
            # Un solo tema - generar respuesta completa
            theme = list(themes_groups.keys())[0]
            return self._generate_complete_response(themes_groups[theme], theme, query_text)
    
    def _generate_clarification_response(self, themes_groups, query_text):
        """Genera respuesta clarificadora cuando hay múltiples temas."""
        response = f"Encontré información sobre '{query_text}' en varios temas:\n\n"
        
        for theme, results in themes_groups.items():
            subtemas = list(set([r['data']['subtema'] for r in results]))
            articles_count = len(results)
            response += f"🔹 **{theme.upper()}** ({articles_count} artículo{'s' if articles_count > 1 else ''})\n"
            if subtemas and subtemas[0]:  # Si hay subtemas
                response += f"   Subtemas: {', '.join(subtemas)}\n"
            response += "\n"
        
        response += "¿Podrías especificar sobre qué tema te gustaría obtener más información?"
        
        # Retornar la mejor similitud encontrada
        best_similarity = max([r['similarity'] for r in sum(themes_groups.values(), [])])
        return response, best_similarity
    
    def _generate_complete_response(self, results, theme, query_text):
        """Genera respuesta completa para un tema específico."""
        response = f"📋 **Información sobre {theme.upper()}:**\n\n"
        
        # Agrupar por subtema si existe
        subtema_groups = {}
        for result in results:
            subtema = result['data']['subtema'] or 'General'
            if subtema not in subtema_groups:
                subtema_groups[subtema] = []
            subtema_groups[subtema].append(result)
        
        for subtema, subtema_results in subtema_groups.items():
            if len(subtema_groups) > 1:  # Solo mostrar subtema si hay más de uno
                response += f"**{subtema}:**\n"
            
            for result in subtema_results[:3]:  # Limitar a 3 resultados por subtema
                data = result['data']
                article_num = data['articulo']
                source = data['fuente']
                summary = data['resumen_explicativo']
                
                response += f"• **Art. {article_num}** ({source}): {summary}\n"
            
            if len(subtema_results) > 3:
                response += f"   ... y {len(subtema_results) - 3} artículo{'s' if len(subtema_results) - 3 > 1 else ''} más\n"
            response += "\n"
        
        response += "¿Necesitas información más detallada de algún artículo específico?"
        
        # Retornar la mejor similitud
        best_similarity = max([r['similarity'] for r in results])
        return response, best_similarity

# Crear instancia de la base de datos
vector_db = VectorDB()
