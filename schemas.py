from pydantic import BaseModel

# Modelo para la solicitud de consulta
class QueryRequest(BaseModel):
    query: str

# Modelo para la respuesta de consulta
class QueryResponse(BaseModel):
    response: str

# Modelo para la solicitud de ingesta de documentos
class IngestRequest(BaseModel):
    text: str

# Modelo para la respuesta de ingesta
class IngestResponse(BaseModel):
    message: str