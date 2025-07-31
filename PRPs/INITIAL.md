## FEATURE:
Build a WhatsApp conversational agent using Pydantic AI that interacts with clients through natural language to schedule, reschedule, and manage class appointments. The agent should understand client requests, check availability, handle scheduling conflicts, send confirmations, and integrate with a calendar system. The agent should maintain conversation context, handle multiple scheduling requests in a single conversation, and provide a friendly, professional experience for clients booking classes.
## TOOLS:

check_calendar_availability

Arguments: date (string), time_range (optional tuple of start/end times), instructor (optional string)
Returns: List of available time slots with instructor names
Functionality: Queries the calendar API to find open slots


book_class

Arguments: client_name (string), client_phone (string), date (string), time (string), class_type (string), instructor (optional string), notes (optional string)
Returns: Booking confirmation with unique booking ID
Functionality: Creates a calendar event and stores booking details


cancel_booking

Arguments: booking_id (string) or client_phone + date + time
Returns: Cancellation confirmation
Functionality: Removes the booking from calendar and updates availability


get_client_bookings

Arguments: client_phone (string), date_range (optional)
Returns: List of upcoming bookings for the client
Functionality: Retrieves all future bookings for a specific client


send_whatsapp_message

Arguments: to_number (string), message (string), template_type (optional enum: confirmation/reminder/cancellation)
Returns: Message delivery status
Functionality: Sends formatted WhatsApp messages using WhatsApp Business API


parse_datetime_natural

Arguments: user_input (string), timezone (optional string)
Returns: Structured datetime object
Functionality: Converts natural language time expressions ("tomorrow at 3pm", "next Tuesday morning") to datetime



## DEPENDENCIES

WhatsApp Business API credentials: API key, phone number ID, business account ID
Calendar API connection: Google Calendar API credentials or CalDAV connection details
HTTP client: For making API calls to WhatsApp and calendar services
Database connection: PostgreSQL or SQLite for storing booking history and client preferences
Redis connection (optional): For caching availability and session management
Timezone library: pytz for handling timezone conversions
Environment variables:

WHATSAPP_API_KEY
WHATSAPP_PHONE_ID
CALENDAR_API_KEY
DATABASE_URL
REDIS_URL (optional)
DEFAULT_TIMEZONE



## SYSTEM PROMPT(S)
You are a friendly and efficient scheduling assistant for [Business Name]. Your role is to help clients book, reschedule, and manage their class appointments through WhatsApp.
Key responsibilities:

Greet clients warmly and professionally
Understand scheduling requests in natural language
Check availability and suggest suitable time slots
Handle booking confirmations and send details
Manage rescheduling and cancellations
Answer basic questions about class types, duration, and instructors
Maintain conversation context throughout the interaction

Guidelines:

Always confirm the details before finalizing a booking
Offer 3-5 available time slots when possible
Be proactive about potential scheduling conflicts
Use the client's timezone for all communications
Send confirmation messages with all relevant details
Be concise but thorough in responses
Handle edge cases gracefully (no availability, last-minute changes)

You should NOT:

Discuss pricing or payment (redirect to staff)
Make changes to instructor schedules
Share other clients' information
Book outside of business hours without special authorization

## EXAMPLES:

examples/basic_chat_agent - Basic chat agent with conversation memory
examples/tool_enabled_agent - Tool-enabled agent with web search capabilities
examples/structured_output_agent - Structured output agent for data validation
examples/testing_examples - Testing examples with TestModel and FunctionModel
examples/main_agent_reference - Best practices for building Pydantic AI agents
examples/whatsapp_webhook_handler - Example webhook integration for WhatsApp Business API
examples/calendar_integration - Google Calendar API integration patterns
examples/appointment_scheduler - Reference implementation of appointment scheduling logic

## DOCUMENTATION:

Pydantic AI Official Documentation: https://ai.pydantic.dev/
Agent Creation Guide: https://ai.pydantic.dev/agents/
Tool Integration: https://ai.pydantic.dev/tools/
Testing Patterns: https://ai.pydantic.dev/testing/
Model Providers: https://ai.pydantic.dev/models/
WhatsApp Business API: https://developers.facebook.com/docs/whatsapp/business-management-api
Google Calendar API: https://developers.google.com/calendar/api/v3/reference
Natural Language Date Parsing: https://dateparser.readthedocs.io/

## OTHER CONSIDERATIONS:

Use environment variables for API key configuration instead of hardcoded model strings
Keep agents simple - default to string output unless structured output is specifically needed
Follow the main_agent_reference patterns for configuration and providers
Always include comprehensive testing with TestModel for development
Implement rate limiting for WhatsApp API calls to avoid hitting limits
Store conversation history for context management (consider 24-hour window)
Handle WhatsApp message delivery failures gracefully with retry logic
Implement proper error handling for calendar API failures
Consider implementing a queue system for handling multiple simultaneous booking requests
Add logging for all booking transactions for audit purposes
Ensure GDPR/privacy compliance for storing client phone numbers and conversation data
Implement business hours validation to prevent out-of-hours bookings
Consider adding multi-language support based on client preferences
Cache frequently accessed calendar data to improve response times