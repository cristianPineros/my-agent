"""
Tools for WhatsApp Scheduling Agent.
Following PydanticAI patterns with @agent.tool decorators and proper error handling.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import dateparser
from pydantic_ai import RunContext

from .dependencies import SchedulingDependencies, BookingInfo, CalendarEvent

logger = logging.getLogger(__name__)


async def send_whatsapp_message(
    ctx: RunContext[SchedulingDependencies],
    to_number: str,
    message: str,
    template_type: Optional[str] = None
) -> str:
    """
    Send a WhatsApp message using the Business API.
    
    Args:
        to_number: Phone number to send message to
        message: Message content to send
        template_type: Optional template type (confirmation/reminder/cancellation)
    
    Returns:
        Message delivery status
    """
    try:
        if not ctx.deps.http_client:
            return "Error: HTTP client not available"
        
        # WhatsApp API endpoint
        url = f"{ctx.deps.whatsapp_base_url}/{ctx.deps.whatsapp_phone_id}/messages"
        
        headers = {
            "Authorization": f"Bearer {ctx.deps.whatsapp_api_key}",
            "Content-Type": "application/json"
        }
        
        # Prepare message payload
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "text",
            "text": {
                "body": message
            }
        }
        
        # Send the message
        response = await ctx.deps.http_client.post(
            url, 
            headers=headers, 
            json=payload
        )
        
        if response.status_code == 200:
            response_data = response.json()
            message_id = response_data.get("messages", [{}])[0].get("id", "unknown")
            logger.info(f"WhatsApp message sent successfully: {message_id}")
            return f"Message sent successfully (ID: {message_id})"
        else:
            error_msg = f"Failed to send WhatsApp message: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return f"Error sending message: {response.status_code}"
            
    except Exception as e:
        error_msg = f"Error sending WhatsApp message: {str(e)}"
        logger.error(error_msg)
        return error_msg


async def check_calendar_availability(
    ctx: RunContext[SchedulingDependencies],
    date: str,
    time_range: Optional[Tuple[str, str]] = None,
    instructor: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Check calendar availability for scheduling.
    
    Args:
        date: Date to check (YYYY-MM-DD format)
        time_range: Optional tuple of (start_time, end_time)
        instructor: Optional specific instructor
    
    Returns:
        List of available time slots
    """
    try:
        logger.info(f"Checking availability for {date} with time_range: {time_range}")
        
        # For demo purposes, return mock availability
        # In production, this would integrate with Google Calendar API
        available_slots = []
        
        # Generate available slots for business hours
        start_hour = ctx.deps.business_hours_start
        end_hour = ctx.deps.business_hours_end
        
        for hour in range(start_hour, end_hour):
            if hour % 2 == 0:  # Mock: even hours are available
                slot_time = f"{hour:02d}:00"
                available_slots.append({
                    "time": slot_time,
                    "instructor": instructor or "Available Staff",
                    "duration": "60 minutes",
                    "available": True
                })
        
        logger.info(f"Found {len(available_slots)} available slots")
        return available_slots
        
    except Exception as e:
        error_msg = f"Error checking calendar availability: {str(e)}"
        logger.error(error_msg)
        return [{"error": error_msg}]


