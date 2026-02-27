"""
Resume to Role Classification System

This script loads resume data and classifies each resume to appropriate job roles
based on skills, experience, and domain keywords.

Output: Shows which resume fits which role with confidence scores.

Author: Python NLP/Data Analysis Agent
Date: 2026-02-06
"""

import pandas as pd
import numpy as np
from collections import defaultdict
import re
import os

# ============================================================================
# ROLE DEFINITIONS WITH REQUIRED SKILLS
# ============================================================================

ROLE_DEFINITIONS = {
    'Software Engineer': {
        'required_skills': ['python', 'java', 'c++', 'javascript', 'git'],
        'preferred_skills': ['docker', 'kubernetes', 'aws', 'sql', 'linux'],
        'keywords': ['software', 'development', 'programming', 'coding', 'engineer'],
        'weight': 1.0
    },
    'Data Scientist': {
        'required_skills': ['python', 'machine learning', 'statistics', 'sql'],
        'preferred_skills': ['pandas', 'numpy', 'tensorflow', 'pytorch', 'scikit-learn'],
        'keywords': ['data science', 'machine learning', 'analytics', 'modeling', 'prediction'],
        'weight': 1.0
    },
    'Full Stack Developer': {
        'required_skills': ['javascript', 'html', 'css', 'node.js', 'react'],
        'preferred_skills': ['angular', 'vue', 'mongodb', 'express', 'sql'],
        'keywords': ['full stack', 'web development', 'frontend', 'backend', 'web app'],
        'weight': 1.0
    },
    'DevOps Engineer': {
        'required_skills': ['docker', 'kubernetes', 'jenkins', 'git', 'linux'],
        'preferred_skills': ['aws', 'azure', 'terraform', 'ansible', 'python'],
        'keywords': ['devops', 'ci/cd', 'automation', 'infrastructure', 'deployment'],
        'weight': 1.0
    },
    'Mobile Developer': {
        'required_skills': ['android', 'ios', 'java', 'kotlin', 'swift'],
        'preferred_skills': ['react native', 'flutter', 'firebase', 'mobile', 'app'],
        'keywords': ['mobile', 'android', 'ios', 'app development', 'mobile app'],
        'weight': 1.0
    },
    'Cloud Architect': {
        'required_skills': ['aws', 'azure', 'cloud', 'architecture', 'terraform'],
        'preferred_skills': ['kubernetes', 'docker', 'microservices', 'serverless', 'networking'],
        'keywords': ['cloud', 'architecture', 'infrastructure', 'scalable', 'distributed'],
        'weight': 1.0
    },
    'Data Engineer': {
        'required_skills': ['python', 'sql', 'spark', 'hadoop', 'etl'],
        'preferred_skills': ['kafka', 'airflow', 'aws', 'data pipeline', 'big data'],
        'keywords': ['data engineering', 'pipeline', 'etl', 'big data', 'data warehouse'],
        'weight': 1.0
    },
    'Machine Learning Engineer': {
        'required_skills': ['python', 'machine learning', 'tensorflow', 'pytorch', 'deep learning'],
        'preferred_skills': ['nlp', 'computer vision', 'neural networks', 'keras', 'scikit-learn'],
        'keywords': ['machine learning', 'deep learning', 'ai', 'neural network', 'ml engineer'],
        'weight': 1.0
    },
    'Frontend Developer': {
        'required_skills': ['javascript', 'html', 'css', 'react', 'typescript'],
        'preferred_skills': ['angular', 'vue', 'webpack', 'sass', 'responsive design'],
        'keywords': ['frontend', 'ui', 'user interface', 'web design', 'responsive'],
        'weight': 1.0
    },
    'Backend Developer': {
        'required_skills': ['python', 'java', 'node.js', 'sql', 'api'],
        'preferred_skills': ['django', 'flask', 'spring', 'mongodb', 'redis'],
        'keywords': ['backend', 'server', 'api', 'database', 'microservices'],
        'weight': 1.0
    },
    'QA Engineer': {
        'required_skills': ['testing', 'automation', 'selenium', 'junit', 'quality assurance'],
        'preferred_skills': ['python', 'java', 'jenkins', 'ci/cd', 'test automation'],
        'keywords': ['qa', 'quality assurance', 'testing', 'test automation', 'quality'],
        'weight': 1.0
    },
    'Security Engineer': {
        'required_skills': ['security', 'cybersecurity', 'penetration testing', 'encryption', 'firewall'],
        'preferred_skills': ['python', 'linux', 'networking', 'vulnerability', 'compliance'],
        'keywords': ['security', 'cybersecurity', 'penetration', 'vulnerability', 'infosec'],
        'weight': 1.0
    }
}

print("="*80)
print("RESUME TO ROLE CLASSIFICATION SYSTEM")
print("="*80)
print(f"\nClassifying resumes into {len(ROLE_DEFINITIONS)} predefined roles")
print("Roles:", ', '.join(ROLE_DEFINITIONS.keys()))
print("="*80)

