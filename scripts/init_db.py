import os
import sys
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")


def init_db(db_url):
    """Initialize database if it doesn't exist"""
    engine = create_engine(db_url)

    if not database_exists(engine.url):
        create_database(engine.url)
        print(f"Created database at {engine.url}")
    else:
        print(f"Database already exists at {engine.url}")


if __name__ == "__main__":
    # Initialize main database
    init_db(DATABASE_URL)

    # Initialize test database
    init_db(TEST_DATABASE_URL)