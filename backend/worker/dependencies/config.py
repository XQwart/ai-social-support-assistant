from typing import Annotated

from fastapi import Depends

from worker.core.config import get_config, Config


ConfigDep = Annotated[Config, Depends(get_config)]
