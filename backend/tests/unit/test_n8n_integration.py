"""
Unit tests for the n8n integration.
"""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.integrations.n8n import N8nAPIClient, WorkflowExecutionData, WorkflowStatus
from app.features.workflows.service.workflow_service import WorkflowService


class TestN8nIntegration(unittest.TestCase):
    """Test the n8n integration functionality."""
    
    def setUp(self):
        """Set up the test case."""
        # Create a mock n8n client
        self.n8n_client = MagicMock(spec=N8nAPIClient)
        self.n8n_client.trigger_workflow = AsyncMock()
        self.n8n_client.get_workflow_status = AsyncMock()
        self.n8n_client.get_workflow_by_name = AsyncMock()
        
        # Create the workflow service with the mock client
        self.workflow_service = WorkflowService(n8n_client=self.n8n_client)
    
    @pytest.mark.asyncio
    async def test_trigger_onboarding_workflow(self):
        """Test triggering the onboarding workflow."""
        # Mock the workflow lookup
        mock_workflow = {"id": "123", "name": "User Onboarding Workflow"}
        self.n8n_client.get_workflow_by_name.return_value = mock_workflow
        
        # Mock the workflow execution
        self.n8n_client.trigger_workflow.return_value = "execution_123"
        
        # Trigger the workflow
        execution_id = await self.workflow_service.trigger_onboarding_workflow(
            user_id=1,
            email="test@example.com",
            name="Test User",
            verification_url="https://example.com/verify?token=123",
            token="verification_token",
            team_name="Test Team"
        )
        
        # Verify the results
        self.assertEqual(execution_id, "execution_123")
        self.n8n_client.get_workflow_by_name.assert_called_once_with("User Onboarding Workflow")
        self.n8n_client.trigger_workflow.assert_called_once()
        
        # Verify the execution data
        call_args = self.n8n_client.trigger_workflow.call_args[0][0]
        self.assertIsInstance(call_args, WorkflowExecutionData)
        self.assertEqual(call_args.workflow_id, "123")
        self.assertEqual(call_args.data["user_id"], 1)
        self.assertEqual(call_args.data["email"], "test@example.com")
        self.assertEqual(call_args.data["name"], "Test User")
        self.assertEqual(call_args.data["token"], "verification_token")
        self.assertEqual(call_args.data["team_name"], "Test Team")
    
    @pytest.mark.asyncio
    async def test_send_notification(self):
        """Test sending a notification through the notification workflow."""
        # Mock the workflow lookup
        mock_workflow = {"id": "456", "name": "Notification System Workflow"}
        self.n8n_client.get_workflow_by_name.return_value = mock_workflow
        
        # Mock the workflow execution
        self.n8n_client.trigger_workflow.return_value = "execution_456"
        
        # Send a notification
        execution_id = await self.workflow_service.send_notification(
            user_id=1,
            title="Test Notification",
            message="This is a test notification",
            notification_type="test",
            channel="email",
            email="test@example.com"
        )
        
        # Verify the results
        self.assertEqual(execution_id, "execution_456")
        self.n8n_client.get_workflow_by_name.assert_called_once_with("Notification System Workflow")
        self.n8n_client.trigger_workflow.assert_called_once()
        
        # Verify the execution data
        call_args = self.n8n_client.trigger_workflow.call_args[0][0]
        self.assertIsInstance(call_args, WorkflowExecutionData)
        self.assertEqual(call_args.workflow_id, "456")
        self.assertEqual(call_args.data["user_id"], 1)
        self.assertEqual(call_args.data["title"], "Test Notification")
        self.assertEqual(call_args.data["message"], "This is a test notification")
        self.assertEqual(call_args.data["type"], "test")
        self.assertEqual(call_args.data["channel"], "email")
        self.assertEqual(call_args.data["to"], "test@example.com")
    
    @pytest.mark.asyncio
    async def test_process_billing_event(self):
        """Test processing a billing event through the billing workflow."""
        # Mock the workflow lookup
        mock_workflow = {"id": "789", "name": "Billing Workflow"}
        self.n8n_client.get_workflow_by_name.return_value = mock_workflow
        
        # Mock the workflow execution
        self.n8n_client.trigger_workflow.return_value = "execution_789"
        
        # Process a billing event
        event_data = {
            "id": "evt_123",
            "customer": "cus_123",
            "amount": 1000,
            "status": "succeeded"
        }
        
        execution_id = await self.workflow_service.process_billing_event(
            event_type="invoice.payment_succeeded",
            event_data=event_data
        )
        
        # Verify the results
        self.assertEqual(execution_id, "execution_789")
        self.n8n_client.get_workflow_by_name.assert_called_once_with("Billing Workflow")
        self.n8n_client.trigger_workflow.assert_called_once()
        
        # Verify the execution data
        call_args = self.n8n_client.trigger_workflow.call_args[0][0]
        self.assertIsInstance(call_args, WorkflowExecutionData)
        self.assertEqual(call_args.workflow_id, "789")
        self.assertEqual(call_args.data["type"], "invoice.payment_succeeded")
        self.assertEqual(call_args.data["data"]["object"], event_data)
        self.assertEqual(call_args.data["id"], "evt_123")
    
    @pytest.mark.asyncio
    async def test_check_workflow_status(self):
        """Test checking a workflow execution status."""
        # Mock the status response
        mock_status = WorkflowStatus(
            execution_id="execution_123",
            status="completed",
            data={"result": "success"},
            started_at="2023-01-01T00:00:00Z",
            finished_at="2023-01-01T00:01:00Z"
        )
        self.n8n_client.get_workflow_status.return_value = mock_status
        
        # Check the status
        status = await self.workflow_service.check_workflow_status("execution_123")
        
        # Verify the results
        self.assertEqual(status, mock_status)
        self.n8n_client.get_workflow_status.assert_called_once_with("execution_123")


if __name__ == "__main__":
    unittest.main()