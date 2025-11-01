from typing import Any, Awaitable, Callable, Dict, Optional, cast
import uuid

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI, Request, Response, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
import structlog
from app.controllers.url_controllers.rag_url import url_router as rag_url_router
from app.controllers.pdf_controller.rag_pdf import pdf_router as rag_pdf_router
from app.controllers.url_controllers.expert_url import url_router as expert_url_router
from app.controllers.pdf_controller.expert_pdf import pdf_router as expert_pdf_router
from app.controllers.url_controllers.recommend_data import recommend_router
from app.utils.helpers import LoggingMiddleware
from app.utils.helpers.exception_handler import ExceptionHandler, FunctionName, ServiceName
from app.utils.logger import get_logger, setup_logging
from app.utils.tracing import extract_context_from_request
from app.utils.auth import require_admin_role

setup_logging(json_logs=True)
logger = get_logger(__name__)
app = FastAPI(
    title="Preprocessing Service",
    description="API for processing files and URLs, extracting content, and storing in vector databases",
    version="0.1.0",
    docs_url=None,  # Disable /docs endpoint (we'll create a custom one)
    redoc_url=None,  # Disable /redoc endpoint (we'll create a custom one)
    openapi_url=r"/api/openapi.json",
    # lifespan=lifespan
)

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


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    """
    Global exception handler for Pydantic validation errors.
    Transforms the error into the standardized error response format.
    """
    exception_handler = ExceptionHandler(
        logger=logger.bind(),
        service_name=ServiceName.PREPROCESSING,
        function_name=FunctionName.DATA_PIPELINE,
    )
    trace_id = request.headers.get("trace_id", "unknown")

    # Extract error details
    error_details = [
        {
            "field": ".".join(map(str, error["loc"])),
            "message": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors()
    ]

    # Log the error
    logger.error(
        "Validation error occurred",
        trace_id=trace_id,
        errors=error_details,
        exc_info=True,
    )

    # Return a standardized bad request response
    return exception_handler.handle_bad_request(
        e="Invalid request payload. Please check the input fields.",
        extra={"errors": error_details},
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
async def trace_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    """
    FastAPI middleware for tracing and Structlog context integration (simplified version without OpenTelemetry).

    This middleware performs the following actions for each incoming request:
    1. Extracts trace context from request headers if available
    2. Generates new trace/span IDs if not present
    3. Binds HTTP request information into Structlog's contextvars
    4. Calls the next middleware or endpoint handler
    5. Updates Structlog context with response status
    6. Adds trace headers to the response

    Args:
        request: The incoming FastAPI Request object.
        call_next: A callable that receives the request and returns an awaitable response.

    Returns:
        The Response object with trace headers added.
    """
    # Extract or generate trace IDs
    trace_context = extract_context_from_request(request)
    if trace_context and trace_context.get("trace_id"):
        current_trace_id = trace_context["trace_id"]
        current_span_id = trace_context.get("span_id") or format(uuid.uuid4().int & (2**64 - 1), "016x")
    else:
        # Generate new trace IDs if not present
        current_trace_id = format(uuid.uuid4().int & (2**128 - 1), "032x")
        current_span_id = format(uuid.uuid4().int & (2**64 - 1), "016x")

    client_ip: Optional[str] = request.client.host if request.client else None
    http_info_for_log: Dict[str, Optional[str]] = {
        "method": request.method,
        "uri": str(request.url),
        "client_ip": client_ip,
    }
    structlog.contextvars.bind_contextvars(
        http=http_info_for_log,
        trace_id=current_trace_id,
        span_id=current_span_id,
    )

    response: Optional[Response] = None
    try:
        # Call the next middleware/handler
        response = await call_next(request)

        # Update contextvars with response status
        structlog.contextvars.bind_contextvars(http={"status_code": response.status_code})

    except Exception as e:
        # Log exception and set status code for error context
        structlog.contextvars.bind_contextvars(http={"status_code": 500})
        raise e  # Re-raise the exception

    finally:
        # Clear Structlog contextvars to prevent context leakage
        structlog.contextvars.clear_contextvars()

    # Add trace headers to the outgoing response
    if current_trace_id:
        response.headers["trace_id"] = current_trace_id
    if current_span_id:
        response.headers["span_id"] = current_span_id

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


# All routes require admin authentication
app.include_router(
    rag_url_router, 
    prefix="/internal/v1", 
    tags=["RAG controller"],
    # dependencies=[Depends(require_admin_role)]  # Temporarily commented for testing
)
app.include_router(
    rag_pdf_router, 
    prefix="/internal/v1", 
    tags=["RAG controller"],
    # dependencies=[Depends(require_admin_role)]  # Temporarily commented for testing
)
app.include_router(
    expert_pdf_router, 
    prefix="/internal/v1", 
    tags=["Expert controller"],
    # dependencies=[Depends(require_admin_role)]  # Temporarily commented for testing
)
app.include_router(
    expert_url_router, 
    prefix="/internal/v1", 
    tags=["Expert controller"],
    # dependencies=[Depends(require_admin_role)]  # Temporarily commented for testing
)
app.include_router(
    recommend_router, 
    prefix="/internal/v1", 
    tags=["Reommmend controller"],
    # dependencies=[Depends(require_admin_role)]  # Temporarily commented for testing
)


# For local development
if __name__ == "__main__":
    import uvicorn

    # Start the server
    uvicorn.run("app.main:app", host="0.0.0.0", port=8888, reload=False, log_level="debug")
