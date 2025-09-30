# AzuSENA - Backend RAG con FastAPI, Socket.IO, Ollama y Faiss

Este proyecto es un backend avanzado en Python que implementa un asistente virtual inteligente para el Servicio Nacional de Aprendizaje (SENA) de Colombia. Utiliza el patrón de Generación Aumentada por Recuperación (RAG) con FastAPI, Socket.IO para comunicación en tiempo real, Ollama para modelos de lenguaje, y Faiss como base de datos vectorial.

## 🏗️ Arquitectura del Sistema

### Componentes Principales

El proyecto sigue una arquitectura moderna en capas con comunicación en tiempo real:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │◄──►│   FastAPI       │◄──►│   RAG Service   │
│   (Socket.IO)   │    │   + Socket.IO   │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Ollama LLM    │    │   Faiss Vector  │
                       │   (mistral:7b)  │    │   Database      │
                       └─────────────────┘    └─────────────────┘
```

### Estructura de Archivos

- **`main.py`**: Punto de entrada principal con FastAPI y Socket.IO
- **`schemas.py`**: Modelos de datos y validación con Pydantic
- **`database/faiss_db.py`**: Gestión de la base de datos vectorial Faiss
- **`llm/ollama_model.py`**: Interfaz con el modelo de lenguaje Ollama
- **`services/rag_service.py`**: Servicio principal que orquesta el flujo RAG
- **`data_preprocessing/ingest_data.py`**: Script para ingesta de documentos
- **`test_frontend/`**: Frontend de prueba con Socket.IO

## 🚀 Características Principales

### ✅ Comunicación en Tiempo Real
- **Socket.IO**: Comunicación bidireccional instantánea
- **WebSockets**: Conexiones persistentes para respuestas en streaming
- **Eventos personalizados**: `query_text` para consultas y `response` para respuestas

### ✅ APIs Duales
- **HTTP REST API**: Endpoints tradicionales para integración
- **Socket.IO Events**: Comunicación en tiempo real para interfaces interactivas

### ✅ RAG Avanzado
- **Embeddings**: Generación de vectores con Ollama
- **Búsqueda semántica**: Recuperación de documentos relevantes con Faiss
- **Generación contextual**: Respuestas informadas por documentos específicos

### ✅ Modelo de Lenguaje
- **Ollama Integration**: Soporte para múltiples modelos (mistral:7b por defecto)
- **Streaming responses**: Respuestas en tiempo real
- **Configuración personalizada**: Temperatura, timeouts, y parámetros ajustables

## 📋 Prerrequisitos

### Software Requerido

1. **Python 3.8+**: Versión mínima recomendada
2. **Ollama**: Servidor de modelos de lenguaje local
3. **Git**: Para clonar el repositorio

### Modelos Ollama Disponible De Código abierto

El sistema está configurado para usar `mistral:7b`, pero soporta otros modelos:
- `mistral:7b` (recomendado)
- `tinyllama:1.1b` (unico modelo de llama con licencia 100% de codigo abierto, y altamente optimizado para ser ejecutado en servidores con recursos limitados, pero con menor precisión)
- `phi3:3.8b` (requiere un servidor con una gpu con cuda, y alta capacidad de VRAM)
- `deepseek-r1:8b` (requiere un servidor con una gpu con cuda, y alta capacidad de VRAM)
- `qwen3:4b` (requiere un servidor con una gpu con cuda, y alta capacidad de VRAM) 

## 🛠️ Instalación y Configuración

### Paso 1: Instalar Ollama

#### Windows/macOS/Linux:
```bash
# Descargar desde https://ollama.ai/
# O usar el instalador automático:
curl -fsSL https://ollama.ai/install.sh | sh
```

#### Verificar instalación:
```bash
ollama --version
```

### Paso 2: Descargar Modelo de Lenguaje

```bash
# Descargar el modelo mistral:7b
ollama pull mistral:7b

# Verificar que el modelo esté disponible
ollama list

# Probar el modelo (opcional)
ollama run mistral:7b "Hola, ¿estás funcionando?"
```

### Paso 3: Clonar y Configurar el Proyecto

```bash
# Clonar el repositorio
git clone <repository-url>
cd azusena

# Crear entorno virtual
python -m venv azusena_whisper_env

# Activar entorno virtual
# Windows:
azusena_whisper_env\Scripts\activate
# Linux/macOS:
source azusena_whisper_env/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### Paso 4: Preparar Base de Datos

```bash
# Ingestar documentos en la base de datos vectorial
python data_preprocessing/ingest_data.py
```

### Paso 5: Ejecutar el Servidor

```bash
# Iniciar el servidor con Socket.IO
python -m uvicorn main:socket_app --reload --host 0.0.0.0 --port 8000
```

El servidor estará disponible en:
- **API REST**: `http://localhost:8000`
- **Socket.IO**: `http://localhost:8000/socket.io/`
- **Documentación**: `http://localhost:8000/docs`

## 📡 APIs Disponibles

### HTTP REST Endpoints

#### POST `/azusena_api/query/text`
Consulta de texto tradicional

**Request:**
```json
{
  "query": "¿Qué es el SENA?"
}
```

**Response:**
```json
{
  "response": "El SENA (Servicio Nacional de Aprendizaje) es una institución pública colombiana..."
}
```

