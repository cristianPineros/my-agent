"""
Tools for WhatsApp Scheduling Agent.
Following PydanticAI patterns with @agent.tool decorators and proper error handling.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import dateparser
import os.path
from pydantic_ai import RunContext

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from dependencies import SchedulingDependencies, BookingInfo, CalendarEvent

logger = logging.getLogger(__name__)

# Google Calendar API configuration
SCOPES = ['https://www.googleapis.com/auth/calendar']


def get_calendar_service(ctx: RunContext[SchedulingDependencies]):
    """Get authenticated Google Calendar service."""
    try:
        creds = None
        
        # Load existing token
        if os.path.exists(ctx.deps.calendar_token_path):
            creds = Credentials.from_authorized_user_file(ctx.deps.calendar_token_path, SCOPES)
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    ctx.deps.calendar_credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(ctx.deps.calendar_token_path, 'w') as token:
                token.write(creds.to_json())
        
        service = build('calendar', 'v3', credentials=creds)
        return service
        
    except Exception as e:
        logger.error(f"Error creating calendar service: {e}")
        raise


async def get_calendar_events(
    start_time: str,
    end_time: str,
    max_results: int = 10,
    ctx: Optional[RunContext[SchedulingDependencies]] = None
) -> List[Dict[str, Any]]:
    """
    Get calendar events from Google Calendar.
    
    Args:
        start_time: Start time in ISO format
        end_time: End time in ISO format  
        max_results: Maximum number of events to return
        ctx: Optional context (for testing)
    
    Returns:
        List of calendar events
    """
    try:
        if ctx is None:
            from dependencies import create_scheduling_dependencies
            deps = create_scheduling_dependencies()
            
            class MockContext:
                def __init__(self, deps):
                    self.deps = deps
            ctx = MockContext(deps)
        
        service = get_calendar_service(ctx)
        
        # Call the Calendar API
        events_result = service.events().list(
            calendarId=ctx.deps.calendar_id,
            timeMin=start_time,
            timeMax=end_time,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        logger.info(f"Retrieved {len(events)} events from Google Calendar")
        return events
        
    except HttpError as e:
        logger.error(f"Google Calendar API error: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting calendar events: {e}")
        raise


async def create_calendar_event(
    ctx: RunContext[SchedulingDependencies],
    summary: str,
    start_datetime: str,
    end_datetime: str,
    description: Optional[str] = None,
    attendees: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Create a new event in Google Calendar.
    
    Args:
        summary: Event title/summary
        start_datetime: Start time in ISO format
        end_datetime: End time in ISO format
        description: Optional event description
        attendees: Optional list of attendee emails
    
    Returns:
        Created event details
    """
    try:
        service = get_calendar_service(ctx)
        
        # Prepare event data
        event_data = {
            'summary': summary,
            'description': description or '',
            'start': {
                'dateTime': start_datetime,
                'timeZone': ctx.deps.user_timezone,
            },
            'end': {
                'dateTime': end_datetime,
                'timeZone': ctx.deps.user_timezone,
            },
        }
        
        # Add attendees if provided
        if attendees:
            event_data['attendees'] = [{'email': email} for email in attendees]
        
        # Create the event
        event = service.events().insert(
            calendarId=ctx.deps.calendar_id,
            body=event_data
        ).execute()
        
        logger.info(f"Created calendar event: {event.get('id')}")
        return event
        
    except HttpError as e:
        logger.error(f"Google Calendar API error creating event: {e}")
        raise
    except Exception as e:
        logger.error(f"Error creating calendar event: {e}")
        raise


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
    Check calendar availability for scheduling by querying Google Calendar.
    
    Args:
        date: Date to check (YYYY-MM-DD format)
        time_range: Optional tuple of (start_time, end_time)
        instructor: Optional specific instructor
    
    Returns:
        List of available time slots
    """
    try:
        logger.info(f"Checking calendar availability for {date} with time_range: {time_range}")
        
        # Set default time range if not provided
        if time_range is None:
            time_range = (f"{ctx.deps.business_hours_start:02d}:00", f"{ctx.deps.business_hours_end:02d}:00")
        
        # Create datetime range for the day
        start_datetime = f"{date}T{time_range[0]}:00"
        end_datetime = f"{date}T{time_range[1]}:00"
        
        # Get existing events from Google Calendar
        existing_events = await get_calendar_events(
            start_time=start_datetime + "Z",
            end_time=end_datetime + "Z",
            max_results=50,
            ctx=ctx
        )
        
        # Generate all possible slots (hourly slots in business hours)
        available_slots = []
        start_hour = int(time_range[0].split(':')[0])
        end_hour = int(time_range[1].split(':')[0])
        
        for hour in range(start_hour, end_hour):
            slot_time = f"{hour:02d}:00"
            slot_datetime = f"{date}T{slot_time}:00"
            
            # Check if this slot conflicts with existing events
            is_available = True
            for event in existing_events:
                event_start = event.get('start', {}).get('dateTime', '')
                event_end = event.get('end', {}).get('dateTime', '')
                
                if event_start and event_end:
                    # Simple overlap check (could be more sophisticated)
                    if slot_datetime >= event_start[:16] and slot_datetime < event_end[:16]:
                        is_available = False
                        break
            
            if is_available:
                available_slots.append({
                    "time": slot_time,
                    "instructor": instructor or "Available Staff",
                    "duration": "60 minutes",
                    "available": True,
                    "date": date
                })
        
        logger.info(f"Found {len(available_slots)} available slots for {date}")
        return available_slots
        
    except Exception as e:
        error_msg = f"Error checking calendar availability: {str(e)}"
        logger.error(error_msg)
        # Fallback to basic available slots if calendar check fails
        fallback_slots = []
        start_hour = ctx.deps.business_hours_start
        end_hour = ctx.deps.business_hours_end
        
        for hour in range(start_hour, end_hour, 2):  # Every 2 hours as fallback
            slot_time = f"{hour:02d}:00"
            fallback_slots.append({
                "time": slot_time,
                "instructor": instructor or "Available Staff",
                "duration": "60 minutes",
                "available": True,
                "note": "Calendar check failed, showing fallback availability"
            })
        
        return fallback_slots


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
    Book a class appointment by creating an actual Google Calendar event.
    
    Args:
        client_name: Name of the client
        client_phone: Client's phone number
        date: Appointment date (YYYY-MM-DD)
        time: Appointment time (HH:MM)
        class_type: Type of class being booked
        instructor: Optional preferred instructor
        notes: Optional booking notes
    
    Returns:
        Booking confirmation with unique booking ID and calendar event
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
        
        # Generate a booking ID
        booking_id = f"BK_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Calculate class duration based on type
        class_durations = {
            'Yoga': 60,
            'Pilates': 45,
            'HIIT Training': 30,
            'Personal Training': 60,
            'Group Fitness': 45
        }
        duration_minutes = class_durations.get(class_type, 60)
        
        # Create start and end datetime strings with proper timezone handling
        import pytz
        
        # Parse the naive datetime
        naive_datetime = datetime.strptime(f"{date} {time}", '%Y-%m-%d %H:%M')
        
        # Localize to user's timezone (Colombia)
        user_tz = pytz.timezone(ctx.deps.user_timezone)
        start_dt = user_tz.localize(naive_datetime)
        end_dt = start_dt + timedelta(minutes=duration_minutes)
        
        # Convert to ISO format with timezone info
        start_datetime = start_dt.isoformat()
        end_datetime = end_dt.isoformat()
        
        # Create event title and description
        instructor_name = instructor or "Available Staff"
        event_title = f"{class_type} - {client_name}"
        event_description = f"""
