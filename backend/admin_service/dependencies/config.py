from __future__ import annotations
from typing import Annotated

from fastapi import Depends

from admin_service.core.config import AdminConfig, get_admin_config


AdminConfigDep = Annotated[AdminConfig, Depends(get_admin_config)]
