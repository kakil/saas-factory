#!/bin/bash

# Script to import workflow templates into n8n

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Get project root directory
PROJECT_ROOT="$(dirname "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)")"

# Check if API key is in env or read from secrets
if [ -z "$N8N_API_KEY" ]; then
    if [ -f "$PROJECT_ROOT/secrets/n8n_api_key.txt" ]; then
        export N8N_API_KEY=$(cat "$PROJECT_ROOT/secrets/n8n_api_key.txt")
    else
        echo "Error: N8N_API_KEY environment variable not set and no secret found."
        echo "Please run scripts/setup_n8n.sh first or source .env file: source .env"
        exit 1
    fi
fi

# Set API URL if not already set
if [ -z "$N8N_API_URL" ]; then
    export N8N_API_URL="http://localhost:5678/api/v1"
fi

# Make sure n8n is running
echo "Checking if n8n is running..."
curl -s -o /dev/null -w "%{http_code}" "http://localhost:5678" | grep 200 > /dev/null
if [ $? -ne 0 ]; then
    echo "Error: n8n is not running or not accessible at http://localhost:5678"
    echo "Make sure n8n container is running: docker-compose up -d n8n"
    echo "Wait a few seconds for n8n to start up completely."
    exit 1
fi

# Function to import a workflow
import_workflow() {
    local workflow_file=$1
    local workflow_name=$(basename $workflow_file .json)
    
    echo "Importing workflow: $workflow_name"
    response=$(curl -s -X POST \
        "$N8N_API_URL/workflows" \
        -H "X-N8N-API-KEY: $N8N_API_KEY" \
        -H "Content-Type: application/json" \
        -d @$workflow_file)
    
    # Check if import was successful
    echo $response | grep -q "id"
    if [ $? -eq 0 ]; then
        workflow_id=$(echo $response | grep -o '"id":"[^"]*"' | cut -d':' -f2 | tr -d '"')
        echo "Successfully imported workflow: $workflow_name (ID: $workflow_id)"
    else
        echo "Failed to import workflow: $workflow_name"
        echo "Response: $response"
    fi
}

# Import all workflow templates
echo "Importing workflow templates..."

# Import onboarding workflow
if [ -f "$SCRIPT_DIR/onboarding.json" ]; then
    import_workflow "$SCRIPT_DIR/onboarding.json"
else
    echo "Warning: onboarding.json not found in $SCRIPT_DIR"
fi

# Import notifications workflow
if [ -f "$SCRIPT_DIR/notifications.json" ]; then
    import_workflow "$SCRIPT_DIR/notifications.json"
else
    echo "Warning: notifications.json not found in $SCRIPT_DIR"
fi

# Import billing workflow
if [ -f "$SCRIPT_DIR/billing.json" ]; then
    import_workflow "$SCRIPT_DIR/billing.json"
else
    echo "Warning: billing.json not found in $SCRIPT_DIR"
fi

echo "Workflow import completed."
echo "You can now access n8n at http://localhost:5678 to view and edit the workflows."