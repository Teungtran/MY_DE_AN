from typing import cast

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html


from controllers import api_chat



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




# Health check endpoint
@app.get("/", tags=["health"])
async def root():
    """Root endpoint for health checks"""
    return {
        "service": "BE_ADMIN - Team Chat Service",
        "version": app.version,
        "status": "healthy",
        "endpoints": {
            "team_chat_stream": "/v1/chat/team/chat/stream",
            "team_chat": "/v1/chat/team/chat",
            "report_upload_analyze": "/v1/chat/report/upload-and-analyze",
            "report_files": "/v1/chat/report/files",
            "docs": "/docs"
        }
    }


# Include routers
app.include_router(api_chat.router, prefix="/v1/chat", tags=["Team Chat & Report Analysis API"])

# For local development
if __name__ == "__main__":
    import uvicorn
    import os
    import sys
    
    # Add the parent directory to sys.path to make absolute imports work
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    
    # Start the server
    uvicorn.run("app.main:app", host="0.0.0.0", port=8888, reload=False, log_level="debug")
