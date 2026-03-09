"""
Test script to demonstrate resume validation system.
Tests various resume types to show rejection/acceptance logic.
"""

# Mock extracted data for different resume types
test_cases = [
    {
        "name": "✅ Software Engineer Resume (VALID)",
        "text": """
        John Doe
        Software Engineer
        
        Experience:
        - Senior Software Engineer at Google (3 years)
        - Full Stack Developer at Microsoft (2 years)
        
        Skills: Python, JavaScript, React, Node.js, Docker, Kubernetes, AWS,
        PostgreSQL, MongoDB, Git, CI/CD, REST API, GraphQL, TypeScript
        
        Projects:
        - Built microservices architecture using Docker and Kubernetes
        - Developed React-based dashboard with 100k+ users
        
        Education: B.Tech Computer Science
        """,
        "extracted_data": {
            "skills": ["Python", "JavaScript", "React", "Node.js", "Docker", 
                      "Kubernetes", "AWS", "PostgreSQL", "MongoDB", "Git"],
            "job_titles": ["Software Engineer", "Full Stack Developer"],
            "domain": "software_engineering",
            "experience": {"years": 5, "companies": ["Google", "Microsoft"]},
            "education": ["B.Tech Computer Science"],
            "projects": ["Microservices architecture", "React dashboard"],
            "certifications": []
        },
        "expected": "ACCEPT"
    },
    
    {
        "name": "✅ Data Scientist Resume (VALID)",
        "text": """
        Jane Smith
        Data Scientist
        
        Experience:
        - Senior Data Scientist at Amazon (4 years)
        - ML Engineer at Netflix (2 years)
        
        Skills: Python, R, TensorFlow, PyTorch, Scikit-learn, Pandas, NumPy,
        SQL, Spark, Hadoop, AWS, Machine Learning, Deep Learning, NLP
        
        Projects:
        - Built recommendation system using deep learning
        - Developed NLP model for sentiment analysis
        
        Education: M.S. Data Science
        """,
        "extracted_data": {
            "skills": ["Python", "R", "TensorFlow", "PyTorch", "Scikit-learn",
                      "Pandas", "NumPy", "SQL", "Spark", "Machine Learning"],
            "job_titles": ["Data Scientist", "ML Engineer"],
            "domain": "data_science",
            "experience": {"years": 6, "companies": ["Amazon", "Netflix"]},
            "education": ["M.S. Data Science"],
            "projects": ["Recommendation system", "NLP sentiment analysis"],
            "certifications": []
        },
        "expected": "ACCEPT"
    },
    
    {
        "name": "❌ Medical Doctor Resume (REJECT)",
        "text": """
        Dr. Ahmed Khan
        Medical Doctor (MBBS, MD)
        
        Experience:
        - Senior Physician at City Hospital (5 years)
        - Resident Doctor at General Hospital (3 years)
        
        Skills: Patient care, Diagnosis, Treatment planning, Surgery,
        Emergency medicine, Clinical research, Medical documentation
        
        Education: MBBS, MD Internal Medicine
        Certifications: BLS, ACLS, Medical License
        """,
        "extracted_data": {
            "skills": [],  # No computing skills
            "job_titles": [],  # No computing job titles
            "domain": "general",
            "experience": {"years": 8, "companies": ["City Hospital", "General Hospital"]},
            "education": ["MBBS", "MD Internal Medicine"],
            "projects": [],
            "certifications": ["BLS", "ACLS"]
        },
        "expected": "REJECT - Non-computing field (medical)"
    },
    
    {
        "name": "❌ Civil Engineer Resume (REJECT)",
        "text": """
        Ali Hassan
        Civil Engineer
        
        Experience:
        - Senior Civil Engineer at ABC Construction (4 years)
        - Site Engineer at XYZ Builders (2 years)
        
        Skills: AutoCAD, Revit, Structural design, Construction management,
        Surveying, Concrete technology, Building codes, Project planning
        
        Projects:
        - Designed 10-story residential building
        - Managed highway construction project
        
        Education: B.Tech Civil Engineering
        """,
        "extracted_data": {
            "skills": [],  # AutoCAD might be extracted but not enough
            "job_titles": [],
            "domain": "general",
            "experience": {"years": 6, "companies": ["ABC Construction", "XYZ Builders"]},
            "education": ["B.Tech Civil Engineering"],
            "projects": ["Residential building", "Highway construction"],
            "certifications": []
        },
        "expected": "REJECT - Non-computing field (civil engineering)"
    },
    
    {
        "name": "❌ Sales Executive Resume (REJECT)",
        "text": """
        Sarah Ahmed
        Sales Executive
        
        Experience:
        - Senior Sales Executive at ABC Corp (3 years)
        - Sales Representative at XYZ Ltd (2 years)
        
        Skills: Sales, Customer relationship, Negotiation, Communication,
        Presentation, Microsoft Excel, PowerPoint, CRM software
        
        Achievements:
        - Exceeded sales targets by 150%
        - Managed 50+ client accounts
        
        Education: MBA Marketing
        """,
        "extracted_data": {
            "skills": ["Excel", "PowerPoint"],  # Only 2 skills, not enough
            "job_titles": [],
            "domain": "general",
            "experience": {"years": 5, "companies": ["ABC Corp", "XYZ Ltd"]},
            "education": ["MBA Marketing"],
            "projects": [],
            "certifications": []
        },
        "expected": "REJECT - Insufficient technical skills (only 2)"
    },
    
    {
        "name": "❌ Blank/Empty Resume (REJECT)",
        "text": "",
        "extracted_data": None,  # Won't reach extraction
        "expected": "REJECT - Empty file"
    },
    
    {
        "name": "⚠️ Business Analyst with Tech Skills (EDGE CASE)",
        "text": """
        Omar Ali
        Business Analyst
        
        Experience:
        - Business Analyst at Tech Company (3 years)
        - Data Analyst at Startup (2 years)
        
        Skills: SQL, Python, Tableau, Power BI, Excel, Data Analysis,
        Requirements gathering, Agile, Jira, Confluence
        
        Projects:
        - Built SQL dashboards for business metrics
        - Automated reporting using Python scripts
        
        Education: B.S. Business Administration
        """,
        "extracted_data": {
            "skills": ["SQL", "Python", "Tableau", "Power BI", "Excel", 
                      "Jira", "Confluence"],
            "job_titles": ["Business Analyst", "Data Analyst"],
            "domain": "data_analytics",
            "experience": {"years": 5, "companies": ["Tech Company", "Startup"]},
            "education": ["B.S. Business Administration"],
            "projects": ["SQL dashboards", "Python automation"],
            "certifications": []
        },
        "expected": "ACCEPT - Has technical skills + computing domain"
    },
    
    {
        "name": "✅ DevOps Engineer Resume (VALID)",
        "text": """
        Hassan Ahmed
        DevOps Engineer
        
        Experience:
        - Senior DevOps Engineer at AWS (3 years)
        - Cloud Engineer at Azure (2 years)
        
        Skills: Docker, Kubernetes, Jenkins, Terraform, Ansible, AWS, Azure,
        Linux, Python, Bash, CI/CD, Git, Prometheus, Grafana
        
        Projects:
        - Automated infrastructure deployment using Terraform
        - Built CI/CD pipeline reducing deployment time by 80%
        
        Education: B.S. Computer Engineering
        """,
        "extracted_data": {
            "skills": ["Docker", "Kubernetes", "Jenkins", "Terraform", "Ansible",
                      "AWS", "Azure", "Linux", "Python", "Bash", "Git"],
            "job_titles": ["DevOps Engineer", "Cloud Engineer"],
            "domain": "devops",
            "experience": {"years": 5, "companies": ["AWS", "Azure"]},
            "education": ["B.S. Computer Engineering"],
            "projects": ["Infrastructure automation", "CI/CD pipeline"],
            "certifications": []
        },
        "expected": "ACCEPT"
    }
]


