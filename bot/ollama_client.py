import requests
from .config import AI_BASE_URL, AI_MODEL, AI_API_KEY
from .file_faq_client import query_faq_file
import logging

logger = logging.getLogger(__name__)

class AIClient:
    """Simplified AI client using local FAQ file - NO WEB SCRAPING"""
    
    def __init__(self):
        self.base_url = AI_BASE_URL
        self.model = AI_MODEL
        self.api_key = AI_API_KEY
        logger.info("✅ AI Client initialized with file-based FAQ search (NO web scraping)")
    
    def query_with_faq_context(self, user_query: str) -> str:
        """Fast AI-powered search through local FAQ file"""
        try:
            logger.info(f"🔍 Searching local FAQ file for: {user_query}")
            
            # Use the new file-based FAQ client
            response = query_faq_file(user_query)
            
            if response:
                logger.info("✅ Successfully generated response from local FAQ file")
                return response
            else:
                logger.warning("No response from FAQ file, using fallback")
                return self._emergency_fallback(user_query)
            
        except Exception as e:
            logger.error(f"❌ Error in file-based FAQ search: {e}")
            return self._emergency_fallback(user_query)
    
    def _emergency_fallback(self, query: str) -> str:
        """Emergency fallback when file search fails"""
        query_lower = query.lower()
        
        # Emergency IC chip response
        if any(keyword in query_lower for keyword in ['cip', 'chip', 'ic', 'kad pengenalan']) and \
           any(keyword in query_lower for keyword in ['bayar', 'kos', 'rosak']):
            return """**Bayaran Penggantian Cip IC yang Rosak:**

🆓 **PERCUMA (RM 0.00):**
- Jika kerosakan berlaku dalam tempoh **1 tahun** dari tarikh penyerahan kad
- Kerosakan bukan disebabkan oleh kesengajaan atau salah guna

💰 **RM 10.00:**
- Jika kerosakan berlaku **selepas 1 tahun** dari tarikh penyerahan kad

📋 **Prosedur:**
1. Pergi ke Pejabat Pendaftaran Negara (JPN) terdekat
2. Bawa dokumen sokongan (IC lama, salinan dokumen)
3. Isi borang permohonan penggantian
4. Bayar yuran RM 10.00 (jika berkenaan)

📞 **Hubungi JPN:**
- Website: https://www.jpn.gov.my
- Talian: 03-8000 8000

📚 **Sources:**
• JPN (Emergency Fallback)"""
        
        # Emergency APMM response
        if 'apmm' in query_lower and any(keyword in query_lower for keyword in ['join', 'menyertai', 'cara']):
            return """**Cara Menyertai APMM:**

📝 **Permohonan:**
- Melalui Suruhanjaya Perkhidmatan Awam (SPA)
- Website: https://www.spa.gov.my
- Gunakan borang SPA8i

👥 **Jawatan Ditawarkan:**
- Pegawai Penguatkuasa Maritim Gred T13
- Bintara Muda Maritim Gred T5
- Laskar Kelas II Maritim Gred T1

✅ **Syarat:**
- Warganegara Malaysia
- Sihat tubuh badan
- Tiada rekod jenayah

📞 **Maklumat Lanjut:**
- Website: https://www.apmm.gov.my
- SPA: https://www.spa.gov.my

📚 **Sources:**
• APMM (Emergency Fallback)"""
        
        # General fallback
        return """Maaf, maklumat spesifik untuk soalan anda tidak tersedia pada masa ini.

Untuk maklumat terkini dan tepat, sila hubungi pihak berkuasa berkaitan:

🏢 **Jabatan Pendaftaran Negara (JPN):**
- Website: https://www.jpn.gov.my
- Talian: 03-8000 8000

🏢 **Jabatan Imigresen Malaysia:**
- Website: https://www.imi.gov.my

🚔 **Polis Diraja Malaysia (PDRM):**
- Website: https://www.rmp.gov.my

🌊 **APMM:**
- Website: https://www.apmm.gov.my
- Permohonan: https://www.spa.gov.my

📚 **Sources:**
• Emergency fallback system"""

# Global AI client instance
ai_client = AIClient()

# Backward compatibility function
def query_ollama(prompt: str) -> str:
    """Backward compatibility wrapper - now uses file-based FAQ search"""
    return ai_client.query_with_faq_context(prompt)
