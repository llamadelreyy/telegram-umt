"""
Robust FAQ System - Multiple fallback layers to ensure consistent responses
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class RobustAnswer:
    question: str
    answer: str
    source: str
    confidence: float
    method: str  # How the answer was obtained

class RobustFAQSystem:
    """Robust FAQ system with multiple fallback layers"""
    
    def __init__(self):
        # Layer 1: Hardcoded critical answers (highest priority)
        self.critical_answers = {
            'ic_chip_cost': {
                'keywords': ['cip', 'chip', 'ic', 'kad pengenalan', 'mykad', 'rosak', 'bayar', 'kos',
                           'replacement', 'replace', 'cost', 'fee', 'damaged', 'damage', 'broken', 'repair'],
                'answer': '''**Bayaran Penggantian Cip IC yang Rosak:**

🆓 **PERCUMA (RM 0.00):**
- Jika kerosakan berlaku dalam tempoh **1 tahun** dari tarikh penyerahan kad
- Kerosakan bukan disebabkan oleh kesengajaan atau salah guna
- Gantian diberikan secara percuma

💰 **RM 10.00:**
- Jika kerosakan berlaku **selepas 1 tahun** dari tarikh penyerahan kad
- Bayaran RM 10.00 dikenakan untuk penggantian

📋 **Prosedur:**
1. Pergi ke Pejabat Pendaftaran Negara (JPN) terdekat
2. Bawa dokumen sokongan (IC lama, salinan dokumen)
3. Isi borang permohonan penggantian
4. Bayar yuran RM 10.00 (jika berkenaan)

📞 **Hubungi JPN:**
- Website: https://www.jpn.gov.my
- Talian: 1-300-88-4444

**Sumber:** Jabatan Pendaftaran Negara Malaysia (JPN)''',
                'source': 'www.jpn.gov.my',
                'confidence': 1.0
            },
            'passport_requirements': {
                'keywords': ['passport', 'pasport', 'syarat', 'keperluan', 'dokumen'],
                'answer': '''**Syarat Permohonan Pasport Malaysia:**

📋 **Dokumen Diperlukan:**
- Kad Pengenalan (IC) asal dan salinan
- Sijil kelahiran asal dan salinan
- Borang permohonan pasport (IM.12)
- Gambar passport saiz 2" x 2" (2 keping)

💰 **Bayaran:**
- Pasport 32 halaman: RM 200
- Pasport 64 halaman: RM 300

📍 **Tempat Permohonan:**
- Pejabat Imigresen Malaysia
- Pejabat Pendaftaran Negara (JPN) terpilih
- UTC/KIOSK terpilih

**Sumber:** Jabatan Imigresen Malaysia''',
                'source': 'www.imi.gov.my',
                'confidence': 1.0
            }
        }
        
        # Layer 2: Pattern-based responses
        self.pattern_responses = {
            r'(berapa|kos|bayar|harga|cost|fee|much).*(cip|chip|ic).*(rosak|damage|broken|replace)': 'ic_chip_cost',
            r'(ic|chip|cip).*(replacement|replace|rosak|damage|broken).*(cost|fee|bayar|kos)': 'ic_chip_cost',
            r'(syarat|keperluan|dokumen).*(passport|pasport)': 'passport_requirements',
            r'(bagaimana|cara).*(mohon|apply).*(passport|pasport)': 'passport_requirements'
        }
    
    def get_robust_answer(self, query: str) -> RobustAnswer:
        """Get robust answer with multiple fallback layers"""
        logger.info(f"🔍 Getting robust answer for: {query}")
        
        # Layer 1: Check critical hardcoded answers
        critical_answer = self._check_critical_answers(query)
        if critical_answer:
            logger.info("✅ Found critical hardcoded answer")
            return critical_answer
        
        # Layer 2: Pattern matching
        pattern_answer = self._check_pattern_answers(query)
        if pattern_answer:
            logger.info("✅ Found pattern-based answer")
            return pattern_answer
        
        # Layer 3: Try intelligent agent (if available)
        try:
            from .intelligent_agent import intelligent_agent
            agent_results = intelligent_agent.find_specific_answer(query)
            if agent_results and agent_results[0].confidence > 0.7:
                best_result = agent_results[0]
                logger.info("✅ Found high-confidence agent answer")
                return RobustAnswer(
                    question=best_result.question,
                    answer=best_result.answer,
                    source=best_result.website,
                    confidence=best_result.confidence,
                    method="intelligent_agent"
                )
        except Exception as e:
            logger.warning(f"Intelligent agent failed: {e}")
        
        # Layer 4: Try regular FAQ crawler
        try:
            from .faq_crawler import faq_crawler
            faq_results = faq_crawler.search_faqs(query, max_results=3)
            if faq_results and faq_results[0].relevance_score > 5:
                best_faq = faq_results[0]
                logger.info("✅ Found FAQ crawler answer")
                return RobustAnswer(
                    question=best_faq.question,
                    answer=best_faq.answer,
                    source=best_faq.website,
                    confidence=min(0.8, best_faq.relevance_score / 10),
                    method="faq_crawler"
                )
        except Exception as e:
            logger.warning(f"FAQ crawler failed: {e}")
        
        # Layer 5: Fallback response
        logger.info("⚠️ Using fallback response")
        return self._get_fallback_response(query)
    
    def _check_critical_answers(self, query: str) -> Optional[RobustAnswer]:
        """Check if query matches critical hardcoded answers"""
        query_lower = query.lower()
        
        for answer_type, config in self.critical_answers.items():
            # Count keyword matches
            keyword_matches = sum(1 for keyword in config['keywords'] if keyword in query_lower)
            
            # If enough keywords match, return the critical answer
            if keyword_matches >= 3:  # At least 3 keywords must match
                return RobustAnswer(
                    question=query,
                    answer=config['answer'],
                    source=config['source'],
                    confidence=config['confidence'],
                    method="critical_hardcoded"
                )
        
        return None
    
    def _check_pattern_answers(self, query: str) -> Optional[RobustAnswer]:
        """Check if query matches known patterns"""
        query_lower = query.lower()
        
        for pattern, answer_type in self.pattern_responses.items():
            if re.search(pattern, query_lower, re.IGNORECASE):
                if answer_type in self.critical_answers:
                    config = self.critical_answers[answer_type]
                    return RobustAnswer(
                        question=query,
                        answer=config['answer'],
                        source=config['source'],
                        confidence=0.9,
                        method="pattern_matched"
                    )
        
        return None
    
    def _get_fallback_response(self, query: str) -> RobustAnswer:
        """Provide fallback response when all else fails"""
        return RobustAnswer(
            question=query,
            answer="""Maaf, maklumat spesifik untuk soalan anda tidak tersedia dalam FAQ yang disediakan. 

Untuk maklumat terkini dan tepat, sila hubungi pihak berkuasa berkaitan:

🏢 **Jabatan Pendaftaran Negara (JPN):**
- Website: https://www.jpn.gov.my
- Talian: 1-300-88-4444

🏢 **Jabatan Imigresen Malaysia:**
- Website: https://www.imi.gov.my
- Talian: 03-8880 1000

🚔 **Polis Diraja Malaysia (PDRM):**
- Website: https://www.rmp.gov.my
- Talian Kecemasan: 999""",
            source="general_fallback",
            confidence=0.5,
            method="fallback"
        )

# Global robust system instance
robust_faq_system = RobustFAQSystem()