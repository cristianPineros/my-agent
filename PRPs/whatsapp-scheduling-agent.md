---
name: "WhatsApp Conversational Scheduling Agent PRP"
description: "Comprehensive PRP for building a WhatsApp conversational agent using PydanticAI for appointment scheduling and management"
---

## Purpose

Build a WhatsApp conversational agent using PydanticAI that interacts with clients through natural language to schedule, reschedule, and manage class appointments. The agent will understand client requests, check availability, handle scheduling conflicts, send confirmations, and integrate with a calendar system while maintaining conversation context and providing a friendly, professional experience.

## Core Principles

1. **PydanticAI Best Practices**: Deep integration with PydanticAI patterns for agent creation, tools, and structured outputs
2. **Production Ready**: Include security, testing, and monitoring for production deployments
3. **Type Safety First**: Leverage PydanticAI's type-safe design and Pydantic validation throughout
4. **Context Engineering Integration**: Apply proven context engineering workflows to AI agent development
5. **Comprehensive Testing**: Use TestModel and FunctionModel for thorough agent validation

## ⚠️ Implementation Guidelines: Don't Over-Engineer

**IMPORTANT**: Keep your agent implementation focused and practical. Don't build unnecessary complexity.

### What NOT to do:
- ❌ **Don't create dozens of tools** - Build only the tools your agent actually needs
- ❌ **Don't over-complicate dependencies** - Keep dependency injection simple and focused
- ❌ **Don't add unnecessary abstractions** - Follow main_agent_reference patterns directly
- ❌ **Don't build complex workflows** unless specifically required
- ❌ **Don't add structured output** unless validation is specifically needed (default to string)

### What TO do:
- ✅ **Start simple** - Build the minimum viable agent that meets requirements
- ✅ **Add tools incrementally** - Implement only what the agent needs to function
- ✅ **Follow main_agent_reference** - Use proven patterns, don't reinvent
- ✅ **Use string output by default** - Only add result_type when validation is required
- ✅ **Test early and often** - Use TestModel to validate as you build

### Key Question:
**"Does this agent really need this feature to accomplish its core purpose?"**

If the answer is no, don't build it. Keep it simple, focused, and functional.

---

## Goal

Create a production-ready WhatsApp conversational agent that enables clients to book, reschedule, and manage class appointments through natural language conversations. The agent should handle multiple scheduling requests in a single conversation, check calendar availability, manage booking conflicts, send confirmations via WhatsApp, and maintain professional conversation context throughout the interaction.

## Why

Current appointment scheduling often requires clients to call during business hours or use complex online booking systems. A WhatsApp conversational agent provides a familiar, accessible interface that clients can use 24/7 to manage their appointments using natural language, reducing friction and improving customer experience while automating routine scheduling tasks.

## What

### Agent Type Classification
- [x] **Chat Agent**: Conversational interface with memory and context
- [x] **Tool-Enabled Agent**: Agent with external tool integration capabilities
- [ ] **Workflow Agent**: Multi-step task processing and orchestration
- [ ] **Structured Output Agent**: Complex data validation and formatting

### Model Provider Requirements
- [x] **OpenAI**: `openai:gpt-4o` or `openai:gpt-4o-mini`
- [x] **Anthropic**: `anthropic:claude-3-5-sonnet-20241022` or `anthropic:claude-3-5-haiku-20241022`
- [ ] **Google**: `gemini-1.5-flash` or `gemini-1.5-pro`
- [x] **Fallback Strategy**: Multiple provider support with automatic failover

### External Integrations
- [x] WhatsApp Business API (webhooks, message sending)
- [x] Google Calendar API (availability checking, event creation)
- [x] Database connections (PostgreSQL or SQLite for booking history)
- [ ] Redis connection (optional for caching and session management)
- [x] Natural language date parsing (dateparser library)

### Success Criteria
- [x] Agent successfully handles scheduling conversations in natural language
- [x] All tools work correctly with proper error handling
- [x] WhatsApp webhook integration works reliably
- [x] Calendar integration manages availability and bookings accurately
- [x] Comprehensive test coverage with TestModel and FunctionModel
- [x] Security measures implemented (API keys, input validation, rate limiting)
- [x] Performance meets requirements (sub-5 second response time)

## All Needed Context

### PydanticAI Documentation & Research

**ESSENTIAL PYDANTIC AI DOCUMENTATION - Researched and Available:**

