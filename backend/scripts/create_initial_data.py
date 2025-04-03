import asyncio
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.core.config.settings import settings
from app.core.db.base import Base
from app.features.users.models import User
from app.features.teams.models import Organization, Team, user_team

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create async engine and session
async_engine = create_async_engine(
    str(settings.SQLALCHEMY_DATABASE_URI).replace("postgresql://", "postgresql+asyncpg://"),
    echo=True,
)
async_session = sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)


async def create_initial_data():
    """Create initial data for the application."""
    logger.info("Creating initial data")

    # Creating admin user
    async with async_session() as session:
        # Check if admin user already exists
        result = await session.execute(select(User).filter_by(email="admin@example.com"))
        admin_user = result.scalars().first()

        if not admin_user:
            logger.info("Creating admin user")
            admin_user = User(
                email="admin@example.com",
                name="Admin User",
                is_active=True,
                is_superuser=True,
            )
            admin_user.set_password("admin")
            session.add(admin_user)
            await session.commit()
            logger.info(f"Admin user created with ID: {admin_user.id}")
        else:
            logger.info("Admin user already exists")

        # Create default organization
        result = await session.execute(select(Organization).filter_by(name="Default Organization"))
        default_org = result.scalars().first()

        if not default_org:
            logger.info("Creating default organization")
            default_org = Organization(
                name="Default Organization",
                plan_id="free",
            )
            session.add(default_org)
            await session.commit()
            logger.info(f"Default organization created with ID: {default_org.id}")
        else:
            logger.info("Default organization already exists")

        # Create test user
        result = await session.execute(select(User).filter_by(email="user@example.com"))
        test_user = result.scalars().first()

        if not test_user:
            logger.info("Creating test user")
            test_user = User(
                email="user@example.com",
                name="Test User",
                is_active=True,
                is_superuser=False,
                organization_id=default_org.id,
            )
            test_user.set_password("password")
            session.add(test_user)
            await session.commit()
            logger.info(f"Test user created with ID: {test_user.id}")
        else:
            logger.info("Test user already exists")

        # Create test team
        result = await session.execute(select(Team).filter_by(name="Test Team"))
        test_team = result.scalars().first()

        if not test_team:
            logger.info("Creating test team")
            test_team = Team(
                name="Test Team",
                description="A team for testing",
                organization_id=default_org.id,
            )
            session.add(test_team)
            await session.commit()
            logger.info(f"Test team created with ID: {test_team.id}")

            # Add test user to test team
            stmt = user_team.insert().values(user_id=test_user.id, team_id=test_team.id)
            await session.execute(stmt)
            await session.commit()
            logger.info(f"Added user {test_user.id} to team {test_team.id}")
        else:
            logger.info("Test team already exists")

    logger.info("Initial data creation completed successfully")


if __name__ == "__main__":
    asyncio.run(create_initial_data())