#### POST `/azusena_api/query/voice`
Consulta por audio (Whisper integration)

**Request:** Multipart form con archivo de audio

**Response:**
```json
{
  "transcription": "¿Qué es el SENA?",
  "response": "El SENA es una institución..."
}
```

### Socket.IO Events

#### Cliente → Servidor

**`query_text`**: Enviar consulta de texto
```javascript
socket.emit('query_text', {
  query: "¿Cuáles son los programas del SENA?"
});
```

#### Servidor → Cliente

**`response`**: Recibir respuesta (streaming)
```javascript
socket.on('response', (data) => {
  console.log('Chunk recibido:', data.chunk);
  console.log('Respuesta completa:', data.complete);
});
```

**`error`**: Manejo de errores
```javascript
socket.on('error', (data) => {
  console.error('Error:', data.message);
});
```

## 🔧 Configuración Avanzada

### Variables de Entorno

Crea un archivo `.env` para configuraciones personalizadas:

```env
# Ollama Configuration
OLLAMA_HOST=localhost
OLLAMA_PORT=11434
OLLAMA_MODEL=mistral:7b

# Server Configuration
API_HOST=0.0.0.0
API_PORT=8000

# RAG Configuration
MAX_DOCS=5
TEMPERATURE=0.2
TIMEOUT_SECONDS=300
```

### Personalización del Modelo

Para cambiar el modelo de Ollama, edita `llm/ollama_model.py`:

```python
class OllamaModel:
    def __init__(self, model_name="tu-modelo-preferido"):
        self.model_name = model_name
        # ... resto de la configuración
```

## 🧪 Testing

### Frontend de Prueba

El proyecto incluye un frontend básico para testing:

```bash
# Abrir en navegador
open test_frontend/index.html
```

### Pruebas con cURL

```bash
# Probar endpoint HTTP
curl -X POST "http://localhost:8000/azusena_api/query/text" \
  -H "Content-Type: application/json" \
  -d '{"query": "Explícame los programas técnicos del SENA"}'

# Verificar salud del servidor
curl http://localhost:8000/health
```

### Pruebas con Socket.IO

```javascript
// Ejemplo básico con Socket.IO client
const io = require('socket.io-client');
const socket = io('http://localhost:8000');

socket.on('connect', () => {
  console.log('Conectado al servidor');
  socket.emit('query_text', { query: 'Hola AzuSENA' });
});

socket.on('response', (data) => {
  console.log('Respuesta:', data);
});
```

## 🔍 Troubleshooting

### Problemas Comunes

#### 1. Error de Conexión con Ollama
```
Error: No se pudo conectar al modelo Ollama
```

**Solución:**
```bash
# Verificar que Ollama esté ejecutándose
ollama ps

# Si no hay modelos cargados, ejecutar:
ollama run mistral:7b "test"
```

#### 2. Timeout en Respuestas
```
TimeoutError: Timeout al generar respuesta
```

**Solución:**
- El modelo puede estar cargándose por primera vez
- Esperar unos minutos para que el modelo se cargue en memoria
- Verificar recursos del sistema (RAM/CPU)

#### 3. Error de Socket.IO
```
404 Not Found - /socket.io/
```

**Solución:**
```bash
# Verificar que se esté usando socket_app en lugar de app
python -m uvicorn main:socket_app --reload
```

#### 4. Base de Datos Vacía
```
No se encontraron documentos relevantes
```

**Solución:**
```bash
# Ejecutar ingesta de datos
python data_preprocessing/ingest_data.py

# Verificar archivos generados
ls -la faiss_index.*
```

### Logs y Debugging

El sistema incluye logging detallado:

```bash
# Ver logs en tiempo real
tail -f logs/azusena.log

# Logs específicos de Ollama
ollama logs
```

## 📊 Monitoreo y Performance

### Métricas del Sistema

- **Tiempo de respuesta promedio**: < 5 segundos
- **Memoria RAM requerida**: 8GB+ (para mistral:7b)
- **Almacenamiento**: 5GB+ (modelo + índices)

### Optimizaciones

1. **Caché de embeddings**: Los vectores se almacenan en Faiss
2. **Streaming responses**: Respuestas progresivas para mejor UX
3. **Connection pooling**: Reutilización de conexiones HTTP
4. **Timeouts configurables**: Evita bloqueos indefinidos

## 🤝 Contribución

### Estructura para Nuevas Características

1. **Servicios**: Agregar en `services/`
2. **Modelos**: Definir en `schemas.py`
3. **Endpoints**: Registrar en `main.py`
4. **Tests**: Crear en `test/`

### Estándares de Código

- **PEP 8**: Estilo de código Python
- **Type hints**: Anotaciones de tipos
- **Docstrings**: Documentación de funciones
- **Error handling**: Manejo robusto de excepciones

## 📄 Licencia

Este proyecto está bajo la licencia AGPL. Ver `LICENSE` para más detalles.

## 🆘 Soporte

Para soporte técnico o preguntas:

1. **Issues**: Crear issue en GitHub
2. **Documentación**: Revisar `/docs`
3. **Logs**: Verificar archivos de log
4. **Community**: Foro de desarrolladores SENA

---

**Desarrollado por SENNOVA** - Servicio Nacional de Aprendizaje (SENA) Colombia
