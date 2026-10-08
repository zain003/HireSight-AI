import pytest
from app.ai.extraction import get_extraction_service
from app.resume.service import ResumeService


def test_clinical_informatics_physician_detected_and_rejected():
    cv_text = """Dr. Omar Raza, MD, MPH Physician – Clinical Informatics-Savvy Internist | Islamabad, Pakistan | +92 300 0000000 |
omar.raza@example.com
PROFESSIONAL PROFILE
Practicing physician and clinical researcher who applies digital tools to improve patient care. Comfortable with EHR
workflows, data analytics, telemedicine platforms and AI-assisted diagnostics, while remaining fully focused on bedside
medicine rather than software development.
CLINICAL EXPERIENCE
Attending Physician, Cardiometabolic Clinic, Capital Medical Center 2019 – Present
• Run a hybrid practice: in-person OPD plus telemedicine consultations and remote patient monitoring (RPM) using
connected glucometers and BP wearables.
• Document and order via EHR/EMR with CPOE and clinical decision support alerts; trained 40+ staff on the system
rollout.
• Review imaging through PACS and use AI-assisted chest X-ray triage as a second reader, with physician sign-off on
every report.
• Built patient dashboards (Excel / Power BI) to track HbA1c, LDL and readmission trends; cut missed follow-ups by
22%.
Medical Officer, Emergency & Acute Medicine, Regional Hospital 2015 – 2019
• Used barcode medication administration and e-prescribing to lower dispensing errors.
• Supported the hospital's transition from paper charts to a cloud-based HIS (hospital information system).
RESEARCH & DATA SKILLS
• Data collection with REDCap; basic statistical analysis in SPSS and R; literature management with Zotero.
• Familiar with HL7/FHIR concepts, data privacy / HIPAA-style confidentiality, de-identification and audit trails.
• Co-authored 6 peer-reviewed papers on digital health, machine-learning risk scores for cardiovascular disease and
diabetic care outcomes.
EDUCATION
MPH (Epidemiology & Health Data), Aga Khan University 2018
MD, Dow University of Health Sciences 2014
CERTIFICATIONS
• PMDC Registered Physician | ACLS, BLS
• Certificate in Digital Health & Telemedicine | Good Clinical Practice (GCP)
TECHNICAL FAMILIARITY (CLINICAL USE)
EHR/EMR · PACS/RIS · LIS · Telehealth platforms · Wearables & IoT medical devices · AI diagnostic assistants · Cloud
storage · Cybersecurity awareness · Excel/Power BI · REDCap · R/SPSS
SELECTED PRESENTATIONS
• "Using Wearable Data to Manage Hypertension," National Cardiology Conference, 2023
• "Responsible Use of AI in Radiology Triage," Digital Health Summit, 2024"""

    extractor = get_extraction_service()
    extracted = extractor.extract_all(cv_text)

    # Assert accurate non-computing domain detection
    assert extracted["domain"] == "medical_healthcare", f"Expected medical_healthcare, got {extracted['domain']}"

    # Assert non-computing job titles extracted without corruption (no 'Intern' from 'Internist')
    job_titles_lower = [t.lower() for t in extracted["job_titles"]]
    assert any("physician" in t for t in job_titles_lower)
    assert any("internist" in t for t in job_titles_lower)
    assert "intern" not in job_titles_lower

    # Assert accurate non-computing degrees extracted
    degree_names = [e["degree"] for e in extracted["education"]]
    assert any("MD" in d for d in degree_names)
    assert any("MPH" in d for d in degree_names)

    # Assert resume validation strictly rejects non-computing candidate
    service = ResumeService()
    is_valid, error_msg = service._validate_computing_resume(cv_text, extracted)
    assert is_valid is False
    assert "non-computing" in error_msg.lower() or "medical" in error_msg.lower()


def test_computing_software_engineer_accepted():
    se_text = """
    Alex Johnson
    Senior Software Engineer
    
    Experience:
    - Senior Software Engineer at TechCorp (4 years)
    - Full Stack Developer at WebSolutions (3 years)
    
    Skills: Python, TypeScript, React, Node.js, FastAPI, PostgreSQL, Docker, Kubernetes, AWS, Git, CI/CD
    
    Projects:
    - Microservices platform with event-driven architecture using Kafka
    - Real-time React dashboard with GraphQL API
    
    Education: B.S. in Computer Science from University of Engineering 2017
    """
    extractor = get_extraction_service()
    extracted = extractor.extract_all(se_text)

    assert extracted["domain"] in ("software_engineering", "backend", "fullstack")
    assert len(extracted["skills"]) >= 3

    service = ResumeService()
    is_valid, error_msg = service._validate_computing_resume(se_text, extracted)
    assert is_valid is True
    assert error_msg == ""


def test_healthtech_software_engineer_accepted():
    healthtech_se = """
    Sarah Connor
    Senior Full Stack Engineer
    
    Experience:
    - Senior Full Stack Engineer at Epic HealthTech (4 years)
      Architected hospital EHR integrations and FHIR APIs using Python, FastAPI, React, and PostgreSQL.
      Deployed HIPAA-compliant containerized microservices to AWS with Docker and Kubernetes.
    - Software Developer at MedCloud (2 years)
      Built clinical portal dashboards with TypeScript, Next.js, and Redis.
    
    Skills: Python, TypeScript, React, Next.js, FastAPI, Docker, Kubernetes, AWS, PostgreSQL, Redis, Git, CI/CD
    
    Education: B.Tech Computer Science from State University 2018
    """
    extractor = get_extraction_service()
    extracted = extractor.extract_all(healthtech_se)

    # A real software engineer working in HealthTech should be recognized as computing
    assert extracted["domain"] in ("software_engineering", "fullstack", "backend", "frontend")
    service = ResumeService()
    is_valid, error_msg = service._validate_computing_resume(healthtech_se, extracted)
    assert is_valid is True
