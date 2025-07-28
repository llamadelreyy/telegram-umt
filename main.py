import asyncio
import logging
import signal
import sys
from telegram.ext import ApplicationBuilder, MessageHandler, filters
from bot.handler import handle_message
from bot.config import TELEGRAM_BOT_TOKEN

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    level=logging.INFO,
)

def signal_handler(sig, frame):
    print('\nBot stopped by user')
    sys.exit(0)

def main():
    """Main function to run the bot with proper event loop handling"""
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Create new event loop to avoid conflicts
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Build the application
        app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
        
        print("🤖 Telegram Bot Starting...")
        print("Press Ctrl+C to stop")
        
        # Run the bot
        loop.run_until_complete(app.run_polling())
        
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        print("💡 Try stopping any existing bot instances and run again")
    finally:
        try:
            # Clean up the event loop
            if 'loop' in locals() and not loop.is_closed():
                loop.close()
        except:
            pass

if __name__ == "__main__":
    main()
