from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import update, delete
from sqlalchemy.sql.expression import and_, or_
from sqlalchemy.orm import selectinload

from app.core.db.base import Base

# Define a generic type for models
ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Base repository class for database operations
    Provides common CRUD functionality for all repositories
    """
    
    def __init__(self, db: AsyncSession, model: Type[ModelType]):
        """
        Initialize the repository
        
        Args:
            db: AsyncSession instance
            model: SQLAlchemy model class
        """
        self.db = db
        self.model = model

    async def get(self, id: Any, options: Optional[List] = None) -> Optional[ModelType]:
        """
        Get a record by ID
        
        Args:
            id: Record ID
            options: Optional query options (e.g., selectinload)
            
        Returns:
            Model instance or None if not found
        """
        stmt = select(self.model).where(self.model.id == id)
        
        if options:
            for option in options:
                stmt = stmt.options(option)
                
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def list(self, options: Optional[List] = None, **filters) -> List[ModelType]:
        """
        List records with optional filters
        
        Args:
            options: Optional query options (e.g., selectinload)
            **filters: Equality filters
            
        Returns:
            List of model instances
        """
        stmt = select(self.model)
        
        # Apply filters
        for field, value in filters.items():
            if value is not None:
                stmt = stmt.where(getattr(self.model, field) == value)
                
        if options:
            for option in options:
                stmt = stmt.options(option)
                
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(self, obj_in: Union[Dict[str, Any], ModelType]) -> ModelType:
        """
        Create a new record
        
        Args:
            obj_in: Data to create record
            
        Returns:
            Created model instance
        """
        if isinstance(obj_in, dict):
            # Create from dict
            db_obj = self.model(**obj_in)
        else:
            # Create from model instance
            db_obj = obj_in
            
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def update(self, id: Any, **kwargs) -> Optional[ModelType]:
        """
        Update a record by ID
        
        Args:
            id: Record ID
            **kwargs: Fields to update
            
        Returns:
            Updated model instance or None if not found
        """
        # Check if record exists
        db_obj = await self.get(id)
        if not db_obj:
            return None
            
        # Prepare update statement
        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(**kwargs)
            .execution_options(synchronize_session="fetch")
        )
        
        # Execute update
        await self.db.execute(stmt)
        await self.db.commit()
        
        # Return updated object
        return await self.get(id)

    async def delete(self, id: Any) -> bool:
        """
        Delete a record by ID
        
        Args:
            id: Record ID
            
        Returns:
            Success flag
        """
        # Check if record exists
        db_obj = await self.get(id)
        if not db_obj:
            return False
            
        # Prepare delete statement
        stmt = (
            delete(self.model)
            .where(self.model.id == id)
            .execution_options(synchronize_session="fetch")
        )
        
        # Execute delete
        await self.db.execute(stmt)
        await self.db.commit()
        return True