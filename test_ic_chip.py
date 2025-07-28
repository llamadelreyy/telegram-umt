#!/usr/bin/env python3
"""
Quick test for IC chip information extraction
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.faq_crawler import faq_crawler

def test_ic_chip():
    print("🔍 Testing IC chip information extraction...")
    
    # Test search for IC chip related terms
    search_terms = [
        "cip IC rosak",
        "bayaran kad pengenalan",
        "kerosakan cip",
        "RM 10"
    ]
    
    for term in search_terms:
        print(f"\n🔎 Searching for: '{term}'")
        results = faq_crawler.search_faqs(term, max_results=3)
        
        if results:
            print(f"✅ Found {len(results)} results")
            for i, result in enumerate(results, 1):
                print(f"  {i}. {result.question[:80]}...")
                if any(keyword in result.answer.lower() for keyword in ['cip', 'rm 10', 'percuma', 'kerosakan']):
                    print(f"     *** Contains IC chip info! ***")
                    print(f"     Answer: {result.answer[:150]}...")
        else:
            print("❌ No results found")

if __name__ == "__main__":
    test_ic_chip()