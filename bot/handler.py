from telegram import Update
from telegram.ext import ContextTypes
from .ollama_client import query_ollama
import logging

logger = logging.getLogger(__name__)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    logger.info(f"📥 Message from user {user_id} in chat {chat_id}: {user_input}")

    await update.message.chat.send_action(action="typing")

    response = query_ollama(user_input)
    logger.info(f"📤 Response to user {user_id}: {response[:100]}...")  # log first 100 chars

    await update.message.reply_text(response)