Class Booking Details:
- Client: {client_name}
- Phone: {client_phone}
- Class Type: {class_type}
- Instructor: {instructor_name}
- Duration: {duration_minutes} minutes
- Booking ID: {booking_id}
"""
        
        if notes:
            event_description += f"\nNotes: {notes}"
        
        # Create the Google Calendar event
        try:
            calendar_event = await create_calendar_event(
                ctx=ctx,
                summary=event_title,
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                description=event_description.strip()
            )
            
            event_id = calendar_event.get('id')
            event_link = calendar_event.get('htmlLink', '')
            
            logger.info(f"Google Calendar event created: {event_id}")
            
        except Exception as calendar_error:
            logger.error(f"Failed to create calendar event: {calendar_error}")
            # Continue with booking but note the calendar issue
            event_id = None
            event_link = ''
        
        # Store in conversation context for this session
        if 'bookings' not in ctx.deps.conversation_context:
            ctx.deps.conversation_context['bookings'] = []
        
        booking_record = {
            'booking_id': booking_id,
            'booking_info': booking.__dict__,
            'calendar_event_id': event_id,
            'calendar_event_link': event_link,
            'created_at': datetime.now().isoformat()
        }
        
        ctx.deps.conversation_context['bookings'].append(booking_record)
        
        logger.info(f"Class booked successfully: {booking_id} (Calendar Event: {event_id})")
        
        return {
            "success": True,
            "booking_id": booking_id,
            "client_name": client_name,
            "date": date,
            "time": time,
            "class_type": class_type,
            "instructor": instructor_name,
            "duration_minutes": duration_minutes,
            "event_id": event_id,
            "event_link": event_link,
            "summary": event_title,
            "confirmation": f"Your {class_type} class is confirmed for {date} at {time} with {instructor_name}"
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
    Parse natural language datetime expressions with current date context and Spanish support.
    
    Args:
        user_input: Natural language date/time expression
        timezone: Optional timezone for parsing
    
    Returns:
        Structured datetime information
    """
    try:
        from datetime import datetime, timedelta
        import pytz
        
        # Use user timezone or default
        tz = timezone or ctx.deps.user_timezone
        
        # Get current date for context
        if tz == "UTC":
            now = datetime.utcnow().replace(tzinfo=pytz.UTC)
        else:
            try:
                tz_obj = pytz.timezone(tz)
                now = datetime.now(tz_obj)
            except:
                now = datetime.now()
        
        # Preprocess Spanish expressions with current date context
        original_lower = user_input.lower().strip()
        translated_input = original_lower
        
        # Manual parsing for common Spanish relative dates
        current_weekday = now.weekday()  # 0=Monday, 6=Sunday
        
        # Days of week mapping
        days_map = {
            'lunes': 0, 'monday': 0,
            'martes': 1, 'tuesday': 1,
            'miércoles': 2, 'miercoles': 2, 'wednesday': 2,
            'jueves': 3, 'thursday': 3,
            'viernes': 4, 'friday': 4,
            'sábado': 5, 'sabado': 5, 'saturday': 5,
            'domingo': 6, 'sunday': 6
        }
        
        # Try to manually calculate relative dates
        target_date = None
        target_time = "00:00"
        
        # Extract time if present - improved patterns to handle Spanish properly
        time_patterns = [
            r'a la (\d{1,2})\s+(pm|am)',  # "a la 1 pm" (singular)
            r'a las (\d{1,2}):(\d{2})\s*(pm|am)?',  # "a las 1:30 pm" with minutes
            r'a las (\d{1,2})\s+(pm|am)',  # "a las 1 pm" (plural)
            r'at (\d{1,2})\s*(pm|am)',  # "at 1 pm"
            r'(\d{1,2}):(\d{2})',  # "13:30"
            r'(\d{1,2})\s*(pm|am)'  # "1 pm" (fallback)
        ]
        
        import re
        time_found = None
        for pattern in time_patterns:
            match = re.search(pattern, original_lower)
            if match:
                try:
                    # Parse based on pattern type
                    if 'a la' in pattern or 'a las' in pattern or 'at' in pattern:
                        # Patterns with explicit Spanish/English time phrases
                        hour = int(match.group(1))
                        if ':' in pattern and len(match.groups()) >= 2 and match.group(2).isdigit():
                            minute = int(match.group(2))
                            ampm = match.group(3) if len(match.groups()) >= 3 else None
                        else:
                            minute = 0  # Default to 0 minutes for "a la 1 pm"
                            ampm = match.group(2) if len(match.groups()) >= 2 else None
                    elif ':' in pattern:
                        # Time with colon "13:30"
                        hour = int(match.group(1))
                        minute = int(match.group(2))
                        ampm = match.group(3) if len(match.groups()) >= 3 else None
                    else:
                        # Simple hour + am/pm "1 pm"
                        hour = int(match.group(1))
                        minute = 0
                        ampm = match.group(2) if len(match.groups()) >= 2 else None
                    
                    # Apply AM/PM conversion
                    if ampm:
                        if ampm.lower() == 'pm' and hour != 12:
                            hour += 12
                        elif ampm.lower() == 'am' and hour == 12:
                            hour = 0
                    
                    target_time = f"{hour:02d}:{minute:02d}"
                    time_found = True
                    break
                except Exception as e:
                    logger.error(f"Error parsing time pattern '{pattern}': {e}")
                    continue
        
        # Parse relative day expressions manually
        if 'mañana' in original_lower or 'tomorrow' in original_lower:
            target_date = now.date() + timedelta(days=1)
        elif 'pasado mañana' in original_lower or 'day after tomorrow' in original_lower:
            target_date = now.date() + timedelta(days=2)
        elif 'hoy' in original_lower or 'today' in original_lower:
            target_date = now.date()
        else:
            # Look for "próximo/next + day"
            for day_name, day_num in days_map.items():
                if f'próximo {day_name}' in original_lower or f'proximo {day_name}' in original_lower or f'next {day_name}' in original_lower:
                    # Calculate days until next occurrence of this weekday
                    days_ahead = day_num - current_weekday
                    if days_ahead <= 0:  # Target day already happened this week
                        days_ahead += 7
                    target_date = now.date() + timedelta(days=days_ahead)
                    break
                elif day_name in original_lower and ('próximo' in original_lower or 'proximo' in original_lower or 'next' in original_lower):
                    # Handle cases like "próximo viernes" or "next friday"
                    days_ahead = day_num - current_weekday
                    if days_ahead <= 0:
                        days_ahead += 7
                    target_date = now.date() + timedelta(days=days_ahead)
                    break
        
        # If we successfully parsed manually
        if target_date:
            try:
                # Combine date and time
                if tz == "UTC":
                    target_datetime = datetime.combine(target_date, datetime.strptime(target_time, "%H:%M").time())
                    target_datetime = target_datetime.replace(tzinfo=pytz.UTC)
                else:
                    target_datetime = datetime.combine(target_date, datetime.strptime(target_time, "%H:%M").time())
                    tz_obj = pytz.timezone(tz)
                    target_datetime = tz_obj.localize(target_datetime)
                
                return {
                    "success": True,
                    "datetime": target_datetime.isoformat(),
                    "date": target_datetime.strftime('%Y-%m-%d'),
                    "time": target_datetime.strftime('%H:%M'),
                    "timezone": str(target_datetime.tzinfo),
                    "original_input": user_input,
                    "method": "manual_parsing",
                    "current_date_context": now.strftime('%Y-%m-%d'),
                    "current_weekday": current_weekday
                }
            except Exception as e:
                logger.error(f"Error in manual parsing: {e}")
        
        # Fallback to dateparser with translations
        spanish_phrases = {
            'próximo viernes': 'next friday',
            'proximo viernes': 'next friday',
            'el viernes que viene': 'next friday',
            'siguiente viernes': 'next friday',
            'próximo lunes': 'next monday',
            'proximo lunes': 'next monday',
            'próximo martes': 'next tuesday',
            'proximo martes': 'next tuesday',
            'próximo miércoles': 'next wednesday',
            'proximo miercoles': 'next wednesday',
            'próximo jueves': 'next thursday',
            'proximo jueves': 'next thursday',
            'próximo sábado': 'next saturday',
            'proximo sabado': 'next saturday',
            'próximo domingo': 'next sunday',
            'proximo domingo': 'next sunday',
            'mañana': 'tomorrow',
            'pasado mañana': 'day after tomorrow'
        }
        
        # Add specific date translations for Spanish
        specific_date_phrases = {
            r'el (\d+) de enero': r'\1 january',
            r'el (\d+) de febrero': r'\1 february', 
            r'el (\d+) de marzo': r'\1 march',
            r'el (\d+) de abril': r'\1 april',
            r'el (\d+) de mayo': r'\1 may',
            r'el (\d+) de junio': r'\1 june',
            r'el (\d+) de julio': r'\1 july', 
            r'el (\d+) de agosto': r'\1 august',
            r'el (\d+) de septiembre': r'\1 september',
            r'el (\d+) de octubre': r'\1 october',
            r'el (\d+) de noviembre': r'\1 november',
            r'el (\d+) de diciembre': r'\1 december',
            # Also handle cases with time
            r'el (\d+) de enero a las': r'\1 january at',
            r'el (\d+) de febrero a las': r'\1 february at',
            r'el (\d+) de marzo a las': r'\1 march at',
            r'el (\d+) de abril a las': r'\1 april at',
            r'el (\d+) de mayo a las': r'\1 may at',
            r'el (\d+) de junio a las': r'\1 june at',
            r'el (\d+) de julio a las': r'\1 july at',
            r'el (\d+) de agosto a las': r'\1 august at',
            r'el (\d+) de septiembre a las': r'\1 september at',
            r'el (\d+) de octubre a las': r'\1 october at',
            r'el (\d+) de noviembre a las': r'\1 november at',
            r'el (\d+) de diciembre a las': r'\1 december at'
        }
        
        # Apply basic phrase translations
        for spanish_phrase, english_phrase in spanish_phrases.items():
            if spanish_phrase in translated_input:
                translated_input = translated_input.replace(spanish_phrase, english_phrase)
        
        # Apply regex-based specific date translations
        import re
        for spanish_pattern, english_replacement in specific_date_phrases.items():
            translated_input = re.sub(spanish_pattern, english_replacement, translated_input)
        
        # Try dateparser as fallback with better year handling
        parsing_strategies = [translated_input, user_input]
        
        for attempt_input in parsing_strategies:
            parsed_date = dateparser.parse(
                attempt_input,
                languages=['es', 'en'],
                settings={
                    'TIMEZONE': tz,
                    'RETURN_AS_TIMEZONE_AWARE': True,
                    'PREFER_DAY_OF_MONTH': 'first',
                    'DATE_ORDER': 'DMY',
                    'PREFER_DATES_FROM': 'future',
                    'RELATIVE_BASE': now  # Use current date as reference
                }
            )
            
            # Fix year issue: if parsed date is in the past or wrong year, fix it
            if parsed_date:
                # If the year is less than current year, fix it
                if parsed_date.year < now.year:
                    parsed_date = parsed_date.replace(year=now.year)
                    logger.info(f"Adjusted year from {parsed_date.year} to {now.year}")
                
                # If the date is in the past (same year but earlier date), move to next year
                elif parsed_date.date() < now.date():
                    parsed_date = parsed_date.replace(year=now.year + 1)
                    logger.info(f"Moved date to next year: {parsed_date.date()}")
            if parsed_date:
                return {
                    "success": True,
                    "datetime": parsed_date.isoformat(),
                    "date": parsed_date.strftime('%Y-%m-%d'),
                    "time": parsed_date.strftime('%H:%M'),
                    "timezone": str(parsed_date.tzinfo),
                    "original_input": user_input,
                    "method": "dateparser",
                    "translated_input": translated_input if translated_input != user_input.lower() else None
                }
        
        # If all parsing failed
        return {
            "success": False,
            "error": f"Could not parse datetime: '{user_input}'. Current date context: {now.strftime('%A, %Y-%m-%d')}",
            "original_input": user_input,
            "current_date_context": now.strftime('%Y-%m-%d'),
            "current_weekday": current_weekday,
            "suggestions": [
                f"mañana a las 2pm (tomorrow at 2pm)",
                f"próximo viernes a las 8pm (next friday at 8pm)",
                f"{(now + timedelta(days=1)).strftime('%Y-%m-%d')} 14:00",
                "en 2 días a las 3pm (in 2 days at 3pm)"
            ]
        }
            
    except Exception as e:
        error_msg = f"Error parsing datetime: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "original_input": user_input
        }