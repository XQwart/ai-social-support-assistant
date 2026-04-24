from __future__ import annotations
from typing import Annotated

from fastapi import Depends

from admin_service.core.config import (
    AdminConfig,
    get_admin_config,
    get_shared_backend_config,
)
from app.core.config import Config as BackendConfig


AdminConfigDep = Annotated[AdminConfig, Depends(get_admin_config)]
BackendConfigDep = Annotated[BackendConfig, Depends(get_shared_backend_config)]
