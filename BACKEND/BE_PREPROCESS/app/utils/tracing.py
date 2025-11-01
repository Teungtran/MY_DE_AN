"""
Tracing Utilities (Simplified - No OpenTelemetry)

This module provides simplified helper functions for tracing within the FastAPI application.
OpenTelemetry dependencies have been removed.
"""

from typing import Optional, Tuple
import uuid

from fastapi import Request


class SimpleTracer:
    """Simple tracer stub that mimics OpenTelemetry Tracer interface without dependencies."""
    
    def __init__(self, name: str):
        self.name = name
    
    def start_as_current_span(self, name: str, context=None, kind=None, attributes=None):
        """Create a span context manager."""
        return SimpleSpan(name, attributes or {})
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


class SimpleSpan:
    """Simple span stub that mimics OpenTelemetry Span interface."""
    
    def __init__(self, name: str, attributes: dict):
        self.name = name
        self.attributes = attributes
        self.trace_id = format(uuid.uuid4().int & (2**128 - 1), "032x")
        self.span_id = format(uuid.uuid4().int & (2**64 - 1), "016x")
        self.status_code = None
        self.status_message = None
    
    def set_attribute(self, key: str, value):
        """Set a span attribute."""
        self.attributes[key] = value
    
    def set_status(self, status_code, message: Optional[str] = None):
        """Set span status."""
        self.status_code = status_code
        self.status_message = message
    
    def record_exception(self, exception: Exception):
        """Record an exception on the span."""
        self.attributes["exception.type"] = type(exception).__name__
        self.attributes["exception.message"] = str(exception)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


def extract_context_from_request(request: Request) -> Optional[dict]:
    """
    Extracts trace context from incoming request headers (simplified version).

    Args:
        request: The incoming FastAPI Request object containing the headers.

    Returns:
        A dictionary with trace information if headers are found, None otherwise.
    """
    # Check for traceparent header (W3C Trace Context format)
    traceparent = request.headers.get("traceparent")
    if traceparent:
        try:
            # Parse traceparent: version-trace_id-parent_id-flags
            parts = traceparent.split("-")
            if len(parts) >= 2:
                return {
                    "trace_id": parts[1][:32] if len(parts[1]) >= 32 else None,
                    "span_id": parts[2][:16] if len(parts) >= 3 and len(parts[2]) >= 16 else None,
                }
        except Exception:
            pass
    return None


def get_current_trace_ids() -> Tuple[Optional[str], Optional[str]]:
    """
    Retrieves trace IDs from the current request context.

    Returns:
        A tuple containing (trace_id, span_id) or (None, None) if not available.
    """
    # This is a stub - in a real implementation, you'd get this from context vars
    return None, None


def get_tracer(name: Optional[str] = None) -> SimpleTracer:
    """
    Gets a Tracer instance for creating new spans.

    Args:
        name: The name for the tracer.

    Returns:
        A SimpleTracer instance.
    """
    tracer_name = name if name is not None else "default"
    return SimpleTracer(tracer_name)
