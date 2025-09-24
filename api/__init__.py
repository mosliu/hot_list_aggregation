"""API模块"""

from .app import app
from .endpoints import news, events, labeling, system

__all__ = ["app"]