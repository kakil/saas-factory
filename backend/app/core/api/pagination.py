from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from pydantic import BaseModel
from fastapi import Query, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, select

from app.core.db.base import Base
from app.core.db.repository import BaseRepository, ModelType, CreateSchemaType, UpdateSchemaType

T = TypeVar('T', bound=Base)
SchemaType = TypeVar('SchemaType', bound=BaseModel)


class PaginationParams:
    """
    Reusable pagination parameters for API endpoints
    """
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(50, ge=1, le=500, description="Items per page"),
    ):
        self.page = page
        self.page_size = page_size
        self.skip = (page - 1) * page_size
        self.limit = page_size


class PaginatedResult(Generic[T]):
    """
    Paginated result with items and metadata
    """
    def __init__(
        self,
        items: List[T],
        total: int,
        page: int,
        page_size: int,
    ):
        self.items = items
        self.total = total
        self.page = page
        self.page_size = page_size
        self.pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        self.has_next = page < self.pages
        self.has_prev = page > 1


def paginate_query(
    repo: BaseRepository[ModelType, CreateSchemaType, UpdateSchemaType],
    params: PaginationParams,
    schema_cls: Type[SchemaType] = None,
    query_filter = None,
    query_options = None,
) -> PaginatedResult[Union[ModelType, SchemaType]]:
    """
    Create a paginated result from a repository query
    
    Args:
        repo: The repository instance
        params: Pagination parameters
        schema_cls: Optional Pydantic schema class to convert models
        query_filter: Optional filter to apply to the query
        query_options: Optional options to apply to the query
        
    Returns:
        PaginatedResult containing items and pagination metadata
    """
    # Create base query
    query = repo.db.query(repo.model)
    
    # Apply tenant filtering if repository is tenant-aware
    if hasattr(repo, '_apply_tenant_filter') and callable(getattr(repo, '_apply_tenant_filter')):
        query = repo._apply_tenant_filter(query)
    
    # Apply additional filter if provided
    if query_filter is not None:
        query = query.filter(query_filter)
    
    # Apply query options if provided
    if query_options is not None:
        query = query.options(query_options)
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    items = query.offset(params.skip).limit(params.limit).all()
    
    # Convert to schema if schema_cls is provided
    if schema_cls is not None:
        items = [schema_cls.from_orm(item) for item in items]
    
    return PaginatedResult(
        items=items,
        total=total,
        page=params.page,
        page_size=params.page_size,
    )


# Cursor-based pagination for very large datasets
class CursorPaginationParams:
    """
    Cursor-based pagination parameters for API endpoints
    """
    def __init__(
        self,
        cursor: Optional[str] = Query(None, description="Pagination cursor"),
        limit: int = Query(50, ge=1, le=500, description="Items per page"),
    ):
        self.cursor = cursor
        self.limit = limit