- **url**: https://ai.pydantic.dev/
  **content**: Core framework understanding - model-agnostic design supporting OpenAI, Anthropic, Gemini; type-safe agent development with Pydantic validation; dependency injection for flexible agent configuration

- **url**: https://ai.pydantic.dev/agents/
  **content**: Agent architecture patterns - system prompts (static/dynamic), dependency injection via RunContext, execution modes (run/run_sync/run_stream), error handling and retry mechanisms

- **url**: https://ai.pydantic.dev/tools/
  **content**: Tool integration patterns - @agent.tool decorators with RunContext access, parameter validation, automatic schema generation, error handling with ModelRetry

- **url**: https://ai.pydantic.dev/testing/
  **content**: Testing strategies - TestModel for development validation, FunctionModel for custom behavior, Agent.override() for test isolation, pytest patterns

- **url**: https://ai.pydantic.dev/models/
  **content**: Model provider configuration - OpenAI, Anthropic, Gemini setup, API key management, fallback models, authentication patterns

### Agent Architecture Research

**PydanticAI Architecture Patterns (following main_agent_reference):**

**Configuration Structure:**
- `settings.py`: Environment-based configuration with pydantic-settings and python-dotenv
- `providers.py`: Model provider abstraction with get_llm_model() function
- Environment variables for API keys and model selection (never hardcode model strings)

**Agent Definition Patterns:**
- Default to string output (no result_type unless structured output needed)
- Use get_llm_model() from providers.py for model configuration
- System prompts as string constants or dynamic functions
- Dataclass dependencies for external services (WhatsAppDependencies, CalendarDependencies)

**Tool Integration Patterns:**
- `@agent.tool` for context-aware tools with RunContext[DepsType]
- Tool functions as pure functions that can be called independently
- Proper error handling and logging in tool implementations
- Dependency injection through RunContext.deps

**Testing Strategy Patterns:**
- TestModel for rapid development validation without API calls
- FunctionModel for custom behavior testing and controlled responses
- Agent.override() for test isolation and mock dependencies
- Comprehensive tool testing with mocks for external services

### WhatsApp Business API Integration Research

**Flask Webhook Server Pattern (Primary Approach):**
- Flask application handling POST requests from WhatsApp webhooks
- Webhook verification using challenge/verify_token mechanism
- Message processing for text, audio, and media types
- Rate limiting to prevent API quota exhaustion
- HTTPS requirement for webhook endpoints

**Authentication & Security:**
- WhatsApp Business API credentials: API key, phone number ID, business account ID
- Webhook verification token for secure message receiving
- HTTPS endpoints required for webhook configuration
- Request signature validation for message authenticity

**Message Handling Patterns:**
- Incoming message processing with message ID tracking
- Outgoing message sending with template support
- Message status tracking (sent, delivered, read, failed)
- Media message handling (images, documents, audio)

**Integration Libraries:**
- Flask for webhook server implementation
- `requests` or `httpx` for WhatsApp API calls
- WhatsApp Cloud API (preferred over legacy Business API)

### Google Calendar API Integration Research

**API Limitations and Approach:**
- No direct API for appointment scheduling feature (manual-only)
- Use standard Calendar API v3 for event creation and management
- Custom availability checking by querying existing events
- Event creation with proper attendee management and notifications

**Integration Patterns:**
- Service account authentication for automated access
- Calendar sharing with service account for full access
- Event creation with conflict detection and resolution
- Automated reminder configuration and management

**Key Implementation Features:**
- Smart availability checking across multiple calendars
- Automated invitation management and RSVP tracking
- Timezone handling for accurate scheduling
- Recurrence pattern support for recurring appointments

### Natural Language Date Parsing Research

**Dateparser Library (Primary Choice):**
- Supports 200+ language locales and numerous formats
- Handles relative dates: "tomorrow", "next Tuesday", "in 2 hours"
- Timezone abbreviation support: "EST", "PST", "+0500"
- Multi-language support: English, Spanish, French, etc.

**Usage Patterns:**
```python
import dateparser
dateparser.parse('tomorrow at 3pm')  # Returns datetime object
dateparser.parse('next Tuesday morning')  # Handles relative dates
dateparser.parse('in 30 minutes')  # Supports duration-based parsing
```

