from flask import Flask
from flask_cors import CORS
from .config import Config
from .routes import images, json, store

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app, resources={
        r"/uploads/*": {"origins": ["http://localhost:3000"]},
        r"/upload/*": {"origins": ["http://localhost:3000"]},
        r"/delete/*": {"origins": ["http://localhost:3000"]}
    })
    # Register blueprints
    app.register_blueprint(images.bp)
    app.register_blueprint(json.bp)
    app.register_blueprint(store.bp)
    return app