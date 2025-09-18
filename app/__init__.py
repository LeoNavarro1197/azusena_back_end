from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO

socketio = SocketIO(cors_allowed_origins="*")

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev'
    CORS(app, resources={r"/*": {"origins": "*"}})
    socketio.init_app(app)

    from .routes import bp as routes_blueprint 
    print(f"[DEBUG] Registrando blueprint: {routes_blueprint}")
    app.register_blueprint(routes_blueprint)
    
    print("[DEBUG] Rutas registradas después del blueprint:")
    for rule in app.url_map.iter_rules():
        print(f"  {rule.rule} -> {rule.endpoint} ({rule.methods})")

    return app
