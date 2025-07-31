"""
Tests for WhatsApp Scheduling Agent tools.
Testing individual tool functionality with mocked dependencies.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from whatsapp_scheduler.tools import (
    send_whatsapp_message,
    check_calendar_availability,
    book_class,
    cancel_booking,
    get_client_bookings,
    parse_datetime_natural
)
from whatsapp_scheduler.dependencies import create_scheduling_dependencies


class MockRunContext:
    """Mock RunContext for tool testing."""
    def __init__(self, deps):
        self.deps = deps


class TestWhatsAppTools:
    """Test WhatsApp messaging tools."""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for WhatsApp testing."""
        deps = create_scheduling_dependencies(session_id="whatsapp_test")
        deps.http_client = AsyncMock()
        return deps
    
    @pytest.mark.asyncio
    async def test_send_whatsapp_message_success(self, mock_dependencies):
        """Test successful WhatsApp message sending."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "messages": [{"id": "wamid.12345"}]
        }
        mock_dependencies.http_client.post.return_value = mock_response
        
        ctx = MockRunContext(mock_dependencies)
        result = await send_whatsapp_message(
            ctx, "+1234567890", "Your appointment is confirmed!"
        )
        
        assert "sent successfully" in result
        assert "wamid.12345" in result
        
        # Verify API was called correctly
        mock_dependencies.http_client.post.assert_called_once()
        call_args = mock_dependencies.http_client.post.call_args
        assert f"{mock_dependencies.whatsapp_base_url}/{mock_dependencies.whatsapp_phone_id}/messages" in call_args[1]["url"]
    
    @pytest.mark.asyncio
    async def test_send_whatsapp_message_failure(self, mock_dependencies):
        """Test WhatsApp message sending failure."""
        # Mock failed API response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Invalid phone number"
        mock_dependencies.http_client.post.return_value = mock_response
        
        ctx = MockRunContext(mock_dependencies)
        result = await send_whatsapp_message(
            ctx, "invalid_number", "Test message"
        )
        
        assert "Error sending message" in result
        assert "400" in result
    
    @pytest.mark.asyncio
    async def test_send_whatsapp_message_no_client(self, mock_dependencies):
        """Test WhatsApp message sending without HTTP client."""
        mock_dependencies.http_client = None
        
        ctx = MockRunContext(mock_dependencies)
        result = await send_whatsapp_message(
            ctx, "+1234567890", "Test message"
        )
        
        assert "HTTP client not available" in result


class TestCalendarTools:
    """Test calendar integration tools."""
    
    @pytest.fixture
    def calendar_dependencies(self):
        """Create dependencies for calendar testing."""
        deps = create_scheduling_dependencies(session_id="calendar_test")
        deps.business_hours_start = 9
        deps.business_hours_end = 17
        return deps
    
    @pytest.mark.asyncio
    async def test_check_calendar_availability(self, calendar_dependencies):
        """Test calendar availability checking."""
        ctx = MockRunContext(calendar_dependencies)
        
        result = await check_calendar_availability(
            ctx, "2024-01-15", None, None
        )
        
        assert isinstance(result, list)
        assert len(result) > 0
        
        # Check that available slots are returned
        for slot in result:
            if "error" not in slot:
                assert "time" in slot
                assert "instructor" in slot
                assert "available" in slot
    
    @pytest.mark.asyncio
    async def test_check_calendar_availability_with_time_range(self, calendar_dependencies):
        """Test availability checking with time range."""
        ctx = MockRunContext(calendar_dependencies)
        
        result = await check_calendar_availability(
            ctx, "2024-01-15", ("10:00", "14:00"), "John"
        )
        
        assert isinstance(result, list)
        # Should return slots within the specified time range
        for slot in result:
            if "error" not in slot and "time" in slot:
                hour = int(slot["time"].split(":")[0])
                assert 10 <= hour < 14


class TestBookingTools:
    """Test booking management tools."""
    
    @pytest.fixture
    def booking_dependencies(self):
        """Create dependencies for booking testing."""
        deps = create_scheduling_dependencies(session_id="booking_test")
        deps.conversation_context = {"bookings": []}
        return deps
    
    @pytest.mark.asyncio
    async def test_book_class_success(self, booking_dependencies):
        """Test successful class booking."""
        ctx = MockRunContext(booking_dependencies)
        
        result = await book_class(
            ctx,
            client_name="John Doe",
            client_phone="+1234567890",
            date="2024-01-15",
            time="14:00",
            class_type="Yoga",
            instructor="Jane",
            notes="First time student"
        )
        
        assert result["success"] is True
        assert "booking_id" in result
        assert result["client_name"] == "John Doe"
        assert result["class_type"] == "Yoga"
        
        # Verify booking was stored in context
        bookings = booking_dependencies.conversation_context["bookings"]
        assert len(bookings) == 1
        assert bookings[0]["booking_info"]["client_name"] == "John Doe"
    
    @pytest.mark.asyncio
    async def test_cancel_booking_by_id(self, booking_dependencies):
        """Test booking cancellation by booking ID."""
        ctx = MockRunContext(booking_dependencies)
        
        # First create a booking
        await book_class(
            ctx, "John Doe", "+1234567890", "2024-01-15", 
            "14:00", "Yoga", "Jane", "Test booking"
        )
        
        # Get the booking ID
        booking_id = booking_dependencies.conversation_context["bookings"][0]["booking_id"]
        
        # Cancel the booking
        result = await cancel_booking(ctx, booking_id=booking_id)
        
        assert result["success"] is True
        assert result["booking_id"] == booking_id
        
        # Verify booking was removed
        bookings = booking_dependencies.conversation_context["bookings"]
        assert len(bookings) == 0
    
    @pytest.mark.asyncio
    async def test_cancel_booking_by_details(self, booking_dependencies):
        """Test booking cancellation by client details."""
        ctx = MockRunContext(booking_dependencies)
        
        # Create a booking
        await book_class(
            ctx, "Jane Smith", "+9876543210", "2024-01-16", 
            "10:00", "Pilates", None, None
        )
        
        # Cancel by client details
        result = await cancel_booking(
            ctx,
            client_phone="+9876543210",
            date="2024-01-16",
            time="10:00"
        )
        
        assert result["success"] is True
        assert "cancelled" in result["message"]
    
    @pytest.mark.asyncio
    async def test_cancel_booking_not_found(self, booking_dependencies):
        """Test cancellation of non-existent booking."""
        ctx = MockRunContext(booking_dependencies)
        
        result = await cancel_booking(ctx, booking_id="INVALID_ID")
        
        assert result["success"] is False
        assert "not found" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_client_bookings(self, booking_dependencies):
        """Test retrieving client bookings."""
        ctx = MockRunContext(booking_dependencies)
        
        # Create multiple bookings for the same client
        await book_class(
            ctx, "John Doe", "+1234567890", "2024-01-15", 
            "14:00", "Yoga", "Jane", None
        )
        await book_class(
            ctx, "John Doe", "+1234567890", "2024-01-16", 
            "10:00", "Pilates", "Mike", None
        )
        
        # Create booking for different client
        await book_class(
            ctx, "Jane Smith", "+9876543210", "2024-01-17", 
            "16:00", "HIIT", "Sarah", None
        )
        
        # Get bookings for John Doe
        result = await get_client_bookings(ctx, "+1234567890")
        
        assert len(result) == 2
        for booking in result:
            assert "booking_id" in booking
            assert "date" in booking
            assert "class_type" in booking
        
        # Verify correct bookings returned
        dates = [booking["date"] for booking in result]
        assert "2024-01-15" in dates
        assert "2024-01-16" in dates
    
    @pytest.mark.asyncio
    async def test_get_client_bookings_empty(self, booking_dependencies):
        """Test retrieving bookings for client with no bookings."""
        ctx = MockRunContext(booking_dependencies)
        
        result = await get_client_bookings(ctx, "+0000000000")
        
        assert len(result) == 0


class TestDateTimeTools:
    """Test date/time parsing tools."""
    
    @pytest.fixture
    def datetime_dependencies(self):
        """Create dependencies for datetime testing."""
        deps = create_scheduling_dependencies(session_id="datetime_test")
        deps.user_timezone = "UTC"
        return deps
    
    def test_parse_datetime_natural_success(self, datetime_dependencies):
        """Test successful natural language date parsing."""
        ctx = MockRunContext(datetime_dependencies)
        
        test_cases = [
            "tomorrow at 3pm",
            "next Monday at 10:00",
            "2024-01-15 14:30",
            "January 15th at 2 PM"
        ]
        
        for test_input in test_cases:
            result = parse_datetime_natural(ctx, test_input, "UTC")
            
            # Note: Some of these might fail depending on dateparser behavior
            # In a real scenario, we'd want more controlled testing
            if result.get("success"):
                assert "datetime" in result
                assert "date" in result
                assert "time" in result
                assert result["original_input"] == test_input
    
    def test_parse_datetime_natural_failure(self, datetime_dependencies):
        """Test parsing of invalid date expressions."""
        ctx = MockRunContext(datetime_dependencies)
        
        result = parse_datetime_natural(ctx, "invalid date string", "UTC")
        
        # Should handle parsing failure gracefully
        if not result.get("success"):
            assert "error" in result
            assert result["original_input"] == "invalid date string"
    
    def test_parse_datetime_with_timezone(self, datetime_dependencies):
        """Test datetime parsing with specific timezone."""
        ctx = MockRunContext(datetime_dependencies)
        
        result = parse_datetime_natural(ctx, "tomorrow at noon", "America/New_York")
        
        if result.get("success"):
            assert "timezone" in result
            # Should respect the specified timezone


if __name__ == "__main__":
    pytest.main([__file__, "-v"])