from __future__ import annotations
from typing import TYPE_CHECKING

from fastapi.templating import Jinja2Templates

from .config import TEMPLATES_DIR, get_admin_config

if TYPE_CHECKING:
    pass


def create_templates() -> Jinja2Templates:
    config = get_admin_config()
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
    templates.env.globals["app_name"] = "SOC Admin"
    # ``base_path`` is the public mount path of the admin service
    # behind nginx (e.g. ``/admin``). Templates prepend it to every
    # absolute URL — links, form actions, /static/ refs — so the
    # browser stays inside the admin namespace.
    templates.env.globals["base_path"] = config.normalized_base_path
    return templates


templates = create_templates()
