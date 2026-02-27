import os
import re
from bs4 import BeautifulSoup
from collections import defaultdict
import json

# Language detection
def detect_language(text):
    """Detect if text contains non-English characters"""
    # Check for Japanese characters (Hiragana, Katakana, Kanji)
    japanese_pattern = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]')
    # Check for Chinese characters
    chinese_pattern = re.compile(r'[\u4E00-\u9FFF]')
    # Check for Korean characters
    korean_pattern = re.compile(r'[\uAC00-\uD7AF\u1100-\u11FF\u3130-\u318F]')
    
    if japanese_pattern.search(text):
        return 'Japanese'
    elif korean_pattern.search(text):
        return 'Korean'
    elif chinese_pattern.search(text) and not japanese_pattern.search(text):
        return 'Chinese'
    else:
        return 'English'

# Categorization based on keywords
def categorize_problem(text):
    """Categorize problem based on content analysis"""
    text_lower = text.lower()
    
    categories = {
        'Data Structures': [
            'array', 'list', 'stack', 'queue', 'tree', 'graph', 'heap', 
            'hash', 'linked list', 'binary tree', 'trie', 'segment tree'
        ],
        'Algorithms - Sorting & Searching': [
            'sort', 'search', 'binary search', 'quicksort', 'mergesort',
            'bubble sort', 'insertion sort', 'selection sort'
        ],
        'Algorithms - Dynamic Programming': [
            'dynamic programming', 'dp', 'memoization', 'optimal substructure',
            'knapsack', 'longest common subsequence', 'lcs'
        ],
        'Algorithms - Graph Theory': [
            'shortest path', 'dijkstra', 'bellman', 'floyd', 'dfs', 'bfs',
            'minimum spanning tree', 'topological sort', 'strongly connected'
        ],
        'String Processing': [
            'string', 'substring', 'pattern matching', 'regex', 'palindrome',
            'anagram', 'text processing'
        ],
        'Mathematics & Number Theory': [
            'prime', 'factorial', 'fibonacci', 'gcd', 'lcm', 'modulo',
            'combinatorics', 'probability', 'geometry', 'matrix'
        ],
        'Greedy Algorithms': [
            'greedy', 'interval', 'scheduling', 'huffman'
        ],
        'Simulation & Implementation': [
            'simulation', 'game', 'grid', 'matrix manipulation', 'cellular automata'
        ],
        'Computational Geometry': [
            'point', 'line', 'polygon', 'convex hull', 'distance', 'coordinate'
        ],
        'Bit Manipulation': [
            'bit', 'bitwise', 'xor', 'binary representation'
        ],
        'Recursion & Backtracking': [
            'recursion', 'recursive', 'backtrack', 'permutation', 'combination'
        ],
        'Database & SQL': [
            'sql', 'database', 'query', 'table', 'join', 'select'
        ],
        'Basic Programming': [
            'input', 'output', 'loop', 'condition', 'basic', 'simple calculation',
            'multiplication table', 'print'
        ]
    }
    
    # Score each category
    category_scores = defaultdict(int)
    
    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in text_lower:
                category_scores[category] += text_lower.count(keyword)
    
    # Return the category with highest score, or 'General Problem Solving' if no match
    if category_scores:
        return max(category_scores.items(), key=lambda x: x[1])[0]
    else:
        return 'General Problem Solving'

def analyze_html_file(filepath):
    """Extract and analyze content from HTML file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse HTML
        soup = BeautifulSoup(content, 'html.parser')
        text = soup.get_text()
        
        # Detect language
        language = detect_language(text)
        
        # Categorize
        category = categorize_problem(text)
        
        return {
            'language': language,
            'category': category,
            'text_length': len(text)
        }
    except Exception as e:
        return {
            'language': 'Error',
            'category': 'Error',
            'error': str(e)
        }

def main():
    problem_dir = 'problem_descriptions'
    
    # Statistics
    language_stats = defaultdict(int)
    category_stats = defaultdict(int)
    non_english_files = []
    
    # Get all HTML files
    html_files = [f for f in os.listdir(problem_dir) if f.endswith('.html')]
    total_files = len(html_files)
    
    print(f"Analyzing {total_files} HTML files...")
    print("=" * 80)
    
    # Analyze each file
    for i, filename in enumerate(html_files, 1):
        if i % 100 == 0:
            print(f"Progress: {i}/{total_files} files processed...")
        
        filepath = os.path.join(problem_dir, filename)
        result = analyze_html_file(filepath)
        
        language_stats[result['language']] += 1
        category_stats[result['category']] += 1
        
        if result['language'] != 'English':
            non_english_files.append({
                'filename': filename,
                'language': result['language']
            })
    
    # Print results
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    
    print("\n### LANGUAGE DISTRIBUTION ###")
    print("-" * 80)
    for lang, count in sorted(language_stats.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_files) * 100
        print(f"{lang:20s}: {count:5d} files ({percentage:5.2f}%)")
    
    print("\n### CATEGORY DISTRIBUTION ###")
    print("-" * 80)
    for category, count in sorted(category_stats.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_files) * 100
        print(f"{category:40s}: {count:5d} problems ({percentage:5.2f}%)")
    
    print("\n### NON-ENGLISH FILES ###")
    print("-" * 80)
    print(f"Total non-English files: {len(non_english_files)}")
    if len(non_english_files) > 0 and len(non_english_files) <= 50:
        print("\nList of non-English files:")
        for item in non_english_files[:50]:
            print(f"  - {item['filename']} ({item['language']})")
    elif len(non_english_files) > 50:
        print(f"\nShowing first 50 non-English files:")
        for item in non_english_files[:50]:
            print(f"  - {item['filename']} ({item['language']})")
        print(f"  ... and {len(non_english_files) - 50} more")
    
    # Save detailed results to JSON
    results = {
        'total_files': total_files,
        'language_stats': dict(language_stats),
        'category_stats': dict(category_stats),
        'non_english_files': non_english_files
    }
    
    with open('analysis_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 80)
    print("Detailed results saved to: analysis_results.json")
    print("=" * 80)

if __name__ == "__main__":
    main()
