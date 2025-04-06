#!/bin/bash
# Script to test WilmerAI Docker configuration

set -e  # Exit on any error

echo "=== Testing WilmerAI Docker Configuration ==="

# Step 1: Create directories for configs if needed
echo "Setting up directory structure..."
mkdir -p ./secrets
mkdir -p ./wilmerai/logs

# Note: WilmerAI doesn't require an API key for itself
# The wilmer_api_key.txt is only used if you want to secure the API server
# and is completely optional

# Step 2: Create .env file if it doesn't exist
echo "Setting up environment variables..."
if [ ! -f ./.env ]; then
    cp .env.example .env
    echo "Created .env from example template"
    # Add test values for required API keys
    echo "GOOGLE_API_KEY=test-google-api-key" >> ./.env
    echo "OPENAI_API_KEY=test-openai-api-key" >> ./.env
    echo "ANTHROPIC_API_KEY=test-anthropic-api-key" >> ./.env
    echo "DEEPSEEK_API_KEY=test-deepseek-api-key" >> ./.env
    echo "Added test API key values to .env"
fi

# Step 3: Build and start just the WilmerAI service with Redis
echo "Building WilmerAI and Redis containers..."
docker-compose up --build -d redis wilmerai

# Step 4: Wait for containers to be healthy
echo "Waiting for containers to be ready..."
sleep 10

# Step 5: Check if containers are running
echo "Checking container status..."
docker-compose ps

# Step 6: Check WilmerAI container logs
echo -e "\nChecking WilmerAI logs..."
docker-compose logs wilmerai | tail -n 20

# Step 7: Test connectivity to WilmerAI
echo -e "\nTesting connectivity to WilmerAI..."
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost:8765/health || {
    echo "Failed to connect to WilmerAI on port 8765"
    echo "Checking for startup errors..."
    docker-compose logs wilmerai
    exit 1
}

# Step 8: Send a test request to WilmerAI API
echo -e "\nSending test request to WilmerAI API..."
curl -s -X POST \
  http://localhost:8765/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemini-pro",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Hello, is the WilmerAI container working?"}
    ]
  }' | jq 2>/dev/null || {
    # If jq fails (which it will if the API returns an error), print the raw response
    echo "Getting API response without JSON formatting..."
    curl -s -X POST \
      http://localhost:8765/v1/chat/completions \
      -H "Content-Type: application/json" \
      -d '{
        "model": "gemini-pro",
        "messages": [
          {"role": "system", "content": "You are a helpful assistant."},
          {"role": "user", "content": "Hello, is the WilmerAI container working?"}
        ]
      }' || echo "Error: Failed to get any response"
  }

# The above test will likely return an error about missing API keys
# This is expected without real API keys and confirms that the container is working
echo -e "\nNote: If you see an error about missing API keys, that's expected without real API keys configured."
echo "The important part is that the WilmerAI API server is running and responding to requests."

# Step 9: Clean up
echo -e "\nTest complete. Stopping containers..."
docker-compose stop wilmerai redis

echo -e "\nWilmerAI Docker configuration test complete!"