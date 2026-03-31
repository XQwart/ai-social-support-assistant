import time
import logging

from starlette.requests import Request
from starlette.middleware.base import BaseHTTPMiddleware


logger = logging.getLogger(__name__)


class LogRequestsMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        path = request.url.path
        method = request.method

        try:
            response = await call_next(request)
        except Exception:
            process_time = (time.time() - start_time) * 1000
            logger.exception(
                "Request failed: %s %s - Failed in %.2fms",
                method,
                path,
                process_time,
            )
            raise

        process_time = (time.time() - start_time) * 1000
        logger.info(
            "Request: %s %s - Status: %s - Completed in %.2fms",
            method,
            path,
            response.status_code,
            process_time,
        )
        return response
