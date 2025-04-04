from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.core.errors.exceptions import (
    BaseAPIException,
    NotFoundException,
    AuthenticationException,
    PermissionDeniedException,
    ValidationException,
    ServiceUnavailableException,
)


def add_exception_handlers(app: FastAPI) -> None:
    """
    Add exception handlers to the FastAPI application
    """
    
    @app.exception_handler(BaseAPIException)
    async def handle_base_api_exception(request: Request, exc: BaseAPIException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "code": exc.error_code,
                "message": exc.detail,
            },
            headers=exc.headers,
        )

    @app.exception_handler(NotFoundException)
    async def handle_not_found_exception(request: Request, exc: NotFoundException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "code": exc.error_code,
                "message": exc.detail,
            },
            headers=exc.headers,
        )

    @app.exception_handler(AuthenticationException)
    async def handle_authentication_exception(request: Request, exc: AuthenticationException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "code": exc.error_code,
                "message": exc.detail,
            },
            headers=exc.headers,
        )

    @app.exception_handler(PermissionDeniedException)
    async def handle_permission_denied_exception(request: Request, exc: PermissionDeniedException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "code": exc.error_code,
                "message": exc.detail,
            },
            headers=exc.headers,
        )

    @app.exception_handler(ValidationException)
    async def handle_validation_exception(request: Request, exc: ValidationException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "code": exc.error_code,
                "message": exc.detail,
            },
            headers=exc.headers,
        )

    @app.exception_handler(ServiceUnavailableException)
    async def handle_service_unavailable_exception(request: Request, exc: ServiceUnavailableException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "code": exc.error_code,
                "message": exc.detail,
            },
            headers=exc.headers,
        )

    @app.exception_handler(SQLAlchemyError)
    async def handle_sqlalchemy_exception(request: Request, exc: SQLAlchemyError):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "code": "DATABASE_ERROR",
                "message": "A database error occurred",
            },
        )

    @app.exception_handler(Exception)
    async def handle_generic_exception(request: Request, exc: Exception):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
            },
        )
