import time
import logging
from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

from app.routes import auth, message, chat
from app.core.lifespan import lifespan

logger = logging.getLogger(__name__)

app = FastAPI(lifespan=lifespan)

@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    start_time = time.time()
    path = request.url.path
    method = request.method
    
    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        logger.info(
            "Request: %s %s - Status: %s - Completed in %.2fms",
            method, path, response.status_code, process_time
        )
        return response
    except Exception as e:
        process_time = (time.time() - start_time) * 1000
        logger.exception(
            "Request failed: %s %s - Error: %s - Failed in %.2fms",
            method, path, str(e), process_time
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error"}
        )

app.include_router(auth.router)
app.include_router(message.router)
app.include_router(chat.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root(state: str = Query(...), code: str = Query(...)):  # Временный костыль
    return RedirectResponse(
        f"/auth/sber/callback?code={code}&state={state}", status_code=302
    )
