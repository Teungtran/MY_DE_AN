"""
OpenTelemetry Tracing Utilities

This module provides helper functions for integrating OpenTelemetry tracing
within the FastAPI application, specifically focusing on context propagation
and accessing trace/span identifiers.
"""

from typing import Optional, Tuple

from fastapi import Request
from opentelemetry import context, trace
from opentelemetry.propagate import extract, set_global_textmap
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
from opentelemetry.trace import Tracer, get_current_span
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

# 1. Init TracerProvider
trace_provider = TracerProvider()
trace_provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
trace.set_tracer_provider(TracerProvider())

# 1. Config W3C Trace Context global propagator
set_global_textmap(TraceContextTextMapPropagator())


def extract_context_from_request(request: Request) -> Optional[context.Context]:
    """
    Extracts the OpenTelemetry trace context from incoming request headers.

    Uses the globally configured text map propagator (typically W3C TraceContext)
    to parse headers like 'traceparent' and 'tracestate'.

    Args:
        request: The incoming FastAPI Request object containing the headers.

    Returns:
        An OpenTelemetry Context object containing the extracted trace information
        if propagation headers are found and valid. Returns None if headers are
        missing, invalid, or an error occurs during extraction.
    """
    # Create a carrier dictionary with lowercase keys from request headers
    # for case-insensitive header extraction, as required by propagators.
    carrier = {k.lower(): v for k, v in request.headers.items()}
    try:
        # Attempt to extract the context using the globally set propagator.
        # This will return a new context object populated with data from the carrier.
        extracted_context: Optional[context.Context] = extract(carrier)
        return extracted_context
    except Exception:
        # Log a warning if context extraction fails (optional but recommended)
        # logger.warning(
        #     "Failed to extract trace context from request headers.",
        #     exc_info=True, # Include exception details in the log
        #     headers=carrier # Optionally log the headers (be careful with sensitive data)
        # )
        # Return None to indicate that no valid parent context was found.
        return None


def get_current_trace_ids() -> Tuple[Optional[str], Optional[str]]:
    """
    Retrieves the Trace ID and Span ID from the currently active OpenTelemetry span.

    This function accesses the current span context managed by OpenTelemetry.
    If a valid span is active, it returns its identifiers formatted as hex strings.

    Returns:
        A tuple containing:
            - The Trace ID (str): 32-character lowercase hex string, or None if no valid span.
            - The Span ID (str): 16-character lowercase hex string, or None if no valid span.
    """
    # Get the current span from the active OpenTelemetry context.
    current_span = get_current_span()
    # Retrieve the SpanContext associated with the current span.
    span_context = current_span.get_span_context()

    # Check if the SpanContext is valid. A valid context typically means it has
    # non-zero Trace ID and Span ID, and its trace flags indicate sampling.
    if span_context.is_valid:
        # Format Trace ID as a 32-character zero-padded lowercase hex string.
        trace_id = format(span_context.trace_id, "032x")
        # Format Span ID as a 16-character zero-padded lowercase hex string.
        span_id = format(span_context.span_id, "016x")
        return trace_id, span_id
    else:
        # If the current span context is not valid (e.g., no active span,
        # or it's a non-recording span), return None for both identifiers.
        return None, None


def get_tracer(name: Optional[str] = None) -> Tracer:
    """
    Gets an OpenTelemetry Tracer instance for creating new spans.

    It's standard practice to name tracers after the instrumented module or library.
    If no name is provided, it defaults to the name of the module calling this function.

    Args:
        name: The name for the tracer. Defaults to the calling module's name (`__name__`).

    Returns:
        An OpenTelemetry Tracer instance.
    """
    # If no specific name is provided, use the standard Python `__name__`
    # of the module where get_tracer is called. This helps identify the
    # origin of spans created by this tracer.
    tracer_name = name if name is not None else __name__
    return trace.get_tracer(tracer_name)
