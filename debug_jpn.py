#!/usr/bin/env python3
"""
Debug script to check JPN FAQ extraction
"""

import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_jpn_extraction():
    url = 'https://www.jpn.gov.my/my/soalan-lazim/soalan-lazim-kad-pengenalan'
    
    print(f"Testing URL: {url}")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    session.verify = False
    
    try:
        response = session.get(url, timeout=15)
        response.raise_for_status()
        
        print(f"Response status: {response.status_code}")
        print(f"Content length: {len(response.content)}")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for FAQ content
        print("\n=== Looking for FAQ patterns ===")
        
        # Check for common FAQ structures
        questions = soup.find_all(['h3', 'h4', 'h5', 'strong', 'b'])
        print(f"Found {len(questions)} potential question elements")
        
        for i, q in enumerate(questions[:5]):
            text = q.get_text().strip()
            if len(text) > 10:
                print(f"{i+1}. {text[:100]}...")
        
        # Look for specific IC chip content
        print("\n=== Searching for IC chip content ===")
        text_content = soup.get_text().lower()
        
        if 'cip' in text_content:
            print("✅ Found 'cip' in content")
        if 'rm 10' in text_content or 'rm10' in text_content:
            print("✅ Found 'RM 10' in content")
        if 'percuma' in text_content:
            print("✅ Found 'percuma' in content")
        if 'kerosakan' in text_content:
            print("✅ Found 'kerosakan' in content")
            
        # Extract a sample of the content
        print("\n=== Sample content ===")
        sample = soup.get_text()[:1000]
        print(sample)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_jpn_extraction()