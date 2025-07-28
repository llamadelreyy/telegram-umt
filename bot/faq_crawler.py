"""
FAQ Web Crawler Module
Fast multithreaded crawler for Malaysian government FAQ sites
"""

import re
import time
import logging
import asyncio
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup
import html2text
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from .config import FAQ_WEBSITES, SCRAPING_CONFIG

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class FAQItem:
    """Represents a single FAQ item"""
    question: str
    answer: str
    url: str
    website: str
    relevance_score: float = 0.0

class FAQCrawler:
    """Fast multithreaded FAQ crawler"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': SCRAPING_CONFIG["user_agent"]
        })
        # Disable SSL verification for government sites with certificate issues
        self.session.verify = False
        # Disable SSL warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = True
        self.html_converter.ignore_images = True
        self.html_converter.body_width = 0  # No line wrapping
        
        # Cache for scraped content
        self._cache = {}
        self._cache_timestamp = {}
        self.cache_duration = 3600  # 1 hour cache
    
    def _is_cache_valid(self, url: str) -> bool:
        """Check if cached content is still valid"""
        if url not in self._cache:
            return False
        return time.time() - self._cache_timestamp[url] < self.cache_duration
    
    def _extract_faq_content(self, soup: BeautifulSoup, url: str) -> List[FAQItem]:
        """Extract FAQ items from parsed HTML"""
        faq_items = []
        website = urlparse(url).netloc
        
        # Enhanced FAQ extraction strategies
        strategies = [
            self._extract_structured_faqs,
            self._extract_text_based_faqs,
            self._extract_table_faqs,
            self._extract_accordion_faqs,
            self._extract_general_content_faqs
        ]
        
        for strategy in strategies:
            items = strategy(soup, url, website)
            if items:
                faq_items.extend(items)
                # If we found good structured content, don't try fallback methods
                if len(items) > 3:
                    break
        
        return faq_items
    
    def _extract_structured_faqs(self, soup: BeautifulSoup, url: str, website: str) -> List[FAQItem]:
        """Extract FAQs from structured HTML elements"""
        faq_items = []
        
        # Look for common FAQ structures
        question_selectors = [
            'h3', 'h4', 'h5', 'h6',
            '.question', '.faq-question', '.accordion-header',
            'strong', 'b', 'dt'
        ]
        
        for selector in question_selectors:
            elements = soup.select(selector)
            for elem in elements:
                question_text = self._clean_text(elem.get_text())
                
                # Check if this looks like a question
                if self._is_likely_question(question_text):
                    answer_text = self._find_answer_for_element(elem)
                    if answer_text and len(answer_text) > 20:
                        faq_items.append(FAQItem(
                            question=question_text,
                            answer=answer_text,
                            url=url,
                            website=website
                        ))
        
        return faq_items
    
    def _extract_text_based_faqs(self, soup: BeautifulSoup, url: str, website: str) -> List[FAQItem]:
        """Extract FAQs by analyzing text patterns"""
        faq_items = []
        
        # Get main content areas
        content_areas = self._get_main_content_areas(soup)
        
        for area in content_areas:
            text_content = area.get_text()
            lines = [line.strip() for line in text_content.split('\n') if line.strip()]
            
            i = 0
            while i < len(lines):
                line = lines[i]
                
                # Check if this line is a question
                if self._is_likely_question(line):
                    question = line
                    answer_parts = []
                    
                    # Collect answer lines until next question or end
                    j = i + 1
                    while j < len(lines) and not self._is_likely_question(lines[j]):
                        if len(lines[j]) > 10:  # Skip very short lines
                            answer_parts.append(lines[j])
                        j += 1
                    
                    if answer_parts:
                        answer = ' '.join(answer_parts)
                        if len(answer) > 30:  # Ensure substantial answer
                            faq_items.append(FAQItem(
                                question=question,
                                answer=answer,
                                url=url,
                                website=website
                            ))
                    
                    i = j
                else:
                    i += 1
        
        return faq_items
    
    def _extract_table_faqs(self, soup: BeautifulSoup, url: str, website: str) -> List[FAQItem]:
        """Extract FAQs from table structures"""
        faq_items = []
        
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    question_text = self._clean_text(cells[0].get_text())
                    answer_text = self._clean_text(cells[1].get_text())
                    
                    if (self._is_likely_question(question_text) and
                        len(answer_text) > 20):
                        faq_items.append(FAQItem(
                            question=question_text,
                            answer=answer_text,
                            url=url,
                            website=website
                        ))
        
        return faq_items
    
    def _extract_accordion_faqs(self, soup: BeautifulSoup, url: str, website: str) -> List[FAQItem]:
        """Extract FAQs from accordion/collapsible structures"""
        faq_items = []
        
        # Look for accordion patterns
        accordion_selectors = [
            '.accordion-item', '.collapse', '.panel',
            '[data-toggle="collapse"]', '.expandable'
        ]
        
        for selector in accordion_selectors:
            items = soup.select(selector)
            for item in items:
                # Look for question in header
                header = item.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', '.header', '.title'])
                if header:
                    question_text = self._clean_text(header.get_text())
                    
                    # Look for answer in body/content
                    body = item.find(['.body', '.content', '.panel-body', '.collapse-content'])
                    if not body:
                        # Fallback: get all text except header
                        body_text = item.get_text()
                        header_text = header.get_text()
                        answer_text = body_text.replace(header_text, '').strip()
                    else:
                        answer_text = self._clean_text(body.get_text())
                    
                    if (self._is_likely_question(question_text) and
                        len(answer_text) > 20):
                        faq_items.append(FAQItem(
                            question=question_text,
                            answer=answer_text,
                            url=url,
                            website=website
                        ))
        
        return faq_items
    
    def _extract_general_content_faqs(self, soup: BeautifulSoup, url: str, website: str) -> List[FAQItem]:
        """Fallback: extract general content as single FAQ item"""
        content_areas = self._get_main_content_areas(soup)
        
        if content_areas:
            all_text = ' '.join([self._clean_text(area.get_text()) for area in content_areas])
            if len(all_text) > 100:
                return [FAQItem(
                    question="General FAQ Information",
                    answer=all_text[:SCRAPING_CONFIG["max_content_length"]],
                    url=url,
                    website=website
                )]
        
        return []
    
    def _get_main_content_areas(self, soup: BeautifulSoup) -> List:
        """Get main content areas from the page"""
        # Remove navigation, footer, header elements
        for elem in soup(['nav', 'footer', 'header', 'script', 'style', 'aside']):
            elem.decompose()
        
        # Look for main content containers
        content_selectors = [
            'main', 'article', '.content', '.main-content',
            '.page-content', '.entry-content', '#content',
            '.container', '.wrapper', 'body'
        ]
        
        content_areas = []
        for selector in content_selectors:
            areas = soup.select(selector)
            if areas:
                content_areas.extend(areas)
                break  # Use first successful selector
        
        # Fallback: use body if no specific content areas found
        if not content_areas:
            body = soup.find('body')
            if body:
                content_areas = [body]
        
        return content_areas
    
    def _is_likely_question(self, text: str) -> bool:
        """Check if text looks like a question"""
        if not text or len(text) < 10:
            return False
        
        text_lower = text.lower().strip()
        
        # Check for question markers
        question_indicators = [
            '?', 'adakah', 'bagaimana', 'apakah', 'mengapa', 'bila', 'kapan',
            'siapa', 'di mana', 'berapa', 'what', 'how', 'when', 'where',
            'why', 'who', 'which', 'can', 'could', 'should', 'would',
            'is', 'are', 'do', 'does', 'did'
        ]
        
        # Must contain at least one question indicator
        has_indicator = any(indicator in text_lower for indicator in question_indicators)
        
        # Additional checks
        ends_with_question = text.strip().endswith('?')
        starts_with_question_word = any(text_lower.startswith(word) for word in
                                      ['adakah', 'bagaimana', 'apakah', 'what', 'how', 'when', 'where', 'why', 'who'])
        
        return has_indicator and (ends_with_question or starts_with_question_word or len(text) < 200)
    
    def _find_answer_for_element(self, element) -> str:
        """Find answer text for a question element"""
        answer_parts = []
        
        # Strategy 1: Look at next siblings
        for sibling in element.find_next_siblings():
            if sibling.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                break  # Stop at next heading
            
            text = self._clean_text(sibling.get_text())
            if len(text) > 10:
                answer_parts.append(text)
                if len(' '.join(answer_parts)) > 500:  # Limit answer length
                    break
        
        # Strategy 2: Look at parent's next sibling
        if not answer_parts and element.parent:
            next_elem = element.parent.find_next_sibling()
            if next_elem:
                text = self._clean_text(next_elem.get_text())
                if len(text) > 10:
                    answer_parts.append(text)
        
        # Strategy 3: Look within same container
        if not answer_parts:
            container = element.find_parent(['div', 'section', 'article', 'li'])
            if container:
                container_text = container.get_text()
                element_text = element.get_text()
                answer_text = container_text.replace(element_text, '').strip()
                if len(answer_text) > 20:
                    answer_parts.append(answer_text)
        
        return ' '.join(answer_parts).strip()
    
    def _extract_with_pattern(self, soup: BeautifulSoup, pattern: Dict, url: str, website: str) -> List[FAQItem]:
        """Extract FAQ items using a specific pattern"""
        faq_items = []
        
        # Find question elements
        question_elements = []
        for tag in pattern['question_tags']:
            if tag.startswith('.'):
                question_elements.extend(soup.find_all(class_=tag[1:]))
            else:
                question_elements.extend(soup.find_all(tag))
        
        for q_elem in question_elements:
            question_text = self._clean_text(q_elem.get_text())
            if not question_text or len(question_text) < 10:
                continue
            
            # Find corresponding answer
            answer_text = self._find_answer_for_question(q_elem, pattern['answer_tags'])
            
            if answer_text and len(answer_text) > 20:
                faq_items.append(FAQItem(
                    question=question_text,
                    answer=answer_text,
                    url=url,
                    website=website
                ))
        
        return faq_items
    
    def _find_answer_for_question(self, question_elem, answer_tags: List[str]) -> str:
        """Find answer text following a question element"""
        answer_parts = []
        
        # Look for next siblings
        for sibling in question_elem.find_next_siblings():
            if sibling.name in answer_tags or any(cls in sibling.get('class', []) for cls in [tag[1:] for tag in answer_tags if tag.startswith('.')]):
                answer_parts.append(self._clean_text(sibling.get_text()))
            elif sibling.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                break  # Stop at next heading
        
        # If no siblings found, look for parent's next elements
        if not answer_parts and question_elem.parent:
            next_elem = question_elem.parent.find_next_sibling()
            if next_elem:
                answer_parts.append(self._clean_text(next_elem.get_text()))
        
        return ' '.join(answer_parts).strip()
    
    def _extract_general_content(self, soup: BeautifulSoup, url: str, website: str) -> List[FAQItem]:
        """Extract general content when no structured FAQ is found"""
        # Remove navigation, footer, header elements
        for elem in soup(['nav', 'footer', 'header', 'script', 'style']):
            elem.decompose()
        
        # Get main content
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|main'))
        if not main_content:
            main_content = soup.find('body')
        
        if main_content:
            text_content = self._clean_text(main_content.get_text())
            if len(text_content) > 100:
                return [FAQItem(
                    question="General FAQ Information",
                    answer=text_content[:SCRAPING_CONFIG["max_content_length"]],
                    url=url,
                    website=website
                )]
        
        return []
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n', text)
        text = text.strip()
        
        # Remove common unwanted patterns
        text = re.sub(r'^\s*[-•]\s*', '', text)  # Remove bullet points
        text = re.sub(r'\s*\|\s*', ' ', text)   # Remove pipe separators
        
        return text
    
    def scrape_single_faq(self, url: str) -> List[FAQItem]:
        """Scrape FAQ content from a single URL"""
        try:
            # Check cache first
            if self._is_cache_valid(url):
                logger.info(f"Using cached content for {url}")
                return self._cache[url]
            
            logger.info(f"Scraping FAQ from: {url}")
            response = self.session.get(url, timeout=SCRAPING_CONFIG["timeout"])
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract FAQ items
            faq_items = self._extract_faq_content(soup, url)
            
            # Cache the results
            self._cache[url] = faq_items
            self._cache_timestamp[url] = time.time()
            
            logger.info(f"Extracted {len(faq_items)} FAQ items from {url}")
            return faq_items
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return []
    
    def scrape_all_faqs(self) -> List[FAQItem]:
        """Scrape all FAQ websites using multithreading"""
        all_faqs = []
        
        logger.info(f"Starting to scrape {len(FAQ_WEBSITES)} FAQ websites with {SCRAPING_CONFIG['max_workers']} workers")
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=SCRAPING_CONFIG['max_workers']) as executor:
            # Submit all scraping tasks
            future_to_url = {executor.submit(self.scrape_single_faq, url): url for url in FAQ_WEBSITES}
            
            # Collect results as they complete
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    faq_items = future.result()
                    all_faqs.extend(faq_items)
                except Exception as e:
                    logger.error(f"Error processing {url}: {str(e)}")
        
        end_time = time.time()
        logger.info(f"Scraped {len(all_faqs)} total FAQ items in {end_time - start_time:.2f} seconds")
        
        return all_faqs
    
    def search_faqs(self, query: str, max_results: int = 10) -> List[FAQItem]:
        """Search FAQ items for relevant content"""
        logger.info(f"Searching FAQs for: {query}")
        
        # Get all FAQ items
        all_faqs = self.scrape_all_faqs()
        
        if not all_faqs:
            return []
        
        # Calculate relevance scores
        query_lower = query.lower()
        query_words = set(re.findall(r'\w+', query_lower))
        
        for faq in all_faqs:
            score = 0.0
            
            # Check question relevance (higher weight)
            question_lower = faq.question.lower()
            question_words = set(re.findall(r'\w+', question_lower))
            question_matches = len(query_words.intersection(question_words))
            score += question_matches * 3.0
            
            # Check answer relevance
            answer_lower = faq.answer.lower()
            answer_words = set(re.findall(r'\w+', answer_lower))
            answer_matches = len(query_words.intersection(answer_words))
            score += answer_matches * 1.0
            
            # Bonus for exact phrase matches
            if query_lower in question_lower:
                score += 5.0
            elif query_lower in answer_lower:
                score += 2.0
            
            faq.relevance_score = score
        
        # Sort by relevance and return top results
        relevant_faqs = [faq for faq in all_faqs if faq.relevance_score > 0]
        relevant_faqs.sort(key=lambda x: x.relevance_score, reverse=True)
        
        logger.info(f"Found {len(relevant_faqs)} relevant FAQ items")
        return relevant_faqs[:max_results]

# Global crawler instance
faq_crawler = FAQCrawler()