# ============================================================================
# LOAD DATASET
# ============================================================================

print("\n[1/4] Loading resume dataset...")

# Try to find dataset
dataset_files = ['resumes.csv', 'resumeatlas.csv', 'ResumeAtlas.csv', 'resume_data.csv']
dataset_file = None

for filename in dataset_files:
    if os.path.exists(filename):
        dataset_file = filename
        break

if not dataset_file:
    print(f"      [ERROR] No dataset file found!")
    print(f"      Please ensure one of these files exists: {', '.join(dataset_files)}")
    exit(1)

df = pd.read_csv(dataset_file, encoding='utf-8')
print(f"      [OK] Loaded {len(df):,} resumes from {dataset_file}")

# ============================================================================
# CLASSIFICATION FUNCTION
# ============================================================================

def classify_resume_to_roles(resume_text, skills_text, category=None):
    """
    Classify a resume to multiple roles with confidence scores.
    
    Returns: List of (role, confidence_score) tuples sorted by confidence
    """
    resume_text = str(resume_text).lower()
    skills_text = str(skills_text).lower()
    combined_text = resume_text + " " + skills_text
    
    role_scores = {}
    
    for role, definition in ROLE_DEFINITIONS.items():
        score = 0.0
        max_score = 0.0
        
        # Check required skills (high weight)
        required_found = 0
        for skill in definition['required_skills']:
            max_score += 2.0
            if skill.lower() in combined_text:
                score += 2.0
                required_found += 1
        
        # Check preferred skills (medium weight)
        for skill in definition['preferred_skills']:
            max_score += 1.0
            if skill.lower() in combined_text:
                score += 1.0
        
        # Check keywords (low weight)
        for keyword in definition['keywords']:
            max_score += 0.5
            if keyword.lower() in combined_text:
                score += 0.5
        
        # Calculate confidence percentage
        confidence = (score / max_score * 100) if max_score > 0 else 0
        
        # Bonus if category matches role
        if category and category.lower() in role.lower():
            confidence = min(confidence + 10, 100)
        
        role_scores[role] = round(confidence, 2)
    
    # Sort by confidence
    sorted_roles = sorted(role_scores.items(), key=lambda x: x[1], reverse=True)
    
    return sorted_roles

# ============================================================================
# CLASSIFY ALL RESUMES
# ============================================================================

print("\n[2/4] Classifying resumes to roles...")

# Identify columns
text_col = None
skills_col = None
category_col = None

for col in ['resume_text', 'text', 'resume', 'description', 'content']:
    if col in df.columns:
        text_col = col
        break

for col in ['skills', 'Skills', 'skill', 'technologies']:
    if col in df.columns:
        skills_col = col
        break

for col in ['category', 'Category', 'domain', 'job_category']:
    if col in df.columns:
        category_col = col
        break

if not text_col and not skills_col:
    print(f"      [ERROR] No text or skills column found!")
    exit(1)

print(f"      Using columns:")
print(f"        Text: {text_col if text_col else 'N/A'}")
print(f"        Skills: {skills_col if skills_col else 'N/A'}")
print(f"        Category: {category_col if category_col else 'N/A'}")

# Classify each resume
classifications = []

for idx, row in df.iterrows():
    resume_text = row[text_col] if text_col else ""
    skills_text = row[skills_col] if skills_col else ""
    category = row[category_col] if category_col else None
    
    # Get role classifications
    role_scores = classify_resume_to_roles(resume_text, skills_text, category)
    
    # Get top 3 roles
    top_roles = role_scores[:3]
    
    # Store classification
    classifications.append({
        'Resume_ID': row.get('resume_id', idx + 1),
        'Original_Category': category if category else 'N/A',
        'Best_Fit_Role': top_roles[0][0],
        'Confidence': top_roles[0][1],
        'Second_Best_Role': top_roles[1][0] if len(top_roles) > 1 else 'N/A',
        'Second_Confidence': top_roles[1][1] if len(top_roles) > 1 else 0,
        'Third_Best_Role': top_roles[2][0] if len(top_roles) > 2 else 'N/A',
        'Third_Confidence': top_roles[2][1] if len(top_roles) > 2 else 0,
        'All_Roles': ', '.join([f"{role}({score}%)" for role, score in role_scores if score > 0])
    })
    
    if (idx + 1) % 10 == 0:
        print(f"      Classified {idx + 1}/{len(df)} resumes...")

print(f"      [OK] Classified all {len(df)} resumes")

# ============================================================================
# DISPLAY RESULTS
# ============================================================================

print("\n[3/4] Classification Results")
print("="*80)

results_df = pd.DataFrame(classifications)

# Display each resume classification
print(f"\nRESUME TO ROLE MAPPING:")
print("-"*80)
print(f"{'Resume':<10} {'Original':<25} {'Best Fit Role':<25} {'Confidence':<12}")
print("-"*80)

