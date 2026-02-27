import os
import re
from bs4 import BeautifulSoup
from collections import defaultdict
import json

def detect_language(text):
    """Detect if text contains non-English characters"""
    japanese_pattern = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]')
    korean_pattern = re.compile(r'[\uAC00-\uD7AF\u1100-\u11FF\u3130-\u318F]')
    
    if japanese_pattern.search(text):
        return 'Japanese'
    elif korean_pattern.search(text):
        return 'Korean'
    else:
        return 'English'

def categorize_by_computing_field(text):
    """Categorize problems by computing field/job role"""
    text_lower = text.lower()
    
    # Define computing fields with their keywords
    fields = {
        'Software Development - Backend': [
            'api', 'server', 'database', 'sql', 'query', 'transaction',
            'rest', 'http', 'authentication', 'authorization'
        ],
        'Software Development - Frontend': [
            'html', 'css', 'javascript', 'dom', 'ui', 'user interface',
            'web page', 'browser'
        ],
        'Data Structures & Algorithms': [
            'array', 'list', 'stack', 'queue', 'tree', 'graph', 'heap',
            'hash', 'linked list', 'binary tree', 'sort', 'search',
            'algorithm', 'complexity', 'big o'
        ],
        'Competitive Programming': [
            'contest', 'competitive', 'optimization', 'time limit',
            'memory limit', 'test case', 'sample input', 'sample output'
        ],
        'Machine Learning & AI': [
            'neural', 'machine learning', 'classification', 'regression',
            'training', 'model', 'prediction', 'ai', 'artificial intelligence'
        ],
        'Data Science & Analytics': [
            'statistics', 'data analysis', 'visualization', 'dataset',
            'mean', 'median', 'standard deviation', 'correlation'
        ],
        'Computer Graphics & Game Development': [
            'graphics', 'rendering', 'game', 'sprite', 'animation',
            'collision', '3d', '2d', 'pixel', 'texture'
        ],
        'Systems Programming': [
            'memory management', 'pointer', 'process', 'thread',
            'concurrency', 'parallel', 'operating system', 'kernel'
        ],
        'Network Programming': [
            'network', 'socket', 'tcp', 'udp', 'ip address', 'packet',
            'protocol', 'routing'
        ],
        'Cryptography & Security': [
            'encryption', 'decryption', 'cipher', 'hash function',
            'security', 'cryptography', 'key', 'password'
        ],
        'Computational Mathematics': [
            'prime', 'factorial', 'fibonacci', 'gcd', 'lcm', 'modulo',
            'combinatorics', 'probability', 'number theory', 'matrix',
            'linear algebra', 'calculus'
        ],
        'Computational Geometry': [
            'point', 'line', 'polygon', 'convex hull', 'distance',
            'coordinate', 'geometry', 'angle', 'circle', 'rectangle'
        ],
        'String Processing & Text Analysis': [
            'string', 'substring', 'pattern matching', 'regex',
            'palindrome', 'anagram', 'text processing', 'parsing'
        ],
        'Dynamic Programming & Optimization': [
            'dynamic programming', 'dp', 'memoization', 'optimal',
            'knapsack', 'longest common subsequence', 'optimization'
        ],
        'Graph Theory & Networks': [
            'shortest path', 'dijkstra', 'bellman', 'floyd', 'dfs', 'bfs',
            'minimum spanning tree', 'topological sort', 'connected component',
            'cycle detection'
        ],
        'Simulation & Modeling': [
            'simulation', 'cellular automata', 'game of life', 'model',
            'simulate', 'step by step'
        ],
        'Basic Programming & Logic': [
            'input', 'output', 'loop', 'condition', 'if', 'else',
            'for loop', 'while loop', 'basic', 'simple', 'print',
            'read', 'write', 'variable'
        ]
    }
    
    # Score each field
    field_scores = defaultdict(int)
    
    for field, keywords in fields.items():
        for keyword in keywords:
            if keyword in text_lower:
                # Weight longer keywords more heavily
                weight = len(keyword.split())
                field_scores[field] += text_lower.count(keyword) * weight
    
    # Return the field with highest score
    if field_scores:
        return max(field_scores.items(), key=lambda x: x[1])[0]
    else:
        return 'General Problem Solving'

