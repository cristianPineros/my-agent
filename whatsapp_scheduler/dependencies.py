"""
Dependencies for the WhatsApp Scheduling Agent.
Following main_agent_reference patterns with simple, focused dataclasses.
"""

import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any
import httpx
from settings import settings

logger = logging.getLogger(__name__)


@dataclass
class SchedulingDependencies:
    """Combined dependencies for WhatsApp scheduling agent."""
    
    # WhatsApp API Configuration
    whatsapp_api_key: str
    whatsapp_phone_id: str
    whatsapp_business_account_id: str
    whatsapp_base_url: str
    
    # Google Calendar Configuration
    calendar_credentials_path: str
    calendar_token_path: str
    calendar_id: str
    
    # Application Configuration
    session_id: Optional[str] = None
    user_timezone: str = "America/Bogota"
    business_hours_start: int = 9
    business_hours_end: int = 17
    
    # HTTP Client for API calls
    http_client: Optional[httpx.AsyncClient] = None
    
    # Rate limiting and context
    conversation_context: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialize HTTP client if not provided."""
        if self.http_client is None:
            self.http_client = httpx.AsyncClient(timeout=30.0)
        
        if self.conversation_context is None:
            self.conversation_context = {}


def create_scheduling_dependencies(
    session_id: Optional[str] = None,
    user_timezone: str = "America/Bogota",
    http_client: Optional[httpx.AsyncClient] = None
) -> SchedulingDependencies:
    """
    Create scheduling dependencies from settings.
    
    Args:
        session_id: Optional session identifier for conversation tracking
        user_timezone: User's timezone for scheduling
        http_client: Optional HTTP client for API calls
        
    Returns:
        Configured SchedulingDependencies instance
    """
    return SchedulingDependencies(
        # WhatsApp configuration from settings
        whatsapp_api_key=settings.whatsapp_api_key,
        whatsapp_phone_id=settings.whatsapp_phone_id,
        whatsapp_business_account_id=settings.whatsapp_business_account_id,
        whatsapp_base_url=settings.whatsapp_base_url,
        
        # Calendar configuration from settings
        calendar_credentials_path=settings.calendar_credentials_path,
        calendar_token_path=settings.calendar_token_path,
        calendar_id=settings.calendar_id,
        
        # Application configuration
        session_id=session_id,
        user_timezone=user_timezone,
        business_hours_start=settings.business_hours_start,
        business_hours_end=settings.business_hours_end,
        
        # Optional HTTP client
        http_client=http_client,
        
        # Initialize empty conversation context
        conversation_context={}
    )


@dataclass
class BookingInfo:
    """Information for a booking request."""
    client_name: str
    client_phone: str
    date: str
    time: str
    class_type: str
    instructor: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class CalendarEvent:
    """Represents a calendar event/appointment."""
    event_id: Optional[str] = None
    title: str = ""
    start_time: str = ""
    end_time: str = ""
    attendees: Optional[list] = None
    description: Optional[str] = None
    location: Optional[str] = None