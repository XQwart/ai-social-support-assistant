export class UnauthorizedError extends Error {
  constructor(message = "Сессия истекла. Войдите снова.") {
    super(message);
    this.name = "UnauthorizedError";
  }
}