**Integration Approach:**
- Create parse_datetime_natural tool using dateparser library
- Handle timezone conversion based on business location
- Fallback to asking for clarification on ambiguous dates
- Store user timezone preferences for accurate parsing

### Security and Production Considerations

**PydanticAI Security Patterns:**

**API Management:**
- Environment variables: OPENAI_API_KEY, ANTHROPIC_API_KEY, WHATSAPP_API_KEY, CALENDAR_API_KEY
- Secure storage using python-dotenv with .env files
- Never commit API keys to version control
- Key rotation strategy and management

**Input Validation:**
- Sanitize all user inputs with Pydantic models
- Prevent prompt injection through input validation
- Rate limiting to prevent abuse (per phone number)
- Message content filtering and validation

**Output Security:**
- Ensure no sensitive data in agent responses
- Safe logging without exposing secrets or personal information
- Content validation before sending WhatsApp messages
- Error message sanitization to prevent information leakage

### Common PydanticAI Gotchas (Researched and Documented)

**Async Patterns:**
- Issue: Mixing sync and async agent calls inconsistently
- Solution: Use async patterns throughout for WhatsApp webhook handling and Calendar API calls
- Pattern: `await agent.run()` for async, `agent.run_sync()` for sync contexts

**Model Limits:**
- Issue: Different models have different capabilities and token limits
- Solution: Configure fallback models (OpenAI GPT-4o → GPT-4o-mini → Anthropic Claude)
- Pattern: Model provider abstraction in providers.py handles fallbacks

**Dependency Complexity:**
- Issue: Complex dependency graphs can be hard to debug
- Solution: Keep dependencies simple with clear dataclass structures
- Pattern: WhatsAppDependencies, CalendarDependencies as separate, focused classes

**Tool Error Handling:**
- Issue: Tool failures can crash entire agent runs
- Solution: Comprehensive try/catch in all tools with graceful degradation
- Pattern: Return error messages that allow agent to continue conversation

## Implementation Blueprint

### Technology Research Phase

**RESEARCH COMPLETED - Implementation Ready:**

✅ **PydanticAI Framework Deep Dive:**
- [x] Agent creation patterns using main_agent_reference approach
- [x] Model provider configuration with fallback strategies (OpenAI → Anthropic)
- [x] Tool integration patterns (@agent.tool with RunContext[DepsType])
- [x] Dependency injection system with dataclasses for type safety
- [x] Testing strategies with TestModel and FunctionModel

✅ **Agent Architecture Investigation:**
- [x] Project structure conventions (agent.py, tools.py, models.py, dependencies.py, settings.py, providers.py)
- [x] System prompt design (static conversational prompt for scheduling)
- [x] String output (no structured output needed for conversational agent)
- [x] Async/sync patterns for webhook handling
- [x] Error handling and retry mechanisms for external API calls

✅ **Security and Production Patterns:**
- [x] API key management with python-dotenv and pydantic-settings
- [x] Input validation and prompt injection prevention strategies
- [x] Rate limiting patterns for WhatsApp API and Calendar API
- [x] Logging and observability patterns without exposing sensitive data
- [x] Webhook security with signature verification and HTTPS

### Agent Implementation Plan

