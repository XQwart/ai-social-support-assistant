class AppError(Exception):
    detail: str

    status_code = 500

    def __init__(self, detail: str = "Application error") -> None:
        self.detail = detail


class NotFoundError(AppError):
    status_code = 404


class NotAuthenticatedError(AppError):
    status_code = 401


class ForbiddenError(AppError):
    status_code = 403


class BadRequestError(AppError):
    status_code = 400


class ExternalServiceError(AppError):
    status_code = 502
