"""Shared utility functions used across the application."""

from __future__ import annotations


def clean_string(value: str | None) -> str | None:
    """Strip whitespace and return None for empty strings."""
    if value is None:
        return None
    candidate = value.strip()
    return candidate or None
