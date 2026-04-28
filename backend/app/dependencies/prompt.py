from typing import Annotated

from fastapi import Depends, Request

from app.services.prompt_service import PromptService


def get_prompt_service(request: Request) -> PromptService:
    return request.app.state.prompt_service


PromptServiceDep = Annotated[PromptService, Depends(get_prompt_service)]