def extract_problem_info(filepath):
    """Extract detailed information from HTML file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        text = soup.get_text()
        
        # Extract title if available
        title_tag = soup.find('h1')
        title = title_tag.get_text().strip() if title_tag else 'No Title'
        
        # Detect language
        language = detect_language(text)
        
        # Categorize by field
        field = categorize_by_computing_field(text)
        
        return {
            'title': title,
            'language': language,
            'field': field,
            'text_length': len(text),
            'has_code_template': 'template' in text.lower()
        }
    except Exception as e:
        return {
            'title': 'Error',
            'language': 'Error',
            'field': 'Error',
            'error': str(e)
        }

def main():
    problem_dir = 'problem_descriptions'
    
    # Statistics
    language_stats = defaultdict(int)
    field_stats = defaultdict(int)
    non_english_files = []
    field_examples = defaultdict(list)
    
    # Get all HTML files
    html_files = sorted([f for f in os.listdir(problem_dir) if f.endswith('.html')])
    total_files = len(html_files)
    
    print(f"Analyzing {total_files} HTML files for computing field categorization...")
    print("=" * 80)
    
    # Analyze each file
    for i, filename in enumerate(html_files, 1):
        if i % 100 == 0:
            print(f"Progress: {i}/{total_files} files processed...")
        
        filepath = os.path.join(problem_dir, filename)
        result = extract_problem_info(filepath)
        
        language_stats[result['language']] += 1
        field_stats[result['field']] += 1
        
        # Store examples for each field (max 3 per field)
        if len(field_examples[result['field']]) < 3:
            field_examples[result['field']].append({
                'filename': filename,
                'title': result['title']
            })
        
        if result['language'] != 'English':
            non_english_files.append({
                'filename': filename,
                'language': result['language'],
                'title': result['title']
            })
    
    # Print results
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE - COMPUTING FIELDS CATEGORIZATION")
    print("=" * 80)
    
    print("\n### LANGUAGE DISTRIBUTION ###")
    print("-" * 80)
    for lang, count in sorted(language_stats.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_files) * 100
        print(f"{lang:20s}: {count:5d} files ({percentage:5.2f}%)")
    
    print("\n### COMPUTING FIELD / JOB CATEGORY DISTRIBUTION ###")
    print("-" * 80)
    print(f"{'Field/Category':<50s} {'Count':>8s} {'Percentage':>12s}")
    print("-" * 80)
    
    for field, count in sorted(field_stats.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_files) * 100
        print(f"{field:<50s} {count:>8d} {percentage:>11.2f}%")
    
    print("\n### FIELD EXAMPLES ###")
    print("-" * 80)
    for field in sorted(field_stats.keys()):
        if field_examples[field]:
            print(f"\n{field}:")
            for example in field_examples[field]:
                print(f"  - {example['filename']}: {example['title'][:60]}")
    
    print("\n### SUMMARY FOR AI COMPILER PROJECT ###")
    print("=" * 80)
    print(f"Total Problems: {total_files}")
    print(f"English Problems: {language_stats['English']} ({language_stats['English']/total_files*100:.1f}%)")
    print(f"Japanese Problems: {language_stats.get('Japanese', 0)} ({language_stats.get('Japanese', 0)/total_files*100:.1f}%)")
    print(f"Need Translation: {len(non_english_files)} files")
    print("\nTop 5 Computing Fields:")
    for i, (field, count) in enumerate(sorted(field_stats.items(), key=lambda x: x[1], reverse=True)[:5], 1):
        print(f"  {i}. {field}: {count} problems ({count/total_files*100:.1f}%)")
    
    # Save detailed results
    results = {
        'total_files': total_files,
        'language_stats': dict(language_stats),
        'field_stats': dict(field_stats),
        'non_english_files': non_english_files[:100],  # Save first 100
        'field_examples': {k: v for k, v in field_examples.items()}
    }
    
    with open('field_categorization_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 80)
    print("Detailed results saved to: field_categorization_results.json")
    print("=" * 80)

if __name__ == "__main__":
    main()
