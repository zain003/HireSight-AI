"""
O*NET Technology Skills Dataset Analysis - Final Version

Analyzes O*NET Technology Skills with proper occupation titles and category names.

IMPORTANT: O*NET is NOT an interview question database.
It provides occupational skill requirements for workforce analysis.

Author: Python Data Analysis Agent
Date: 2026-02-06
"""

import pandas as pd
from collections import Counter, defaultdict
import os
import urllib.request

# ============================================================================
# CONFIGURATION
# ============================================================================

ONET_BASE_URL = "https://www.onetcenter.org/dl_files/database/db_28_3_text/"
TECH_SKILLS_FILE = "Technology Skills.txt"
OCCUPATION_FILE = "Occupation Data.txt"
OUTPUT_FILE = "onet_skill_distribution.csv"

# Mapping of common commodity codes to readable category names
CATEGORY_NAMES = {
    '43232605': 'Enterprise Resource Planning (ERP) Software',
    '43232306': 'Data Management Software',
    '43232610': 'Project Management Software',
    '43232104': 'Spreadsheet Software',
    '43231602': 'Operating System Software',
    '43232402': 'Development Environment Software',
    '43233501': 'Computer Aided Design (CAD) Software',
    '43232604': 'Customer Relationship Management (CRM) Software',
    '43232110': 'Presentation Software',
    '43233004': 'Graphics Software',
    '43232304': 'Database Management Software',
    '43232408': 'Web Platform Development Software',
    '43232801': 'Network Security Software',
    '43231507': 'Programming Languages',
    '43232202': 'Document Management Software'
}

print("="*80)
print("O*NET TECHNOLOGY SKILLS ANALYSIS")
print("="*80)
print("\nIMPORTANT CLARIFICATION:")
print("O*NET is a comprehensive occupational information database maintained by the")
print("U.S. Department of Labor. It does NOT contain interview questions.")
print("\nO*NET provides:")
print("  - Standardized occupational skill requirements")
print("  - Technology and tool proficiency indicators")
print("  - Domain coverage metrics for workforce planning")
print("="*80)

# ============================================================================
# LOAD DATASETS
# ============================================================================

print("\n[1/6] Loading O*NET datasets...")

# Load Technology Skills
if not os.path.exists(TECH_SKILLS_FILE):
    print(f"      [ERROR] {TECH_SKILLS_FILE} not found")
    print(f"      Please download from: https://www.onetcenter.org/database.html")
    exit(1)

df_skills = pd.read_csv(TECH_SKILLS_FILE, sep='\t', encoding='utf-8')
print(f"      [OK] Loaded {len(df_skills):,} skill records")

# Load Occupation Data for titles
if not os.path.exists(OCCUPATION_FILE):
    print(f"      Downloading occupation titles...")
    try:
        url = ONET_BASE_URL + OCCUPATION_FILE.replace(" ", "%20")
        urllib.request.urlretrieve(url, OCCUPATION_FILE)
        print(f"      [OK] Downloaded: {OCCUPATION_FILE}")
    except:
        print(f"      [WARNING] Could not download occupation titles")
        print(f"      Continuing with SOC codes only...")
        df_occupations = None
else:
    print(f"      [OK] Found: {OCCUPATION_FILE}")

# Load occupation titles if available
if os.path.exists(OCCUPATION_FILE):
    try:
        df_occupations = pd.read_csv(OCCUPATION_FILE, sep='\t', encoding='utf-8')
        print(f"      [OK] Loaded {len(df_occupations):,} occupation titles")
    except:
        df_occupations = None
        print(f"      [WARNING] Could not load occupation titles")

# ============================================================================
# CHECK FOR LANGUAGES
# ============================================================================

print("\n[2/6] Checking for multiple languages...")

language_field = None
for field in ['Language', 'language']:
    if field in df_skills.columns:
        language_field = field
        break

