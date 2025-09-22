# Backend RAG con FastAPI, Ollama y Faiss

Este proyecto es una demostración de un backend en Python, construido con el framework FastAPI, que implementa el patrón de Generación Aumentada por Recuperación (RAG). Utiliza un modelo de lenguaje de Ollama y una base de datos vectorial de Faiss para proporcionar respuestas informadas por un corpus de documentos.

## Arquitectura del Proyecto

El proyecto sigue una arquitectura en capas para una clara separación de responsabilidades:

- _main.py_: El punto de entrada de la API. Define los endpoints y se encarga de la inyección de dependencias.

- _schemas.py_: Define los modelos de datos para la validación de peticiones y respuestas (capa de datos).

- _database/_: Contiene la lógica para interactuar con la base de datos vectorial (Faiss).

- _llm/_: Contiene la lógica para interactuar con el modelo de lenguaje de Ollama.

- _services/_: Contiene el servicio principal que orquesta el flujo de trabajo de RAG, combinando la lógica de las otras capas.
- _ingest_data.py_: Un script de utilidad para automatizar la ingesta de un dataset en la base de datos de contexto.

# Prerrequisitos

Antes de ejecutar este proyecto, necesitas tener instalado lo siguiente:

1. Python 3.7+: Asegúrate de tener una versión compatible.

2. Docker (o el cliente de Ollama): Ollama se ejecuta como un servidor local. La forma más sencilla es usar Docker.

3. El cliente de Ollama: Sigue las instrucciones en la página oficial de Ollama.

# Configuración y Ejecución

Sigue estos pasos para poner el servidor en marcha:

### Paso 1: Iniciar el servidor de Ollama

Abre una terminal y ejecuta el servidor de Ollama. La forma recomendada es con Docker:

```
docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
```

### Paso 2: Descargar el modelo de lenguaje


Descarga un modelo compatible con Ollama. En este proyecto, se ha configurado mistral:7b por defecto. Puedes usar otro, pero asegúrate de cambiarlo en el archivo _main.py._, como opción recomendada:

```
ollama pull mistral:7b
```

Para correrlo y ejecutarlo al mismo tiempo, se puede usar el comando:

```
ollama run mistral:7b
```

### Paso 3: Clonar el Repositorio e Instalar Dependencias

Clona este repositorio (si aplica) y navega al directorio del proyecto. Luego, instala los paquetes necesarios usando pip:

```
pip install -r requirements.txt
```

### Paso 4: Ejecutar el Servidor FastAPI

Ahora puedes iniciar el servidor FastAPI usando Uvicorn:

```
uvicorn main:app --reload
```

El servidor estará en ejecución en _http://127.0.0.1:8000_.

## Paso 5: Ingestar tu dataset

Una vez que el servidor de FastAPI está en funcionamiento, abre una nueva terminal y ejecuta el script de ingesta para cargar tus documentos en Faiss.

```
python ingest_data.py
```

El script puede leer archivos .txt, .csv, y .pdf. Si usas un CSV, puedes especificar las columnas de texto que deseas ingestar en el script _ingest_data.py_.

## Uso de la API

La API tiene un único endpoint principal para hacer consultas. Puedes acceder a la documentación interactiva en http://127.0.0.1:8000/docs.

Para probar el endpoint de consulta, puedes usar curl o cualquier cliente HTTP (como Postman o Insomnia).

Endpoint: /query (POST)
Envía una consulta de texto y recibe una respuesta generada por el LLM.

-  Ejemplo de Petición

```
curl -X POST "http://localhost:8000/query" \
-H "Content-Type: application/json" \
-d '{"query": "Explícame qué es RAG en programación."}'
```
- Ejemplo de Respuesta

```
{
  "response": "La generación aumentada por recuperación (RAG) es una técnica que combina un LLM con una fuente de datos externa para generar respuestas. Esto permite que el LLM acceda a información actualizada y específica que no estaba en sus datos de entrenamiento, lo que mejora la precisión y la relevancia de sus respuestas."
}
```
