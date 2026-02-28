"""
MMLU-Pro Computing Domain Analysis - Final Clean Version

Analyzes MMLU-Pro dataset focusing on computing-relevant domains.
Produces clean, meaningful output for academic reporting.

Author: Python Data Analysis Agent
Date: 2026-02-06
"""

from datasets import load_dataset
import pandas as pd
from collections import Counter

# ============================================================================
# CONFIGURATION
# ============================================================================

# Define computing-relevant categories with detailed metadata
COMPUTING_DOMAINS = {
    'computer science': {
        'display_name': 'Computer Science',
        'relevance': 'Direct CS Knowledge',
        'difficulty': 'Graduate Level',
        'target': 'Senior/Expert',
        'description': 'Algorithms, Data Structures, Security, Complexity Theory'
    },
    'math': {
        'display_name': 'Mathematics',
        'relevance': 'Logic & Reasoning',
        'difficulty': 'Advanced',
        'target': 'Mid to Senior',
        'description': 'Discrete Math, Logic, Computational Thinking'
    },
    'engineering': {
        'display_name': 'Engineering',
        'relevance': 'System Logic',
        'difficulty': 'Advanced',
        'target': 'Senior (Systems)',
        'description': 'Embedded Systems, Hardware-Software Interaction'
    },
    'physics': {
        'display_name': 'Physics',
        'relevance': 'Computational Physics',
        'difficulty': 'Advanced',
        'target': 'Senior (Scientific)',
        'description': 'Simulations, Numerical Methods, ML Applications'
    },
    'economics': {
        'display_name': 'Economics',
        'relevance': 'Algorithmic Thinking',
        'difficulty': 'Advanced',
        'target': 'Senior (FinTech)',
        'description': 'Game Theory, Optimization, Trading Algorithms'
    }
}

# ============================================================================
# LOAD DATASET
# ============================================================================

print("="*80)
print("MMLU-PRO COMPUTING DOMAIN ANALYSIS")
print("="*80)
print("\n[1/4] Loading MMLU-Pro dataset from HuggingFace...")

dataset = load_dataset("TIGER-Lab/MMLU-Pro", split="test")
total_questions = len(dataset)

print(f"      [OK] Loaded {total_questions:,} questions from test split")

# ============================================================================
# ANALYZE ALL DOMAINS
# ============================================================================

print("\n[2/4] Analyzing domain distribution...")

# Count questions per category
category_counts = Counter([ex['category'] for ex in dataset])
all_domains = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)

# Calculate computing-relevant total
computing_total = sum(count for cat, count in all_domains if cat in COMPUTING_DOMAINS)

print(f"      [OK] Found {len(all_domains)} domains")
print(f"      [OK] Computing-relevant: {computing_total:,} questions ({computing_total/total_questions*100:.1f}%)")

# ============================================================================
# DISPLAY RESULTS
# ============================================================================

print("\n[3/4] Domain Distribution Summary")
print("="*80)
print(f"\n{'Domain':<30} {'Questions':>12} {'Percentage':>12} {'Relevant':>15}")
print("-"*80)

for category, count in all_domains:
    percentage = (count / total_questions) * 100
    is_computing = "[YES]" if category in COMPUTING_DOMAINS else "No"
    print(f"{category.title():<30} {count:>12,} {percentage:>11.2f}% {is_computing:>15}")

print("-"*80)
print(f"{'TOTAL':<30} {total_questions:>12,} {100.0:>11.2f}%")
print(f"{'Computing-Relevant Total':<30} {computing_total:>12,} {computing_total/total_questions*100:>11.2f}%")
print("="*80)

# ============================================================================
# COMPUTING-RELEVANT BREAKDOWN
# ============================================================================

print("\n" + "="*80)
print("COMPUTING-RELEVANT DOMAINS BREAKDOWN")
print("="*80)
print(f"\n{'#':<4} {'Domain':<25} {'Questions':>12} {'%':>8} {'Target Level':<25}")
print("-"*80)

computing_data = []
for category, info in COMPUTING_DOMAINS.items():
    count = category_counts.get(category, 0)
    if count > 0:
        computing_data.append({
            'Domain': info['display_name'],
            'Questions': count,
            'Percentage': round((count / total_questions) * 100, 2),
            'Relevance_Type': info['relevance'],
            'Difficulty_Level': info['difficulty'],
            'Target_Candidate': info['target'],
            'Description': info['description']
        })

# Sort by question count
computing_data.sort(key=lambda x: x['Questions'], reverse=True)

# Display summary table
for i, item in enumerate(computing_data, 1):
    print(f"{i:<4} {item['Domain']:<25} {item['Questions']:>12,} {item['Percentage']:>7.2f}% {item['Target_Candidate']:<25}")

