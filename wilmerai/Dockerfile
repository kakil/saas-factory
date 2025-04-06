FROM python:3.10-slim

LABEL maintainer="SaaS Factory <support@saas-factory.com>"
LABEL description="WilmerAI integration for SaaS Factory Blueprint"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Clone WilmerAI repository
RUN git clone https://github.com/SomeOddCodeGuy/WilmerAI.git .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create directory structure
RUN mkdir -p \
    logs \
    Public/Configs \
    Public/Configs/Users \
    Public/Configs/workflows \
    Public/Configs/Routing \
    Public/KnowledgeBases

# Copy custom configuration files
COPY ./config/wilmer.ini Public/Configs/
COPY ./config/categories_config.json Public/Configs/
COPY ./config/Users/*.json Public/Configs/Users/
COPY ./config/workflows/*.json Public/Configs/workflows/
COPY ./config/Routing/*.json Public/Configs/Routing/

# Expose the port
EXPOSE 8765

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    WILMER_USER=default \
    WILMER_API_URL=http://0.0.0.0:8765

# Setup health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8765/health || exit 1

# Run the application
CMD ["python", "server.py"]