```yaml
Implementation Task 1 - Agent Architecture Setup (Follow main_agent_reference):
  CREATE agent project structure:
    - settings.py: Environment configuration with WhatsApp and Calendar API keys
    - providers.py: Model provider abstraction with get_llm_model() and fallback
    - agent.py: Main scheduling agent definition (string output)
    - tools.py: WhatsApp and Calendar integration tools
    - dependencies.py: WhatsAppDependencies and CalendarDependencies dataclasses
    - webhook.py: Flask webhook server for WhatsApp integration
    - tests/: Comprehensive test suite with TestModel patterns

Implementation Task 2 - Core Agent Development:
  IMPLEMENT agent.py following main_agent_reference patterns:
    - Use get_llm_model() from providers.py for model configuration
    - System prompt optimized for appointment scheduling conversations
    - Dependencies combining WhatsApp and Calendar access
    - String output (conversational, no structured validation needed)
    - Error handling and graceful conversation recovery

Implementation Task 3 - WhatsApp Integration:
  IMPLEMENT webhook.py and WhatsApp tools:
    - Flask webhook server with verification and security
    - send_whatsapp_message tool with template support
    - Message processing with conversation context tracking
    - Rate limiting and error handling for API quota management
    - HTTPS webhook endpoint configuration

Implementation Task 4 - Calendar Integration:
  IMPLEMENT Calendar API tools:
    - check_calendar_availability tool with conflict detection
    - book_class tool with event creation and invitations
    - cancel_booking tool with proper calendar cleanup
    - get_client_bookings tool for appointment history
    - Timezone handling and recurring appointment support

Implementation Task 5 - Natural Language Processing:
  IMPLEMENT date parsing and validation:
    - parse_datetime_natural tool using dateparser library
    - Timezone conversion and business hours validation
    - Ambiguous date clarification handling
    - Multi-language support for common scheduling phrases

Implementation Task 6 - Comprehensive Testing:
  IMPLEMENT testing suite:
    - TestModel integration for agent conversation validation
    - FunctionModel tests for specific scheduling scenarios
    - Tool testing with mocked WhatsApp and Calendar APIs
    - Webhook endpoint testing with simulated WhatsApp requests
    - Integration tests with full conversation flows

Implementation Task 7 - Security and Production:
  SETUP production patterns:
    - Environment variable management for all API keys
    - Input sanitization and validation for all user messages
    - Rate limiting implementation for API protection
    - Secure logging without exposing personal information
    - Webhook signature verification and HTTPS enforcement
```

## Validation Loop

### Level 1: Agent Structure Validation

```bash
# Verify complete agent project structure
find whatsapp_scheduler -name "*.py" | sort
test -f whatsapp_scheduler/agent.py && echo "Agent definition present"
test -f whatsapp_scheduler/tools.py && echo "Tools module present"
test -f whatsapp_scheduler/dependencies.py && echo "Dependencies module present"
test -f whatsapp_scheduler/webhook.py && echo "Webhook server present"
test -f whatsapp_scheduler/settings.py && echo "Settings module present"
test -f whatsapp_scheduler/providers.py && echo "Providers module present"

# Verify proper PydanticAI imports
grep -q "from pydantic_ai import Agent" whatsapp_scheduler/agent.py
grep -q "@agent.tool" whatsapp_scheduler/tools.py
grep -q "from pydantic_settings import BaseSettings" whatsapp_scheduler/settings.py

# Expected: All required files with proper PydanticAI patterns
# If missing: Generate missing components with correct patterns
```

### Level 2: Agent Functionality Validation

```bash
# Test agent can be imported and instantiated
python -c "
from whatsapp_scheduler.agent import scheduling_agent
print('Agent created successfully')
print(f'Model: {scheduling_agent.model}')
print(f'Tools: {len(scheduling_agent.tools)}')
"

# Test with TestModel for validation
python -c "
from pydantic_ai.models.test import TestModel
from whatsapp_scheduler.agent import scheduling_agent
test_model = TestModel()
with scheduling_agent.override(model=test_model):
    result = scheduling_agent.run_sync('I want to book a class tomorrow at 3pm')
    print(f'Agent response: {result.data}')
"

# Expected: Agent instantiation works, tools registered, TestModel validation passes
# If failing: Debug agent configuration and tool registration
```

### Level 3: WhatsApp Integration Validation

```bash
# Test webhook server starts correctly
python -c "
from whatsapp_scheduler.webhook import app
print('Webhook server configuration valid')
print(f'Routes: {[rule.rule for rule in app.url_map.iter_rules()]}')
"

# Test WhatsApp API configuration
python -c "
from whatsapp_scheduler.settings import settings
print(f'WhatsApp API configured: {bool(settings.whatsapp_api_key)}')
print(f'Phone ID configured: {bool(settings.whatsapp_phone_id)}')
"

# Expected: Webhook server starts, WhatsApp API configured
# If failing: Check environment variables and API configuration
```

### Level 4: Calendar Integration Validation

```bash
# Test Calendar API authentication
python -c "
from whatsapp_scheduler.tools import check_calendar_availability
print('Calendar API authentication configured')
"

# Test basic calendar operations
python -c "
from whatsapp_scheduler.dependencies import CalendarDependencies
deps = CalendarDependencies()
print(f'Calendar API configured: {bool(deps.calendar_api_key)}')
"

# Expected: Calendar API authentication works
# If failing: Check Google Calendar API setup and service account
```

### Level 5: Comprehensive Testing Validation

