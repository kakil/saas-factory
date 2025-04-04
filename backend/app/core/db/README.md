# Multi-tenant Database Access

This module provides a comprehensive solution for multi-tenant database access in the SaaS Factory application. It implements secure tenant isolation at multiple levels while providing a flexible, developer-friendly API.

## Features

- **PostgreSQL Row-Level Security (RLS)**: Database-level security ensures data isolation between tenants
- **Tenant Context Middleware**: Automatically sets tenant context for all requests
- **Tenant-aware Repository Pattern**: Repository classes that enforce tenant isolation
- **Tenant Dependency Injection**: FastAPI dependencies for easy tenant context management
- **Flexible Tenant Resolution**: Extract tenant IDs from headers, user context, or explicit parameters

## Architecture

The multi-tenant implementation follows a layered approach:

1. **Database Layer (RLS Policies)**  
   PostgreSQL Row-Level Security policies filter data based on the `app.current_tenant` session variable.

2. **Middleware Layer**  
   `TenantMiddleware` automatically extracts tenant information and sets database session variables.

3. **Repository Layer**  
   `BaseRepository` enforces tenant isolation by applying tenant filters to all queries.

4. **API Layer**  
   FastAPI dependencies provide tenant context to route handlers.

## Usage

### Using Tenant-aware Repositories

```python
# Create a tenant-aware repository
from app.core.db.repository import BaseRepository
from app.features.users.models import User

class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    """User repository with tenant isolation"""
    pass

# Use the repository factory in dependencies
from app.core.dependencies import get_tenant_repository

# Create a dependency that provides a tenant-aware repository
get_user_repo = get_tenant_repository(lambda db: UserRepository(User, db))

# Use the dependency in an API endpoint
@router.get("/users/")
def list_users(
    repo: UserRepository = Depends(get_user_repo)
):
    """List users for current tenant"""
    return repo.get_multi()  # Automatically filtered by tenant
```

### Setting Tenant Context Explicitly

```python
from app.core.dependencies import set_tenant_context

@router.get("/custom-tenant-data/")
def get_custom_tenant_data(
    tenant_id: int = Depends(set_tenant_context)
):
    """Endpoint that requires tenant context"""
    # The tenant context is automatically set by the dependency
    return {"message": f"Data for tenant {tenant_id}"}
```

### Access Tenant Information

```python
from app.core.dependencies import get_tenant_info

@router.get("/tenant-info/")
def get_tenant_details(
    tenant_info: dict = Depends(get_tenant_info)
):
    """Get information about the current tenant"""
    return {
        "tenant_id": tenant_info["id"],
        "name": tenant_info["name"],
        "plan": tenant_info["plan_id"]
    }
```

## Design Considerations

### Security

The multi-tenant implementation ensures tenant isolation through multiple mechanisms:

1. **Database-level Security**: PostgreSQL RLS policies prevent unauthorized access to data
2. **Application-level Validation**: Repository methods validate tenant contexts
3. **Context Cleanup**: Tenant context is cleared between requests to prevent leakage

### Performance

1. **Caching**: Tenant information is cached to minimize database queries
2. **Efficient Filtering**: Database-level RLS is more efficient than application filtering
3. **Selective Application**: Tenant filtering can be disabled for specific repositories

### Flexibility

1. **Multiple Tenant Sources**: Tenant context can be extracted from headers, user state, or parameters
2. **Explicit Control**: Tenant context can be set explicitly when needed
3. **Repository Modes**: Repositories can operate in different modes based on requirements

## Testing

The multi-tenant implementation includes comprehensive unit tests that verify:

1. **Tenant Context Management**: Setting and clearing tenant context
2. **Repository Tenant Filtering**: Proper application of tenant filters
3. **Data Isolation**: Preventing cross-tenant data access
4. **Edge Cases**: Handling null contexts, invalid tenants, and superuser access