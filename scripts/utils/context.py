#!/usr/bin/env python3
"""Context Management for Distributed Tracing.

This module provides thread-safe and async-safe context management
for tracing distributed operations using Python's contextvars.

The Trace ID is automatically generated and can be propagated across
function calls, async tasks, and even thread boundaries.

Example Usage:
    >>> from scripts.utils.context import trace_context, get_trace_id
    >>>
    >>> # Automatic trace ID generation
    >>> with trace_context():
    ...     print(f"Trace ID: {get_trace_id()}")
    ...     do_work()
    >>>
    >>> # Custom trace ID (e.g., from HTTP header)
    >>> with trace_context("custom-trace-id-123"):
    ...     process_request()

Autor: DevOps Engineering Team
Versão: 1.0.0
"""

from __future__ import annotations

import contextvars
import uuid
from collections.abc import Generator
from contextlib import contextmanager

# ============================================================
# 1. CONTEXT VARIABLE STORAGE
# ============================================================

# Thread-safe and async-safe storage for Trace ID
# This ContextVar is isolated per execution context (thread, async task, etc.)
_trace_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "trace_id",
    default="",  # Empty default, will be generated on first access
)


# ============================================================
# 2. PUBLIC API
# ============================================================


def get_trace_id() -> str:
    """Get the current Trace ID from context.

    If no Trace ID exists in the current context, a new UUID4 is
    generated and stored automatically.

    Returns:
        Current Trace ID as a string (UUID4 format)

    Example:
        >>> trace_id = get_trace_id()
        >>> print(trace_id)
        'a1b2c3d4-e5f6-7890-1234-567890abcdef'
    """
    trace_id = _trace_id_ctx.get()

    # Generate new Trace ID if not set
    if not trace_id:
        trace_id = str(uuid.uuid4())
        _trace_id_ctx.set(trace_id)

    return trace_id


def set_trace_id(trace_id: str) -> None:
    """Set a custom Trace ID in the current context.

    Use this when you want to propagate a Trace ID from an external
    source (e.g., HTTP headers, message queue metadata).

    Args:
        trace_id: Custom trace ID string

    Example:
        >>> # Propagate trace ID from HTTP header
        >>> incoming_trace_id = request.headers.get("X-Trace-ID")
        >>> if incoming_trace_id:
        ...     set_trace_id(incoming_trace_id)
    """
    _trace_id_ctx.set(trace_id)


@contextmanager
def trace_context(trace_id: str | None = None) -> Generator[str, None, None]:
    """Context manager for scoped Trace ID management.

    This ensures that operations within the context share the same
    Trace ID, and the context is properly cleaned up afterwards.

    Args:
        trace_id: Optional custom trace ID. If None, generates a new UUID4.

    Yields:
        The active Trace ID for this context

    Example:
        >>> # Auto-generate trace ID
        >>> with trace_context() as tid:
        ...     logger.info("Starting operation")
        ...     do_work()
        ...     logger.info("Operation completed")
        >>>
        >>> # Use custom trace ID
        >>> with trace_context("external-trace-123") as tid:
        ...     logger.info(f"Processing with trace: {tid}")

    Note:
        The Trace ID is automatically reset when exiting the context.
        Nested contexts will inherit the parent's Trace ID unless
        explicitly overridden.
    """
    # Save the current trace ID (for restoration)
    token = _trace_id_ctx.set(trace_id if trace_id else str(uuid.uuid4()))

    try:
        # Yield the active trace ID
        yield get_trace_id()
    finally:
        # Restore the previous trace ID
        _trace_id_ctx.reset(token)


# ============================================================
# 3. UTILITY FUNCTIONS
# ============================================================


def reset_trace_id() -> None:
    """Reset the Trace ID to empty state.

    This is primarily useful for testing scenarios where you want
    to ensure a clean state between test cases.

    Warning:
        This should NOT be used in production code. Use trace_context()
        instead for proper context management.

    Example:
        >>> # In test setup
        >>> def setUp(self):
        ...     reset_trace_id()
    """
    _trace_id_ctx.set("")


def generate_new_trace_id() -> str:
    """Generate and set a new Trace ID, returning it.

    This is a convenience function that combines generation and
    setting in one call.

    Returns:
        The newly generated Trace ID

    Example:
        >>> new_trace = generate_new_trace_id()
        >>> assert new_trace == get_trace_id()
    """
    new_id = str(uuid.uuid4())
    set_trace_id(new_id)
    return new_id
