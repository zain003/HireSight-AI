"""
Test script to demonstrate skill classification system.
Shows how skills are separated into "Experienced" vs "Known" categories.
"""

# Sample resume text with clear experience and skills sections
sample_resume = """
JOHN DOE
Software Engineer

EXPERIENCE:
Senior Software Engineer at Google (2020-2023)
- Built microservices architecture using Python, FastAPI, and Docker
- Developed REST APIs with PostgreSQL database
- Implemented CI/CD pipelines using Jenkins and Kubernetes
- Led team of 5 developers using Agile methodology

Full Stack Developer at Microsoft (2018-2020)
- Created React-based dashboard with TypeScript
- Integrated AWS services (S3, Lambda, EC2)
- Worked with MongoDB and Redis for caching
- Used Git for version control

PROJECTS:
E-commerce Platform
- Built using Node.js, Express, and React
- Deployed on AWS with Docker containers
- Implemented payment gateway integration

Machine Learning Model
- Developed using Python, TensorFlow, and Scikit-learn
- Deployed using Flask API
- Used Pandas and NumPy for data processing

SKILLS:
Programming Languages: Python, JavaScript, TypeScript, Java, C++, Go, Rust
Frontend: React, Angular, Vue.js, HTML, CSS, Tailwind CSS
Backend: FastAPI, Node.js, Express, Django, Flask, Spring Boot
Databases: PostgreSQL, MongoDB, MySQL, Redis, Cassandra
Cloud: AWS, Azure, GCP, Heroku
DevOps: Docker, Kubernetes, Jenkins, GitLab CI, Terraform, Ansible
Tools: Git, Jira, Confluence, Postman, VS Code
Machine Learning: TensorFlow, PyTorch, Scikit-learn, Pandas, NumPy, Keras
Other: GraphQL, gRPC, RabbitMQ, Kafka, Elasticsearch

EDUCATION:
B.Tech Computer Science, XYZ University (2014-2018)
"""

# Expected classification
expected_experienced_skills = [
    # From Experience section
    "Python", "FastAPI", "Docker", "PostgreSQL", "Jenkins", "Kubernetes",
    "React", "TypeScript", "AWS", "MongoDB", "Redis", "Git",
    
    # From Projects section
    "Node.js", "Express", "TensorFlow", "Scikit-learn", "Flask", "Pandas", "NumPy"
]

expected_known_skills = [
    # Mentioned in skills section but NOT in experience/projects
    "Java", "C++", "Go", "Rust", "Angular", "Vue.js", "HTML", "CSS", 
    "Tailwind CSS", "Django", "Spring Boot", "MySQL", "Cassandra",
    "Azure", "GCP", "Heroku", "GitLab CI", "Terraform", "Ansible",
    "Jira", "Confluence", "Postman", "VS Code", "PyTorch", "Keras",
    "GraphQL", "gRPC", "RabbitMQ", "Kafka", "Elasticsearch"
]


