# n8n Integration for SaaS Factory

This directory contains configuration and workflow templates for n8n, the workflow automation platform used in the SaaS Factory Blueprint.

## Overview

n8n is used for automating various processes within the SaaS Factory Blueprint:

1. **Customer Onboarding Automation**
   - User registration workflows
   - Email verification
   - Welcome sequences

2. **Notification System**
   - Event-based notifications
   - Email templates for system events

3. **Billing Workflows**
   - Subscription management
   - Invoice generation
   - Payment notifications

## Configuration

The n8n instance is configured in the main `docker-compose.yml` file with the following settings:

- **Port**: 5678 (accessible at http://localhost:5678 when running locally)
- **Authentication**: Basic auth (credentials in .env file)
- **Data Persistence**: Docker volume `n8n_data`
- **Dependencies**: Redis for queueing and caching

## API Access

To access the n8n API from your backend:

1. Ensure the `N8N_API_URL` and `N8N_API_KEY` are properly set in your `.env` file
2. Use the n8n API client in the backend to trigger workflows and fetch workflow status

## Environment Variables

The following environment variables should be set in your `.env` file:

```
N8N_API_URL=http://n8n:5678/api/v1
N8N_API_KEY=your-n8n-api-key
N8N_USER=admin
N8N_PASSWORD=password
```

## Workflow Templates

This directory contains JSON workflow templates that can be imported into n8n:

- `onboarding.json`: User registration and welcome sequence
- `notifications.json`: General notification workflows
- `billing.json`: Subscription and payment workflows

## Getting Started

1. Start the Docker containers:
   ```
   docker-compose up -d
   ```

2. Access the n8n interface: http://localhost:5678

3. Log in with the credentials specified in your `.env` file

4. Import the workflow templates from this directory

5. Configure the n8n credentials for:
   - Database access (PostgreSQL)
   - Email (SMTP)
   - Stripe (if using)

## Security Considerations

- Never commit sensitive credentials to the repository
- Use environment variables for all sensitive information
- Limit n8n access to authorized personnel only
- Configure proper authentication for the n8n instance