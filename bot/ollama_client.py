import requests
from .config import OLLAMA_SERVER_URL, OLLAMA_MODEL
import logging

logger = logging.getLogger(__name__)

def query_ollama(prompt: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }

    logger.info(f"🔁 Sending prompt to Ollama at {OLLAMA_SERVER_URL} with model {OLLAMA_MODEL}")

    try:
        response = requests.post(OLLAMA_SERVER_URL, json=payload, timeout=10)
        response.raise_for_status()
        result = response.json()
        logger.info("✅ Ollama returned response.")
        return result.get("response", "⚠️ Model returned no response.")
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Error contacting Ollama: {e}")
        return f"⚠️ Error contacting model: {e}"
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return f"⚠️ Unexpected error: {e}"
