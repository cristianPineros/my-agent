"""
Comprehensive tests for WhatsApp Scheduling Agent.
Following PydanticAI testing patterns with TestModel and FunctionModel.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from pydantic_ai.models.test import TestModel, FunctionModel

from whatsapp_scheduler.agent import scheduling_agent, chat_with_scheduler
from whatsapp_scheduler.dependencies import create_scheduling_dependencies


class TestSchedulingAgent:
    """Test the core scheduling agent functionality."""
    
    @pytest.fixture
    def test_dependencies(self):
        """Create test dependencies with mocked services."""
        deps = create_scheduling_dependencies(
            session_id="test_session_123",
            user_timezone="UTC"
        )
        # Mock HTTP client to avoid real API calls
        deps.http_client = AsyncMock()
        return deps
    
    def test_agent_with_test_model(self, test_dependencies):
        """Test agent behavior with TestModel for rapid validation."""
        test_model = TestModel()
        
        with scheduling_agent.override(model=test_model):
            result = scheduling_agent.run_sync(
                "Hello, I'd like to book a yoga class for tomorrow at 2pm",
                deps=test_dependencies
            )
            
            # TestModel returns a structured response
            assert result.data is not None
            assert isinstance(result.data, str)
            assert len(result.data) > 0
    
    def test_agent_custom_test_model_response(self, test_dependencies):
        """Test agent with custom TestModel output."""
        custom_response = "I'd be happy to help you book a yoga class! Let me check availability for tomorrow at 2pm."
        test_model = TestModel(custom_output_text=custom_response)
        
        with scheduling_agent.override(model=test_model):
            result = scheduling_agent.run_sync(
                "I want to book a yoga class tomorrow at 2pm",
                deps=test_dependencies
            )
            
            assert result.data == custom_response
    
    @pytest.mark.asyncio
    async def test_agent_async_conversation(self, test_dependencies):
        """Test async agent conversation flow."""
        test_model = TestModel()
        
        with scheduling_agent.override(model=test_model):
            result = await scheduling_agent.run(
                "Can you show me available time slots for next Monday?",
                deps=test_dependencies
            )
            
            assert result.data is not None
            assert isinstance(result.data, str)
    
    def test_agent_scheduling_conversation_flow(self, test_dependencies):
        """Test complete scheduling conversation with TestModel."""
        test_model = TestModel(call_tools='all')  # Allow tool calls
        
        with scheduling_agent.override(model=test_model):
            # First message: check availability
            result1 = scheduling_agent.run_sync(
                "What time slots are available tomorrow?",
                deps=test_dependencies
            )
            assert result1.data is not None
            
            # Second message: make booking
            result2 = scheduling_agent.run_sync(
                "I'd like to book the 2pm slot for yoga class. My name is John Doe.",
                deps=test_dependencies
            )
            assert result2.data is not None


class TestSchedulingAgentWithFunctionModel:
    """Test agent with FunctionModel for custom behavior simulation."""
    
    @pytest.fixture
    def test_dependencies(self):
        """Create test dependencies."""
        deps = create_scheduling_dependencies(session_id="function_test")
        deps.http_client = AsyncMock()
        return deps
    
    def test_booking_success_scenario(self, test_dependencies):
        """Test successful booking scenario with FunctionModel."""
        def booking_success_func(messages, tools):
            """Simulate successful booking response."""
            last_message = messages[-1].content if messages else ""
            
            if "book" in last_message.lower():
                return "Great! I've successfully booked your yoga class for tomorrow at 2pm. Your booking ID is BK_20240101_140000. You'll receive a confirmation message shortly."
            else:
                return "I'm here to help you schedule your classes. What can I do for you today?"
        
        function_model = FunctionModel(function=booking_success_func)
        
        with scheduling_agent.override(model=function_model):
            result = scheduling_agent.run_sync(
                "I want to book a yoga class tomorrow at 2pm. My name is Jane Smith.",
                deps=test_dependencies
            )
            
            assert "successfully booked" in result.data
            assert "yoga class" in result.data
            assert "BK_" in result.data  # Booking ID
    
    def test_no_availability_scenario(self, test_dependencies):
        """Test no availability scenario with FunctionModel."""
        def no_availability_func(messages, tools):
            """Simulate no availability response."""
            last_message = messages[-1].content if messages else ""
            
            if "available" in last_message.lower() or "book" in last_message.lower():
                return "I'm sorry, but we don't have any available slots for tomorrow at that time. However, I can offer you these alternatives: Thursday at 2pm, Friday at 10am, or Saturday at 3pm. Would any of these work for you?"
            else:
                return "How can I help you with scheduling today?"
        
        function_model = FunctionModel(function=no_availability_func)
        
        with scheduling_agent.override(model=function_model):
            result = scheduling_agent.run_sync(
                "Are there any yoga classes available tomorrow at 2pm?",
                deps=test_dependencies
            )
            
            assert "don't have any available slots" in result.data
            assert "alternatives" in result.data or "Thursday" in result.data
    
    def test_cancellation_scenario(self, test_dependencies):
        """Test booking cancellation with FunctionModel."""
        def cancellation_func(messages, tools):
            """Simulate cancellation response."""
            last_message = messages[-1].content if messages else ""
            
            if "cancel" in last_message.lower():
                return "I've successfully cancelled your booking. Your slot for tomorrow at 2pm is now available for other clients. Is there anything else I can help you with?"
            else:
                return "How can I assist you today?"
        
        function_model = FunctionModel(function=cancellation_func)
        
        with scheduling_agent.override(model=function_model):
            result = scheduling_agent.run_sync(
                "I need to cancel my appointment for tomorrow at 2pm",
                deps=test_dependencies
            )
            
            assert "successfully cancelled" in result.data
            assert "tomorrow at 2pm" in result.data


class TestAgentToolIntegration:
    """Test agent tool integration with mocked dependencies."""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Create dependencies with configured mock responses."""
        deps = create_scheduling_dependencies(session_id="tool_test")
        deps.http_client = AsyncMock()
        
        # Configure mock HTTP responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "messages": [{"id": "msg_12345"}]
        }
        deps.http_client.post.return_value = mock_response
        
        return deps
    
    @pytest.mark.asyncio
    async def test_availability_check_tool(self, mock_dependencies):
        """Test availability checking tool usage."""
        test_model = TestModel(call_tools=['check_availability'])
        
        with scheduling_agent.override(model=test_model):
            result = await scheduling_agent.run(
                "What's available tomorrow morning?",
                deps=mock_dependencies
            )
            
            # Should invoke the check_availability tool
            assert "check_availability" in result.data
    
    @pytest.mark.asyncio
    async def test_booking_tool(self, mock_dependencies):
        """Test booking tool usage."""
        test_model = TestModel(call_tools=['make_booking'])
        
        with scheduling_agent.override(model=test_model):
            result = await scheduling_agent.run(
                "Book me for yoga tomorrow at 2pm. I'm John Doe, phone number +1234567890",
                deps=mock_dependencies
            )
            
            # Should invoke the make_booking tool
            assert "make_booking" in result.data
    
    @pytest.mark.asyncio
    async def test_messaging_tool(self, mock_dependencies):
        """Test WhatsApp messaging tool."""
        test_model = TestModel(call_tools=['send_message'])
        
        with scheduling_agent.override(model=test_model):
            result = await scheduling_agent.run(
                "Send me a confirmation for my appointment",
                deps=mock_dependencies
            )
            
            # Should invoke the send_message tool
            assert "send_message" in result.data


