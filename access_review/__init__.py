"""Manager Access Review Assistant."""

from .analyzer import analyze_access
from .repository import load_snapshot

__all__ = ["analyze_access", "load_snapshot"]
