import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
AI_BASE_URL = os.getenv("AI_BASE_URL")
AI_MODEL = os.getenv("AI_MODEL", "Qwen3-14B")
AI_API_KEY = os.getenv("AI_API_KEY", "not-needed-for-vllm")

# FAQ websites to crawl
FAQ_WEBSITES = [
    "https://www.moha.gov.my/index.php/ms/soalan-lazim",
    "https://www.rela.gov.my/?page_id=4621",
    "https://www.jpn.gov.my/my/soalan-lazim/soalan-lazim-kad-pengenalan",
    "https://www.ros.gov.my/portal-main/faq",
    "https://www.prison.gov.my/ms/article-news/176-informasi/70-soalan-lazim",
    "https://www.mmea.gov.my/index.php/ms/44-soalan-lazim?layout=*",
    "https://www.rmp.gov.my/faq",
    "https://www.aadk.gov.my/en/faq/",
    "https://mcba.moha.gov.my/ms/component/content/article/333-soalan-lazim.html?catid=2"
]

# Scraping configuration
SCRAPING_CONFIG = {
    "timeout": 10,
    "max_content_length": 15000,
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "max_workers": 5  # For multithreading
}
