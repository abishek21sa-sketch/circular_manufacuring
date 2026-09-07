from __future__ import annotations

class PlatformError(Exception):
    code = "PLATFORM_ERROR"
    http_status = 400

    def __init__(self, message: str, *, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

class ValidationError(PlatformError):
    code = "VALIDATION_ERROR"
    http_status = 422

class NotFoundError(PlatformError):
    code = "NOT_FOUND"
    http_status = 404

class ConflictError(PlatformError):
    code = "CONFLICT"
    http_status = 409

class ExecutionError(PlatformError):
    code = "EXECUTION_ERROR"
    http_status = 500
