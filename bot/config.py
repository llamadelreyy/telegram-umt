import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OLLAMA_SERVER_URL = os.getenv("OLLAMA_SERVER_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")