print("-"*80)
print(f"{'':4} {'TOTAL':<25} {computing_total:>12,} {computing_total/total_questions*100:>7.2f}%")
print("="*80)

# Display detailed breakdown
print("\nDETAILED BREAKDOWN:")
print("-"*80)

for i, item in enumerate(computing_data, 1):
    print(f"\n{i}. {item['Domain'].upper()}")
    print(f"   Questions:    {item['Questions']:,} ({item['Percentage']}%)")
    print(f"   Relevance:    {item['Relevance_Type']}")
    print(f"   Difficulty:   {item['Difficulty_Level']}")
    print(f"   Target:       {item['Target_Candidate']}")
    print(f"   Description:  {item['Description']}")

# ============================================================================
# SAVE TO CSV
# ============================================================================

print("\n[4/4] Saving results to CSV...")

# Create comprehensive DataFrame
df = pd.DataFrame(computing_data)
df = df[['Domain', 'Questions', 'Percentage', 'Relevance_Type', 
         'Difficulty_Level', 'Target_Candidate', 'Description']]

# Save to CSV
output_file = 'mmlu_computing_domains.csv'
df.to_csv(output_file, index=False)

print(f"      [OK] Saved to: {output_file}")
print(f"      [OK] Contains: {len(computing_data)} computing-relevant domains")

# ============================================================================
# SUMMARY STATISTICS
# ============================================================================

print("="*80)
print("SUMMARY STATISTICS")
print("="*80)

print(f"\nDataset: MMLU-Pro (Test Split)")
print(f"  Total Questions:        {total_questions:,}")
print(f"  Total Domains:          {len(all_domains)}")
print(f"\nComputing-Relevant:")
print(f"  Domains:                {len(computing_data)}")
print(f"  Questions:              {computing_total:,} ({computing_total/total_questions*100:.1f}%)")
print(f"  Largest Domain:         {computing_data[0]['Domain']} ({computing_data[0]['Questions']:,} questions)")
print(f"  Smallest Domain:        {computing_data[-1]['Domain']} ({computing_data[-1]['Questions']:,} questions)")
print()

# ============================================================================
# USAGE RECOMMENDATIONS
# ============================================================================

print("\n" + "="*80)
print("USAGE RECOMMENDATIONS (TIE-BREAKER STRATEGY)")
print("="*80)

recommendations = [
    ("Junior/Intern", "CS-Bench Only", "Not Recommended", 
     "Focus on foundational knowledge"),
    ("Mid-Level", "CS-Bench + CodeNet", "Optional (Math only)", 
     "Test coding + logical thinking"),
    ("Senior/Lead", "CS-Bench + MMLU-Pro", "Required (CS + Math)", 
     "Validate deep technical reasoning"),
    ("Expert/Architect", "All Datasets", "Required (All 5 domains)", 
     "Prove top 1% mastery")
]

print(f"\n{'Level':<20} {'Primary Dataset':<25} {'MMLU-Pro Usage':<30}")
print("-"*80)
for level, primary, mmlu, reason in recommendations:
    print(f"{level:<20} {primary:<25} {mmlu:<30}")
    print(f"{'':20} -> {reason}")
    print()

# ============================================================================
# ACADEMIC EXPLANATION
# ============================================================================

print("\n" + "="*80)
print("EXPLANATION FOR ACADEMIC REPORT")
print("="*80)

print(f"""
DATASET: MMLU-Pro (Massive Multitask Language Understanding - Professional)
FIELD USED: 'category' (domain classifier across 14 academic subjects)

METHODOLOGY:
The MMLU-Pro test split was analyzed to identify computing-relevant domains.
Five categories were classified as computing-relevant based on their direct
applicability to software engineering roles and technical interviews.

COMPUTING-RELEVANT DOMAINS ({len(computing_data)} identified):
""")

for i, item in enumerate(computing_data, 1):
    print(f"{i}. {item['Domain']} ({item['Questions']:,} questions, {item['Percentage']}%)")
    print(f"   → {item['Description']}")

print(f"""
TOTAL COMPUTING-RELEVANT: {computing_total:,} questions ({computing_total/total_questions*100:.1f}%)

KEY INSIGHT:
MMLU-Pro serves as a "Distinguisher" for senior candidates. Unlike CS-Bench
(foundational knowledge) or CodeNet (coding ability), MMLU-Pro tests deep
theoretical understanding. The Computer Science category contains graduate-level
problems that separate candidates who can "code" from those who understand
"why the code works."

STRATEGIC USE:
Use MMLU-Pro as a "Hard Mode" switch for senior candidates who have already
demonstrated proficiency in CS-Bench. This tie-breaker approach identifies
top-tier candidates with both practical skills and theoretical mastery.
""")

print("="*80)
print("\n[SUCCESS] Analysis Complete!")
print(f"[OUTPUT] Results saved to: {output_file}")
print("="*80)