if language_field:
    languages = df_skills[language_field].unique()
    print(f"      [OK] Languages found: {', '.join(map(str, languages))}")
    
    non_english = len(df_skills[df_skills[language_field].str.lower() != 'english'])
    if non_english > 0:
        print(f"      [INFO] Translating {non_english:,} non-English records...")
        try:
            from deep_translator import GoogleTranslator
            translator = GoogleTranslator(source='auto', target='en')
            
            for idx, row in df_skills.iterrows():
                if row[language_field].lower() != 'english':
                    if pd.notna(row['Example']) and any(ord(c) > 127 for c in str(row['Example'])):
                        try:
                            df_skills.at[idx, 'Example'] = translator.translate(str(row['Example']))
                        except:
                            pass
            print(f"      [OK] Translation complete")
        except:
            print(f"      [WARNING] Translation skipped")
else:
    print(f"      [OK] Assuming all content is in English")

# ============================================================================
# ANALYZE SKILL DISTRIBUTION
# ============================================================================

print("\n[3/6] Analyzing skill distribution...")

# Merge with occupation titles if available
if df_occupations is not None:
    # Get occupation titles
    occ_titles = df_occupations[['O*NET-SOC Code', 'Title']].drop_duplicates()
    df_skills = df_skills.merge(occ_titles, on='O*NET-SOC Code', how='left')
    print(f"      [OK] Merged occupation titles")
else:
    df_skills['Title'] = df_skills['O*NET-SOC Code']

# Basic statistics
total_records = len(df_skills)
unique_occupations = df_skills['O*NET-SOC Code'].nunique()
unique_skills = df_skills['Example'].nunique()
unique_categories = df_skills['Commodity Code'].nunique()

print(f"      Total Records:          {total_records:,}")
print(f"      Unique Occupations:     {unique_occupations:,}")
print(f"      Unique Skills:          {unique_skills:,}")
print(f"      Unique Categories:      {unique_categories:,}")

# ============================================================================
# COMPUTE DISTRIBUTIONS
# ============================================================================

print("\n[4/6] Computing distributions...")

# Skills per occupation
occ_skill_counts = df_skills.groupby(['O*NET-SOC Code', 'Title']).agg({
    'Example': ['count', 'nunique'],
    'Commodity Code': lambda x: x.mode()[0] if len(x) > 0 else None
}).reset_index()

occ_skill_counts.columns = ['Occupation_Code', 'Occupation_Title', 'Total_Skills', 
                             'Unique_Skills', 'Primary_Category_Code']

# Map category codes to names
occ_skill_counts['Primary_Domain'] = occ_skill_counts['Primary_Category_Code'].map(
    lambda x: CATEGORY_NAMES.get(str(int(x)) if pd.notna(x) else '', f'Category {x}')
)

# Calculate skill diversity ratio
occ_skill_counts['Skill_Diversity_Ratio'] = (
    occ_skill_counts['Unique_Skills'] / occ_skill_counts['Total_Skills']
).round(3)

# Sort by total skills
occ_skill_counts = occ_skill_counts.sort_values('Total_Skills', ascending=False)

# Top occupations
print(f"\n      Top 10 Occupations by Skill Count:")
print(f"      " + "-"*76)
for i, row in occ_skill_counts.head(10).iterrows():
    title = row['Occupation_Title'][:45] if len(row['Occupation_Title']) > 45 else row['Occupation_Title']
    print(f"      {i+1:2d}. {title:<45} {row['Total_Skills']:>5,} skills")

# Top skills
skill_freq = df_skills['Example'].value_counts()
print(f"\n      Top 10 Most Common Skills:")
print(f"      " + "-"*76)
for i, (skill, count) in enumerate(skill_freq.head(10).items(), 1):
    skill_name = skill[:55] if len(skill) > 55 else skill
    print(f"      {i:2d}. {skill_name:<55} {count:>5,} occurrences")

# Category distribution
category_dist = df_skills['Commodity Code'].value_counts()
print(f"\n      Top 10 Technology Categories:")
print(f"      " + "-"*76)
for i, (code, count) in enumerate(category_dist.head(10).items(), 1):
    cat_name = CATEGORY_NAMES.get(str(int(code)), f'Category {code}')
    percentage = (count / total_records) * 100
    print(f"      {i:2d}. {cat_name[:50]:<50} {count:>5,} ({percentage:>5.2f}%)")

# ============================================================================
# SAVE RESULTS
# ============================================================================

print(f"\n[5/6] Saving results to CSV...")

# Prepare final output
output_df = occ_skill_counts[[
    'Occupation_Code', 'Occupation_Title', 'Total_Skills', 'Unique_Skills',
    'Primary_Domain', 'Skill_Diversity_Ratio'
]]

