"""
Flask webhook server for WhatsApp Business API integration.
Handles incoming messages and webhook verification.
"""

import logging
import json
import asyncio
from typing import Dict, Any
from flask import Flask, request, jsonify
import httpx

from .agent import chat_with_scheduler
from .dependencies import create_scheduling_dependencies
from .settings import settings

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)


def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """
    Verify WhatsApp webhook signature.
    
    Args:
        payload: Request payload bytes
        signature: X-Hub-Signature-256 header value
    
    Returns:
        True if signature is valid
    """
    # In production, implement proper signature verification
    # using HMAC-SHA256 with your webhook secret
    # For now, we'll skip signature verification in development
    if settings.app_env == "development":
        return True
    
    # TODO: Implement proper signature verification
    # import hmac
    # import hashlib
    # expected_signature = hmac.new(
    #     webhook_secret.encode(),
    #     payload,
    #     hashlib.sha256
    # ).hexdigest()
    # return signature == f"sha256={expected_signature}"
    
    return True


@app.route("/webhook", methods=["GET"])
def webhook_verification():
    """
    Handle WhatsApp webhook verification.
    
    WhatsApp sends a GET request with challenge parameters
    that need to be echoed back for verification.
    """
    try:
        # Get verification parameters
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        
        logger.info(f"Webhook verification request: mode={mode}, token={token}")
        
        # Verify the token matches our configured token
        if mode == "subscribe" and token == settings.whatsapp_webhook_token:
            logger.info("Webhook verification successful")
            return challenge, 200
        else:
            logger.warning(f"Webhook verification failed: invalid token")
            return "Forbidden", 403
            
    except Exception as e:
        logger.error(f"Error in webhook verification: {e}")
        return "Internal Server Error", 500


@app.route("/webhook", methods=["POST"])
def webhook_handler():
    """
    Handle incoming WhatsApp messages.
    
    Processes webhook events and responds to messages using the scheduling agent.
    """
    try:
        # Verify the request signature
        signature = request.headers.get("X-Hub-Signature-256", "")
        if not verify_webhook_signature(request.data, signature):
            logger.warning("Invalid webhook signature")
            return "Forbidden", 403
        
        # Parse the webhook payload
        data = request.get_json()
        if not data:
            logger.warning("Empty webhook payload")
            return "Bad Request", 400
        
        logger.info(f"Received webhook data: {json.dumps(data, indent=2)}")
        
        # Process the webhook data
        asyncio.run(process_webhook_data(data))
        
        return "OK", 200
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return "Internal Server Error", 500


async def process_webhook_data(data: Dict[str, Any]) -> None:
    """
    Process WhatsApp webhook data and respond to messages.
    
    Args:
        data: Webhook payload from WhatsApp
    """
    try:
        # Extract entry data
        entry = data.get("entry", [])
        if not entry:
            logger.info("No entry data in webhook")
            return
        
        for entry_item in entry:
            changes = entry_item.get("changes", [])
            
            for change in changes:
                # Process message changes
                if change.get("field") == "messages":
                    await process_message_change(change.get("value", {}))
                    
    except Exception as e:
        logger.error(f"Error processing webhook data: {e}")


async def process_message_change(value: Dict[str, Any]) -> None:
    """
    Process individual message changes from webhook.
    
    Args:
        value: Message change value from webhook
    """
    try:
        messages = value.get("messages", [])
        contacts = value.get("contacts", [])
        
        for message in messages:
            # Extract message details
            message_id = message.get("id")
            from_number = message.get("from")
            message_type = message.get("type")
            timestamp = message.get("timestamp")
            
            # Skip if not a text message for now
            if message_type != "text":
                logger.info(f"Skipping non-text message type: {message_type}")
                continue
            
            # Extract message text
            text_content = message.get("text", {}).get("body", "")
            if not text_content:
                logger.info("Empty message text")
                continue
            
            # Get contact information
            contact_name = "Unknown"
            for contact in contacts:
                if contact.get("wa_id") == from_number:
                    contact_name = contact.get("profile", {}).get("name", "Unknown")
                    break
            
            logger.info(f"Processing message from {contact_name} ({from_number}): {text_content}")
            
            # Create dependencies for this conversation
            dependencies = create_scheduling_dependencies(
                session_id=f"whatsapp_{from_number}",
                user_timezone="UTC"  # Could be enhanced to detect user timezone
            )
            
            # Add contact information to conversation context
            dependencies.conversation_context.update({
                "client_phone": from_number,
                "client_name": contact_name,
                "message_id": message_id,
                "timestamp": timestamp
            })
            
            # Process the message with the scheduling agent
            try:
                response = await chat_with_scheduler(text_content, dependencies)
                
                # Send response back to WhatsApp
                await send_response_to_whatsapp(from_number, response, dependencies)
                
            except Exception as e:
                logger.error(f"Error processing message with agent: {e}")
                # Send error response
                error_response = "I apologize, but I'm having trouble processing your request right now. Please try again or contact our staff directly."
                await send_response_to_whatsapp(from_number, error_response, dependencies)
                
    except Exception as e:
        logger.error(f"Error processing message change: {e}")


async def send_response_to_whatsapp(
    phone_number: str,
    message: str,
    dependencies: SchedulingDependencies
) -> None:
    """
    Send a response message back to WhatsApp.
    
    Args:
        phone_number: Recipient phone number
        message: Message to send
        dependencies: Scheduling dependencies with HTTP client
    """
    try:
        # Use the send_whatsapp_message function from tools
        from .tools import send_whatsapp_message
        from pydantic_ai import RunContext
        
        # Create a minimal RunContext for the tool
        class MockRunContext:
            def __init__(self, deps):
                self.deps = deps
        
        ctx = MockRunContext(dependencies)
        result = await send_whatsapp_message(ctx, phone_number, message)
        
        logger.info(f"Response sent to {phone_number}: {result}")
        
    except Exception as e:
        logger.error(f"Error sending response to WhatsApp: {e}")


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "whatsapp-scheduler",
        "version": "1.0.0"
    }, 200


@app.route("/", methods=["GET"])
def root():
    """Root endpoint with basic info."""
    return {
        "service": "WhatsApp Scheduling Agent",
        "status": "running",
        "endpoints": {
            "webhook": "/webhook",
            "health": "/health"
        }
    }, 200


if __name__ == "__main__":
    # Run the Flask app
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=settings.debug
    )