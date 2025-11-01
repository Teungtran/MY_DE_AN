from typing import Awaitable, Callable, Dict, Optional

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from typing import cast
import structlog

from app.controllers import api_chat
from app.utils.helpers import LoggingMiddleware
from app.utils.logging.logger import get_logger, setup_logging

setup_logging(json_logs=True)
logger = get_logger(__name__)


# Create FastAPI app
app = FastAPI(
    title="Orchestrator Service",
    description="API for handling and orchestrating chatbot requests.",
    version="0.1.0",
    docs_url=None,  # Disable /docs endpoint (we'll create a custom one)
    redoc_url=None,  # Disable /redoc endpoint (we'll create a custom one)
    openapi_url=r"/api/openapi.json",
    # lifespan=lifespan
)
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

app.add_middleware(LoggingMiddleware, logger=logger)
app.add_middleware(CorrelationIdMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Custom API docs
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Custom Swagger UI docs endpoint"""
    return get_swagger_ui_html(
        openapi_url=cast(str, app.openapi_url),
        title=f"{app.title} - API Documentation",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
    )


@app.middleware("http")
async def http_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    """
    Simple HTTP middleware for Structlog context integration.
    
    Binds HTTP request information to Structlog contextvars for consistent structured logging.
    """
    client_ip: Optional[str] = request.client.host if request.client else None
    
    # Bind HTTP info to Structlog contextvars for logging
    http_info_for_log: Dict[str, Optional[str]] = {
        "method": request.method,
        "uri": str(request.url),
        "client_ip": client_ip,
    }
    structlog.contextvars.bind_contextvars(http=http_info_for_log)

    response: Optional[Response] = None
    try:
        # Call the next middleware/handler
        response = await call_next(request)
        
        # Update contextvars with final status code
        structlog.contextvars.bind_contextvars(http={"status_code": response.status_code})
        
    except Exception as e:
        # Set status code to 500 for unhandled exceptions
        structlog.contextvars.bind_contextvars(http={"status_code": 500})
        raise e
    
    finally:
        # Clear Structlog contextvars to prevent context leakage
        structlog.contextvars.clear_contextvars()

    return response


# Health check endpoint
@app.get("/", tags=["health"])
async def root():
    """Root endpoint for health checks"""
    return {
        # "name": get_settings().APP_NAME,
        "version": app.version,
        "status": "healthy",
    }


app.include_router(api_chat.router, prefix="/v1/chat", tags=["Chat controller"])

# For local development
if __name__ == "__main__":
    import uvicorn
    import os
    import sys
    
    # Add the parent directory to sys.path to make absolute imports work
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    

    
    # Start the server
    uvicorn.run("app.main:app", host="0.0.0.0", port=8888, reload=False, log_level="debug")
