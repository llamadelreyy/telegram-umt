import requests
from .config import AI_BASE_URL, AI_MODEL, AI_API_KEY
from .robust_faq_system import robust_faq_system, RobustAnswer
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class AIClient:
    """AI client with robust FAQ system integration"""
    
    def __init__(self):
        self.base_url = AI_BASE_URL
        self.model = AI_MODEL
        self.api_key = AI_API_KEY
    
    def query_with_faq_context(self, user_query: str) -> str:
        """AI-driven dynamic search through government websites"""
        try:
            logger.info(f"🤖 AI Agent searching websites for: {user_query}")
            
            # Step 1: Search through FAQ content using existing crawler
            from .faq_crawler import faq_crawler
            search_results = faq_crawler.search_faqs(user_query, max_results=10)
            
            if not search_results:
                logger.warning("No FAQ results found, using emergency fallback")
                return self._emergency_fallback(user_query)
            
            # Step 2: Prepare context from multiple sources
            context_sources = []
            for result in search_results[:5]:  # Use top 5 results
                context_sources.append({
                    'source': result.website,
                    'question': result.question,
                    'answer': result.answer,
                    'relevance': result.relevance_score
                })
            
            # Step 3: Use AI to analyze and synthesize answer
            ai_response = self._ai_search_and_answer(user_query, context_sources)
            
            if ai_response:
                logger.info("✅ AI successfully generated answer from website search")
                return ai_response
            else:
                logger.warning("AI failed to generate answer, using best FAQ result")
                best_result = search_results[0]
                return f"{best_result.answer}\n\n📚 **Sources:**\n• {best_result.website}"
            
        except Exception as e:
            logger.error(f"❌ Error in AI search system: {e}")
            return self._emergency_fallback(user_query)
    
    def _ai_search_and_answer(self, query: str, context_sources: List[Dict]) -> str:
        """Use AI to search through website content and generate answer"""
        try:
            # Prepare context from multiple sources
            context_text = ""
            sources_list = []
            
            for i, source in enumerate(context_sources, 1):
                context_text += f"\n--- Source {i}: {source['source']} ---\n"
                context_text += f"Q: {source['question']}\n"
                context_text += f"A: {source['answer']}\n"
                context_text += f"Relevance Score: {source['relevance']}\n"
                
                if source['source'] not in sources_list:
                    sources_list.append(source['source'])
            
            # Create AI prompt for dynamic search
            search_prompt = f"""You are an AI assistant that helps users find information from Malaysian government websites. You have been provided with search results from official government FAQ pages.

User Question: {query}

Search Results from Government Websites:
{context_text}

Instructions:
1. Analyze the search results to find the most relevant and accurate answer to the user's question
2. If you find a direct answer, provide it with specific details (costs, procedures, requirements, etc.)
3. If multiple sources have similar information, synthesize them into a comprehensive answer
4. If the information is not sufficient or not found, clearly state that the information is not available in the provided sources
5. Always maintain accuracy - only use information that is explicitly stated in the search results
6. Format your response clearly with proper structure, bullet points, and sections as appropriate
7. Use the same language as the user's question (Malay or English)
8. Include specific government department names and contact information when available

Provide a helpful, accurate answer based solely on the search results provided:"""
            
            ai_response = self._send_to_ai(search_prompt)
            
            # Add sources
            sources_text = "\n\n📚 **Sources:**\n"
            for source in sources_list:
                sources_text += f"• {source}\n"
            
            return ai_response + sources_text
            
        except Exception as e:
            logger.error(f"AI search and answer failed: {e}")
            return None
    
    def _emergency_fallback(self, query: str) -> str:
        """Emergency fallback when everything fails"""
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
- Talian: 1-300-88-4444

📚 **Sources:**
• www.jpn.gov.my"""
        
        # General fallback
        return """Maaf, maklumat spesifik untuk soalan anda tidak tersedia pada masa ini.

Untuk maklumat terkini dan tepat, sila hubungi pihak berkuasa berkaitan:

🏢 **Jabatan Pendaftaran Negara (JPN):**
- Website: https://www.jpn.gov.my
- Talian: 1-300-88-4444

🏢 **Jabatan Imigresen Malaysia:**
- Website: https://www.imi.gov.my

🚔 **Polis Diraja Malaysia (PDRM):**
- Website: https://www.rmp.gov.my

📚 **Sources:**
• Emergency fallback system"""
    
    
    def _send_to_ai(self, prompt: str) -> str:
        """Send prompt to AI model"""
        # Try OpenAI-compatible API first
        try:
            return self._send_openai_compatible(prompt)
        except Exception as e:
            logger.warning(f"OpenAI-compatible API failed: {e}, trying Ollama format")
            return self._send_ollama_format(prompt)
    
    def _send_openai_compatible(self, prompt: str) -> str:
        """Send request using OpenAI-compatible format"""
        url = f"{self.base_url}/v1/chat/completions"
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        logger.info(f"🔁 Sending request to {url} with model {self.model}")
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        logger.info("✅ AI returned response")
        
        return result["choices"][0]["message"]["content"]
    
    def _send_ollama_format(self, prompt: str) -> str:
        """Send request using Ollama format as fallback"""
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        
        logger.info(f"🔁 Sending Ollama format request to {url}")
        
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        logger.info("✅ AI returned response (Ollama format)")
        
        return result.get("response", "⚠️ Model returned no response.")

# Global AI client instance
ai_client = AIClient()

# Backward compatibility function
def query_ollama(prompt: str) -> str:
    """Backward compatibility wrapper"""
    return ai_client.query_with_faq_context(prompt)