for _, row in results_df.iterrows():
    resume_id = str(row['Resume_ID'])[:8]
    original = str(row['Original_Category'])[:23]
    best_role = str(row['Best_Fit_Role'])[:23]
    confidence = f"{row['Confidence']:.1f}%"
    
    print(f"{resume_id:<10} {original:<25} {best_role:<25} {confidence:<12}")

# Role distribution
print(f"\n" + "="*80)
print("ROLE DISTRIBUTION (Best Fit)")
print("="*80)

role_counts = results_df['Best_Fit_Role'].value_counts()
print(f"\n{'Role':<30} {'Count':<10} {'Percentage':<12}")
print("-"*80)

for role, count in role_counts.items():
    percentage = (count / len(results_df)) * 100
    print(f"{role:<30} {count:<10} {percentage:>10.1f}%")

# Average confidence by role
print(f"\n" + "="*80)
print("AVERAGE CONFIDENCE BY ROLE")
print("="*80)

avg_confidence = results_df.groupby('Best_Fit_Role')['Confidence'].mean().sort_values(ascending=False)
print(f"\n{'Role':<30} {'Avg Confidence':<15}")
print("-"*80)

for role, conf in avg_confidence.items():
    print(f"{role:<30} {conf:>13.1f}%")

# ============================================================================
# SAVE RESULTS
# ============================================================================

print(f"\n[4/4] Saving results...")

# Save detailed classification
output_file = 'resume_role_classification.csv'
results_df.to_csv(output_file, index=False)
print(f"      [OK] Saved detailed results to: {output_file}")

# Save summary
summary_data = []
for role in ROLE_DEFINITIONS.keys():
    count = len(results_df[results_df['Best_Fit_Role'] == role])
    avg_conf = results_df[results_df['Best_Fit_Role'] == role]['Confidence'].mean() if count > 0 else 0
    
    summary_data.append({
        'Role': role,
        'Resume_Count': count,
        'Percentage': round((count / len(results_df)) * 100, 2),
        'Avg_Confidence': round(avg_conf, 2),
        'Required_Skills': ', '.join(ROLE_DEFINITIONS[role]['required_skills'][:5])
    })

summary_df = pd.DataFrame(summary_data)
summary_df = summary_df.sort_values('Resume_Count', ascending=False)

summary_file = 'role_distribution_summary.csv'
summary_df.to_csv(summary_file, index=False)
print(f"      [OK] Saved summary to: {summary_file}")

# ============================================================================
# DETAILED EXAMPLES
# ============================================================================

print(f"\n" + "="*80)
print("DETAILED CLASSIFICATION EXAMPLES (First 5 Resumes)")
print("="*80)

for i in range(min(5, len(df))):
    row = df.iloc[i]
    classification = classifications[i]
    
    print(f"\n{'='*80}")
    print(f"RESUME #{classification['Resume_ID']}")
    print(f"{'='*80}")
    print(f"Original Category: {classification['Original_Category']}")
    
    if skills_col:
        skills = str(row[skills_col])[:100]
        print(f"Skills: {skills}...")
    
    print(f"\nTop 3 Role Matches:")
    print(f"  1. {classification['Best_Fit_Role']:<30} Confidence: {classification['Confidence']:.1f}%")
    if classification['Second_Best_Role'] != 'N/A':
        print(f"  2. {classification['Second_Best_Role']:<30} Confidence: {classification['Second_Confidence']:.1f}%")
    if classification['Third_Best_Role'] != 'N/A':
        print(f"  3. {classification['Third_Best_Role']:<30} Confidence: {classification['Third_Confidence']:.1f}%")

# ============================================================================
# SUMMARY
# ============================================================================

print(f"\n" + "="*80)
print("SUMMARY")
print("="*80)

print(f"\nTotal Resumes Analyzed: {len(df):,}")
print(f"Total Roles Defined: {len(ROLE_DEFINITIONS)}")
print(f"Roles with Matches: {len(role_counts)}")

high_confidence = len(results_df[results_df['Confidence'] >= 70])
medium_confidence = len(results_df[(results_df['Confidence'] >= 50) & (results_df['Confidence'] < 70)])
low_confidence = len(results_df[results_df['Confidence'] < 50])

print(f"\nConfidence Distribution:")
print(f"  High (>=70%):   {high_confidence:>3} resumes ({high_confidence/len(df)*100:.1f}%)")
print(f"  Medium (50-69%): {medium_confidence:>3} resumes ({medium_confidence/len(df)*100:.1f}%)")
print(f"  Low (<50%):     {low_confidence:>3} resumes ({low_confidence/len(df)*100:.1f}%)")

print(f"\nMost Common Role: {role_counts.index[0]} ({role_counts.iloc[0]} resumes)")
print(f"Highest Avg Confidence: {avg_confidence.index[0]} ({avg_confidence.iloc[0]:.1f}%)")

print("\n" + "="*80)
print("[SUCCESS] Classification Complete!")
print(f"[OUTPUT] Results saved to:")
print(f"  - {output_file} (detailed classifications)")
print(f"  - {summary_file} (role distribution summary)")
print("="*80)