async def book_class(
    ctx: RunContext[SchedulingDependencies],
    client_name: str,
    client_phone: str,
    date: str,
    time: str,
    class_type: str,
    instructor: Optional[str] = None,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Book a class appointment.
    
    Args:
        client_name: Name of the client
        client_phone: Client's phone number
        date: Appointment date (YYYY-MM-DD)
        time: Appointment time (HH:MM)
        class_type: Type of class being booked
        instructor: Optional preferred instructor
        notes: Optional booking notes
    
    Returns:
        Booking confirmation with unique booking ID
    """
    try:
        # Create booking info
        booking = BookingInfo(
            client_name=client_name,
            client_phone=client_phone,
            date=date,
            time=time,
            class_type=class_type,
            instructor=instructor,
            notes=notes
        )
        
        # Generate a booking ID (in production, this would be from database)
        booking_id = f"BK_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Store in conversation context for this session
        if 'bookings' not in ctx.deps.conversation_context:
            ctx.deps.conversation_context['bookings'] = []
        
        ctx.deps.conversation_context['bookings'].append({
            'booking_id': booking_id,
            'booking_info': booking.__dict__,
            'created_at': datetime.now().isoformat()
        })
        
        logger.info(f"Class booked successfully: {booking_id}")
        
        return {
            "success": True,
            "booking_id": booking_id,
            "client_name": client_name,
            "date": date,
            "time": time,
            "class_type": class_type,
            "instructor": instructor or "Available Staff",
            "confirmation": f"Your {class_type} class is confirmed for {date} at {time}"
        }
        
    except Exception as e:
        error_msg = f"Error booking class: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "error": error_msg
        }


async def cancel_booking(
    ctx: RunContext[SchedulingDependencies],
    booking_id: Optional[str] = None,
    client_phone: Optional[str] = None,
    date: Optional[str] = None,
    time: Optional[str] = None
) -> Dict[str, Any]:
    """
    Cancel a booking by ID or client details.
    
    Args:
        booking_id: Unique booking ID
        client_phone: Client's phone number (alternative identifier)
        date: Booking date (alternative identifier)
        time: Booking time (alternative identifier)
    
    Returns:
        Cancellation confirmation
    """
    try:
        bookings = ctx.deps.conversation_context.get('bookings', [])
        
        if booking_id:
            # Find booking by ID
            for booking in bookings:
                if booking['booking_id'] == booking_id:
                    bookings.remove(booking)
                    logger.info(f"Booking cancelled: {booking_id}")
                    return {
                        "success": True,
                        "booking_id": booking_id,
                        "message": f"Booking {booking_id} has been cancelled successfully"
                    }
        
        elif client_phone and date and time:
            # Find booking by client details
            for booking in bookings:
                booking_info = booking['booking_info']
                if (booking_info['client_phone'] == client_phone and 
                    booking_info['date'] == date and 
                    booking_info['time'] == time):
                    bookings.remove(booking)
                    logger.info(f"Booking cancelled for {client_phone} on {date} at {time}")
                    return {
                        "success": True,
                        "booking_id": booking['booking_id'],
                        "message": f"Your booking for {date} at {time} has been cancelled"
                    }
        
        return {
            "success": False,
            "error": "Booking not found with the provided details"
        }
        
    except Exception as e:
        error_msg = f"Error cancelling booking: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "error": error_msg
        }


async def get_client_bookings(
    ctx: RunContext[SchedulingDependencies],
    client_phone: str,
    date_range: Optional[Tuple[str, str]] = None
) -> List[Dict[str, Any]]:
    """
    Get all bookings for a specific client.
    
    Args:
        client_phone: Client's phone number
        date_range: Optional date range (start_date, end_date)
    
    Returns:
        List of client's bookings
    """
    try:
        bookings = ctx.deps.conversation_context.get('bookings', [])
        client_bookings = []
        
        for booking in bookings:
            booking_info = booking['booking_info']
            if booking_info['client_phone'] == client_phone:
                client_bookings.append({
                    "booking_id": booking['booking_id'],
                    "date": booking_info['date'],
                    "time": booking_info['time'],
                    "class_type": booking_info['class_type'],
                    "instructor": booking_info.get('instructor', 'Available Staff'),
                    "created_at": booking['created_at']
                })
        
        logger.info(f"Found {len(client_bookings)} bookings for {client_phone}")
        return client_bookings
        
    except Exception as e:
        error_msg = f"Error retrieving client bookings: {str(e)}"
        logger.error(error_msg)
        return [{"error": error_msg}]


def parse_datetime_natural(
    ctx: RunContext[SchedulingDependencies],
    user_input: str,
    timezone: Optional[str] = None
) -> Dict[str, Any]:
    """
    Parse natural language datetime expressions.
    
    Args:
        user_input: Natural language date/time expression
        timezone: Optional timezone for parsing
    
    Returns:
        Structured datetime information
    """
    try:
        # Use user timezone or default
        tz = timezone or ctx.deps.user_timezone
        
        # Parse using dateparser
        parsed_date = dateparser.parse(
            user_input,
            settings={
                'TIMEZONE': tz,
                'RETURN_AS_TIMEZONE_AWARE': True,
                'PREFER_DAY_OF_MONTH': 'first'
            }
        )
        
        if parsed_date:
            return {
                "success": True,
                "datetime": parsed_date.isoformat(),
                "date": parsed_date.strftime('%Y-%m-%d'),
                "time": parsed_date.strftime('%H:%M'),
                "timezone": str(parsed_date.tzinfo),
                "original_input": user_input
            }
        else:
            return {
                "success": False,
                "error": f"Could not parse datetime: '{user_input}'",
                "original_input": user_input
            }
            
    except Exception as e:
        error_msg = f"Error parsing datetime: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "original_input": user_input
        }