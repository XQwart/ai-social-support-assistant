from typing import Annotated

from fastapi import Depends

from app.services.ai_service import AIService
from app.dependencies.config import ConfigDep


def get_ai_service(config: ConfigDep) -> AIService:
    return AIService(config)


AIServiceDep = Annotated[AIService, Depends(get_ai_service)]
