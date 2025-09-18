from flask import Flask
from app.routes import init_app
from flask_cors import CORS
from flask_socketio import SocketIO

# Inicialización de la aplicación Flask
app = Flask(__name__)

# Configuración de SocketIO

CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# Inicializa las rutas y SocketIO
init_app(app)

if __name__ == "__main__":
    # Ejecuta la aplicación con soporte de WebSocket
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
