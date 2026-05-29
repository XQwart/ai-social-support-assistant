"""Pytest configuration shared by all backend tests.

Ensures the backend root is on sys.path so the tests can ``import app``,
``import shared``, ``import worker`` and ``import admin_service`` without
having to package them.
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
