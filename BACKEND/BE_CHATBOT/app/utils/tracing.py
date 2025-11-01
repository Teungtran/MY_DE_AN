"""
Tracing utilities stub - OpenTelemetry removed
All functions return empty values to maintain compatibility.
"""

from typing import Optional, Tuple

from fastapi import Request


def extract_context_from_request(request: Request) -> Optional[None]:
    """Stub - always returns None"""
    return None


def get_current_trace_ids() -> Tuple[Optional[str], Optional[str]]:
    """Stub - always returns None, None"""
    return None, None


def get_tracer(name: Optional[str] = None):
    """Stub - returns None"""
    return None