#!/bin/bash
set -e

# Navigate to the backend directory
cd "$(dirname "$0")/.."

# Check if alembic is installed
if ! command -v alembic &> /dev/null; then
    echo "Error: alembic is not installed. Please run 'pip install alembic' or use Poetry to install dependencies."
    exit 1
fi

# Check if the versions directory exists
if [ ! -d "alembic/versions" ]; then
    mkdir -p alembic/versions
    echo "Created alembic/versions directory"
fi

# If no arguments are provided, run migration upgrade
if [ $# -eq 0 ]; then
    echo "Running database migrations..."
    alembic upgrade head
    echo "Migrations complete!"
    exit 0
fi

# Handle different commands
case "$1" in
    upgrade)
        shift
        echo "Running upgrade migrations..."
        alembic upgrade "${1:-head}"
        ;;
    downgrade)
        shift
        echo "Running downgrade migrations..."
        alembic downgrade "${1:-base}"
        ;;
    revision)
        shift
        echo "Creating new migration revision..."
        alembic revision --autogenerate -m "${1:-new_migration}"
        ;;
    current)
        echo "Current migration version:"
        alembic current
        ;;
    history)
        echo "Migration history:"
        alembic history
        ;;
    *)
        echo "Unknown command: $1"
        echo "Usage: $0 [upgrade|downgrade|revision|current|history] [arguments]"
        exit 1
        ;;
esac

echo "Operation complete!"