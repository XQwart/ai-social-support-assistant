from typing import Annotated

from fastapi import Depends

from app.core.config import get_config, Config


ConfigDep = Annotated[Config, Depends(get_config)]
