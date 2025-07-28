#!/usr/bin/env python3
"""
Demonstration that the system is working correctly
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.ollama_client import ai_client

def main():
    print("🎯 DEMONSTRATION: Working FAQ System")
    print("=" * 60)
    
    # The exact question the user asked
    question = "Berapa saya kena bayar kalau cip IC rosak?"
    
    print(f"User Question: {question}")
    print("=" * 60)
    
    try:
        print("🤖 Getting AI response with intelligent agent...")
        response = ai_client.query_with_faq_context(question)
        
        print("\n📝 COMPLETE AI RESPONSE:")
        print("-" * 40)
        print(response)
        print("-" * 40)
        
        # Verify the response contains the correct information
        response_lower = response.lower()
        
        print("\n✅ VERIFICATION:")
        checks = [
            ("Contains RM 10 fee information", "rm 10" in response_lower or "rm10" in response_lower),
            ("Contains free replacement info", "percuma" in response_lower or "free" in response_lower),
            ("References JPN authority", "jpn" in response_lower or "jabatan pendaftaran" in response_lower),
            ("Contains one year period", "satu tahun" in response_lower or "1 tahun" in response_lower),
            ("Mentions damage conditions", "kerosakan" in response_lower or "rosak" in response_lower)
        ]
        
        for check_name, result in checks:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {status}: {check_name}")
        
        # Overall assessment
        passed_checks = sum(1 for _, result in checks if result)
        print(f"\n🏆 OVERALL: {passed_checks}/{len(checks)} checks passed")
        
        if passed_checks >= 4:
            print("🎉 SYSTEM IS WORKING CORRECTLY!")
            print("The intelligent agent successfully found and provided accurate IC chip cost information.")
        else:
            print("⚠️  System may need further adjustment")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()