```bash
# Run complete test suite
cd whatsapp_scheduler
python -m pytest tests/ -v

# Test specific agent behavior
python -m pytest tests/test_agent.py::test_scheduling_conversation -v
python -m pytest tests/test_tools.py::test_calendar_booking -v
python -m pytest tests/test_webhook.py::test_webhook_verification -v

# Expected: All tests pass, comprehensive coverage achieved
# If failing: Fix implementation based on test failures
```

### Level 6: Production Readiness Validation

```bash
# Verify security patterns
grep -r "API_KEY" whatsapp_scheduler/ | grep -v ".py:" # Should not expose keys
test -f whatsapp_scheduler/.env.example && echo "Environment template present"

# Check error handling
grep -r "try:" whatsapp_scheduler/ | wc -l  # Should have error handling
grep -r "except" whatsapp_scheduler/ | wc -l  # Should have exception handling

# Verify logging setup
grep -r "logging\|logger" whatsapp_scheduler/ | wc -l  # Should have logging

# Test webhook security
curl -X POST http://localhost:5000/webhook -d '{"test": "invalid"}' -H "Content-Type: application/json"
# Expected: Should reject invalid requests

# Expected: Security measures in place, error handling comprehensive, logging configured
# If issues: Implement missing security and production patterns
```

## Final Validation Checklist

### Agent Implementation Completeness

- [x] Complete agent project structure: `agent.py`, `tools.py`, `dependencies.py`, `webhook.py`, `settings.py`, `providers.py`
- [x] Agent instantiation with proper model provider configuration and fallback
- [x] Tool registration with @agent.tool decorators and RunContext integration
- [x] String output with conversational responses (no structured output needed)
- [x] Dependency injection properly configured for WhatsApp and Calendar APIs
- [x] Comprehensive test suite with TestModel and FunctionModel

### PydanticAI Best Practices

- [x] Type safety throughout with proper type hints and validation
- [x] Security patterns implemented (API keys via environment, input validation, rate limiting)
- [x] Error handling and retry mechanisms for robust operation
- [x] Async patterns consistent for webhook and API integration
- [x] Documentation and code comments for maintainability

### WhatsApp Integration Completeness

- [x] Flask webhook server with proper verification and security
- [x] Message sending with template support and rate limiting
- [x] Conversation context tracking and memory management
- [x] Media message handling and error recovery
- [x] HTTPS webhook endpoint configuration

### Calendar Integration Completeness

- [x] Google Calendar API authentication and service account setup
- [x] Availability checking with conflict detection and resolution
- [x] Event creation with proper attendee management
- [x] Booking cancellation and modification support
- [x] Timezone handling and business hours validation

### Production Readiness

- [x] Environment configuration with .env files and validation
- [x] Logging and monitoring setup for observability
- [x] Performance optimization and resource management
- [x] Security measures for API protection and data privacy
- [x] Deployment readiness with Docker and production configuration

---

## Anti-Patterns to Avoid

### PydanticAI Agent Development

- ❌ Don't skip TestModel validation - always test with TestModel during development
- ❌ Don't hardcode API keys - use environment variables for all credentials
- ❌ Don't ignore async patterns - WhatsApp webhooks require consistent async handling
- ❌ Don't create overly complex tool chains - keep tools focused and composable
- ❌ Don't skip error handling - implement comprehensive retry and fallback mechanisms

### WhatsApp Integration

- ❌ Don't ignore webhook verification - always validate WhatsApp signatures
- ❌ Don't expose sensitive data - sanitize all outgoing messages
- ❌ Don't exceed rate limits - implement proper throttling and queue management
- ❌ Don't ignore message status - track delivery and read receipts

### Calendar Integration

- ❌ Don't ignore timezone complexities - handle timezones consistently
- ❌ Don't create booking conflicts - always check availability before booking
- ❌ Don't skip calendar permissions - ensure proper service account access
- ❌ Don't ignore recurring events - handle recurring appointment patterns

### Security and Production

- ❌ Don't expose sensitive data - validate all outputs and logs for security
- ❌ Don't skip input validation - sanitize and validate all user inputs
- ❌ Don't ignore rate limiting - implement proper throttling for external services
- ❌ Don't deploy without monitoring - include proper observability from the start

**RESEARCH STATUS: COMPLETED** - Comprehensive PydanticAI, WhatsApp API, Calendar API, and dateparser research completed. Implementation ready with detailed patterns and examples.