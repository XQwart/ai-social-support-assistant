from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import router
from app.core.lifespan import lifespan
from app.exceptions.handlers import init_exception_handlers
from app.middlewares.logging_middleware import LogRequestsMiddleware


app = FastAPI(lifespan=lifespan)

app.include_router(router)

init_exception_handlers(app)

app.add_middleware(LogRequestsMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