output_df.to_csv(OUTPUT_FILE, index=False)

print(f"      [OK] Saved to: {OUTPUT_FILE}")
print(f"      [OK] Contains: {len(output_df):,} occupations")

# ============================================================================
# SUMMARY STATISTICS
# ============================================================================

print("\n[6/6] Generating summary statistics...")
print("="*80)
print("SUMMARY STATISTICS")
print("="*80)

print(f"\nDataset: O*NET Technology Skills Database")
print(f"  Total Skill Records:    {total_records:,}")
print(f"  Unique Occupations:     {unique_occupations:,}")
print(f"  Unique Skills:          {unique_skills:,}")
print(f"  Unique Categories:      {unique_categories:,}")

print(f"\nTop Occupation (by skill count):")
top_occ = output_df.iloc[0]
print(f"  Title:                  {top_occ['Occupation_Title']}")
print(f"  Code:                   {top_occ['Occupation_Code']}")
print(f"  Total Skills:           {top_occ['Total_Skills']:,}")
print(f"  Unique Skills:          {top_occ['Unique_Skills']:,}")
print(f"  Primary Domain:         {top_occ['Primary_Domain']}")

print(f"\nMost Common Skill:")
print(f"  Skill:                  {skill_freq.index[0]}")
print(f"  Occurrences:            {skill_freq.iloc[0]:,} occupations")

print(f"\nSkill Diversity:")
print(f"  Average per occupation: {output_df['Total_Skills'].mean():.1f} skills")
print(f"  Median per occupation:  {output_df['Total_Skills'].median():.0f} skills")
print(f"  Max per occupation:     {output_df['Total_Skills'].max():,} skills")
print(f"  Min per occupation:     {output_df['Total_Skills'].min():,} skills")

# ============================================================================
# RESEARCH DOCUMENTATION
# ============================================================================

print("\n" + "="*80)
print("RESEARCH DOCUMENTATION")
print("="*80)

print("""
DATASET: O*NET Technology Skills Database
SOURCE: U.S. Department of Labor/Employment and Training Administration
VERSION: Database 28.3

IMPORTANT CLARIFICATION:
O*NET is NOT an interview question database. It is a comprehensive occupational
information system providing standardized descriptions of skills, knowledge,
abilities, and work activities required for occupations in the U.S. economy.

DATA STRUCTURE:
- Occupation-based organization using SOC (Standard Occupational Classification)
- Technology skills mapped to occupations
- Categorical grouping by technology domains (Commodity Codes)
- Skill frequency indicates prevalence across occupations

ANALYSIS METRICS:
1. Total_Skills: Number of technology skills associated with an occupation
2. Unique_Skills: Count of distinct skills (indicates diversity)
3. Primary_Domain: Most prevalent technology category for the occupation
4. Skill_Diversity_Ratio: Unique/Total ratio (specialization metric)
   - Higher ratio = more specialized skill set
   - Lower ratio = broader, more general skill requirements

INTERPRETATION GUIDE:
- High Total_Skills: Technology-intensive occupation
- High Unique_Skills: Requires diverse technical knowledge
- Low Diversity Ratio: Skills are repeated/emphasized (core competencies)
- High Diversity Ratio: Wide range of different skills needed

USE CASES FOR THIS ANALYSIS:
1. Workforce Planning: Identify skill gaps and training priorities
2. Curriculum Development: Align education with industry requirements
3. Job Analysis: Understand technical requirements for roles
4. Career Pathways: Map skill progression across occupations
5. Labor Market Research: Analyze technology adoption trends

LIMITATIONS:
- Does not include interview questions or assessment items
- Represents general occupational requirements, not specific job postings
- Updated periodically; may lag behind cutting-edge technologies
- U.S.-centric occupational classification (SOC codes)
- Skill presence indicates requirement, not proficiency level

CITATION:
National Center for O*NET Development. (2024). O*NET Technology Skills Database.
Retrieved from https://www.onetcenter.org/database.html
""")

print("="*80)
print("\n[SUCCESS] Analysis Complete!")
print(f"[OUTPUT] Results saved to: {OUTPUT_FILE}")
print("="*80)
