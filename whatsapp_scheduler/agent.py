"""
WhatsApp Conversational Scheduling Agent.
Following main_agent_reference patterns with string output and focused tools.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from pydantic_ai import Agent, RunContext

from .providers import get_llm_model
from .dependencies import SchedulingDependencies
from .tools import (
    send_whatsapp_message,
    check_calendar_availability,
    book_class,
    cancel_booking,
    get_client_bookings,
    parse_datetime_natural
)

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """
You are a friendly and efficient scheduling assistant for a fitness studio. Your role is to help clients book, reschedule, and manage their class appointments through WhatsApp.

Key responsibilities:
- Greet clients warmly and professionally
- Understand scheduling requests in natural language
- Check availability and suggest suitable time slots
- Handle booking confirmations and send details
- Manage rescheduling and cancellations
- Answer basic questions about class types, duration, and instructors
- Maintain conversation context throughout the interaction

Guidelines:
- Always confirm the details before finalizing a booking
- Offer 3-5 available time slots when possible
- Be proactive about potential scheduling conflicts
- Use the client's timezone for all communications
- Send confirmation messages with all relevant details
- Be concise but thorough in responses
- Handle edge cases gracefully (no availability, last-minute changes)
- Remember conversation context and previous bookings

Class Types Available:
- Yoga (60 minutes)
- Pilates (45 minutes)
- HIIT Training (30 minutes)
- Personal Training (60 minutes)
- Group Fitness (45 minutes)

You should NOT:
- Discuss pricing or payment (redirect to staff)
- Make changes to instructor schedules
- Share other clients' information
- Book outside of business hours without special authorization

Always be helpful, professional, and focus on making scheduling as easy as possible for clients.
"""


# Create the scheduling agent - using string output (no result_type)
scheduling_agent = Agent(
    get_llm_model(),
    deps_type=SchedulingDependencies,
    system_prompt=SYSTEM_PROMPT
)


@scheduling_agent.tool
async def send_message(
    ctx: RunContext[SchedulingDependencies],
    to_number: str,
    message: str,
    template_type: Optional[str] = None
) -> str:
    """
    Send a WhatsApp message to a client.
    
    Args:
        to_number: Client's phone number
        message: Message content to send
        template_type: Optional template type (confirmation/reminder/cancellation)
    
    Returns:
        Message delivery status
    """
    return await send_whatsapp_message(ctx, to_number, message, template_type)


@scheduling_agent.tool
async def check_availability(
    ctx: RunContext[SchedulingDependencies],
    date: str,
    time_range: Optional[str] = None,
    instructor: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Check calendar availability for a specific date.
    
    Args:
        date: Date to check (e.g., "2024-01-15", "tomorrow", "next Monday")
        time_range: Optional time range (e.g., "morning", "afternoon", "9am-12pm")
        instructor: Optional preferred instructor name
    
    Returns:
        List of available time slots with instructor information
    """
    # Parse the date if it's in natural language
    parsed_date = parse_datetime_natural(ctx, date)
    if not parsed_date.get("success"):
        return [{"error": f"Could not understand date: {date}"}]
    
    formatted_date = parsed_date["date"]
    
    # Parse time range if provided
    time_tuple = None
    if time_range:
        # Simple time range parsing (can be enhanced)
        if "morning" in time_range.lower():
            time_tuple = ("09:00", "12:00")
        elif "afternoon" in time_range.lower():
            time_tuple = ("12:00", "17:00")
        elif "evening" in time_range.lower():
            time_tuple = ("17:00", "20:00")
    
    return await check_calendar_availability(ctx, formatted_date, time_tuple, instructor)


@scheduling_agent.tool
async def make_booking(
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
    Create a new class booking.
    
    Args:
        client_name: Name of the client
        client_phone: Client's phone number
        date: Booking date (will be parsed if natural language)
        time: Booking time (e.g., "3pm", "15:00")
        class_type: Type of class (Yoga, Pilates, HIIT, etc.)
        instructor: Optional preferred instructor
        notes: Optional booking notes
    
    Returns:
        Booking confirmation details
    """
    # Parse date and time if in natural language
    parsed_datetime = parse_datetime_natural(ctx, f"{date} at {time}")
    if not parsed_datetime.get("success"):
        return {
            "success": False,
            "error": f"Could not understand date/time: {date} at {time}"
        }
    
    booking_date = parsed_datetime["date"]
    booking_time = parsed_datetime["time"]
    
    return await book_class(
        ctx, client_name, client_phone, booking_date, 
        booking_time, class_type, instructor, notes
    )


@scheduling_agent.tool
async def cancel_appointment(
    ctx: RunContext[SchedulingDependencies],
    booking_id: Optional[str] = None,
    client_phone: Optional[str] = None,
    date: Optional[str] = None,
    time: Optional[str] = None
) -> Dict[str, Any]:
    """
    Cancel an existing booking.
    
    Args:
        booking_id: Booking ID (if known)
        client_phone: Client's phone number
        date: Booking date (if booking_id not provided)
        time: Booking time (if booking_id not provided)
    
    Returns:
        Cancellation confirmation
    """
    # Parse date if provided and in natural language
    formatted_date = date
    if date and not booking_id:
        parsed_date = parse_datetime_natural(ctx, date)
        if parsed_date.get("success"):
            formatted_date = parsed_date["date"]
    
    return await cancel_booking(ctx, booking_id, client_phone, formatted_date, time)


@scheduling_agent.tool
async def view_bookings(
    ctx: RunContext[SchedulingDependencies],
    client_phone: str,
    date_range: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    View all bookings for a client.
    
    Args:
        client_phone: Client's phone number
        date_range: Optional date range (e.g., "this week", "next month")
    
    Returns:
        List of client's upcoming bookings
    """
    # For now, ignore date_range parsing and return all bookings
    # In production, this would filter by date range
    return await get_client_bookings(ctx, client_phone)


@scheduling_agent.tool
def parse_date_time(
    ctx: RunContext[SchedulingDependencies],
    user_input: str,
    timezone: Optional[str] = None
) -> Dict[str, Any]:
    """
    Parse natural language date and time expressions.
    
    Args:
        user_input: Natural language date/time (e.g., "tomorrow at 3pm", "next Tuesday morning")
        timezone: Optional timezone for parsing
    
    Returns:
        Structured datetime information
    """
    return parse_datetime_natural(ctx, user_input, timezone)


# Convenience function to create agent with dependencies
async def chat_with_scheduler(
    message: str,
    dependencies: SchedulingDependencies
) -> str:
    """
    Main function to chat with the scheduling agent.
    
    Args:
        message: User's message to the agent
        dependencies: Configured scheduling dependencies
    
    Returns:
        String response from the agent
    """
    try:
        result = await scheduling_agent.run(message, deps=dependencies)
        return result.data
    except Exception as e:
        logger.error(f"Error in scheduling agent: {e}")
        return f"I apologize, but I encountered an error: {str(e)}. Please try again or contact our staff for assistance."


def chat_with_scheduler_sync(
    message: str,
    dependencies: SchedulingDependencies
) -> str:
    """
    Synchronous version of chat_with_scheduler.
    
    Args:
        message: User's message to the agent
        dependencies: Configured scheduling dependencies
    
    Returns:
        String response from the agent
    """
    try:
        result = scheduling_agent.run_sync(message, deps=dependencies)
        return result.data
    except Exception as e:
        logger.error(f"Error in scheduling agent: {e}")
        return f"I apologize, but I encountered an error: {str(e)}. Please try again or contact our staff for assistance."