def simulate_skill_classification():
    """Simulate the skill classification logic"""
    print("="*80)
    print("SKILL CLASSIFICATION DEMONSTRATION")
    print("="*80)
    
    print("\n📄 RESUME SAMPLE:")
    print("-" * 80)
    print(sample_resume[:500] + "...\n")
    
    print("\n🔍 EXTRACTION PROCESS:")
    print("-" * 80)
    
    # Step 1: Extract all skills
    all_skills = [
        "Python", "JavaScript", "TypeScript", "Java", "C++", "Go", "Rust",
        "React", "Angular", "Vue.js", "HTML", "CSS", "Tailwind CSS",
        "FastAPI", "Node.js", "Express", "Django", "Flask", "Spring Boot",
        "PostgreSQL", "MongoDB", "MySQL", "Redis", "Cassandra",
        "AWS", "Azure", "GCP", "Heroku",
        "Docker", "Kubernetes", "Jenkins", "GitLab CI", "Terraform", "Ansible",
        "Git", "Jira", "Confluence", "Postman", "VS Code",
        "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy", "Keras",
        "GraphQL", "gRPC", "RabbitMQ", "Kafka", "Elasticsearch"
    ]
    
    print(f"✅ Step 1: Extracted {len(all_skills)} total skills")
    print(f"   → {', '.join(all_skills[:10])}...")
    
    # Step 2: Extract experience and project sections
    print(f"\n✅ Step 2: Extracted experience and project sections")
    print(f"   → Experience: Google (Python, FastAPI, Docker, PostgreSQL, Jenkins, Kubernetes)")
    print(f"   → Experience: Microsoft (React, TypeScript, AWS, MongoDB, Redis, Git)")
    print(f"   → Project: E-commerce (Node.js, Express, React, AWS, Docker)")
    print(f"   → Project: ML Model (Python, TensorFlow, Scikit-learn, Flask, Pandas, NumPy)")
    
    # Step 3: Classify skills
    experience_project_text = """
    senior software engineer google python fastapi docker postgresql jenkins kubernetes
    full stack developer microsoft react typescript aws mongodb redis git
    e-commerce platform node.js express react aws docker
    machine learning model python tensorflow scikit-learn flask pandas numpy
    """.lower()
    
    experienced_skills = []
    known_skills = []
    
    for skill in all_skills:
        if skill.lower() in experience_project_text:
            experienced_skills.append(skill)
        else:
            known_skills.append(skill)
    
    print(f"\n✅ Step 3: Classified skills into two categories")
    
    # Display results
    print("\n" + "="*80)
    print("📊 CLASSIFICATION RESULTS")
    print("="*80)
    
    print(f"\n💪 EXPERIENCED SKILLS ({len(experienced_skills)} skills)")
    print("   (Skills used in actual work experience and projects)")
    print("-" * 80)
    for i, skill in enumerate(experienced_skills, 1):
        print(f"   {i:2d}. {skill}")
    
    print(f"\n📚 KNOWN SKILLS ({len(known_skills)} skills)")
    print("   (Skills mentioned but not demonstrated in experience/projects)")
    print("-" * 80)
    for i, skill in enumerate(known_skills, 1):
        print(f"   {i:2d}. {skill}")
    
    # Dashboard display simulation
    print("\n" + "="*80)
    print("🎨 DASHBOARD DISPLAY PREVIEW")
    print("="*80)
    
    print("\n┌─────────────────────────────────────────────────────────────────┐")
    print("│                        USER DASHBOARD                           │")
    print("├─────────────────────────────────────────────────────────────────┤")
    print("│                                                                 │")
    print("│  👤 John Doe                                                    │")
    print("│  💼 Software Engineer                                           │")
    print("│  🏢 Domain: Software Engineering                                │")
    print("│  📅 Experience: 5 years                                         │")
    print("│                                                                 │")
    print("├─────────────────────────────────────────────────────────────────┤")
    print("│  💪 EXPERIENCED SKILLS (Used in Projects/Experience)           │")
    print("├─────────────────────────────────────────────────────────────────┤")
    print("│                                                                 │")
    
    # Display experienced skills in rows of 5
    for i in range(0, len(experienced_skills), 5):
        row_skills = experienced_skills[i:i+5]
        skill_badges = "  ".join([f"[{skill}]" for skill in row_skills])
        print(f"│  {skill_badges:<63} │")
    
    print("│                                                                 │")
    print("├─────────────────────────────────────────────────────────────────┤")
    print("│  📚 KNOWN SKILLS (Mentioned but not demonstrated)              │")
    print("├─────────────────────────────────────────────────────────────────┤")
    print("│                                                                 │")
    
    # Display known skills in rows of 5
    for i in range(0, len(known_skills), 5):
        row_skills = known_skills[i:i+5]
        skill_badges = "  ".join([f"[{skill}]" for skill in row_skills])
        print(f"│  {skill_badges:<63} │")
    
    print("│                                                                 │")
    print("└─────────────────────────────────────────────────────────────────┘")
    
    # Benefits explanation
    print("\n" + "="*80)
    print("✨ BENEFITS OF SKILL CLASSIFICATION")
    print("="*80)
    
    print("\n1. 🎯 ACCURATE SKILL ASSESSMENT")
    print("   → Experienced skills show PROVEN expertise")
    print("   → Known skills show LEARNING potential")
    
    print("\n2. 🤖 BETTER AI INTERVIEW QUESTIONS (Module 2)")
    print("   → Focus questions on experienced skills (higher difficulty)")
    print("   → Ask basic questions on known skills (lower difficulty)")
    
    print("\n3. 📈 IMPROVED CANDIDATE EVALUATION")
    print("   → Recruiters see which skills are actually used")
    print("   → Avoid candidates who just list skills without experience")
    
    print("\n4. 🎓 PERSONALIZED LEARNING PATH")
    print("   → Suggest projects to convert known skills → experienced skills")
    print("   → Identify skill gaps in candidate's domain")
    
    print("\n" + "="*80)
    print("✅ SKILL CLASSIFICATION COMPLETE")
    print("="*80)
    print()


if __name__ == "__main__":
    simulate_skill_classification()
