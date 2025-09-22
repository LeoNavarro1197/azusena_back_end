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
        response = await rag_service.query_documents(request.query)
        print(response)
        return QueryResponse(response=response)
    except Exception as e:
        print(f"Error en la consulta: {e}")
        raise HTTPException(status_code=500, detail="Lo siento, no pude procesar la consulta. Por favor, intenta de nuevo más tarde.")

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