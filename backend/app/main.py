from fastapi import FastAPI

from app.routes import auth

from core.lifespan import lifespan


app = FastAPI(lifespan=lifespan)

app.include_router(auth.router)
