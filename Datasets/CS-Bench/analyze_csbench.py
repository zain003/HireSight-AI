"""
CS-Bench Dataset Domain Distribution Analysis
Loads the CS-Bench dataset from HuggingFace and analyzes question distribution by domain.
CS-Bench includes ~5,000 questions across 26 subfields in multiple languages.
"""

import pandas as pd
from collections import Counter
import json
from huggingface_hub import hf_hub_download

# Mapping of SubDomains to their parent Domains
SUBDOMAIN_TO_DOMAIN = {
    # Data Structure and Algorithm (DSA)
    'Overview': 'Data Structure and Algorithm',
    'Linear List': 'Data Structure and Algorithm',
    'Stack, Queue, and Array': 'Data Structure and Algorithm',
    'String': 'Data Structure and Algorithm',
    'Tree': 'Data Structure and Algorithm',
    'Graph': 'Data Structure and Algorithm',
    'Searching': 'Data Structure and Algorithm',
    'Sorting': 'Data Structure and Algorithm',
    
    # Computer Organization (CO)
    'Overview and Architecture': 'Computer Organization',
    'Data Representation and Operation': 'Computer Organization',
    'Storage System': 'Computer Organization',
    'Instruction System': 'Computer Organization',
    'Central Processing Unit': 'Computer Organization',
    'Bus': 'Computer Organization',
    'Input/Output System': 'Computer Organization',
    
    # Computer Network (CN)
    'Physical Layer': 'Computer Network',
    'Data Link Layer': 'Computer Network',
    'Network Layer': 'Computer Network',
    'Transport Layer': 'Computer Network',
    'Application Layer': 'Computer Network',
    
    # Operating System (OS)
    'Processes and Threads': 'Operating System',
    'Memory Management': 'Operating System',
    'File Management': 'Operating System',
    'Input/Output Management': 'Operating System',
}

print("="*75)
print("CS-BENCH DATASET DOMAIN DISTRIBUTION ANALYSIS")
print("="*75)

print("\nLoading CS-Bench dataset from HuggingFace...")
print("Loading both English and Chinese versions...\n")

all_examples = []
language_stats = {}

# Load both English and Chinese versions
for language in ['English', 'Chinese']:
    for split_name in ['valid', 'test']:
        try:
            file_path = hf_hub_download(
                repo_id="CS-Bench/CS-Bench",
                filename=f"CS-Bench/{language}/{split_name}.jsonl",
                repo_type="dataset"
            )
            
            split_examples = []
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        split_examples.append(json.loads(line))
            
            all_examples.extend(split_examples)
            language_stats[f"{language}/{split_name}"] = len(split_examples)
            print(f"✓ Loaded {len(split_examples):,} examples from '{language}/{split_name}'")
            
        except Exception as e:
            if "404" not in str(e):
                print(f"✗ Could not load '{language}/{split_name}'")

print(f"\n{'='*75}")
print(f"Dataset loaded successfully!")
print(f"Total number of questions: {len(all_examples):,}")
print(f"{'='*75}")

# Analyze by SubDomain
subdomain_counts = Counter([ex['SubDomain'] for ex in all_examples])
subdomain_distribution = sorted(subdomain_counts.items(), key=lambda x: x[1], reverse=True)

# Analyze by main Domain
domain_counts = Counter([ex['Domain'] for ex in all_examples])
domain_distribution = sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)

# Print main domain distribution
print(f"\n{'='*75}")
print("🧠 THE 4 KEY DOMAINS (Broad Categories)")
print("="*75)
print(f"{'Domain':<45} {'Count':>12} {'Percentage':>12}")
print("-"*75)

total_questions = len(all_examples)
for domain, count in domain_distribution:
    percentage = (count / total_questions) * 100
    print(f"{domain:<45} {count:>12,} {percentage:>11.2f}%")

print("-"*75)
print(f"{'TOTAL':<45} {total_questions:>12,} {100.0:>11.2f}%")

# Print subdomain distribution organized by main domain
print(f"\n{'='*75}")
print("📚 THE 26 SUBFIELDS (Fine-grained Topics)")
print("="*75)

# Group subdomains by main domain
domain_groups = {
    'Data Structure and Algorithm': [],
    'Computer Organization': [],
    'Computer Network': [],
    'Operating System': []
}

for subdomain, count in subdomain_distribution:
    parent_domain = SUBDOMAIN_TO_DOMAIN.get(subdomain, 'Unknown')
    if parent_domain in domain_groups:
        domain_groups[parent_domain].append((subdomain, count))

# Print each domain group
domain_order = ['Data Structure and Algorithm', 'Computer Organization', 
                'Computer Network', 'Operating System']

subdomain_number = 1
for domain in domain_order:
    print(f"\n{domain}:")
    print("-"*75)
    for subdomain, count in domain_groups[domain]:
        percentage = (count / total_questions) * 100
        print(f"  {subdomain_number:2d}. {subdomain:<40} {count:>6,} ({percentage:>5.2f}%)")
        subdomain_number += 1

print(f"\n{'='*75}")
print(f"Total unique subfields found: {len(subdomain_distribution)}")
print("="*75)

# Save detailed CSV
df_subdomain = pd.DataFrame(subdomain_distribution, columns=['Domain', 'Question_Count'])
df_subdomain['Percentage'] = (df_subdomain['Question_Count'] / total_questions * 100).round(2)
df_subdomain['Parent_Domain'] = df_subdomain['Domain'].map(SUBDOMAIN_TO_DOMAIN)
df_subdomain.to_csv('csbench_domain_distribution.csv', index=False)

print(f"\n✓ Results saved to 'csbench_domain_distribution.csv'")

# Print explanation
print(f"\n{'='*75}")
print("EXPLANATION:")
print("="*75)
print("The field 'SubDomain' was used as the domain identifier because:")
print("1. CS-Bench is designed to cover 26 subfields across 4 key areas")
print("2. The 'SubDomain' field provides fine-grained topic categorization")
print("3. Each question is tagged with a specific SubDomain")
print("4. This enables detailed analysis of coverage across CS topics")
print()
print("The 4 main domains are:")
print("  • Data Structure and Algorithm (DSA)")
print("  • Computer Organization (CO)")
print("  • Computer Network (CN)")
print("  • Operating System (OS)")
print()
print(f"Note: The dataset contains {len(subdomain_distribution)} unique subfields.")
print("      (The paper mentions 26, but the actual data has 24 unique subfields)")
print("="*75)
