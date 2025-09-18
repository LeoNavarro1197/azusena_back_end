# AzuSena Backend

Este repositorio contiene el backend para el proyecto **AzuSena**, diseñado para interactuar con un modelo de lenguaje de **Ollama** y una base de datos vectorial **Chroma**. Originalmente, el backend estaba contenido dentro del proyecto React, pero fue separado para una mejor organización, escalabilidad y mantenimiento del sistema.

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

**AzuSena Backend** es una API moderna y eficiente desarrollada en **FastAPI**, que sirve como núcleo de procesamiento de la plataforma. Es responsable de recibir, interpretar y responder a las consultas enviadas desde el frontend.

Funciones principales:

- **Recepción de Consultas**: desde el frontend en React.
- **Procesamiento Semántico**: mediante modelos alojados en **Ollama**, permitiendo comprensión contextual.
- **Recuperación de Información**: usando **Chroma DB**, una base de datos vectorial para búsquedas semánticas eficientes.
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

3. **Ejecutar el backend**

   ```bash
   uvicorn main:app --reload
   ```

## Iniciador Local

Para iniciar los proyectos en modo **DEMO**, puedes utilizar los scripts disponibles:

- [Iniciador para Windows](https://github.com/farrojo/AzuSena-React/blob/main/Iniciador.bat)
- [Iniciador para Linux](https://github.com/farrojo/AzuSena-React/blob/main/Iniciador.sh)

> ⚠️ Asegúrate de colocar el archivo dentro del directorio del frontend (`AzuSena-React`). Al ejecutarlo, se encargarán de iniciar tanto el frontend como el backend automáticamente.

## Estructura del Proyecto

```bash
AzuSena-Backend/
├── main.py                # Punto de entrada de la API
├── app/
│   ├── api/               # Rutas de la API
│   ├── core/              # Lógica de negocio
│   ├── services/          # Integraciones con Ollama y Chroma
│   ├── models/            # Esquemas Pydantic
│   └── utils/             # Utilidades generales
├── requirements.txt       # Dependencias
└── README.md
```

## Funcionamiento del Sistema

1. **Frontend React** captura la consulta del usuario.
2. **FastAPI Backend** recibe la petición y gestiona el contexto conversacional.
3. **Chroma DB** realiza una búsqueda vectorial para recuperar conocimiento relacionado.
4. **Ollama** genera una respuesta enriquecida usando el contexto recuperado.
5. El resultado es enviado de nuevo al frontend.

## Pruebas

Las pruebas pueden ejecutarse usando `pytest`:

```bash
pytest
```

## Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue para sugerencias o mejoras, y sigue el flujo estándar de pull requests.

## Licencia

MIT License.