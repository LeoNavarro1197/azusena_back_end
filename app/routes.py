import logging
from flask import Blueprint, request, jsonify
from flask_socketio import emit
from .query import query_rag_system
from app.models.vector_db import vector_db
from app import socketio
import traceback

bp = Blueprint('routes', __name__)

@bp.route('/test', methods=['GET'])
def test_endpoint():
    print("[PRINT DEBUG] Test endpoint ejecutándose")
    return jsonify({"status": "OK", "message": "Test endpoint funcionando"})

@bp.route('/debug-query', methods=['POST'])
def debug_query():
    print("[PRINT DEBUG] ===== DEBUG QUERY ENDPOINT INICIADO =====")
    data = request.get_json()
    print(f"[PRINT DEBUG] Datos recibidos: {data}")
    return jsonify({
        "response": "Debug endpoint funcionando correctamente",
        "similarity": 0.95,
        "used_knowledge_base": True,
        "received_data": data
    })

@socketio.on("connect")
def handle_connect():
    """Manejo de conexión WebSocket."""
    logging.info("Cliente conectado a WebSocket")
    emit("connection_response", {"message": "Conectado exitosamente"})

@bp.route('/query', methods=['POST'])
def query():
    """Procesa la consulta del usuario utilizando el sistema RAG."""
    print("[PRINT DEBUG] ===== ENDPOINT /query INICIADO =====")
    print(f"[PRINT DEBUG] query_rag_system disponible: {query_rag_system}")
    print(f"[PRINT DEBUG] Tipo de query_rag_system: {type(query_rag_system)}")
    try:
        logging.info("=== INICIO DE CONSULTA HTTP ===")
        data = request.get_json()
        print(f"[PRINT DEBUG] Datos recibidos: {data}")
        logging.info(f"Datos recibidos: {data}")
        
        query_text = data.get("query") or data.get("query_text")
        print(f"[PRINT DEBUG] Query extraído: '{query_text}'")
        logging.info(f"Query text extraído: '{query_text}'")

        if not query_text:
            logging.error("No se proporcionó texto para la consulta.")
            return jsonify({"error": "No se proporcionó texto para la consulta"}), 400

        logging.info(f"Consulta recibida: '{query_text}'")
        logging.info(f"Instancia query_rag_system: {query_rag_system}")
        logging.info(f"Tipo de query_rag_system: {type(query_rag_system)}")

        # Procesar la consulta usando el sistema RAG
        logging.info("Llamando a query_rag_system.query_rag...")
        result = query_rag_system.query_rag(query_text)
        print(f"[PRINT DEBUG] Resultado de query_rag: {result}")
        logging.info(f"Resultado de query_rag: {type(result)} - {result}")
        
        if not isinstance(result, tuple) or len(result) != 3:
            logging.error(f"ERROR: Resultado no es una tupla de 3 elementos: {result}")
            raise Exception(f"Resultado inválido del sistema RAG: {result}")
        
        response_text, similarity_score, used_kb = result
        print(f"[PRINT DEBUG] Desempaquetado - response: {response_text[:50]}..., similarity: {similarity_score}, used_kb: {used_kb}")
        logging.info(f"Desempaquetado - response_text: {type(response_text)}, similarity_score: {similarity_score}, used_kb: {used_kb}")
        
        # Sanitizar posibles tokens 'undefined' al final
        try:
            import re
            if isinstance(response_text, str):
                response_text = re.sub(r"\s*undefined\s*$", "", response_text)
        except Exception as _san_err:
            logging.debug(f"No se pudo sanitizar 'undefined': {_san_err}")
        
        # Preparar y enviar la respuesta
        response = {
            "response": response_text,
            "similarity": similarity_score,
            "used_knowledge_base": used_kb
        }
        # Enviar respuesta por WebSocket si hay conexión activa
        try:
            socketio.emit("final_response", response)
        except Exception as socket_error:
            print(f"[DEBUG] No se pudo enviar por WebSocket: {socket_error}")
        
        return jsonify(response)

    except Exception as e:
        error_msg = f"Error al procesar la consulta: {str(e)}"
        print(f"[PRINT DEBUG ERROR] {error_msg}")
        print(f"[PRINT DEBUG ERROR] Traceback: {traceback.format_exc()}")
        logging.error(error_msg)
        logging.error(f"Traceback completo: {traceback.format_exc()}")
        
        response = {
            "response": f"Lo siento, hubo un problema al procesar tu consulta: {str(e)}",
            "similarity": 0.0,
            "used_knowledge_base": False
        }
        print(f"[PRINT DEBUG ERROR] Devolviendo respuesta de error: {response}")
        # Enviar respuesta de error por WebSocket si hay conexión activa
        try:
            socketio.emit("final_response", response)
        except Exception as socket_error:
            print(f"[DEBUG] No se pudo enviar error por WebSocket: {socket_error}")
        
        return jsonify(response)

def init_app(app):
    """Inicializa las rutas en la aplicación Flask."""
    app.register_blueprint(bp)
