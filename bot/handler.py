from telegram import Update
from telegram.ext import ContextTypes
from .ollama_client import query_ollama
import logging

logger = logging.getLogger(__name__)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_input = update.message.text
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        logger.info(f"📥 Message from user {user_id} in chat {chat_id}: {user_input}")

        await update.message.chat.send_action(action="typing")

        response = query_ollama(user_input)
        logger.info(f"📤 Response to user {user_id}: {response[:100]}...")  # log first 100 chars

        # Handle Telegram's 4096 character limit
        max_length = 4000  # Leave some buffer
        
        if len(response) > max_length:
            logger.info(f"Response too long ({len(response)} chars), splitting into chunks")
            
            # Split response into chunks
            chunks = []
            current_chunk = ""
            
            # Split by paragraphs first
            paragraphs = response.split('\n\n')
            
            for paragraph in paragraphs:
                if len(current_chunk) + len(paragraph) + 2 <= max_length:
                    if current_chunk:
                        current_chunk += '\n\n' + paragraph
                    else:
                        current_chunk = paragraph
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                        current_chunk = paragraph
                    else:
                        # Paragraph itself is too long, split by sentences
                        sentences = paragraph.split('. ')
                        for sentence in sentences:
                            if len(current_chunk) + len(sentence) + 2 <= max_length:
                                if current_chunk:
                                    current_chunk += '. ' + sentence
                                else:
                                    current_chunk = sentence
                            else:
                                if current_chunk:
                                    chunks.append(current_chunk)
                                current_chunk = sentence
            
            if current_chunk:
                chunks.append(current_chunk)
            
            logger.info(f"Split into {len(chunks)} chunks")
            
            # Send chunks with error handling
            for i, chunk in enumerate(chunks):
                try:
                    if i == 0:
                        await update.message.reply_text(chunk)
                    else:
                        await update.message.reply_text(f"(sambungan {i+1})\n\n{chunk}")
                except Exception as chunk_error:
                    logger.error(f"Error sending chunk {i+1}: {chunk_error}")
                    # Try sending a truncated version
                    truncated = chunk[:3500] + "\n\n[Pesan dipotong karena terlalu panjang]"
                    await update.message.reply_text(truncated)
        else:
            await update.message.reply_text(response)
            
    except Exception as e:
        logger.error(f"Error in handle_message: {e}")
        error_msg = "Maaf, terjadi kesalahan saat memproses permintaan Anda. Silakan coba lagi."
        try:
            await update.message.reply_text(error_msg)
        except:
            logger.error("Failed to send error message to user")
