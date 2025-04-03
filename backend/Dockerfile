FROM python:3.10-slim

WORKDIR /app

# Install Poetry
RUN pip install poetry==1.6.0

# Copy poetry configuration files
COPY pyproject.toml poetry.lock* /app/

# Configure poetry to not use a virtual environment
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-dev

# Copy the rest of the application
COPY . /app/

# Make sure the scripts are executable
RUN chmod +x /app/scripts/*.sh

# Create a user to run the application
RUN adduser --disabled-password --gecos "" appuser
USER appuser

# Expose the port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]