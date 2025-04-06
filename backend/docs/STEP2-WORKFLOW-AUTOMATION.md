# SaaS Factory - Workflow Automation with n8n

This document provides an overview of the Workflow Automation system implemented in Step 2 of the SaaS Factory Blueprint application.

## Overview

The Workflow Automation system integrates n8n as a powerful workflow automation engine to handle business processes in the SaaS Factory application. It focuses on three key areas:

1. **n8n Integration Setup** - Container configuration and API integration
2. **Customer Onboarding Automation** - User registration and welcome flow
3. **Notification System** - Event-based notifications across the platform

## Architecture

The workflow automation system follows this architecture:

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   FastAPI   │◄────►│    n8n      │◄────►│   Email     │
│  Backend    │      │  Workflows  │      │  Service    │
└─────────────┘      └─────────────┘      └─────────────┘
       ▲                    ▲                   ▲
       │                    │                   │
       ▼                    ▼                   ▼
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  Database   │      │ Webhook     │      │ Templates   │
│  (Events)   │      │ Triggers    │      │ (Email/SMS) │
└─────────────┘      └─────────────┘      └─────────────┘
```

- **FastAPI Backend**: Triggers workflow events and provides API endpoints
- **n8n Workflows**: Automation engine for business processes
- **Email Service**: Sends transactional emails based on system events
- **Database Events**: Stores event records and workflow status
- **Webhook Triggers**: HTTP endpoints for triggering workflows
- **Templates**: Email and notification templates

## Key Components

### 1. n8n Integration Setup

The n8n workflow engine is configured as a Docker container within the application's infrastructure:

- Custom Docker configuration for n8n
- Secure API access between backend and n8n
- Workflow templates and credential management

#### n8n Container Configuration:

```yaml
# docker-compose.yml
n8n:
  image: n8nio/n8n:latest
  restart: always
  ports:
    - "5678:5678"
  environment:
    - N8N_HOST=${N8N_HOST}
    - N8N_PROTOCOL=${N8N_PROTOCOL}
    - N8N_PORT=${N8N_PORT}
    - N8N_ENCRYPTION_KEY=${N8N_ENCRYPTION_KEY}
    - N8N_BASIC_AUTH_ACTIVE=true
    - N8N_BASIC_AUTH_USER=${N8N_BASIC_AUTH_USER}
    - N8N_BASIC_AUTH_PASSWORD=${N8N_BASIC_AUTH_PASSWORD}
  volumes:
    - ./n8n_data:/home/node/.n8n
  networks:
    - app-network
