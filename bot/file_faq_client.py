import re
import logging
from typing import List, Dict, Tuple
from .config import AI_BASE_URL, AI_MODEL, AI_API_KEY
import requests

logger = logging.getLogger(__name__)

class FileFAQClient:
    """Fast AI-powered FAQ search using local faq.txt file"""
    
    def __init__(self, faq_file_path: str = "faq.txt"):
        self.faq_file_path = faq_file_path
        self.base_url = AI_BASE_URL
        self.model = AI_MODEL
        self.api_key = AI_API_KEY
        self.faq_content = self._load_faq_content()
        self.faq_sections = self._parse_faq_sections()
        logger.info(f"✅ Loaded {len(self.faq_sections)} FAQ sections from {faq_file_path}")
    
    def _load_faq_content(self) -> str:
        """Load the entire FAQ content from file"""
        try:
            with open(self.faq_file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            logger.info(f"📁 Loaded FAQ file: {len(content)} characters")
            return content
        except Exception as e:
            logger.error(f"❌ Failed to load FAQ file: {e}")
            return ""
    
    def _parse_faq_sections(self) -> List[Dict]:
        """Parse FAQ content into structured sections"""
        sections = []
        
        # Split by major sections (marked with ##)
        major_sections = re.split(r'\n## ', self.faq_content)
        
        for section in major_sections:
            if not section.strip():
                continue
                
            lines = section.split('\n')
            if not lines:
                continue
                
            # Extract section title
            title_line = lines[0].strip()
            if title_line.startswith('##'):
                title_line = title_line[2:].strip()
            
            # Extract agency/category from title
            agency = self._extract_agency_from_title(title_line)
            
            # Find Q&A pairs in this section
            qa_pairs = self._extract_qa_pairs('\n'.join(lines[1:]))
            
            for qa in qa_pairs:
                sections.append({
                    'agency': agency,
                    'category': title_line,
                    'question': qa['question'],
                    'answer': qa['answer'],
                    'full_text': f"Q: {qa['question']}\nA: {qa['answer']}"
                })
        
        return sections
    
    def _extract_agency_from_title(self, title: str) -> str:
        """Extract agency name from section title"""
        # Map common patterns to agency names
        agency_patterns = {
            'PUSPEN': 'AADK',
            'NADA': 'AADK', 
            'PENGAMBILAN': 'PDRM',
            'PASUKAN SUKARELAWAN POLIS': 'PDRM',
            'TRAFIK': 'PDRM',
            'LESEN SENJATA API': 'PDRM',
            'APMM': 'APMM',
            'PENDAFTARAN PERTUBUHAN': 'ROS',
            'KAD PENGENALAN': 'JPN',
            'KELAHIRAN': 'JPN',
            'RELA': 'RELA',
            'KESELAMATAN': 'KDN',
            'PIROTEKNIK': 'KDN',
            'SENJATA API': 'KDN',
            'KAWALAN PENERBITAN': 'KDN',
            'PENAPISAN FILEM': 'KDN',
            'PENDAFTARAN NEGARA': 'KDN',
            'KOMUNIKASI KORPORAT': 'KDN',
            'AKAUN': 'KDN',
            'PENCEGAHAN JENAYAH': 'KDN',
            'LEMBAGA PAROL': 'KDN',
            'KHIDMAT PENGURUSAN': 'KDN',
            'TAPISAN KESELAMATAN': 'KDN',
            'IPCC': 'KDN'
        }
        
        title_upper = title.upper()
        for pattern, agency in agency_patterns.items():
            if pattern in title_upper:
                return agency
        
        return 'KERAJAAN MALAYSIA'
    
    def _extract_qa_pairs(self, content: str) -> List[Dict]:
        """Extract Q&A pairs from content"""
        qa_pairs = []
        
        # Pattern 1: **Q1: Question** format
        pattern1 = r'\*\*Q\d+:\s*([^*]+?)\*\*\s*\n\s*A:\s*([^*]+?)(?=\n\*\*Q\d+:|\n\*\*|\n---|\n##|\Z)'
        matches1 = re.findall(pattern1, content, re.DOTALL | re.IGNORECASE)
        
        for question, answer in matches1:
            qa_pairs.append({
                'question': question.strip(),
                'answer': answer.strip()
            })
        
        # Pattern 2: Numbered questions with flexible spacing and "Jawapan :" format (IMPROVED FOR AL-QURAN)
        pattern2 = r'(\d+)\.\s*\t*\s*([^?\n]+\?[^\n]*)\s*\n(?:\s*\t*\s*\n)*\s*(?:Jawapan\s*:?\s*\n\s*)?(.*?)(?=\n\d+\s*\.|\n---|\n##|\Z)'
        matches2 = re.findall(pattern2, content, re.DOTALL)
        
        for num, question, answer in matches2:
            question = question.strip()
            answer = answer.strip()
            if question and answer and len(answer) > 20 and '?' in question:
                # Clean up the answer by removing extra whitespace
                answer = re.sub(r'\n\s*\n', '\n\n', answer)
                answer = re.sub(r'^\s*\n+', '', answer)
                answer = re.sub(r'\n+\s*$', '', answer)
                
                qa_pairs.append({
                    'question': question,
                    'answer': answer
                })
        
        # Pattern 3: Simple Q: A: format
        pattern3 = r'Q:\s*([^?\n]+\?)\s*\n\s*A:\s*(.*?)(?=\nQ:|\n---|\n##|\Z)'
        matches3 = re.findall(pattern3, content, re.DOTALL)
        
        for question, answer in matches3:
            qa_pairs.append({
                'question': question.strip(),
                'answer': answer.strip()
            })
        
        # Pattern 4: Special format for numbered questions with tabs (for Al-Quran section)
        pattern4 = r'(\d+)\.\s+([^?\n]+\?)\s*\n\s*\t?\s*\n\s*Jawapan\s*:\s*\n\s*(.*?)(?=\n\d+\.|\n---|\n##|\Z)'
        matches4 = re.findall(pattern4, content, re.DOTALL)
        
        for num, question, answer in matches4:
            if question.strip() and answer.strip():
                qa_pairs.append({
                    'question': question.strip(),
                    'answer': answer.strip()
                })
        
        # Pattern 5: Alternative numbered format with different spacing
        pattern5 = r'(\d+)\s+([^?\n]+\?)\s*\n\s*\t?\s*\n\s*\n\s*Jawapan\s*:\s*\n\s*(.*?)(?=\n\d+\s+|\n---|\n##|\Z)'
        matches5 = re.findall(pattern5, content, re.DOTALL)
        
        for num, question, answer in matches5:
            if question.strip() and answer.strip():
                qa_pairs.append({
                    'question': question.strip(),
                    'answer': answer.strip()
                })
        
        # Pattern 6: Very flexible pattern for Al-Quran style with multiple empty lines
        pattern6 = r'(\d+)\.\s*\t?\s*([^?\n]+\?)\s*\n(?:\s*\n)*\s*Jawapan\s*:\s*\n\s*(.*?)(?=\n\d+\.|\n---|\n##|\Z)'
        matches6 = re.findall(pattern6, content, re.DOTALL)
        
        for num, question, answer in matches6:
            if question.strip() and answer.strip() and len(answer.strip()) > 20:
                qa_pairs.append({
                    'question': question.strip(),
                    'answer': answer.strip()
                })
        
        # Pattern 7: Ultra-flexible pattern for any numbered question format
        pattern7 = r'(\d+)\.\s*\t*\s*([^?\n]*\?[^\n]*)\s*\n(?:[^\S\n]*\n)*\s*(?:Jawapan\s*:?\s*)?\n\s*((?:[^\n]*\n)*?)(?=\n\d+\.|\n---|\n##|\Z)'
        matches7 = re.findall(pattern7, content, re.DOTALL)
        
        for num, question, answer in matches7:
            question = question.strip()
            answer = answer.strip()
            if question and answer and len(answer) > 30 and '?' in question:
                # Clean up the answer by removing extra whitespace
                answer = re.sub(r'\n\s*\n', '\n\n', answer)
                answer = re.sub(r'^\s*\n+', '', answer)
                answer = re.sub(r'\n+\s*$', '', answer)
                
                qa_pairs.append({
                    'question': question,
                    'answer': answer
                })
        
        # Pattern 8: Specific pattern for Al-Quran section format with tabs and multiple empty lines
        pattern8 = r'(\d+)\.\s*\t*\s*([^?\n]+al-[Qq]uran[^?\n]*\?)\s*\n\s*\t*\s*\n\s*\n\s*Jawapan\s*:\s*\n\s*(.*?)(?=\n\d+\.|\n---|\n##|\Z)'
        matches8 = re.findall(pattern8, content, re.DOTALL)
        
        for num, question, answer in matches8:
            if question.strip() and answer.strip():
                qa_pairs.append({
                    'question': question.strip(),
                    'answer': answer.strip()
                })
        
        # Pattern 9: Manual extraction for Al-Quran style content (fallback)
        manual_pairs = self._manual_extract_alquran_content(content)
        qa_pairs.extend(manual_pairs)
        
        return qa_pairs
    
    def _manual_extract_alquran_content(self, content: str) -> List[Dict]:
        """Manual extraction for Al-Quran content that regex patterns miss"""
        qa_pairs = []
        lines = content.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for numbered questions with Al-Quran content
            if (re.match(r'^\d+\.', line) and
                ('prosedur' in line.lower() or 'al-quran' in line.lower() or 'quran' in line.lower())):
                
                # Extract question
                question = re.sub(r'^\d+\.\s*\t*\s*', '', line).strip()
                
                if '?' in question:
                    # Find the answer
                    answer_lines = []
                    j = i + 1
                    
                    # Skip empty lines and tabs until we find "Jawapan"
                    while j < len(lines) and 'jawapan' not in lines[j].lower():
                        j += 1
                    
                    if j < len(lines) and 'jawapan' in lines[j].lower():
                        j += 1  # Skip the "Jawapan :" line
                        
                        # Collect answer lines until next numbered question
                        while j < len(lines):
                            answer_line = lines[j].strip()
                            
                            # Stop if we hit the next numbered question
                            if answer_line and re.match(r'^\d+\.', answer_line):
                                break
                            
                            # Add non-empty lines to answer
                            if answer_line:
                                answer_lines.append(answer_line)
                            
                            j += 1
                        
                        if answer_lines:
                            answer = '\n'.join(answer_lines)
                            
                            # Only add if it's substantial content
                            if len(answer) > 30:
                                qa_pairs.append({
                                    'question': question,
                                    'answer': answer
                                })
            
            i += 1
        
        return qa_pairs
    
    def search_faq(self, user_query: str) -> str:
        """Main search function that finds relevant FAQ content and uses AI to generate response"""
        try:
            logger.info(f"🔍 Searching FAQ for: {user_query}")
            
            # Step 1: Find relevant FAQ sections
            relevant_sections = self._find_relevant_sections(user_query)
            
            if not relevant_sections:
                logger.warning("No relevant FAQ sections found")
                return self._fallback_response(user_query)
            
            # Step 2: Use AI to generate focused response
            ai_response = self._generate_ai_response(user_query, relevant_sections)
            
            if ai_response:
                logger.info("✅ AI successfully generated response from FAQ content")
                return ai_response
            else:
                logger.warning("AI failed, using direct FAQ content")
                return self._format_direct_response(relevant_sections)
                
        except Exception as e:
            logger.error(f"❌ Error in FAQ search: {e}")
            return self._fallback_response(user_query)
    
    def _find_relevant_sections(self, query: str) -> List[Dict]:
        """Find FAQ sections relevant to the user query - COMPREHENSIVE SEARCH"""
        query_lower = query.lower()
        relevant_sections = []
        
        # Expanded keywords for better matching
        keywords_map = {
            'ic': ['ic', 'kad pengenalan', 'mykad', 'cip', 'chip', 'pengenalan'],
            'apmm': ['apmm', 'maritim', 'join', 'menyertai', 'permohonan'],
            'pdrm': ['polis', 'pdrm', 'pengambilan', 'recruitment', 'konstabel', 'sarjan', 'inspektor'],
            'rela': ['rela', 'sukarelawan', 'keanggotaan', 'latihan'],
            'jpn': ['jpn', 'kelahiran', 'sijil lahir', 'pendaftaran negara'],
            'ros': ['pertubuhan', 'ros', 'alamat berdaftar', 'organisasi', 'persatuan'],
            'passport': ['pasport', 'passport', 'imigresen', 'travel'],
            'lesen': ['lesen', 'memandu', 'senjata', 'permit', 'kelulusan'],
            'alquran': ['alquran', 'al-quran', 'quran', 'pencetakan', 'penerbitan', 'teks', 'lpppq', 'sistem upq', 'borang a'],
            'filem': ['filem', 'penapisan', 'lpf', 'tayangan', 'pawagam'],
            'senjata': ['senjata api', 'pistol', 'senapang', 'firearm'],
            'piroteknik': ['piroteknik', 'bunga api', 'mercun', 'letupan'],
            'procedure': ['mohon', 'permohonan', 'apply', 'prosedur', 'cara', 'bagaimana', 'macam mana', 'how'],
            'requirements': ['syarat', 'kelayakan', 'requirement', 'criteria', 'eligibility'],
            'cost': ['bayar', 'bayaran', 'kos', 'yuran', 'fee', 'cost', 'charge', 'rm']
        }
        
        # Score each section based on relevance
        for section in self.faq_sections:
            score = 0
            
            # Check question relevance
            question_lower = section['question'].lower()
            answer_lower = section['answer'].lower()
            full_text_lower = section['full_text'].lower()
            
            # Enhanced keyword matching with partial matches
            query_words = query_lower.split()
            for keyword in query_words:
                if len(keyword) > 2:  # Skip very short words
                    # Exact matches
                    if keyword in question_lower:
                        score += 5
                    if keyword in answer_lower:
                        score += 3
                    
                    # Partial matches (substring)
                    for word in question_lower.split():
                        if keyword in word and len(keyword) > 3:
                            score += 2
                    for word in answer_lower.split():
                        if keyword in word and len(keyword) > 3:
                            score += 1
            
            # Topic-based matching with expanded coverage
            for topic, keywords in keywords_map.items():
                query_has_topic = any(kw in query_lower for kw in keywords)
                content_has_topic = any(kw in full_text_lower for kw in keywords)
                
                if query_has_topic and content_has_topic:
                    score += 8
            
            # Context-aware scoring for common question patterns
            if any(word in query_lower for word in ['mohon', 'apply', 'permohonan', 'cara', 'bagaimana', 'macam mana', 'how']):
                if any(word in answer_lower for word in ['permohonan', 'borang', 'sistem', 'prosedur', 'langkah']):
                    score += 10
            
            if any(word in query_lower for word in ['bayar', 'kos', 'yuran', 'fee', 'cost']):
                if any(word in answer_lower for word in ['rm', 'bayaran', 'yuran', 'percuma', 'free']):
                    score += 10
            
            if any(word in query_lower for word in ['syarat', 'requirement', 'kelayakan']):
                if any(word in answer_lower for word in ['syarat', 'kelayakan', 'criteria', 'umur', 'warganegara']):
                    score += 10
            
            # Special enhanced matching for Al-Quran and other specific topics
            if any(word in query_lower for word in ['quran', 'alquran', 'al-quran']):
                if any(word in full_text_lower for word in ['quran', 'al-quran', 'lpppq', 'pencetakan', 'penerbitan', 'sistem upq']):
                    score += 15
            
            # Add sections with any score > 0
            if score > 0:
                section['relevance_score'] = score
                relevant_sections.append(section)
        
        # Sort by relevance score and return more results for better coverage
        relevant_sections.sort(key=lambda x: x['relevance_score'], reverse=True)
        return relevant_sections[:10]  # Return top 10 most relevant for better coverage
    
    def _clean_response_format(self, response):
        """Clean response to remove markdown formatting"""
        if not response:
            return response
            
        # Remove markdown bold formatting
        response = re.sub(r'\*\*(.*?)\*\*', r'\1', response)
        
        # Convert markdown bullet points to simple format
        response = re.sub(r'^[\s]*[-*+]\s+', '• ', response, flags=re.MULTILINE)
        
        # Clean up excessive spacing
        response = re.sub(r'\n\s*\n\s*\n', '\n\n', response)
        
        # Remove any remaining markdown syntax
        response = re.sub(r'[#]{1,6}\s+', '', response)  # Headers
        response = re.sub(r'`([^`]+)`', r'\1', response)  # Inline code
        response = re.sub(r'```[^`]*```', '', response)  # Code blocks
        
        return response.strip()
    
    def _generate_ai_response(self, query: str, sections: List[Dict]) -> str:
        """Use AI to generate a focused response from relevant FAQ sections"""
        try:
            # Prepare context from relevant sections
            context_text = ""
            sources = set()
            
            for i, section in enumerate(sections, 1):
                context_text += f"\n--- FAQ {i} ({section['agency']}) ---\n"
                context_text += f"Q: {section['question']}\n"
                context_text += f"A: {section['answer']}\n"
                sources.add(section['agency'])
            
            # Create AI prompt
            prompt = f"""You are an AI assistant helping users find information from Malaysian government FAQ content. You must search through ALL the provided FAQ content carefully to find ANY relevant information that answers the user's question.

User Question: {query}

Available FAQ Content:
{context_text}

CRITICAL INSTRUCTIONS:
1. CAREFULLY examine ALL FAQ content provided for ANY information related to the user's question
2. Look for RELATED topics, procedures, or information even if keywords don't match exactly
3. If the user asks about "how to apply" or "procedure", look for ANY FAQ that mentions application processes, forms, requirements, or steps
4. If the user asks about costs/fees, look for ANY FAQ that mentions payments, charges, or fees
5. Use the EXACT information from the FAQ content - do not paraphrase or change details
6. If you find relevant information, provide the complete answer with all details
7. Use the same language as the user's question (Malay or English)
8. Only say "no information found" if you have thoroughly checked ALL FAQ content and found nothing related

FORMATTING REQUIREMENTS:
- Use PLAIN TEXT format only - NO markdown syntax
- Do NOT use ** for bold text
- Do NOT use - or * for bullet points
- Use simple numbered lists (1., 2., 3.) when needed
- Use clear paragraph breaks for readability
- Keep the response clean and easy to read

SEARCH STRATEGY:
- Look for synonyms and related terms
- Check for procedural information that might answer "how to" questions
- Look for requirement lists that might answer eligibility questions
- Search for any mention of the topic even in different contexts

Provide a comprehensive answer in PLAIN TEXT format based on the FAQ content:"""

            response = self._send_to_ai(prompt)
            
            if response:
                # Clean the response format
                response = self._clean_response_format(response)
                
                # Add sources in plain text format
                sources_text = "\n\n📚 Sources:\n"
                for source in sorted(sources):
                    sources_text += f"• {source}\n"
                
                return response + sources_text
            
            return None
            
        except Exception as e:
            logger.error(f"AI response generation failed: {e}")
            return None
    
    def _format_direct_response(self, sections: List[Dict]) -> str:
        """Format direct response from FAQ sections when AI fails"""
        if not sections:
            return "Tiada maklumat yang berkaitan ditemui."
        
        # Use the most relevant section
        best_section = sections[0]
        
        response = f"{best_section['question']}\n\n{best_section['answer']}"
        
        # Add source
        response += f"\n\n📚 Sources:\n• {best_section['agency']}"
        
        return response
    
    def _fallback_response(self, query: str) -> str:
        """Fallback response when no relevant content is found"""
        query_lower = query.lower()
        
        # Specific fallbacks for common topics
        if any(keyword in query_lower for keyword in ['ic', 'kad pengenalan', 'mykad']):
            return """Untuk maklumat berkaitan MyKad dan Kad Pengenalan:

📞 Hubungi JPN:
• Website: https://www.jpn.gov.my
• Talian: 03-8000 8000
• E-mel: pro@jpn.gov.my

📚 Sources:
• JPN (Jabatan Pendaftaran Negara)"""
        
        if 'apmm' in query_lower:
            return """Untuk maklumat berkaitan APMM:

📞 Hubungi APMM:
• Permohonan melalui SPA: https://www.spa.gov.my
• Website: https://www.apmm.gov.my

📚 Sources:
• APMM (Agensi Penguatkuasaan Maritim Malaysia)"""
        
        # General fallback
        return """Maaf, maklumat spesifik untuk soalan anda tidak ditemui dalam pangkalan data FAQ.

Untuk maklumat lanjut, sila hubungi agensi kerajaan yang berkaitan:

🏢 Agensi Utama:
• JPN: 03-8000 8000
• PDRM: 03-2266 2222
• APMM: https://www.spa.gov.my

📚 Sources:
• Sistem FAQ Kerajaan Malaysia"""
    
    def _send_to_ai(self, prompt: str) -> str:
        """Send prompt to AI model"""
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
            "temperature": 0.3,  # Lower temperature for more focused responses
            "max_tokens": 800
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

# Global instance
file_faq_client = FileFAQClient()

# Main query function for backward compatibility
def query_faq_file(prompt: str) -> str:
    """Main function to query FAQ from file"""
    return file_faq_client.search_faq(prompt)