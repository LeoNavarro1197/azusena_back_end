# AzuSena Backend

Este repositorio contiene el backend para el proyecto **AzuSena**, un asistente virtual especializado en temas administrativos y jurídicos del SENA (Servicio Nacional de Aprendizaje de Colombia). El sistema implementa un enfoque RAG (Retrieval-Augmented Generation) utilizando **Flask**, **OpenAI GPT-4** y **FAISS** para búsqueda vectorial semántica.

## Tabla de Contenidos

- [AzuSena Backend](#azusena-backend)
  - [Tabla de Contenidos](#tabla-de-contenidos)
  - [Descripción](#descripción)
  - [Instalación](#instalación)
  - [Iniciador Local](#iniciador-local)
  - [Estructura del Proyecto](#estructura-del-proyecto)
  - [Funcionamiento del Sistema](#funcionamiento-del-sistema)
  - [Pruebas](#pruebas)
  - [Contribuciones](#contribuciones)
  - [Licencia](#licencia)

## Descripción

**AzuSena Backend** es una API desarrollada en **Flask** con soporte para WebSockets, que sirve como núcleo de procesamiento de la plataforma. Es responsable de recibir, interpretar y responder a las consultas enviadas desde el frontend.

Funciones principales:

- **Recepción de Consultas**: desde el frontend mediante API REST y WebSockets.
- **Procesamiento Semántico**: usando embeddings multilingües con Sentence Transformers.
- **Recuperación de Información**: mediante **FAISS**, una base de datos vectorial para búsquedas semánticas eficientes.
- **Generación de Respuestas**: utilizando **OpenAI GPT-4o-mini** cuando no hay información suficiente en la base de conocimientos.
- **Gestión de Conversación**: manteniendo coherencia y contexto entre interacciones.

## Instalación

1. **Clonar el repositorio**

   ```bash
   git clone https://github.com/tu_usuario/AzuSena-Backend.git
   cd AzuSena-Backend
   ```

2. **Crear entorno virtual e instalar dependencias**

   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configurar variables de entorno**

   Crea un archivo `.env` en la raíz del proyecto:
   ```
   OPENAI_API_KEY=tu_api_key_aqui
   OPENAI_MODEL=gpt-4o-mini-2024-07-18
   USE_LOCAL_MODEL=False
   ```

4. **Ejecutar el backend**

   ```bash
   python main.py
   ```

   O desde el directorio app:
   ```bash
   python app/main.py
   ```

## Iniciador Local

Para iniciar los proyectos en modo **DEMO**, puedes utilizar los scripts disponibles:

- [Iniciador para Windows](https://github.com/farrojo/AzuSena-React/blob/main/Iniciador.bat)
- [Iniciador para Linux](https://github.com/farrojo/AzuSena-React/blob/main/Iniciador.sh)

> ⚠️ Asegúrate de colocar el archivo dentro del directorio del frontend (`AzuSena-React`). Al ejecutarlo, se encargarán de iniciar tanto el frontend como el backend automáticamente.

## Estructura del Proyecto

```bash
AzuSena-Backend/
├── main.py                # Punto de entrada alternativo
├── app/
│   ├── __init__.py        # Inicialización del paquete
│   ├── main.py            # Aplicación Flask principal
│   ├── routes.py          # Rutas de la API y WebSocket
│   ├── query.py           # Sistema RAG y lógica de consultas
│   ├── config.py          # Configuración y variables de entorno
│   └── models/
│       ├── __init__.py
│       └── vector_db.py   # Base de datos vectorial FAISS
├── data/
│   ├── Compilado_Preguntas_Azusena.xlsx  # Base de conocimientos
│   └── index.faiss        # Índice vectorial FAISS
├── requirements.txt       # Dependencias
└── README.md
```

## Funcionamiento del Sistema

1. **Frontend React** captura la consulta del usuario.
2. **Flask Backend** recibe la petición HTTP o WebSocket y gestiona el contexto conversacional.
3. **FAISS** realiza una búsqueda vectorial usando embeddings de Sentence Transformers para recuperar conocimiento relacionado.
4. Si la similitud es suficiente (≥0.65), devuelve la respuesta de la base de conocimientos.
5. Si no hay información suficiente, **OpenAI GPT-4o-mini** genera una respuesta contextualizada.
6. El resultado es enviado de nuevo al frontend via JSON y WebSocket.

## Pruebas

## Tecnologías Utilizadas

### Framework y API
- **Flask 3.0.2**: Framework web principal
- **Flask-CORS 4.0.0**: Manejo de políticas CORS
- **Flask-SocketIO 5.3.6**: Comunicación WebSocket en tiempo real

### Inteligencia Artificial
- **OpenAI 1.12.0**: Integración con GPT-4o-mini
- **Sentence-Transformers 2.5.1**: Generación de embeddings semánticos
- **FAISS-CPU 1.11.0**: Base de datos vectorial para búsqueda semántica

### Procesamiento de Datos
- **Pandas 2.2.1**: Manipulación de datos
- **NumPy 1.26.4**: Operaciones matemáticas
- **OpenPyXL 3.1.2**: Lectura de archivos Excel

### Utilidades
- **Python-dotenv 1.0.1**: Manejo de variables de entorno
- **Emoji 2.10.1**: Procesamiento de texto
- **HTTPX 0.24.1**: Cliente HTTP moderno

## Endpoints Disponibles

- `GET /test`: Endpoint de prueba
- `POST /query`: Consulta principal al sistema RAG
- `POST /debug-query`: Endpoint de depuración
- WebSocket: Comunicación en tiempo real

## Configuración del Sistema RAG

- **Modelo de Embeddings**: `paraphrase-multilingual-mpnet-base-v2`
- **Umbral de Similitud**: 0.65
- **Modelo OpenAI**: GPT-4o-mini-2024-07-18
- **Base de Conocimientos**: Excel con estructura detallada (fuente, artículo, tema, subtema, etc.)

## Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue para sugerencias o mejoras, y sigue el flujo estándar de pull requests.

## Licencia

MIT License.