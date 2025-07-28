#!/usr/bin/env python3
"""
Test script for FAQ crawler functionality
"""

import os
import sys
import logging
import time
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.faq_crawler import faq_crawler
from bot.ollama_client import ai_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_faq_crawler():
    """Test the FAQ crawler functionality"""
    print("🚀 Testing FAQ Crawler...")
    print("=" * 50)
    
    # Test 1: Scrape a single FAQ site
    print("\n📋 Test 1: Scraping single FAQ site")
    test_url = "https://www.moha.gov.my/index.php/ms/soalan-lazim"
    
    start_time = time.time()
    faq_items = faq_crawler.scrape_single_faq(test_url)
    end_time = time.time()
    
    print(f"✅ Scraped {len(faq_items)} FAQ items in {end_time - start_time:.2f} seconds")
    
    if faq_items:
        print(f"📝 Sample FAQ item:")
        sample = faq_items[0]
        print(f"   Question: {sample.question[:100]}...")
        print(f"   Answer: {sample.answer[:150]}...")
        print(f"   URL: {sample.url}")
    
    # Test 2: Search functionality
    print("\n🔍 Test 2: FAQ Search functionality")
    test_queries = [
        "kad pengenalan",
        "passport",
        "polis",
        "dadah",
        "penjara"
    ]
    
    for query in test_queries:
        print(f"\n🔎 Searching for: '{query}'")
        start_time = time.time()
        results = faq_crawler.search_faqs(query, max_results=3)
        end_time = time.time()
        
        print(f"   Found {len(results)} results in {end_time - start_time:.2f} seconds")
        
        for i, result in enumerate(results[:2], 1):
            print(f"   {i}. {result.question[:80]}... (Score: {result.relevance_score:.1f})")
    
    # Test 3: Full scraping with multithreading
    print("\n⚡ Test 3: Full multithreaded scraping")
    start_time = time.time()
    all_faqs = faq_crawler.scrape_all_faqs()
    end_time = time.time()
    
    print(f"✅ Scraped {len(all_faqs)} total FAQ items in {end_time - start_time:.2f} seconds")
    
    # Group by website
    website_counts = {}
    for faq in all_faqs:
        website_counts[faq.website] = website_counts.get(faq.website, 0) + 1
    
    print("\n📊 FAQ items by website:")
    for website, count in website_counts.items():
        print(f"   {website}: {count} items")

def test_ai_integration():
    """Test AI integration with FAQ context"""
    print("\n🤖 Testing AI Integration...")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Check if AI configuration is available
    ai_base_url = os.getenv("AI_BASE_URL")
    if not ai_base_url:
        print("⚠️  AI_BASE_URL not configured, skipping AI tests")
        return
    
    test_questions = [
        "Bagaimana cara memohon kad pengenalan baru?",
        "What are the requirements for passport application?",
        "Apa itu dadah dan bagaimana mengelakkannya?",
        "How to report to police?"
    ]
    
    for question in test_questions:
        print(f"\n❓ Question: {question}")
        print("-" * 40)
        
        try:
            start_time = time.time()
            response = ai_client.query_with_faq_context(question)
            end_time = time.time()
            
            print(f"🤖 Response (in {end_time - start_time:.2f}s):")
            print(response[:300] + "..." if len(response) > 300 else response)
            
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    """Main test function"""
    print("🧪 FAQ Crawler Test Suite")
    print("=" * 60)
    
    try:
        # Test FAQ crawler
        test_faq_crawler()
        
        # Test AI integration
        test_ai_integration()
        
        print("\n✅ All tests completed!")
        
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()