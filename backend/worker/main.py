from __future__ import annotations

from fastapi import FastAPI

from worker.routes.chunks import router as chunks_router


app = FastAPI(
    title="AI Social Support Assistant API",
    version="1.0.0",
)


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
    }


app.include_router(chunks_router)
