#!/bin/bash

# Setup script for n8n

# Set script to exit on error
set -e

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Setting up n8n for SaaS Factory..."

# Make sure the secrets directory exists
mkdir -p "$PROJECT_ROOT/secrets"

# Check if secrets are already created
if [ -f "$PROJECT_ROOT/secrets/n8n_api_key.txt" ]; then
  echo "n8n secrets already exist. Using existing secrets."
else
  echo "Creating n8n secrets..."
  
  # Generate random API key
  api_key=$(openssl rand -hex 16)
  echo "$api_key" > "$PROJECT_ROOT/secrets/n8n_api_key.txt"
  
  # Generate random encryption key
  encryption_key=$(openssl rand -hex 32)
  echo "$encryption_key" > "$PROJECT_ROOT/secrets/n8n_encryption_key.txt"
  
  # Create admin user credentials
  read -p "Enter n8n admin username [admin]: " username
  username=${username:-admin}
  echo "$username" > "$PROJECT_ROOT/secrets/n8n_user.txt"
  
  # For password, allow user to enter or generate a secure one
  read -p "Generate secure password? (y/n) [y]: " generate_pwd
  generate_pwd=${generate_pwd:-y}
  
  if [[ "$generate_pwd" == "y" ]]; then
    password=$(openssl rand -base64 12)
    echo "Generated password: $password"
  else
    read -s -p "Enter n8n admin password: " password
    echo
  fi
  
  echo "$password" > "$PROJECT_ROOT/secrets/n8n_password.txt"
  
  echo "Secrets created successfully."
fi

# Update the .env file with the API key
api_key=$(cat "$PROJECT_ROOT/secrets/n8n_api_key.txt")

# Check if .env file exists, create from sample if not
if [ ! -f "$PROJECT_ROOT/.env" ]; then
  if [ -f "$PROJECT_ROOT/.env.sample" ]; then
    cp "$PROJECT_ROOT/.env.sample" "$PROJECT_ROOT/.env"
    echo "Created .env file from sample."
  else
    echo "No .env.sample file found. Please create a .env file manually."
  fi
fi

# Update N8N_API_KEY in .env
if grep -q "N8N_API_KEY" "$PROJECT_ROOT/.env"; then
  # Replace existing key
  sed -i.bak "s/N8N_API_KEY=.*/N8N_API_KEY=$api_key/" "$PROJECT_ROOT/.env"
  rm "$PROJECT_ROOT/.env.bak" 2>/dev/null || true
else
  # Add key if not present
  echo "N8N_API_KEY=$api_key" >> "$PROJECT_ROOT/.env"
fi

echo "N8N_API_KEY updated in .env file."

echo ""
echo "n8n setup complete! You can now start the containers with:"
echo "cd $PROJECT_ROOT && docker-compose up -d"
echo ""
echo "Access n8n at http://localhost:5678"
echo "Username: $(cat "$PROJECT_ROOT/secrets/n8n_user.txt")"
echo "Password: $(cat "$PROJECT_ROOT/secrets/n8n_password.txt")"