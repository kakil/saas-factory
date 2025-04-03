from typing import Any, Dict, Optional

from fastapi import HTTPException, status


class BaseAPIException(HTTPException):
    """
    Base exception for API errors with standardized format
    """
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: str = None,
        headers: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code


class NotFoundException(BaseAPIException):
    """
    Exception for resource not found errors
    """
    def __init__(
        self,
        detail: str = "Resource not found",
        error_code: str = "NOT_FOUND",
        headers: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code=error_code,
            headers=headers,
        )


class AuthenticationException(BaseAPIException):
    """
    Exception for authentication errors
    """
    def __init__(
        self,
        detail: str = "Authentication failed",
        error_code: str = "AUTHENTICATION_FAILED",
        headers: Optional[Dict[str, Any]] = None,
    ):
        if headers is None:
            headers = {"WWW-Authenticate": "Bearer"}
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code=error_code,
            headers=headers,
        )


class PermissionDeniedException(BaseAPIException):
    """
    Exception for permission errors
    """
    def __init__(
        self,
        detail: str = "Permission denied",
        error_code: str = "PERMISSION_DENIED",
        headers: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code=error_code,
            headers=headers,
        )


class ValidationException(BaseAPIException):
    """
    Exception for validation errors
    """
    def __init__(
        self,
        detail: str = "Validation error",
        error_code: str = "VALIDATION_ERROR",
        headers: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code=error_code,
            headers=headers,
        )


class ServiceUnavailableException(BaseAPIException):
    """
    Exception for service unavailable errors
    """
    def __init__(
        self,
        detail: str = "Service unavailable",
        error_code: str = "SERVICE_UNAVAILABLE",
        headers: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
            error_code=error_code,
            headers=headers,
        )