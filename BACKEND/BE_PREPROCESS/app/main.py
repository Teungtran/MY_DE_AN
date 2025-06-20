from typing import Any, Awaitable, Callable, Dict, Optional, cast

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from opentelemetry import context
from opentelemetry.trace import SpanKind, StatusCode, Tracer
import structlog
from controllers.url_controllers.url import url_router
from controllers.pdf_controller.pdf import pdf_router

from controllers.url_controllers.recommend_data import recommend_router
from utils.helpers import LoggingMiddleware
from utils.helpers.exception_handler import ExceptionHandler, FunctionName, ServiceName
from utils.logger import get_logger, setup_logging
from utils.tracing import extract_context_from_request, get_current_trace_ids, get_tracer

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
    FastAPI middleware for OpenTelemetry tracing and Structlog context integration.

    This middleware performs the following actions for each incoming request:
    1. Extracts the parent trace context (e.g., from 'traceparent' header)
       using the globally configured OpenTelemetry propagator.
    2. Starts a new OpenTelemetry server span, linking it to the parent context if found.
    3. Populates the new span with standard HTTP semantic attributes (method, URL, etc.).
    4. Binds relevant HTTP request information (method, URI, client IP) into
       Structlog's contextvars for consistent structured logging downstream.
    5. Calls the next middleware or the endpoint handler (`call_next`).
    6. Upon receiving the response (or handling an exception):
        - Sets the 'http.status_code' attribute on the span.
        - Sets the span status (OK or ERROR) based on the HTTP status code.
        - Records any unhandled exceptions originating from `call_next` onto the span.
        - Updates the Structlog contextvars with the final HTTP status code.
    7. Ensures Structlog contextvars specific to this request are cleared using a
       `finally` block to prevent context leakage between requests.
    8. Adds 'trace_id' and 'span_id' (of the created server span) headers
       to the outgoing response for correlation.

    Args:
        request: The incoming FastAPI Request object.
        call_next: A callable that receives the request and returns an awaitable
                   response. This represents the next step in the request processing
                   pipeline (another middleware or the route handler).

    Returns:
        The Response object generated by the subsequent middleware or route handler,
        potentially modified with added trace headers.
    """
    # 1. Extract parent context from request headers
    parent_context: Optional[context.Context] = extract_context_from_request(request)
    tracer: Tracer = get_tracer(__name__)  # Get tracer named after this module

    # 2. & 3. Start a new server span with HTTP attributes
    span_name = f"HTTP {request.method}"  # Standard naming convention
    client_ip: Optional[str] = request.client.host if request.client else None
    attributes: Dict[str, Any] = {
        "http.method": request.method,
        "http.url": str(request.url),
        "http.target": request.url.path,  # Path part of the URL
        "http.host": request.url.hostname,  # Host header value
        "http.scheme": request.url.scheme,  # e.g., "http" or "https"
        "http.client_ip": client_ip,
    }

    with tracer.start_as_current_span(
        span_name,
        context=parent_context,  # Link to parent if context was extracted
        kind=SpanKind.SERVER,  # Mark this as a server-side span
        attributes=attributes,
    ) as span:  # Get the Span object for later modification
        # Get IDs of the *newly created* server span
        current_trace_id: Optional[str]
        current_span_id: Optional[str]
        current_trace_id, current_span_id = get_current_trace_ids()
        http_info_for_log: Dict[str, Optional[str]] = {
            "method": request.method,
            "uri": str(request.url),  # Full URL including query params
            "client_ip": client_ip,
        }
        structlog.contextvars.bind_contextvars(http=http_info_for_log)

        response: Optional[Response] = None
        try:
            # 5. Call the next middleware/handler
            response = await call_next(request)

            # 6a. Record response status on the span and in Structlog context
            span.set_attribute("http.status_code", response.status_code)
            # Update contextvars so access logs (often logged after handler returns)
            # can see the final status code. We merge it with existing 'http' info.
            structlog.contextvars.bind_contextvars(http={"status_code": response.status_code})

            # Set span status based on HTTP status code
            if 500 <= response.status_code < 600:
                span.set_status(StatusCode.ERROR, f"HTTP server error: {response.status_code}")
            # Consider other error ranges (e.g., 4xx) if appropriate for your use case
            # elif 400 <= response.status_code < 500:
            #     span.set_status(StatusCode.ERROR, f"HTTP client error: {response.status_code}")
            else:
                span.set_status(StatusCode.OK)

        except Exception as e:
            # 6b. Record unhandled exceptions on the span and in Structlog context
            span.set_status(StatusCode.ERROR, f"Unhandled exception: {type(e).__name__}")
            # Records exception type, value, and traceback on the span
            span.record_exception(e)
            # Assume status 500 for unhandled exceptions for logging context
            structlog.contextvars.bind_contextvars(http={"status_code": 500})
            raise e  # Re-raise the exception to be handled by FastAPI's exception handlers

        finally:
            # 7. Clear Structlog contextvars bound in this middleware
            # Crucial to prevent leaking context (like 'http' info) to other requests.
            structlog.contextvars.clear_contextvars()

        # 8. Add trace headers to the outgoing response
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


app.include_router(url_router, prefix="/internal/v1", tags=["RAG controller"])
app.include_router(pdf_router, prefix="/internal/v1", tags=["RAG controller"])
app.include_router(recommend_router, prefix="/internal/v1", tags=["Reommmend controller"])


# For local development
if __name__ == "__main__":
    import uvicorn

    # Start the server
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="debug")
