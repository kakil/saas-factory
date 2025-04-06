# SaaS Factory - Backend Service Layer Foundation

This document provides an overview of the Backend Service Layer Foundation implemented in Step 1 of the SaaS Factory Blueprint application.

## Overview

The Backend Service Layer Foundation establishes core infrastructure components that support the entire application. It focuses on three main areas:

1. **Auth Service Layer** - Robust token validation and authentication system
2. **Multi-tenant Database Access** - Database isolation for multi-tenant applications
3. **Core API Improvements** - Standardized API patterns and error handling

## Architecture

The backend service layer follows a clean architecture pattern:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Controller │ --> │   Service   │ --> │ Repository  │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Middleware  │     │  Security   │     │   Models    │
└─────────────┘     └─────────────┘     └─────────────┘
```

- **Controllers**: API endpoints that handle HTTP requests
- **Services**: Business logic implementation
- **Repositories**: Data access layer for database operations
- **Middleware**: Request processing and cross-cutting concerns
- **Security**: Authentication and authorization
- **Models**: Database entity definitions

## Key Components

### 1. Auth Service Layer

The authentication system provides a flexible approach to validating user identity through different token types:

- JWT token validation and creation
- Supabase Auth integration
- Provider-agnostic authentication interface

#### Auth Provider Architecture:

```python
class BaseAuthProvider(ABC):
    @abstractmethod
    async def validate_token(self, token: str) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def get_user_info(self, token: str) -> Dict[str, Any]:
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass
```

Concrete implementations include:
- `JWTAuthProvider`: For custom JWT tokens
- `SupabaseAuthProvider`: For Supabase authentication

#### Usage Example:

```python
# Validate a token using the appropriate provider
token_payload = await auth_service.validate_token(token, provider_hint="jwt")

# Get user information from token
user_info = await auth_service.get_user_info(token)
```

### 2. Multi-tenant Database Access

The multi-tenancy system ensures data isolation between different organizations (tenants):

- Tenant context middleware for request processing
- Row-level security policies in the database
- Repository-based query filtering

#### Tenant Context Management:

The system uses a request-scoped context to track the current tenant:

```python
# Middleware extracts tenant ID from token
tenant_id = extract_tenant_from_token(token)
request.state.tenant_id = tenant_id

# Repositories apply tenant filtering
class BaseRepository:
    def apply_tenant_filter(self, query):
        return query.filter(self.model.tenant_id == get_current_tenant_id())
```

#### Database Session Middleware:

```python
@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    request.state.db = SessionLocal()
    try:
        response = await call_next(request)
        return response
    finally:
        request.state.db.close()
```

### 3. Core API Improvements

Standardized API patterns ensure consistency across all endpoints:

- Unified response format
- Comprehensive error handling
- Pagination support for list endpoints

#### Standard Response Format:

```python
@router.get("/items/", response_model=PaginatedResponse[Item])
async def list_items(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    items = item_repository.list(skip=skip, limit=limit)
    total = item_repository.count()
    
    return PaginatedResponse(
        data=items,
        pagination=PaginationInfo(
            skip=skip,
            limit=limit,
            total=total
        )
    )
```

#### Error Handling:

```python
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": "Validation error", "details": exc.errors()}
    )
```

## API Endpoints

The core API structure includes:

- `/auth/*` - Authentication endpoints
- `/users/*` - User management
- `/organizations/*` - Organization/tenant management
- `/health` - Health check endpoint
- API versioning with `/api/v1` prefix

## Data Models

### User

Core user model with authentication information:

```python
class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    supabase_uid: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organizations: Mapped[List["Organization"]] = relationship(
        "Organization", secondary="user_organization"
    )
```

### Organization (Tenant)

Represents a tenant in the multi-tenant system:

```python
class Organization(Base):
    __tablename__ = "organizations"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    plan_id: Mapped[str] = mapped_column(String(50), default="free")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users: Mapped[List["User"]] = relationship(
        "User", secondary="user_organization", back_populates="organizations"
    )
```

## Setup and Configuration

Key environment variables for the backend service layer:

```
# Authentication settings
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Database settings
DATABASE_URL=postgresql://user:password@localhost:5432/saas_factory

# Supabase settings
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-key
```

## Testing

The backend service layer includes a comprehensive testing strategy:

1. **Unit Tests** - Test individual service and repository methods
2. **Integration Tests** - Test API endpoints with database interaction
3. **Authentication Tests** - Validate token handling with mock providers

Run tests with:

```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit
pytest -m integration
pytest -m auth
```

## Common Operations

### Authenticating a User

```python
from app.core.security.jwt import create_access_token
from app.features.users.service import UserService

# Authenticate user
user = await user_service.authenticate_user(email="user@example.com", password="password123")

# Create access token
access_token = create_access_token(
    subject=user.email,
    extra_data={"user_id": user.id, "is_superuser": user.is_superuser}
)

# Return token to client
return {"access_token": access_token, "token_type": "bearer"}
```

### Adding Multi-tenant Filtering

```python
class ItemRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(db, Item)
    
    def list_by_tenant(self, tenant_id: int, skip: int = 0, limit: int = 100):
        query = self.db.query(self.model).filter(self.model.tenant_id == tenant_id)
        return query.offset(skip).limit(limit).all()
    
    # Base repository handles tenant filtering automatically
    def list_all(self, skip: int = 0, limit: int = 100):
        query = self.db.query(self.model)
        query = self.apply_tenant_filter(query)
        return query.offset(skip).limit(limit).all()
```

### Creating a Standardized API Response

```python
from app.core.api.responses import DataResponse

@router.get("/items/{item_id}", response_model=DataResponse[ItemSchema])
async def get_item(item_id: int, db: Session = Depends(get_db)):
    item = item_repository.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return DataResponse(data=item)
```

## Troubleshooting

### Common Issues

1. **Authentication Failures**
   - Check that the token is properly formatted and not expired
   - Verify the SECRET_KEY environment variable matches the key used to create tokens
   - Check for proper Authorization header format (Bearer token)

2. **Multi-tenant Data Leakage**
   - Ensure all repositories use the apply_tenant_filter method
   - Verify tenant_id is correctly extracted from authentication tokens
   - Check database RLS policies are applied correctly

3. **API Response Format Inconsistencies**
   - Use the standard response models (DataResponse, PaginatedResponse)
   - Ensure all endpoints use proper response_model type annotations
   - Register global exception handlers for consistent error responses

### Debugging Tips

Enable debug logging for authentication issues:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("app.core.security")
```

Manually check tenant context in middleware:
```python
@app.middleware("http")
async def debug_tenant_middleware(request: Request, call_next):
    print(f"Current Tenant ID: {request.state.tenant_id}")
    response = await call_next(request)
    return response
```

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [JWT Authentication](https://jwt.io/)
- [Supabase Authentication](https://supabase.io/docs/guides/auth)
- [PostgreSQL Row-Level Security](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)