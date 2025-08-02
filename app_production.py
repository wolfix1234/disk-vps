"""
Production-ready FastAPI application with all security middleware enabled.
This file is optimized for container deployment.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import Config
from app.api.v1.router import router as api_v1_router
from app.middleware.security import SecurityHeadersMiddleware, RequestLoggingMiddleware, RateLimitMiddleware

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # For container logs
    ]
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info("🚀 Starting Store API in PRODUCTION mode...")
    yield
    logger.info("🛑 Shutting down Store API...")

def create_app() -> FastAPI:
    """Create a production-ready FastAPI application with all security features enabled."""
    
    config = Config()
    
    app = FastAPI(
        title="Store Management API",
        description="""
        A production-ready API for managing stores, images, and JSON files.
        
        ## Features
        - RESTful API design
        - Automatic request/response validation
        - Rate limiting and security headers
        - Comprehensive error handling
        - API versioning
        - Interactive documentation
        
        ## Authentication
        All endpoints require Bearer token authentication.
        
        ### How to authenticate:
        1. Click the "Authorize" button below
        2. Enter your API token in the "Value" field
        3. Click "Authorize"
        4. Now you can test all endpoints with authentication
        
        Alternatively, include your API token in the Authorization header:
        `Authorization: Bearer your-token-here`
        """,
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )
    

    
    # ========================================
    # PRODUCTION MIDDLEWARE - ALL ENABLED
    # ========================================
    
    # Security middleware - Adds security headers (CSP, XSS protection, etc.)
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Request logging - Logs all incoming requests and response times
    app.add_middleware(RequestLoggingMiddleware)
    
    # Rate limiting - Limits requests to 100 per minute per IP
    app.add_middleware(RateLimitMiddleware, calls=100, period=60)
    
    # Trusted hosts - Configure based on your deployment
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Configure this for your specific domains in production
    )
    
    # CORS middleware - Controls cross-origin requests
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
        expose_headers=["*"]
    )
    
    # Include API routes
    app.include_router(api_v1_router)
    
    # Global exception handlers
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle validation errors with detailed messages."""
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": "Validation Error",
                "details": exc.errors(),
                "message": "Please check your request data and try again."
            }
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle HTTP exceptions with consistent format."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": exc.detail,
                "status_code": exc.status_code
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle unexpected errors."""
        logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": "Internal Server Error",
                "message": "An unexpected error occurred. Please try again later."
            }
        )
    
    # Health check endpoint
    @app.get("/health", tags=["health"])
    async def health_check():
        """Health check endpoint for monitoring."""
        return {
            "status": "healthy",
            "version": "1.0.0",
            "environment": "production"
        }
    
    # Root endpoint
    @app.get("/", tags=["root"])
    async def root():
        """Root endpoint with API information."""
        return {
            "message": "Store Management API",
            "version": "1.0.0",
            "environment": "production",
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/health"
        }
    
    return app

# Create the app instance
app = create_app()