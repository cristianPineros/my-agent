# WhatsApp Conversational Scheduling Agent

A PydanticAI-based conversational agent for handling appointment scheduling through WhatsApp Business API.

## Features

- 🤖 **Natural Language Understanding**: Book appointments using natural language like "I want to book yoga tomorrow at 3pm"
- 📅 **Calendar Integration**: Check availability and manage bookings
- 💬 **WhatsApp Integration**: Seamless WhatsApp Business API integration with webhook support
- 🔄 **Conversation Context**: Maintains context throughout multi-turn conversations
- 🛡️ **Type Safety**: Built with PydanticAI for robust type safety and validation
- 🧪 **Comprehensive Testing**: TestModel and FunctionModel validation for reliable operation

## Quick Start

### 1. Installation

```bash
# Clone or copy the whatsapp_scheduler directory
cd whatsapp_scheduler

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your actual API keys and configuration
```

Required environment variables:
- `LLM_API_KEY`: OpenAI API key
- `WHATSAPP_API_KEY`: WhatsApp Business API key
- `WHATSAPP_PHONE_ID`: Your WhatsApp Business phone number ID
- `WHATSAPP_BUSINESS_ACCOUNT_ID`: Your WhatsApp Business account ID
- `WHATSAPP_WEBHOOK_TOKEN`: Webhook verification token

### 3. Run Tests

```bash
# Run the test suite
python -m pytest tests/ -v

# Run specific test files
python -m pytest tests/test_agent.py -v
python -m pytest tests/test_tools.py -v
python -m pytest tests/test_webhook.py -v
```

### 4. Start the Webhook Server

```bash
# Start the Flask webhook server
python webhook.py

# Server will run on http://localhost:5000
# Webhook endpoint: http://localhost:5000/webhook
```

### 5. Test the Agent

```python
from whatsapp_scheduler import chat_with_scheduler, create_scheduling_dependencies

# Create dependencies
deps = create_scheduling_dependencies(
    session_id="test_session",
    user_timezone="UTC"
)

# Chat with the agent
response = chat_with_scheduler(
    "I want to book a yoga class tomorrow at 2pm",
    deps
)
print(response)
```

## Architecture

The agent follows PydanticAI best practices with a modular architecture:

```
whatsapp_scheduler/
├── settings.py          # Environment-based configuration
├── providers.py         # LLM model provider abstraction
├── dependencies.py      # Dependency injection for external services
├── agent.py            # Main scheduling agent with tools
├── tools.py            # WhatsApp and Calendar API tools
├── webhook.py          # Flask webhook server
├── tests/              # Comprehensive test suite
├── .env.example        # Environment configuration template
└── requirements.txt    # Python dependencies
```

## Available Tools

The scheduling agent has access to these tools:

- **`check_availability`**: Check calendar availability for specific dates/times
- **`make_booking`**: Create new class bookings
- **`cancel_appointment`**: Cancel existing bookings
- **`view_bookings`**: View client's upcoming appointments
- **`send_message`**: Send WhatsApp messages to clients
- **`parse_date_time`**: Parse natural language date/time expressions

## Conversation Examples

### Booking a Class
```
User: "Hi, I'd like to book a yoga class"
Agent: "I'd be happy to help you book a yoga class! What date and time would work best for you?"

User: "Tomorrow at 3pm would be perfect"
Agent: "Let me check availability for tomorrow at 3pm... I have a yoga slot available with instructor Jane. May I have your name and phone number to complete the booking?"

User: "Sure, I'm John Doe and my number is +1234567890"
Agent: "Perfect! I've booked your yoga class for tomorrow at 3:00 PM with instructor Jane. Your booking ID is BK_20240101_150000. You'll receive a confirmation message shortly!"
```

### Checking Availability
```
User: "What time slots are available next Monday?"
Agent: "Let me check availability for next Monday... I have these slots available:
- 10:00 AM - Yoga with Jane (60 minutes)
- 12:00 PM - Pilates with Mike (45 minutes)  
- 2:00 PM - HIIT Training with Sarah (30 minutes)
- 4:00 PM - Personal Training with Alex (60 minutes)

Which one interests you?"
```

### Cancelling a Booking
```
User: "I need to cancel my appointment for tomorrow"
Agent: "I can help you cancel your appointment. Let me look up your booking for tomorrow... I found your yoga class at 3:00 PM. Would you like me to cancel this booking?"

User: "Yes please"
Agent: "I've successfully cancelled your yoga class for tomorrow at 3:00 PM. Your slot is now available for other clients. Is there anything else I can help you with?"
```

## Class Types

The agent supports these class types:
- **Yoga** (60 minutes)
- **Pilates** (45 minutes)
- **HIIT Training** (30 minutes)
- **Personal Training** (60 minutes)
- **Group Fitness** (45 minutes)

## Development

### Running Tests with TestModel

```python
from pydantic_ai.models.test import TestModel
from whatsapp_scheduler.agent import scheduling_agent
from whatsapp_scheduler.dependencies import create_scheduling_dependencies

# Test with TestModel for rapid development
test_model = TestModel()
deps = create_scheduling_dependencies()

with scheduling_agent.override(model=test_model):
    result = scheduling_agent.run_sync(
        "Book me a yoga class tomorrow at 2pm",
        deps=deps
    )
    print(result.data)
```

### Adding New Tools

To add new tools, define them in `tools.py` and register with the agent in `agent.py`:

```python
@scheduling_agent.tool
async def new_tool(
    ctx: RunContext[SchedulingDependencies],
    parameter: str
) -> str:
    """Your new tool description."""
    # Tool implementation
    return "Tool result"
```

## Security

The agent implements several security measures:
- Environment variable configuration for API keys
- Webhook signature verification
- Input validation and sanitization
- Rate limiting for API protection
- Secure logging without exposing sensitive data

## Production Deployment

For production deployment:

1. Set `APP_ENV=production` in your `.env` file
2. Use a production WSGI server like Gunicorn:
   ```bash
   gunicorn webhook:app --bind 0.0.0.0:5000
   ```
3. Configure HTTPS for webhook endpoints
4. Set up proper database (PostgreSQL recommended)
5. Implement monitoring and logging
6. Configure proper rate limiting

## Contributing

1. Follow PydanticAI best practices
2. Add tests for new features
3. Use TestModel for development validation
4. Keep tools focused and simple
5. Maintain type safety throughout

## License

MIT License - see LICENSE file for details.