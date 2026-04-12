export class UnauthorizedError extends Error {
  status: number;

  constructor(message = "Сессия истекла. Войдите снова.", status = 401) {
    super(message);
    this.name = "UnauthorizedError";
    this.status = status;
  }
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}