```

#### Integration Service:

The application includes an `N8nService` class that handles interactions with the n8n API:

```python
class N8nService:
    def __init__(self, n8n_url: str, n8n_api_key: str):
        self.n8n_url = n8n_url
        self.n8n_api_key = n8n_api_key
        self.headers = {
            "X-N8N-API-KEY": n8n_api_key,
            "Content-Type": "application/json"
        }
    
    async def trigger_workflow(self, workflow_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger an n8n workflow with the given payload"""
        url = f"{self.n8n_url}/webhook/{workflow_id}"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
```

### 2. Customer Onboarding Automation

The onboarding process automates user registration and welcome sequences:

- Registration confirmation
- Email verification
- Welcome sequence emails
- Account setup guidance

#### Onboarding Workflow:

```python
class OnboardingService:
    def __init__(self, n8n_service: N8nService, email_service: EmailService):
        self.n8n_service = n8n_service
        self.email_service = email_service
    
    async def start_onboarding_flow(self, user_id: int, background_tasks: BackgroundTasks, base_url: str):
        """Start the onboarding flow for a new user"""
        # Get user data
        user = await self.user_service.get_by_id(user_id)
        
        # Prepare payload for n8n
        payload = {
            "userId": user.id,
            "email": user.email,
            "name": user.name,
            "baseUrl": base_url,
            "organizationId": user.organization_id
        }
        
        # Trigger onboarding workflow in n8n
        await self.n8n_service.trigger_workflow(
            workflow_id="onboarding", 
            payload=payload
        )
        
        # Send immediate welcome email
        background_tasks.add_task(
            self.email_service.send_welcome_email,
            email=user.email,
            name=user.name
        )
```

#### Email Verification:

```python
async def verify_email(token: str):
    """Verify user email with token"""
    try:
        # Validate the token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        
        if not email:
            raise HTTPException(status_code=400, detail="Invalid verification token")
        
        # Update user verification status
        user = await user_service.get_by_email(email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        await user_service.verify_email(user.id)
        
        # Trigger post-verification workflow
        await n8n_service.trigger_workflow(
            workflow_id="post_verification",
            payload={"userId": user.id, "email": user.email}
        )
        
        return {"message": "Email successfully verified"}
    
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid verification token")
```

### 3. Notification System

The notification system provides event-based alerts across the platform:

- Email notifications
- In-app notifications
- System alerts and updates
- User activity notifications

#### Notification Model:

```python
class Notification(Base):
    __tablename__ = "notifications"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    type: Mapped[str] = mapped_column(String(50))
    title: Mapped[str] = mapped_column(String(255))
    message: Mapped[str] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="notifications")
```

#### Notification Service:

```python
class NotificationService:
    def __init__(self, n8n_service: N8nService, repository: NotificationRepository):
        self.n8n_service = n8n_service
        self.repository = repository
    
    async def create_notification(self, notification_data: NotificationCreate) -> Notification:
        """Create a new notification and trigger related workflows"""
        # Create notification in database
        notification = await self.repository.create(notification_data)
        
        # Trigger notification workflow
        await self.n8n_service.trigger_workflow(
            workflow_id="notification_created",
            payload={
                "notificationId": notification.id,
                "userId": notification.user_id,
                "type": notification.type,
                "title": notification.title,
                "message": notification.message
            }
        )
        
        return notification
    
    async def get_user_notifications(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Notification]:
        """Get notifications for a specific user"""
        return await self.repository.get_by_user_id(user_id, skip, limit)
    
    async def mark_as_read(self, notification_id: int) -> Notification:
        """Mark a notification as read"""
        return await self.repository.update(notification_id, {"is_read": True})
```

## Workflow Templates

The system includes predefined workflow templates for common business processes:

### Onboarding Workflow

```json
{
  "name": "User Onboarding",
  "nodes": [
    {
      "id": "webhook",
      "type": "n8n-nodes-base.webhook",
      "parameters": {
        "path": "onboarding",
        "responseMode": "responseNode"
      }
    },
    {
      "id": "sendWelcomeEmail",
      "type": "n8n-nodes-base.emailSend",
      "parameters": {
        "fromEmail": "{{$node.webhook.json.fromEmail}}",
        "toEmail": "{{$node.webhook.json.email}}",
        "subject": "Welcome to SaaS Factory!",
        "text": "Hello {{$node.webhook.json.name}},\n\nWelcome to SaaS Factory! We're excited to have you on board.\n\nBest regards,\nThe SaaS Factory Team"
      }
    },
    {
      "id": "delay24Hours",
      "type": "n8n-nodes-base.wait",
      "parameters": {
        "amount": 24,
        "unit": "hours"
      }
    },
    {
      "id": "sendFollowupEmail",
      "type": "n8n-nodes-base.emailSend",
      "parameters": {
        "fromEmail": "{{$node.webhook.json.fromEmail}}",
        "toEmail": "{{$node.webhook.json.email}}",
        "subject": "Getting Started with SaaS Factory",
        "text": "Hello {{$node.webhook.json.name}},\n\nHere are some tips to get started with SaaS Factory...\n\nBest regards,\nThe SaaS Factory Team"
      }
    }
  ],
  "connections": {
    "webhook": {
      "main": [
        [
          {
            "node": "sendWelcomeEmail",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "sendWelcomeEmail": {
      "main": [
        [
          {
            "node": "delay24Hours",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "delay24Hours": {
      "main": [
        [
          {
            "node": "sendFollowupEmail",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  }
}
```

### Notification Workflow

```json
{
  "name": "Notification Processing",
  "nodes": [
    {
      "id": "webhook",
      "type": "n8n-nodes-base.webhook",
      "parameters": {
        "path": "notification",
        "responseMode": "responseNode"
      }
    },
    {
      "id": "switch",
      "type": "n8n-nodes-base.switch",
      "parameters": {
        "dataPropertyName": "type",
        "rules": {
          "rules": [
            {
              "value": "security",
              "outputIndex": 0
            },
            {
              "value": "billing",
              "outputIndex": 1
            },
            {
              "value": "team",
              "outputIndex": 2
            }
          ]
        }
      }
    },
    {
      "id": "securityEmail",
      "type": "n8n-nodes-base.emailSend",
      "parameters": {
        "fromEmail": "security@example.com",
        "toEmail": "{{$node.webhook.json.email}}",
        "subject": "Security Alert: {{$node.webhook.json.title}}",
        "text": "{{$node.webhook.json.message}}"
      }
    },
    {
      "id": "billingEmail",
      "type": "n8n-nodes-base.emailSend",
      "parameters": {
        "fromEmail": "billing@example.com",
        "toEmail": "{{$node.webhook.json.email}}",
        "subject": "Billing Notification: {{$node.webhook.json.title}}",
        "text": "{{$node.webhook.json.message}}"
      }
    },
    {
      "id": "teamEmail",
      "type": "n8n-nodes-base.emailSend",
      "parameters": {
        "fromEmail": "team@example.com",
        "toEmail": "{{$node.webhook.json.email}}",
        "subject": "Team Update: {{$node.webhook.json.title}}",
        "text": "{{$node.webhook.json.message}}"
      }
    }
  ],
  "connections": {
    "webhook": {
      "main": [
        [
          {
            "node": "switch",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "switch": {
      "main": [
        [
          {
            "node": "securityEmail",
            "type": "main",
            "index": 0
          }
        ],
        [
          {
            "node": "billingEmail",
            "type": "main",
            "index": 0
          }
        ],
        [
          {
            "node": "teamEmail",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  }
}
```

## Email Templates

The notification system includes standardized email templates for various notification types:

### Welcome Email Template

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Welcome to SaaS Factory</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; color: #333;">
    <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto; border: 1px solid #eaeaea; border-radius: 5px; overflow: hidden;">
        <tr>
            <td style="background-color: #0070f3; padding: 20px; text-align: center;">
                <h1 style="color: #ffffff; margin: 0;">Welcome to SaaS Factory</h1>
            </td>
        </tr>
        <tr>
            <td style="padding: 20px;">
                <p>Hello {{ name }},</p>
                <p>Welcome to SaaS Factory! We're excited to have you on board.</p>
                <p>Your account has been created successfully. Here are a few things you can do to get started:</p>
                <ul>
                    <li>Complete your profile</li>
                    <li>Explore the dashboard</li>
                    <li>Invite your team members</li>
                </ul>
                <p>If you have any questions, feel free to reply to this email.</p>
                <p>Best regards,<br>The SaaS Factory Team</p>
            </td>
        </tr>
        <tr>
            <td style="background-color: #f6f6f6; padding: 20px; text-align: center; font-size: 12px; color: #666;">
                <p>© 2023 SaaS Factory. All rights reserved.</p>
                <p>If you didn't create this account, please <a href="{{ unsubscribe_link }}" style="color: #666;">click here</a>.</p>
            </td>
        </tr>
    </table>
</body>
</html>
```

### Notification Email Template

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{{ title }}</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; color: #333;">
    <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto; border: 1px solid #eaeaea; border-radius: 5px; overflow: hidden;">
        <tr>
            <td style="background-color: #0070f3; padding: 20px; text-align: center;">
                <h1 style="color: #ffffff; margin: 0;">{{ title }}</h1>
            </td>
        </tr>
        <tr>
            <td style="padding: 20px;">
                <p>Hello {{ name }},</p>
                <div>{{ message }}</div>
                {% if action_url %}
                <p style="text-align: center; margin: 30px 0;">
                    <a href="{{ action_url }}" style="display: inline-block; background-color: #0070f3; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;">{{ action_text }}</a>
                </p>
                {% endif %}
                <p>Best regards,<br>The SaaS Factory Team</p>
            </td>
        </tr>
        <tr>
            <td style="background-color: #f6f6f6; padding: 20px; text-align: center; font-size: 12px; color: #666;">
                <p>© 2023 SaaS Factory. All rights reserved.</p>
                <p>You are receiving this email because you have an account with SaaS Factory.</p>
                <p>If you'd prefer not to receive these types of emails, you can <a href="{{ unsubscribe_link }}" style="color: #666;">unsubscribe</a>.</p>
            </td>
        </tr>
    </table>
</body>
</html>
```

## API Endpoints

The workflow automation system exposes these endpoints:

- `/api/v1/onboarding/start` - Start onboarding workflow
- `/api/v1/auth/verify-email/{token}` - Verify email with token
- `/api/v1/notifications` - Create and retrieve notifications
- `/api/v1/notifications/{id}/read` - Mark notification as read
- `/api/v1/workflows/trigger/{workflow_id}` - Trigger workflow manually

## Setup and Configuration

To set up the workflow automation system, configure these environment variables:

```
# n8n Configuration
N8N_HOST=n8n
N8N_PROTOCOL=http
N8N_PORT=5678
N8N_ENCRYPTION_KEY=your-encryption-key
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=password
N8N_WEBHOOK_URL=http://n8n:5678/webhook

# Email Configuration
EMAIL_SENDER=noreply@example.com
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=smtp-user
SMTP_PASSWORD=smtp-password
```

## Testing

The workflow automation system includes tests for all components:

```bash
# Test email templates
pytest tests/features/notifications/test_email_templates.py

# Test notification API
pytest tests/features/notifications/test_api_endpoints.py

# Test n8n integration
pytest tests/unit/test_n8n_integration.py
```

## Common Operations

### Sending a Notification

```python
# Create notification
notification = await notification_service.create_notification(
    NotificationCreate(
        user_id=user.id,
        type="security",
        title="New login detected",
        message="A new login was detected from a new device. If this wasn't you, please reset your password."
    )
)

# Notification is automatically sent via n8n workflow
```

### Triggering a Custom Workflow

```python
# Prepare workflow data
workflow_data = {
    "user_id": user.id,
    "organization_id": organization.id,
    "event_type": "subscription_upgraded",
    "data": {
        "plan_id": "premium",
        "effective_date": "2023-01-01"
    }
}

# Trigger workflow
result = await n8n_service.trigger_workflow(
    workflow_id="subscription_change",
    payload=workflow_data
)
```

## Troubleshooting

### Common Issues

1. **n8n Connection Issues**
   - Check n8n container is running (`docker-compose ps`)
   - Verify n8n URL and API key configuration
   - Ensure network connectivity between app and n8n

2. **Email Delivery Problems**
   - Check SMTP configuration and credentials
   - Verify email templates are correctly formatted
   - Look for error logs in n8n for failed email actions

3. **Workflow Execution Failures**
   - Check n8n logs for error details
   - Verify workflow JSON structure
   - Test webhook endpoints manually to confirm they're accessible

### Workflow Debug Mode

Enable debug mode in n8n to track workflow execution:

1. Log into the n8n web interface
2. Open the workflow
3. Click the "Debug" button
4. Trigger the workflow and observe execution

## Resources

- [n8n Documentation](https://docs.n8n.io/)
- [Webhook Integration Guide](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook/)
- [Email Template Best Practices](https://sendgrid.com/blog/email-templates-5-best-practices/)