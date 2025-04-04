from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union, cast
import logging
from functools import wraps

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import inspect, Column, text

from app.core.db.base import Base

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


def with_tenant_context(method):
    """
    Decorator to ensure tenant context is properly applied to repository methods
    
    This decorator checks if a tenant_id is provided in kwargs or if the model
    has an organization_id field, and applies tenant filtering if appropriate.
    """
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self.tenant_aware:
            # Skip tenant context if repository is not tenant aware
            return method(self, *args, **kwargs)
            
        # Extract tenant_id from kwargs if provided
        tenant_id = kwargs.pop("tenant_id", None)
        
        # Use current tenant from database context if not provided
        if tenant_id is None and self.use_tenant_context:
            try:
                # Get current tenant from database context
                result = self.db.execute(text("SELECT app.current_tenant_id()"))
                tenant_id = result.scalar()
            except SQLAlchemyError as e:
                logger.warning(f"Error getting tenant context: {str(e)}")
        
        # Call original method with tenant_id in appropriate context
        if hasattr(self.model, "organization_id") and tenant_id is not None:
            # Store original tenant_id for reference
            original_tenant_id = getattr(self, "_tenant_id", None)
            self._tenant_id = tenant_id
            
            try:
                # Execute method with tenant context
                return method(self, *args, **kwargs)
            finally:
                # Restore original tenant_id
                self._tenant_id = original_tenant_id
        else:
            # No tenant context to apply
            return method(self, *args, **kwargs)
            
    return wrapper


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base class for repositories with CRUD operations and tenant support
    
    This repository class provides multi-tenant aware database operations by:
    1. Leveraging PostgreSQL RLS policies via app.current_tenant session variable
    2. Optionally filtering by organization_id for tenant isolation
    3. Caching tenant context and applying it consistently for repository operations
    
    The repository can work in three modes:
    - Tenant aware with automatic filtering (tenant_aware=True, use_tenant_context=False)
    - Tenant aware using database context (tenant_aware=True, use_tenant_context=True)
    - Tenant agnostic (tenant_aware=False)
    """
    def __init__(self, model: Type[ModelType], db: Session, tenant_aware: bool = True, use_tenant_context: bool = True):
        self.model = model
        self.db = db
        self.tenant_aware = tenant_aware
        self.use_tenant_context = use_tenant_context
        self._tenant_id = None
        
        # Check if model has organization_id
        self._has_org_id = hasattr(model, "organization_id")
    
    def _apply_tenant_filter(self, query: Query) -> Query:
        """Apply tenant filtering to query if appropriate"""
        if not self.tenant_aware or not self._has_org_id:
            return query
            
        tenant_id = getattr(self, "_tenant_id", None)
        if tenant_id is not None:
            # Apply explicit tenant filter
            org_column = getattr(self.model, "organization_id")
            return query.filter(org_column == tenant_id)
            
        # Let database RLS handle filtering if we're in tenant-context mode
        return query

    @with_tenant_context
    def get(self, id: Any) -> Optional[ModelType]:
        """
        Get a record by ID with tenant isolation
        """
        query = self.db.query(self.model).filter(self.model.id == id)
        query = self._apply_tenant_filter(query)
        return query.first()

    @with_tenant_context
    def get_by(self, **kwargs) -> Optional[ModelType]:
        """
        Get a record by arbitrary filters with tenant isolation
        """
        query = self.db.query(self.model)
        for key, value in kwargs.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)
                
        query = self._apply_tenant_filter(query)
        return query.first()

    @with_tenant_context
    def get_multi(
        self, *, skip: int = 0, limit: int = 100, **kwargs
    ) -> List[ModelType]:
        """
        Get multiple records with optional filtering and tenant isolation
        """
        query = self.db.query(self.model)
        for key, value in kwargs.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)
                
        query = self._apply_tenant_filter(query)
        return query.offset(skip).limit(limit).all()

    @with_tenant_context
    def create(self, *, obj_in: CreateSchemaType) -> ModelType:
        """
        Create a new record with tenant context if applicable
        """
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        
        # Apply tenant ID if tenant-aware and model has organization_id
        if self.tenant_aware and self._has_org_id:
            tenant_id = getattr(self, "_tenant_id", None)
            if tenant_id and not getattr(db_obj, "organization_id", None):
                setattr(db_obj, "organization_id", tenant_id)
        
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    @with_tenant_context
    def update(
        self,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        Update a record with tenant validation
        
        Ensures that updates maintain tenant integrity by:
        1. Validating that db_obj belongs to current tenant
        2. Preventing changes to organization_id if tenant-aware
        """
        # Validate tenant access if tenant-aware
        if self.tenant_aware and self._has_org_id:
            tenant_id = getattr(self, "_tenant_id", None)
            obj_tenant_id = getattr(db_obj, "organization_id", None)
            
            # Skip tenant validation if no tenant context is set
            if tenant_id is not None and obj_tenant_id is not None:
                # Validate tenant access
                if obj_tenant_id != tenant_id:
                    logger.warning(f"Attempt to update object from different tenant: {db_obj.id}")
                    return None
        
        # Perform update
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
            
        # Prevent changing organization_id if tenant-aware
        if self.tenant_aware and self._has_org_id and "organization_id" in update_data:
            tenant_id = getattr(self, "_tenant_id", None)
            if tenant_id is not None and update_data["organization_id"] != tenant_id:
                # Remove or reset organization_id to maintain tenant integrity
                update_data["organization_id"] = tenant_id
                logger.warning(f"Attempt to change organization_id prevented for object: {db_obj.id}")
        
        # Apply updates
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
                
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    @with_tenant_context
    def delete(self, *, id: int) -> Optional[ModelType]:
        """
        Delete a record with tenant validation
        """
        query = self.db.query(self.model).filter(self.model.id == id)
        query = self._apply_tenant_filter(query)
        obj = query.first()
        
        if obj:
            self.db.delete(obj)
            self.db.commit()
            
        return obj

    @with_tenant_context
    def count(self, **kwargs) -> int:
        """
        Count records with optional filtering and tenant isolation
        """
        query = self.db.query(self.model)
        for key, value in kwargs.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)
                
        query = self._apply_tenant_filter(query)
        return query.count()
        
    def set_tenant_id(self, tenant_id: int) -> None:
        """
        Explicitly set tenant ID for repository operations
        
        This allows overriding the default tenant context for specific operations.
        """
        self._tenant_id = tenant_id