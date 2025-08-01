#!/usr/bin/env python3
"""
Terminal chat interface for testing the WhatsApp scheduling agent.
Test AI provider and calendar integration without WhatsApp.
"""

import asyncio
import sys
import os
import uuid
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import agent
import dependencies
from providers import get_model_info

class TerminalChat:
    """Interactive terminal chat interface for testing the agent."""
    
    def __init__(self):
        self.session_id = str(uuid.uuid4())[:8]
        self.user_timezone = "America/Bogota"
        self.deps = None
        self.chat_history = []
        self.conversation_messages = []  # Store full conversation for context
    
    def print_header(self):
        """Print chat interface header."""
        model_info = get_model_info()
        print("🤖 WHATSAPP SCHEDULING AGENT - TERMINAL CHAT")
        print("=" * 50)
        print(f"🔧 Provider: {model_info['llm_provider']}")
        print(f"🧠 Model: {model_info['llm_model']}")
        print(f"📅 Calendar: {'✅ Enabled' if os.path.exists('credentials.json') else '❌ Not configured'}")
        print(f"🆔 Session: {self.session_id}")
        print("=" * 50)
        print("💡 Commands:")
        print("  /help     - Show available commands")
        print("  /calendar - Test calendar connection")
        print("  /provider - Show provider info")
        print("  /history  - Show chat history")
        print("  /clear    - Clear chat history")
        print("  /quit     - Exit chat")
        print("=" * 50)
        print("💬 Start chatting! Try: 'I want to book an appointment tomorrow at 2pm'")
        print()
    
    def print_help(self):
        """Print help information."""
        print("\n📚 HELP - What you can do:")
        print("-" * 30)
        print("📅 Schedule appointments:")
        print("  • 'Book me a meeting tomorrow at 3pm'")
        print("  • 'What times are available on Monday?'")
        print("  • 'Cancel my appointment on Friday'")
        print()
        print("📋 Check availability:")
        print("  • 'Show my calendar for next week'")
        print("  • 'Am I free on Tuesday morning?'")
        print("  • 'What meetings do I have today?'")
        print()
        print("⚙️  System commands:")
        print("  • /calendar - Test Google Calendar connection")
        print("  • /provider - Show AI provider details")
        print("  • /history  - View conversation history")
        print("  • /clear    - Clear conversation history")
        print("  • /quit     - Exit the chat")
        print()
    
    async def test_calendar_connection(self):
        """Test Google Calendar connection."""
        print("\n📅 TESTING CALENDAR CONNECTION")
        print("-" * 30)
        
        try:
            from tools import get_calendar_events
            
            # Test calendar authentication and connection
            print("🔐 Checking calendar credentials...")
            
            if not os.path.exists('credentials.json'):
                print("❌ credentials.json not found")
                print("💡 To set up Google Calendar:")
                print("   1. Go to Google Cloud Console")
                print("   2. Create a project and enable Calendar API")
                print("   3. Download credentials.json")
                return
            
            print("✅ credentials.json found")
            
            # Try to get today's events
            print("📊 Testing calendar API access...")
            from datetime import datetime, timedelta
            
            start_time = datetime.now().isoformat() + 'Z'
            end_time = (datetime.now() + timedelta(days=1)).isoformat() + 'Z'
            
            events = await get_calendar_events(
                start_time=start_time,
                end_time=end_time,
                max_results=5
            )
            
            print(f"✅ Calendar API working! Found {len(events)} events for today")
            
            if events:
                print("\n📋 Today's events:")
                for event in events[:3]:  # Show first 3 events
                    summary = event.get('summary', 'No title')
                    start = event.get('start', {}).get('dateTime', 'No time')
                    print(f"  • {summary} at {start[:16]}")
            else:
                print("📭 No events found for today")
                
        except Exception as e:
            print(f"❌ Calendar test failed: {e}")
            print("💡 Make sure you've set up Google Calendar API credentials")
    
    def show_provider_info(self):
        """Show AI provider information."""
        print("\n🤖 AI PROVIDER INFORMATION")
        print("-" * 25)
        
        try:
            model_info = get_model_info()
            print(f"🔧 Provider: {model_info['llm_provider']}")
            print(f"🧠 Model: {model_info['llm_model']}")
            print(f"🌐 Base URL: {model_info.get('llm_base_url', 'N/A')}")
            print(f"🔧 Environment: {model_info.get('app_env', 'N/A')}")
            print(f"🔄 Fallback: {'✅' if model_info.get('fallback_enabled') else '❌'}")
            
            # Test model creation
            from providers import get_llm_model
            model = get_llm_model()
            print(f"✅ Model created: {type(model).__name__}")
            
        except Exception as e:
            print(f"❌ Provider info error: {e}")
    
    def show_history(self):
        """Show chat history."""
        print("\n📚 CHAT HISTORY")
        print("-" * 15)
        
        if not self.chat_history:
            print("📭 No messages yet")
            return
        
        for i, (user_msg, agent_response, timestamp) in enumerate(self.chat_history, 1):
            print(f"\n{i}. [{timestamp}]")
            print(f"👤 You: {user_msg}")
            print(f"🤖 Agent: {agent_response}")
    
    def clear_history(self):
        """Clear chat history."""
        self.chat_history.clear()
        self.conversation_messages.clear()
        print("✅ Chat history cleared")
    
    async def process_user_input(self, user_input: str) -> str:
        """Process user input and get agent response with conversation context."""
        try:
            # Create dependencies if not exists
            if not self.deps:
                self.deps = dependencies.create_scheduling_dependencies(
                    session_id=self.session_id,
                    user_timezone=self.user_timezone
                )
            
            # Build conversation context for better memory
            context_message = self._build_context_message(user_input)
            
            # Get agent response with context
            result = await agent.scheduling_agent.run(context_message, deps=self.deps)
            agent_response = result.output
            
            # Store this exchange for future context
            self.conversation_messages.append({
                "user": user_input,
                "agent": agent_response,
                "timestamp": datetime.now().isoformat()
            })
            
            return agent_response
            
        except Exception as e:
            return f"❌ Error: {e}"
    
    def _build_context_message(self, current_input: str) -> str:
        """Build message with conversation context."""
        if not self.conversation_messages:
            # First message - add language preference
            return f"""Usuario dice: {current_input}

INSTRUCCIONES ESPECIALES:
- Responde en el mismo idioma que el usuario (español si escribe en español)
- Esta es una nueva conversación
- Saluda solo UNA VEZ al inicio
- IMPORTANTE: Si el usuario menciona CUALQUIER fecha/hora, USA INMEDIATAMENTE la herramienta parse_date_time
- NO pidas al usuario reformatear fechas - usa las herramientas disponibles
- Mantén un registro mental de toda la información que el usuario proporcione"""
        
        # Subsequent messages - include recent context
        context_parts = ["CONTEXTO DE LA CONVERSACIÓN:"]
        
        # Include last 3 exchanges for context
        recent_messages = self.conversation_messages[-3:]
        for msg in recent_messages:
            context_parts.append(f"Usuario: {msg['user']}")
            context_parts.append(f"Asistente: {msg['agent']}")
        
        context_parts.append(f"\nNUEVO MENSAJE DEL USUARIO: {current_input}")
        context_parts.append("\nINSTRUCCIONES IMPORTANTES:")
        context_parts.append("- NO saludes de nuevo, ya estás en una conversación")
        context_parts.append("- Mantén el mismo idioma de la conversación")
        context_parts.append("- Recuerda TODA la información previa de esta conversación")
        context_parts.append("- Si el usuario menciona fecha/hora, USA parse_date_time INMEDIATAMENTE")
        context_parts.append("- NUNCA pidas al usuario reformatear fechas - usa las herramientas")
        context_parts.append("- El usuario ya mencionó información importante anteriormente")
        
        return "\n".join(context_parts)
    
    async def run_chat(self):
        """Run the interactive chat loop."""
        self.print_header()
        
        while True:
            try:
                # Get user input
                user_input = input("👤 You: ").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.lower() in ['/quit', '/exit', 'quit', 'exit']:
                    print("\n👋 Goodbye! Thanks for testing the agent!")
                    break
                elif user_input.lower() == '/help':
                    self.print_help()
                    continue
                elif user_input.lower() == '/calendar':
                    await self.test_calendar_connection()
                    continue
                elif user_input.lower() == '/provider':
                    self.show_provider_info()
                    continue
                elif user_input.lower() == '/history':
                    self.show_history()
                    continue
                elif user_input.lower() == '/clear':
                    self.clear_history()
                    continue
                
                # Process regular chat message
                print("🤖 Agent: ", end="", flush=True)
                print("🔄 Thinking...", end="", flush=True)
                
                response = await self.process_user_input(user_input)
                
                # Clear the "Thinking..." message
                print("\r🤖 Agent: " + " " * 15, end="")
                print(f"\r🤖 Agent: {response}")
                
                # Save to history
                timestamp = datetime.now().strftime("%H:%M:%S")
                self.chat_history.append((user_input, response, timestamp))
                
                print()  # Add spacing
                
            except KeyboardInterrupt:
                print("\n\n👋 Chat interrupted. Goodbye!")
                break
            except EOFError:
                print("\n\n👋 Chat ended. Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Unexpected error: {e}")
                print("💡 Try /help for available commands")

def main():
    """Main function to start the chat interface."""
    print("🚀 Starting Terminal Chat Interface...")
    
    # Check if API key is configured
    api_key = os.getenv('LLM_API_KEY')
    if not api_key or api_key in ['your_gemini_api_key_here', 'your_openai_api_key_here']:
        print("❌ No API key configured!")
        print("💡 Add your API key to .env file:")
        print("   LLM_API_KEY=your_actual_api_key_here")
        return
    
    # Start chat
    chat = TerminalChat()
    asyncio.run(chat.run_chat())

if __name__ == "__main__":
    main()