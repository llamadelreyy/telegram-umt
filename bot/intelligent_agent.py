"""
Intelligent FAQ Agent
Advanced agent that can navigate and extract specific information from government websites
"""

import re
import time
import logging
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from .config import FAQ_WEBSITES, SCRAPING_CONFIG

logger = logging.getLogger(__name__)

@dataclass
class AnswerResult:
    """Represents a specific answer found by the agent"""
    question: str
    answer: str
    confidence: float
    source_url: str
    website: str
    context: str

class IntelligentFAQAgent:
    """Advanced agent for finding specific answers from government websites"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': SCRAPING_CONFIG["user_agent"]
        })
        self.session.verify = False
        
        # Knowledge base of common question patterns
        self.question_patterns = {
            'ic_chip_cost': {
                'keywords': ['cip', 'chip', 'ic', 'kad pengenalan', 'rosak', 'bayaran', 'kos', 'harga'],
                'patterns': [
                    r'bayaran.*cip.*rosak',
                    r'kos.*ganti.*ic',
                    r'rm\s*\d+.*cip',
                    r'percuma.*kerosakan',
                    r'satu tahun.*percuma'
                ]
            },
            'passport_requirements': {
                'keywords': ['passport', 'pasport', 'syarat', 'keperluan', 'dokumen'],
                'patterns': [
                    r'syarat.*pasport',
                    r'dokumen.*diperlukan',
                    r'keperluan.*passport'
                ]
            }
        }
    
    def find_specific_answer(self, query: str, max_confidence_threshold: float = 0.7) -> List[AnswerResult]:
        """Find specific answers for a query using intelligent search"""
        logger.info(f"🤖 Agent searching for: {query}")
        
        # Analyze query to determine search strategy
        search_strategy = self._analyze_query(query)
        
        # Search all websites concurrently
        results = []
        with ThreadPoolExecutor(max_workers=SCRAPING_CONFIG['max_workers']) as executor:
            future_to_url = {
                executor.submit(self._search_website_intelligently, url, query, search_strategy): url 
                for url in FAQ_WEBSITES
            }
            
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    website_results = future.result()
                    results.extend(website_results)
                except Exception as e:
                    logger.error(f"Error searching {url}: {e}")
        
        # Sort by confidence and return best results
        results.sort(key=lambda x: x.confidence, reverse=True)
        
        # Filter by confidence threshold
        high_confidence_results = [r for r in results if r.confidence >= max_confidence_threshold]
        
        if high_confidence_results:
            return high_confidence_results[:3]  # Return top 3 high-confidence results
        else:
            return results[:5]  # Return top 5 results if no high-confidence ones
    
    def _analyze_query(self, query: str) -> Dict:
        """Analyze query to determine the best search strategy"""
        query_lower = query.lower()
        
        strategy = {
            'type': 'general',
            'keywords': [],
            'patterns': [],
            'target_sites': FAQ_WEBSITES
        }
        
        # Check for specific question types
        for question_type, config in self.question_patterns.items():
            keyword_matches = sum(1 for keyword in config['keywords'] if keyword in query_lower)
            if keyword_matches >= 2:  # At least 2 keywords match
                strategy['type'] = question_type
                strategy['keywords'] = config['keywords']
                strategy['patterns'] = config['patterns']
                break
        
        # Extract key terms from query
        strategy['query_terms'] = re.findall(r'\w+', query_lower)
        
        return strategy
    
    def _search_website_intelligently(self, url: str, query: str, strategy: Dict) -> List[AnswerResult]:
        """Intelligently search a specific website"""
        try:
            logger.info(f"🔍 Agent analyzing: {url}")
            
            response = self.session.get(url, timeout=SCRAPING_CONFIG["timeout"])
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            website = url.split('/')[2]
            
            # Remove navigation and irrelevant content
            for elem in soup(['nav', 'footer', 'header', 'script', 'style', 'aside', 'menu']):
                elem.decompose()
            
            results = []
            
            # Strategy 1: Look for exact pattern matches
            if strategy['type'] != 'general':
                pattern_results = self._find_pattern_matches(soup, url, website, strategy)
                results.extend(pattern_results)
            
            # Strategy 2: Semantic content analysis
            semantic_results = self._semantic_content_analysis(soup, url, website, query, strategy)
            results.extend(semantic_results)
            
            # Strategy 3: Deep text mining
            text_mining_results = self._deep_text_mining(soup, url, website, query, strategy)
            results.extend(text_mining_results)
            
            logger.info(f"✅ Found {len(results)} potential answers from {website}")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error analyzing {url}: {e}")
            return []
    
    def _find_pattern_matches(self, soup: BeautifulSoup, url: str, website: str, strategy: Dict) -> List[AnswerResult]:
        """Find content matching specific patterns"""
        results = []
        
        # Get all text content
        full_text = soup.get_text()
        
        # Look for pattern matches
        for pattern in strategy['patterns']:
            matches = re.finditer(pattern, full_text, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                # Extract context around the match
                start = max(0, match.start() - 200)
                end = min(len(full_text), match.end() + 200)
                context = full_text[start:end].strip()
                
                # Try to identify question and answer
                question, answer = self._extract_qa_from_context(context, match.group())
                
                if question and answer:
                    confidence = self._calculate_confidence(question, answer, strategy)
                    
                    results.append(AnswerResult(
                        question=question,
                        answer=answer,
                        confidence=confidence,
                        source_url=url,
                        website=website,
                        context=context
                    ))
        
        return results
    
    def _semantic_content_analysis(self, soup: BeautifulSoup, url: str, website: str, query: str, strategy: Dict) -> List[AnswerResult]:
        """Analyze content semantically to find relevant Q&A pairs"""
        results = []
        
        # Find all potential content blocks
        content_blocks = soup.find_all(['div', 'section', 'article', 'p', 'li', 'td'])
        
        for block in content_blocks:
            text = block.get_text().strip()
            if len(text) < 50:  # Skip very short blocks
                continue
            
            # Check if this block contains relevant keywords
            text_lower = text.lower()
            keyword_score = sum(1 for keyword in strategy['keywords'] if keyword in text_lower)
            
            if keyword_score >= 2:  # At least 2 keywords present
                # Try to extract Q&A from this block
                qa_pairs = self._extract_qa_pairs_from_block(text)
                
                for question, answer in qa_pairs:
                    confidence = self._calculate_confidence(question, answer, strategy)
                    
                    if confidence > 0.3:  # Minimum confidence threshold
                        results.append(AnswerResult(
                            question=question,
                            answer=answer,
                            confidence=confidence,
                            source_url=url,
                            website=website,
                            context=text[:500]
                        ))
        
        return results
    
    def _deep_text_mining(self, soup: BeautifulSoup, url: str, website: str, query: str, strategy: Dict) -> List[AnswerResult]:
        """Deep text mining to find hidden Q&A patterns"""
        results = []
        
        # Get all text and split into sentences
        full_text = soup.get_text()
        sentences = re.split(r'[.!?]+', full_text)
        
        # Look for sentences that might contain answers
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if len(sentence) < 20:
                continue
            
            # Check if sentence contains relevant information
            sentence_lower = sentence.lower()
            relevance_score = 0
            
            # Score based on keyword presence
            for keyword in strategy['keywords']:
                if keyword in sentence_lower:
                    relevance_score += 1
            
            # Look for monetary amounts (RM patterns)
            if re.search(r'rm\s*\d+', sentence_lower):
                relevance_score += 2
            
            # Look for time periods
            if re.search(r'(satu|1)\s*(tahun|year)', sentence_lower):
                relevance_score += 1
            
            # Look for free/percuma indicators
            if re.search(r'(percuma|free|tiada bayaran)', sentence_lower):
                relevance_score += 2
            
            if relevance_score >= 3:  # High relevance
                # Try to find the question for this answer
                question = self._find_question_for_sentence(sentences, i)
                
                if question:
                    confidence = min(0.9, relevance_score * 0.15)  # Cap at 0.9
                    
                    results.append(AnswerResult(
                        question=question,
                        answer=sentence,
                        confidence=confidence,
                        source_url=url,
                        website=website,
                        context=f"{question} {sentence}"
                    ))
        
        return results
    
    def _extract_qa_from_context(self, context: str, matched_text: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract question and answer from context around a match"""
        lines = context.split('\n')
        lines = [line.strip() for line in lines if line.strip()]
        
        # Find the line containing the match
        match_line_idx = -1
        for i, line in enumerate(lines):
            if matched_text.lower() in line.lower():
                match_line_idx = i
                break
        
        if match_line_idx == -1:
            return None, None
        
        # Look for question before the match
        question = None
        for i in range(max(0, match_line_idx - 3), match_line_idx + 1):
            if i < len(lines) and self._looks_like_question(lines[i]):
                question = lines[i]
                break
        
        # Use the line with match as answer, or combine nearby lines
        answer_lines = []
        start_idx = max(0, match_line_idx - 1)
        end_idx = min(len(lines), match_line_idx + 3)
        
        for i in range(start_idx, end_idx):
            if i < len(lines) and len(lines[i]) > 10:
                answer_lines.append(lines[i])
        
        answer = ' '.join(answer_lines) if answer_lines else None
        
        return question, answer
    
    def _extract_qa_pairs_from_block(self, text: str) -> List[Tuple[str, str]]:
        """Extract question-answer pairs from a text block"""
        pairs = []
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            if self._looks_like_question(line):
                question = line
                answer_parts = []
                
                # Collect answer lines
                j = i + 1
                while j < len(lines) and not self._looks_like_question(lines[j]):
                    if len(lines[j]) > 10:
                        answer_parts.append(lines[j])
                    j += 1
                
                if answer_parts:
                    answer = ' '.join(answer_parts)
                    pairs.append((question, answer))
                
                i = j
            else:
                i += 1
        
        return pairs
    
    def _find_question_for_sentence(self, sentences: List[str], sentence_idx: int) -> Optional[str]:
        """Find a question that might correspond to a given sentence"""
        # Look in nearby sentences for questions
        search_range = range(max(0, sentence_idx - 5), min(len(sentences), sentence_idx + 2))
        
        for i in search_range:
            if i != sentence_idx and self._looks_like_question(sentences[i].strip()):
                return sentences[i].strip()
        
        return None
    
    def _looks_like_question(self, text: str) -> bool:
        """Check if text looks like a question"""
        if not text or len(text) < 10:
            return False
        
        text_lower = text.lower().strip()
        
        # Check for question markers
        question_indicators = [
            '?', 'adakah', 'bagaimana', 'apakah', 'mengapa', 'bila', 'kapan',
            'siapa', 'di mana', 'berapa', 'what', 'how', 'when', 'where',
            'why', 'who', 'which', 'can', 'could', 'should', 'would'
        ]
        
        # Must contain at least one question indicator
        has_indicator = any(indicator in text_lower for indicator in question_indicators)
        
        # Additional checks
        ends_with_question = text.strip().endswith('?')
        starts_with_question_word = any(text_lower.startswith(word) for word in 
                                      ['adakah', 'bagaimana', 'apakah', 'what', 'how', 'when', 'where', 'why', 'who'])
        
        return has_indicator and (ends_with_question or starts_with_question_word or len(text) < 200)
    
    def _calculate_confidence(self, question: str, answer: str, strategy: Dict) -> float:
        """Calculate confidence score for a Q&A pair"""
        confidence = 0.0
        
        # Base confidence
        confidence += 0.2
        
        # Keyword matching
        answer_lower = answer.lower()
        question_lower = question.lower()
        
        keyword_matches = 0
        for keyword in strategy['keywords']:
            if keyword in answer_lower or keyword in question_lower:
                keyword_matches += 1
        
        confidence += min(0.4, keyword_matches * 0.1)
        
        # Specific pattern bonuses
        if strategy['type'] == 'ic_chip_cost':
            # Look for specific IC chip cost indicators
            if re.search(r'rm\s*\d+', answer_lower):
                confidence += 0.3
            if 'percuma' in answer_lower or 'free' in answer_lower:
                confidence += 0.2
            if 'satu tahun' in answer_lower or '1 tahun' in answer_lower:
                confidence += 0.2
            if 'kerosakan' in answer_lower or 'rosak' in answer_lower:
                confidence += 0.1
        
        # Question quality bonus
        if self._looks_like_question(question):
            confidence += 0.1
        
        # Answer length bonus (not too short, not too long)
        answer_length = len(answer)
        if 50 <= answer_length <= 500:
            confidence += 0.1
        elif answer_length > 500:
            confidence -= 0.1
        
        return min(1.0, confidence)

# Global agent instance
intelligent_agent = IntelligentFAQAgent()