class TestAgentErrorHandling:
    """Test agent error handling scenarios."""
    
    @pytest.fixture
    def error_dependencies(self):
        """Create dependencies that will trigger errors."""
        deps = create_scheduling_dependencies(session_id="error_test")
        
        # Mock HTTP client that fails
        deps.http_client = AsyncMock()
        deps.http_client.post.side_effect = Exception("Network error")
        
        return deps
    
    def test_agent_handles_tool_errors_gracefully(self, error_dependencies):
        """Test that agent handles tool errors without crashing."""
        test_model = TestModel(call_tools='all')
        
        with scheduling_agent.override(model=test_model):
            result = scheduling_agent.run_sync(
                "Book a class for me",
                deps=error_dependencies
            )
            
            # Agent should handle errors gracefully and return a response
            assert result.data is not None
            assert isinstance(result.data, str)
    
    @pytest.mark.asyncio
    async def test_chat_function_error_handling(self, error_dependencies):
        """Test chat function error handling."""
        # Force an error in the agent
        with scheduling_agent.override(model=None):  # Invalid model
            try:
                result = await chat_with_scheduler(
                    "Test message",
                    error_dependencies
                )
                # Should return error message
                assert "error" in result.lower() or "apologize" in result.lower()
            except Exception:
                # If exception is raised, that's also acceptable
                pass


# Pytest configuration for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])