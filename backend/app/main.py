from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.routes import auth
from app.core.lifespan import lifespan


app = FastAPI(lifespan=lifespan)

app.include_router(auth.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root(state: str = Query(...), code: str = Query(...)):  # Временный костыль
    return RedirectResponse(
        f"/auth/sber/callback?code={code}&state={state}", status_code=302
    )
