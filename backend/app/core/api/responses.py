from typing import Any, Dict, Generic, List, Optional, TypeVar, Union
from pydantic import BaseModel

DataT = TypeVar('DataT')
MetaT = TypeVar('MetaT')


class PageMeta(BaseModel):
    """
    Metadata for paginated responses
    """
    total: int
    page: int
    page_size: int
    pages: Optional[int] = None
    has_next: Optional[bool] = None
    has_prev: Optional[bool] = None
    next_page: Optional[int] = None
    prev_page: Optional[int] = None


class APIResponse(BaseModel, Generic[DataT, MetaT]):
    """
    Standard API response format
    """
    status: str
    message: Optional[str] = None
    data: Optional[DataT] = None
    meta: Optional[MetaT] = None


def success_response(
    data: Any = None,
    message: str = "Success",
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create a standardized success response
    """
    return {
        "status": "success",
        "message": message,
        "data": data,
        "meta": meta,
    }


def error_response(
    message: str = "An error occurred",
    code: str = "ERROR",
    data: Any = None,
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create a standardized error response
    """
    return {
        "status": "error",
        "code": code,
        "message": message,
        "data": data,
        "meta": meta,
    }


def paginated_response(
    items: List[Any],
    total: int,
    page: int = 1,
    page_size: int = 100,
    message: str = "Success",
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create a standardized paginated response
    """
    # Calculate pagination metadata
    pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    has_next = page < pages
    has_prev = page > 1
    
    # Build pagination metadata
    pagination_meta = {
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
        "has_next": has_next,
        "has_prev": has_prev,
    }
    
    # Add next/prev page numbers if applicable
    if has_next:
        pagination_meta["next_page"] = page + 1
    if has_prev:
        pagination_meta["prev_page"] = page - 1
    
    # Combine with additional metadata
    if meta is None:
        meta = {}
    meta.update({"pagination": pagination_meta})
    
    return {
        "status": "success",
        "message": message,
        "data": items,
        "meta": meta,
    }
