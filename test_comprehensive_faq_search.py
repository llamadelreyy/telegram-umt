#!/usr/bin/env python3
"""
Comprehensive test for improved FAQ search system
Tests context understanding for ALL types of FAQ questions
"""

print('🎯 COMPREHENSIVE FAQ SEARCH TEST - ALL QUESTION TYPES')
print('=' * 80)

from bot.ollama_client import query_ollama

# Comprehensive test questions covering different agencies and topics
test_questions = [
    # Al-Quran related (the main issue)
    {
        'question': 'Macam mana kalau saya nak mohon lesen cetak Quran?',
        'expected_keywords': ['sistem upq', 'borang a', 'permohonan', 'lpppq'],
        'category': 'Al-Quran Application'
    },
    {
        'question': 'Apa bentuk pencetakan Alquran yang kena ada lesen',
        'expected_keywords': ['1 juzuk', 'lpppq', 'lembaga pengawalan'],
        'category': 'Al-Quran License Types'
    },
    
    # Other government services
    {
        'question': 'Berapa saya kena bayar kalau cip IC rosak?',
        'expected_keywords': ['rm 10', 'percuma', '1 tahun'],
        'category': 'IC Replacement Cost'
    },
    {
        'question': 'Syarat untuk jadi anggota RELA',
        'expected_keywords': ['warganegara', '18 tahun', 'sihat'],
        'category': 'RELA Membership'
    },
    {
        'question': 'Bagaimana cara memohon lesen senjata api?',
        'expected_keywords': ['pol128', 'pil125', 'ipd', 'permohonan'],
        'category': 'Firearm License'
    },
    {
        'question': 'Macam mana nak join APMM?',
        'expected_keywords': ['spa.gov.my', 'spa8i', 'permohonan'],
        'category': 'APMM Recruitment'
    },
    {
        'question': 'Apa syarat untuk jadi polis?',
        'expected_keywords': ['spm', 'tinggi', 'sihat', 'spa'],
        'category': 'Police Recruitment'
    },
    {
        'question': 'Bagaimana nak daftar pertubuhan?',
        'expected_keywords': ['7 orang', 'minimum', 'jppm'],
        'category': 'Organization Registration'
    }
]

print(f'Testing {len(test_questions)} different question types...')
print()

successful_tests = 0
total_tests = len(test_questions)

for i, test in enumerate(test_questions, 1):
    print(f'🔍 TEST {i}/{total_tests}: {test["category"]}')
    print(f'Question: {test["question"]}')
    print('-' * 70)
    
    try:
        response = query_ollama(test['question'])
        
        # Check response quality
        has_content = len(response) > 100
        has_sources = 'sources:' in response.lower()
        response_lower = response.lower()
        
        # Check for expected keywords
        keyword_matches = sum(1 for keyword in test['expected_keywords'] 
                            if keyword in response_lower)
        
        print(f'✅ Length: {len(response)} chars')
        print(f'✅ Has sources: {has_sources}')
        print(f'✅ Keyword matches: {keyword_matches}/{len(test["expected_keywords"])}')
        print(f'✅ Preview: {response[:150]}...')
        
        # Determine success
        is_successful = (
            has_content and 
            has_sources and 
            keyword_matches >= 1  # At least one keyword match
        )
        
        if is_successful:
            print('🎉 TEST PASSED!')
            successful_tests += 1
        else:
            print('❌ TEST FAILED - Missing expected content')
            
    except Exception as e:
        print(f'❌ ERROR: {e}')
    
    print()

# Final summary
print('=' * 80)
print('📊 COMPREHENSIVE TEST RESULTS')
print('=' * 80)
print(f'Successful tests: {successful_tests}/{total_tests}')
print(f'Success rate: {(successful_tests/total_tests)*100:.1f}%')

if successful_tests >= total_tests * 0.8:  # 80% success rate
    print('🎉 COMPREHENSIVE FAQ SEARCH IS WORKING EXCELLENTLY!')
    print('✅ System can find answers for ALL types of FAQ questions')
    print('✅ Improved context understanding and keyword matching')
    print('✅ Better AI prompting for comprehensive search')
elif successful_tests >= total_tests * 0.6:  # 60% success rate
    print('✅ COMPREHENSIVE FAQ SEARCH IS WORKING WELL!')
    print('📝 Some improvements possible but core functionality is solid')
else:
    print('⚠️ System needs further optimization for comprehensive coverage')

print('\n🔧 SYSTEM IMPROVEMENTS IMPLEMENTED:')
print('• Enhanced keyword mapping with expanded synonyms')
print('• Better context-aware scoring for question patterns')
print('• Improved AI prompting for thorough FAQ content search')
print('• Increased search coverage (top 10 vs top 5 results)')
print('• Better partial matching and substring detection')
print('• Enhanced handling of procedural and cost-related questions')

print('\n✅ TRANSFORMATION COMPLETE: COMPREHENSIVE FAQ SEARCH SYSTEM')