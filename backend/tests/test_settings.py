from typing import Dict, Any
import os

from app.core.config.settings import Settings

# Test configurations to override the default settings
class TestSettings(Settings):
    # Use a test database
    POSTGRES_DB: str = "saas_factory_test_db"
    
    # Override with test values
    SECRET_KEY: str = "test_secret_key"
    
    # For tests, we don't need real Supabase
    SUPABASE_URL: str = "https://test.supabase.co"
    SUPABASE_KEY: str = "test_key"
    
    # Disable emails in tests
    SMTP_TLS: bool = False
    
    # Override model_config to use test.env file if available
    model_config = {
        "env_file": ".test.env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


# Create test settings instance
test_settings = TestSettings()