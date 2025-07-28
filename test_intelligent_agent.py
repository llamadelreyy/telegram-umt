#!/usr/bin/env python3
"""
Test script for the Intelligent FAQ Agent
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.intelligent_agent import intelligent_agent
from bot.ollama_client import ai_client

def test_intelligent_agent():
    print("🤖 Testing Intelligent FAQ Agent")
    print("=" * 60)
    
    # Test cases
    test_cases = [
        {
            'query': 'Berapa saya kena bayar kalau cip IC rosak?',
            'expected_keywords': ['rm 10', 'percuma', 'satu tahun', 'kerosakan']
        },
        {
            'query': 'Adakah apa-apa bayaran yang dikenakan sekiranya berlaku kerosakan terhadap cip di kad pengenalan saya?',
            'expected_keywords': ['rm 10', 'percuma', 'satu tahun']
        },
        {
            'query': 'IC chip replacement cost',
            'expected_keywords': ['rm 10', 'free', 'one year']
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test Case {i}: {test_case['query']}")
        print("-" * 50)
        
        try:
            # Test intelligent agent
            results = intelligent_agent.find_specific_answer(test_case['query'])
            
            print(f"Agent found {len(results)} results:")
            
            for j, result in enumerate(results[:3], 1):
                print(f"\n  Result {j} (Confidence: {result.confidence:.2f}):")
                print(f"    Q: {result.question}")
                print(f"    A: {result.answer[:200]}...")
                print(f"    Source: {result.website}")
                
                # Check if expected keywords are found
                answer_lower = result.answer.lower()
                found_keywords = [kw for kw in test_case['expected_keywords'] if kw in answer_lower]
                if found_keywords:
                    print(f"    ✅ Found keywords: {found_keywords}")
                else:
                    print(f"    ❌ Missing expected keywords: {test_case['expected_keywords']}")
            
            if not results:
                print("  ❌ No results found")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")

def test_ai_integration():
    print("\n\n🤖 Testing AI Integration with Intelligent Agent")
    print("=" * 60)
    
    test_question = "Berapa saya kena bayar kalau cip IC rosak?"
    print(f"Question: {test_question}")
    print("-" * 50)
    
    try:
        response = ai_client.query_with_faq_context(test_question)
        print("AI Response:")
        print(response)
        
        # Check if response contains expected information
        response_lower = response.lower()
        expected_info = ['rm 10', 'percuma', 'satu tahun', 'kerosakan']
        found_info = [info for info in expected_info if info in response_lower]
        
        print(f"\n✅ Found expected information: {found_info}")
        if len(found_info) >= 2:
            print("🎉 AI response contains relevant IC chip cost information!")
        else:
            print("⚠️ AI response may be missing some expected information")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_intelligent_agent()
    test_ai_integration()