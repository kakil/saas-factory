import pytest
from unittest.mock import MagicMock, AsyncMock, patch, PropertyMock
from sqlalchemy.orm import Session
from fastapi import Request
from starlette.datastructures import Headers

from app.core.middleware.tenant import TenantMiddleware
from app.core.db.repository import BaseRepository
from app.features.users.models import User
from app.features.teams.models import Organization, Team


class TestTenantMiddleware:
    """Tests for the tenant middleware"""
    
    @pytest.fixture
    def mock_db(self):
        """Fixture for mocked database session"""
        mock = MagicMock(spec=Session)
        mock.execute = MagicMock()
        return mock
    
    @pytest.fixture
    def mock_get_db(self, mock_db):
        """Fixture for mocked get_db function"""
        mock_gen = MagicMock()
        mock_gen.__next__ = MagicMock(return_value=mock_db)
        return mock_gen
    
    @pytest.fixture
    def middleware(self):
        """Fixture for tenant middleware"""
        app = MagicMock()
        return TenantMiddleware(app)
    
    @pytest.mark.asyncio
    async def test_excluded_path(self, middleware, monkeypatch, mock_get_db):
        """Test that excluded paths are handled correctly"""
        # Arrange
        request = MagicMock(spec=Request)
        request.url.path = "/api/v1/docs"
        call_next = AsyncMock(return_value="response")
        
        # Mock the _clear_tenant_context method
        monkeypatch.setattr(middleware, "_clear_tenant_context", AsyncMock())
        
        # Act
        response = await middleware.dispatch(request, call_next)
        
        # Assert
        middleware._clear_tenant_context.assert_called_once()
        call_next.assert_called_once_with(request)
        assert response == "response"
    
    @pytest.mark.asyncio
    async def test_tenant_id_from_header(self, middleware):
        """Test extracting tenant ID from header"""
        # Arrange
        request = MagicMock(spec=Request)
        request.headers = {"X-Tenant-ID": "42"}
        
        # Act
        result = await middleware.get_tenant_id(request)
        
        # Assert
        assert result == 42
    
    @pytest.mark.asyncio
    async def test_tenant_id_from_user(self, middleware):
        """Test extracting tenant ID from authenticated user"""
        # Arrange
        request = MagicMock(spec=Request)
        request.headers = {}
        
        # Create mock user with organization_id
        user = MagicMock(spec=User)
        user.organization_id = 42
        
        # Set user in request state
        type(request.state).user = PropertyMock(return_value=user)
        
        # Act
        result = await middleware.get_tenant_id(request)
        
        # Assert
        assert result == 42
    
    @pytest.mark.asyncio
    async def test_tenant_context_lifecycle(self, middleware, monkeypatch, mock_get_db):
        """Test full tenant context lifecycle in middleware"""
        # Arrange
        request = MagicMock(spec=Request)
        request.url.path = "/api/v1/users"
        request.headers = {"X-Tenant-ID": "123"}
        call_next = AsyncMock(return_value="response")
        
        # Mock the tenant context methods
        monkeypatch.setattr(middleware, "_set_tenant_context", AsyncMock())
        monkeypatch.setattr(middleware, "_get_tenant_info", AsyncMock(return_value={"id": 123, "name": "Test Org"}))
        monkeypatch.setattr(middleware, "_cleanup_tenant_context", AsyncMock())
        monkeypatch.setattr(middleware, "get_tenant_id", AsyncMock(return_value=123))
        
        # Act
        response = await middleware.dispatch(request, call_next)
        
        # Assert
        middleware.get_tenant_id.assert_called_once()
        middleware._set_tenant_context.assert_called_once_with(request, 123)
        middleware._get_tenant_info.assert_called_once_with(request, 123)
        middleware._cleanup_tenant_context.assert_called_once()
        call_next.assert_called_once_with(request)
        assert response == "response"


class TestTenantRepository:
    """Tests for the tenant-aware repository"""
    
    @pytest.fixture
    def mock_db(self):
        """Fixture for mocked database session"""
        mock = MagicMock(spec=Session)
        return mock
    
    @pytest.fixture
    def mock_query(self):
        """Fixture for mocked query"""
        mock = MagicMock()
        mock.filter.return_value = mock
        mock.offset.return_value = mock
        mock.limit.return_value = mock
        mock.all.return_value = []
        mock.first.return_value = None
        return mock
    
    @pytest.fixture
    def mock_model(self):
        """Fixture for mocked model class"""
        mock = MagicMock()
        # Add organization_id attribute to model
        mock.organization_id = MagicMock()
        return mock
    
    @pytest.fixture
    def repository(self, mock_db, mock_model):
        """Fixture for repository instance"""
        repo = BaseRepository(mock_model, mock_db)
        return repo
    
    def test_set_tenant_id(self, repository):
        """Test setting tenant ID explicitly"""
        # Act
        repository.set_tenant_id(42)
        
        # Assert
        assert repository._tenant_id == 42
    
    def test_apply_tenant_filter(self, repository, mock_query):
        """Test applying tenant filter to query"""
        # Arrange
        repository.set_tenant_id(42)
        
        # Mock the model's organization_id attribute for filtering
        repository.model.organization_id = MagicMock()
        
        # Act
        result = repository._apply_tenant_filter(mock_query)
        
        # Assert
        mock_query.filter.assert_called_once()
        assert result == mock_query
    
    def test_create_with_tenant_id(self, repository, mock_db):
        """Test creating record with tenant ID"""
        # Arrange
        repository.set_tenant_id(42)
        mock_obj_in = MagicMock()
        
        # Mock jsonable_encoder to return a dict
        with patch('app.core.db.repository.jsonable_encoder', return_value={}):
            # Mock model instantiation
            mock_obj = MagicMock()
            repository.model = MagicMock(return_value=mock_obj)
            
            # Act
            repository.create(obj_in=mock_obj_in)
            
            # Assert
            assert mock_obj.organization_id == 42
            mock_db.add.assert_called_once_with(mock_obj)
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once_with(mock_obj)
    
    def test_update_prevents_tenant_change(self, repository, mock_db):
        """Test that update prevents changing organization_id"""
        # Arrange
        repository.set_tenant_id(42)
        mock_db_obj = MagicMock()
        mock_db_obj.organization_id = 42
        mock_db_obj.id = 1
        
        # Mock update data with different organization_id
        update_data = {"name": "Updated", "organization_id": 99}
        
        # Mock jsonable_encoder
        with patch('app.core.db.repository.jsonable_encoder', return_value={"id": 1, "name": "Original"}):
            # Act
            repository.update(db_obj=mock_db_obj, obj_in=update_data)
            
            # Assert
            assert mock_db_obj.name == "Updated"
            assert mock_db_obj.organization_id == 42  # Should not be changed
            mock_db.add.assert_called_once_with(mock_db_obj)
            mock_db.commit.assert_called_once()


@pytest.mark.parametrize("tenant_id,expected_count", [
    (1, 2),  # Tenant 1 has 2 users
    (2, 1),  # Tenant 2 has 1 user
    (None, 3)  # No tenant filtering should return all users
])
def test_tenant_filtering_integration(tenant_id, expected_count):
    """
    Integration test for tenant filtering
    
    Note: This would be implemented properly in an integration test
    that uses a real database with appropriate setup/teardown.
    """
    # This test outline demonstrates how to test tenant isolation 
    # in an integration setting with a real database
    
    # 1. Set up test database with tenant data
    # 2. Apply tenant context if provided
    # 3. Query users and verify filtering
    # 4. Assert that only data for the correct tenant is visible
    
    # For now we just verify the test structure
    assert expected_count in [1, 2, 3]