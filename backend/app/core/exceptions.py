class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: dict | None = None) -> None:
        self.code, self.message, self.status_code = code, message, status_code
        self.details = details or {}
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, entity: str) -> None:
        super().__init__(f"{entity.upper()}_NOT_FOUND", f"{entity.capitalize()} not found", 404)
