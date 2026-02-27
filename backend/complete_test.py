"""Complete Module 1 Test - Register, Login, Upload Resume"""
import requests

BASE_URL = "http://localhost:8000"

# Step 1: Register new user
print("=" * 60)
print("STEP 1: Registering new test user...")
print("=" * 60)
register_data = {
    "email": "testuser@example.com",
    "username": "testuser123",
    "password": "TestPass123!",
    "full_name": "Test User"
}
response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
print(f"Status: {response.status_code}")
if response.status_code == 201:
    print("✅ User registered successfully!")
    print(f"User: {response.json()}\n")
elif response.status_code == 400:
    print("⚠️  User already exists, continuing with login...\n")
else:
    print(f"Response: {response.json()}\n")

# Step 2: Login
print("=" * 60)
print("STEP 2: Logging in...")
print("=" * 60)
login_data = {
    "username": "testuser123",
    "password": "TestPass123!"
}
response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
print(f"Status: {response.status_code}")

if response.status_code != 200:
    print(f"❌ Login failed: {response.json()}")
    exit(1)

token = response.json()["access_token"]
print(f"✅ Login successful!")
print(f"Token: {token[:50]}...\n")

# Step 3: Verify authentication
print("=" * 60)
print("STEP 3: Verifying authentication...")
print("=" * 60)
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    print(f"✅ Authentication verified!")
    print(f"User Info: {response.json()}\n")
else:
    print(f"❌ Auth failed: {response.json()}")
    exit(1)

# Step 4: Create sample resume
print("=" * 60)
print("STEP 4: Creating sample resume file...")
print("=" * 60)
resume_content = """
TEST USER
Full Stack Software Engineer

PROFESSIONAL SUMMARY
Experienced software engineer with 5 years of expertise in full-stack development,
specializing in Python, JavaScript, and cloud technologies.

WORK EXPERIENCE

Senior Software Engineer | Tech Solutions Inc. | 2021 - Present
• 5 years of experience in software development
• Led development of microservices architecture using Python and FastAPI
• Implemented CI/CD pipelines with Docker and Kubernetes
• Managed AWS infrastructure and deployment
• Mentored junior developers and conducted code reviews

Software Developer | Digital Innovations | 2019 - 2021
• Developed web applications using Django, React, and Node.js
• Built RESTful APIs and integrated with PostgreSQL and MongoDB
• Implemented authentication and authorization systems
• Worked in Agile/Scrum environment

TECHNICAL SKILLS

Programming Languages: Python, JavaScript, TypeScript, Java, SQL
Web Frameworks: FastAPI, Django, Flask, React, Angular, Node.js, Express
Databases: PostgreSQL, MongoDB, Redis, MySQL, Elasticsearch
Cloud & DevOps: AWS, Azure, Docker, Kubernetes, Jenkins, GitLab CI, Terraform
Tools & Technologies: Git, Linux, REST API, GraphQL, Microservices, Agile, Scrum

EDUCATION
Bachelor of Science in Computer Science
University of Technology | 2015 - 2019

CERTIFICATIONS
• AWS Certified Solutions Architect
• Docker Certified Associate
"""

with open("test_resume.txt", "w", encoding="utf-8") as f:
    f.write(resume_content)
print("✅ Resume file created: test_resume.txt\n")

# Step 5: Upload and parse resume
print("=" * 60)
print("STEP 5: Uploading and parsing resume (MODULE 1 TEST)...")
print("=" * 60)
files = {"file": ("resume.txt", open("test_resume.txt", "rb"), "text/plain")}
response = requests.post(f"{BASE_URL}/resume/parse", headers=headers, files=files)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    print("✅ SUCCESS! Resume parsed successfully!\n")
    data = response.json()
    
    print("=" * 60)
    print("EXTRACTED DATA (MODULE 1 RESULTS)")
    print("=" * 60)
    print(f"\n📋 SKILLS EXTRACTED ({len(data.get('skills', []))} skills):")
    for skill in data.get('skills', []):
        print(f"   • {skill}")
    
    print(f"\n💼 EXPERIENCE:")
    exp = data.get('experience', {})
    print(f"   Years: {exp.get('years', 'N/A')}")
    print(f"   Summary: {exp.get('summary', 'N/A')[:100]}...")
    
    print(f"\n🎯 DOMAIN: {data.get('domain', 'N/A')}")
    print(f"\n📄 Text Length: {data.get('raw_text_length', 0)} characters")
    
    print("\n" + "=" * 60)
    print("✅ MODULE 1 CV EXTRACTION IS WORKING!")
    print("=" * 60)
else:
    print(f"❌ Failed to parse resume")
    print(f"Error: {response.json()}")

# Step 6: Verify data saved to profile
print("\n" + "=" * 60)
print("STEP 6: Verifying data saved to profile...")
print("=" * 60)
response = requests.get(f"{BASE_URL}/auth/profile", headers=headers)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    profile = response.json()
    print("✅ Profile data retrieved!")
    print(f"Skills in profile: {profile.get('skills', [])}")
    print(f"Experience years: {profile.get('experience_years', 'N/A')}")
    print(f"Domain: {profile.get('domain', 'N/A')}")
else:
    print(f"Response: {response.json()}")
