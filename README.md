# SaaS Factory Blueprint

A comprehensive framework for rapidly deploying fully-functional SaaS products using Python-first architecture and modern frontend technologies.

## Architecture Overview

The SaaS Factory Blueprint implements a Python-first architecture with vertical slice organization, enabling rapid development and deployment of customizable SaaS applications. The architecture includes:

- **Backend**: FastAPI with PostgreSQL database, implementing vertical slice architecture
- **Frontend**: Next.js with React and modern frontend libraries
- **Authentication**: JWT-based authentication with Supabase Auth
- **Multi-Tenancy**: Support for multiple organizations with data isolation
- **WilmerAI Integration**: AI capabilities with intelligent orchestration
- **Workflow Automation**: n8n workflows for business process automation
- **Containerization**: Docker and Docker Compose for consistent deployment

## Project Structure

```
saas-factory/
├── backend/                # Python/FastAPI backend
│   ├── app/
│   │   ├── features/       # Feature-based organization
│   │   │   ├── auth/       # Authentication feature slice
│   │   │   ├── users/      # User management feature slice
│   │   │   ├── teams/      # Team management feature slice
│   │   │   ├── dashboard/  # Dashboard data feature slice
│   │   │   └── ai/         # AI services feature slice
│   │   ├── core/           # Shared core functionality
│   │   └── main.py         # Application entry point
│   ├── tests/              # Test directory
│   ├── alembic/            # Database migrations
│   └── Dockerfile          # Backend Docker configuration
├── frontend/               # Next.js frontend
│   ├── src/
│   │   ├── features/       # Feature-based organization
│   │   ├── components/     # Shared UI components
│   │   ├── hooks/          # Shared custom hooks
│   │   ├── utils/          # Shared utility functions
│   │   └── pages/          # Next.js pages
│   └── Dockerfile          # Frontend Docker configuration
├── docker-compose.yml      # Multi-container setup
└── .env.sample             # Sample environment variables
```

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.10+
- Node.js 18+
- Poetry (for Python dependency management)
- pnpm (for Node.js dependency management)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/saas-factory.git
   cd saas-factory
   ```

2. Initialize the project:
   ```bash
   chmod +x backend/scripts/init.sh
   ./backend/scripts/init.sh
   ```

3. Set up environment variables:
   ```bash
   cp .env.sample .env
   # Edit .env with your configuration values
   ```

4. Build and start the containers:
   ```bash
   docker-compose up --build
   ```

5. Run database migrations:
   ```bash
   docker-compose exec backend bash -c "cd /app && alembic upgrade head"
   ```

6. Create initial data:
   ```bash
   docker-compose exec backend python -m scripts.create_initial_data
   ```

7. Access the application:
   - Backend API: http://localhost:8000/api/v1/docs
   - Frontend: http://localhost:3000

## Development

### Backend Development

```bash
# Enter the backend directory
cd backend

# Install dependencies with Poetry
poetry install

# Run the development server
poetry run uvicorn app.main:app --reload
```

### Database Migrations

```bash
# Generate a new migration
chmod +x backend/scripts/run-migrations.sh
./backend/scripts/run-migrations.sh revision "migration_name"

# Apply migrations
./backend/scripts/run-migrations.sh upgrade
```

### Frontend Development

```bash
# Enter the frontend directory
cd frontend

# Install dependencies with pnpm
pnpm install

# Run the development server
pnpm dev
```

## Testing

```bash
# Run backend tests
cd backend
poetry run pytest

# Run frontend tests
cd frontend
pnpm test
```

## Deployment

The project is containerized using Docker, making it easy to deploy to various hosting providers:

1. Build the Docker images:
   ```bash
   docker-compose build
   ```

2. Push the images to a container registry (optional):
   ```bash
   docker-compose push
   ```

3. Deploy to your preferred hosting provider, such as:
   - Contabo VPS
   - Digital Ocean
   - AWS
   - Google Cloud
   - Heroku

## Features

- **Authentication**: JWT-based authentication with Supabase Auth
- **User Management**: CRUD operations for user accounts
- **Organization Management**: Multi-tenant support with organizations and teams
- **AI Integration**: WilmerAI for intelligent orchestration of AI capabilities
- **Workflow Automation**: n8n workflows for business process automation
- **Dashboard**: Ready-to-use dashboard components with glass morphism design
- **API Security**: RBAC with granular permissions
- **Database Migrations**: Alembic migrations for version control

## Context Priming
Read README.md, CLAUDE.md, saas-factory/*, and run git ls-files to understand this codebase

## License

This project is licensed under the MIT License - see the LICENSE file for details.