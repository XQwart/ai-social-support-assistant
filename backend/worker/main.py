from __future__ import annotations

from fastapi import FastAPI

from worker.routes.chunks import router as chunks_router
from worker.routes.source import router as source_router
from worker.core.lifespan import lifespan

app = FastAPI(
    title="AI Social Support Assistant API", version="1.0.0", lifespan=lifespan
)


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
    }


app.include_router(chunks_router)
app.include_router(source_router)
