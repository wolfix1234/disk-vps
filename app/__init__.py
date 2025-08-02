from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import Config
from .routes import images, json, store

def create_app():
    app = FastAPI(
        title="Store API",
        description="API for managing stores, images, and JSON files",
        version="1.0.0"
    )
    
    config = Config()
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(images.router, tags=["images"])
    app.include_router(json.router, tags=["json"])
    app.include_router(store.router, tags=["store"])
    
    return app