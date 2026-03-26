import time
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse

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
            method,
            path,
            response.status_code,
            process_time,
        )
        return response
    except Exception as e:
        process_time = (time.time() - start_time) * 1000
        logger.exception(
            "Request failed: %s %s - Error: %s - Failed in %.2fms",
            method,
            path,
            str(e),
            process_time,
        )
        return JSONResponse(
            status_code=500, content={"detail": "Internal Server Error"}
        )


app.include_router(auth.router)
app.include_router(message.router)
app.include_router(chat.router)

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


@app.get("/")
def root():
    html = """
    <!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://id-ift.sber.ru/sdk/web/sberid-sdk.production.js"></script>
    <title>Document</title>
</head>

<body>
    <div class="sberIdButton"></div>


    <script>

        async function init() {
            try {
                // GET запрос
                const response = await fetch("http://localhost:8000/auth/sber/params");

                // Получаем данные из ответа
                const data = await response.json();  // если сервер возвращает JSON

                console.log(data); // смотрим что пришло

                // Теперь используем данные из ответа
                new SberidSDK({
                    baseUrl: 'https://id-ift.sber.ru',
                    oidc: {
                        client_id: data.client_id,        // например из ответа
                        client_type: "PRIVATE",
                        nonce: data.nonce,
                        redirect_uri: data.redirect_uri,
                        state: data.state,
                        scope: data.scopes,
                        response_type: data.response_type,
                        name: "ИИ-помощник по социальной поддержке"
                    },
                    container: '.sberIdButton'
                })
                    .init()
                    .then((sdk) => {
                        // sdk инициализирован
                    });

            } catch (error) {
                console.error("Ошибка запроса:", error);
            }
        }

        init();
    </script>
</body>

</html>
"""
    return HTMLResponse(content=html)