def simulate_validation(test_case):
    """Simulate the validation logic"""
    print(f"\n{'='*80}")
    print(f"TEST: {test_case['name']}")
    print(f"{'='*80}")
    
    text = test_case['text']
    extracted_data = test_case['extracted_data']
    
    # Check if text is too short
    if not text or len(text) < 50:
        print("❌ REJECTED: Empty or insufficient text")
        print(f"Expected: {test_case['expected']}")
        return
    
    if extracted_data is None:
        print("❌ REJECTED: Could not extract data")
        print(f"Expected: {test_case['expected']}")
        return
    
    # Display extracted data
    print(f"\n📊 Extracted Data:")
    print(f"   Skills: {len(extracted_data['skills'])} found")
    if extracted_data['skills']:
        print(f"   → {', '.join(extracted_data['skills'][:5])}")
    print(f"   Job Titles: {extracted_data['job_titles']}")
    print(f"   Domain: {extracted_data['domain']}")
    print(f"   Experience: {extracted_data['experience']['years']} years")
    
    # Validation logic
    text_lower = text.lower()
    
    # Layer 1: Non-computing keywords
    non_computing_keywords = {
        "doctor", "physician", "surgeon", "nurse", "medical", "hospital",
        "civil engineer", "construction", "autocad", "revit",
        "sales representative", "sales executive", "salesman"
    }
    
    non_computing_matches = [kw for kw in non_computing_keywords if kw in text_lower]
    
    if len(non_computing_matches) >= 3:
        print(f"\n❌ REJECTED: Non-computing field detected")
        print(f"   Found: {', '.join(non_computing_matches[:3])}")
        print(f"Expected: {test_case['expected']}")
        return
    
    # Layer 2: Skills check
    if len(extracted_data['skills']) < 3:
        print(f"\n❌ REJECTED: Insufficient technical skills")
        print(f"   Only {len(extracted_data['skills'])} skills found (minimum: 3)")
        print(f"Expected: {test_case['expected']}")
        return
    
    # Layer 3: Domain check
    if extracted_data['domain'] == "general":
        computing_keywords = ["software", "developer", "programming", "python", "java"]
        computing_count = sum(1 for kw in computing_keywords if kw in text_lower)
        
        if computing_count < 5:
            print(f"\n❌ REJECTED: Could not identify computing domain")
            print(f"   Domain: {extracted_data['domain']}")
            print(f"   Computing keywords: {computing_count} (minimum: 5)")
            print(f"Expected: {test_case['expected']}")
            return
    
    # Passed all checks
    print(f"\n✅ ACCEPTED: Valid computing resume")
    print(f"   ✓ {len(extracted_data['skills'])} technical skills")
    print(f"   ✓ Domain: {extracted_data['domain']}")
    print(f"   ✓ Job titles: {', '.join(extracted_data['job_titles'])}")
    print(f"Expected: {test_case['expected']}")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("RESUME VALIDATION SYSTEM - TEST SUITE")
    print("="*80)
    
    for test_case in test_cases:
        simulate_validation(test_case)
    
    print("\n" + "="*80)
    print("TEST SUITE COMPLETED")
    print("="*80)
    print("\n📋 Summary:")
    print("   ✅ Valid computing resumes: ACCEPTED")
    print("   ❌ Non-computing resumes: REJECTED")
    print("   ❌ Blank/empty resumes: REJECTED")
    print("   ❌ Insufficient skills: REJECTED")
    print("\n")
