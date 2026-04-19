"""
Vishleshak AI Backend
=====================
Clean, modular backend architecture.

Structure:
- api/          Flask API routes and handlers
- core/         Shared utilities, config, exceptions
- services/     Business logic layer
- models/       Data models and schemas
"""

from __future__ import annotations

import sys
from pathlib import Path

_APP_MODULES = Path(__file__).resolve().parent / "app_modules"
if _APP_MODULES.exists():
    _p = str(_APP_MODULES)
    if _p not in sys.path:
        sys.path.insert(0, _p)

__version__ = "2.0.0"
