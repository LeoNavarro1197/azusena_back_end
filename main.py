import os
import sys

# Agregar la ruta principal del proyecto para que las importaciones funcionen
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from services.rag_service import RAGService
from database.faiss_db import FaissDB
from llm.ollama_model import OllamaModel
from fastapi.middleware.cors import CORSMiddleware
import socketio

# --- Modelos de Pydantic para la API ---
class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    response: str

# --- Instancias de las clases del proyecto ---
db = FaissDB()
llm_model = OllamaModel()
rag_service = RAGService(db=db, llm=llm_model)

# --- Configuración de la aplicación FastAPI ---
app = FastAPI(title="API de AzuSENA", version="0.8.0")

# --- Configuración de Socket.IO ---
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins="*"
)

# Crear la aplicación ASGI que combina FastAPI y Socket.IO
socket_app = socketio.ASGIApp(sio, app)

# Permitir cualquier origen (para desarrollo). En producción, lista los dominios permitidos.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],               # o ["https://mi-dominio.com"]
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# --- Evento de inicio y apagado de la aplicación ---
@app.on_event("startup")
async def startup_event():
    db._load_or_create_index()
    print("La API de AzuSENA ha iniciado correctamente.")

# --- Rutas de la API ---

# definir la ruta de la url para consultas por texto
@app.post("/azusena_api/query/text", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest):
    """
    Endpoint para realizar una consulta RAG cuando el input es por texto.
    """
    try:
        print(f"Request recibido: {request}")
        print(f"Query a procesar: '{request.query}'")
        response = await rag_service.query_documents(request.query)
        print(f"Respuesta generada: {response}")
        return QueryResponse(response=response)
    except Exception as e:
        print(f"Error en la consulta: {e}")
        print(f"Tipo de error: {type(e)}")
        import traceback
        print(f"Traceback completo: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error específico: {str(e)}")

# definir la ruta de la url para consultas por voz
@app.post("/azusena_api/query/voice", response_model=QueryResponse)
async def query_endpoint_voice(audio_file: UploadFile = File(...)):
    """
    Endpoint para realizar una consulta RAG cuando el input es por voz.
    """
    try:
        # Llama al método de RAGService que ahora manejará la transcripción y la consulta
        response = await rag_service.process_voice_query(audio_file)
        print(response)
        return QueryResponse(response=response)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error en la consulta por voz: {e}")
        raise HTTPException(status_code=500, detail="Lo siento, no pude procesar la consulta por voz. Por favor, intenta de nuevo más tarde.")

# --- Eventos de Socket.IO ---
@sio.event
async def connect(sid, environ):
    """Evento cuando un cliente se conecta"""
    print(f"Cliente conectado: {sid}")
    await sio.emit('connection_response', {'data': 'Conectado a AzuSENA'}, room=sid)

@sio.event
async def disconnect(sid):
    """Evento cuando un cliente se desconecta"""
    print(f"Cliente desconectado: {sid}")

@sio.event
async def query_text(sid, data):
    """Maneja consultas de texto a través de Socket.IO"""
    try:
        print(f"Datos recibidos: {data}")
        query = data.get('query', '')
        print(f"Query extraído: '{query}'")
        
        if not query:
            print("Query vacío detectado")
            await sio.emit('error', {'message': 'Query vacío'}, room=sid)
            return
        
        print(f"Procesando query: {query}")
        response = await rag_service.query_documents(query)
        print(f"Respuesta generada: {response}")
        await sio.emit('query_response', {'response': response}, room=sid)
    except Exception as e:
        print(f"Error en consulta Socket.IO: {e}")
        print(f"Tipo de error: {type(e)}")
        import traceback
        print(f"Traceback completo: {traceback.format_exc()}")
        await sio.emit('error', {'message': f'Error procesando la consulta: {str(e)}'}, room=sid)