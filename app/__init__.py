import os
from flask import Flask

def create_app():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    templates_dir = os.path.join(base_dir, 'templates')
    static_dir = os.path.join(base_dir, 'static')
    
    app = Flask(__name__, template_folder=templates_dir, static_folder=static_dir)
    app.secret_key = os.urandom(24)
    
    from app.db import init_db
    from app.ml_engine import ChurnMLEngine
    from app.routes import register_routes
    
    ml_engine = ChurnMLEngine()
    init_db(ml_engine=ml_engine)
    register_routes(app)
    
    return app
