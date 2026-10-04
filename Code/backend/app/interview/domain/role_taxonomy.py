"""Domain models and definitions for standardized role taxonomy and competency matrices."""

import re
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class SeniorityLevel(str, Enum):
    """Seniority classification levels."""
    ENTRY = "entry"       # 0-2 years
    MID = "mid"           # 3-5 years
    SENIOR = "senior"     # 6-8 years
    LEAD = "lead"         # 8+ years


class StandardRole(str, Enum):
    """Standardized software and AI engineering roles."""
    FRONTEND_ENGINEER = "frontend_engineer"
    BACKEND_ENGINEER = "backend_engineer"
    FULLSTACK_ENGINEER = "fullstack_engineer"
    DEVOPS_ENGINEER = "devops_engineer"
    DATA_ENGINEER = "data_engineer"
    ML_ENGINEER = "ml_engineer"
    QA_AUTOMATION_ENGINEER = "qa_automation_engineer"


class CompetencyWeight(BaseModel):
    """Weighted competency area with required technical concepts."""
    competency_area: str
    importance_weight: float = Field(..., ge=0.0, le=1.0)
    required_concepts: List[str] = Field(default_factory=list)


class RoleMetadata(BaseModel):
    """Metadata describing a standardized role."""
    role: StandardRole
    title: str
    description: str
    competencies: List[CompetencyWeight]


# Complete taxonomy of 7 tech roles with defined competency weights summing to 1.0
ROLE_COMPETENCY_MATRICES: Dict[StandardRole, List[CompetencyWeight]] = {
    StandardRole.FRONTEND_ENGINEER: [
        CompetencyWeight(
            competency_area="Core Web Technologies (HTML5/CSS3/JavaScript)",
            importance_weight=0.25,
            required_concepts=[
                "DOM Manipulation",
                "ES6+ Modern JS",
                "CSS Flexbox/Grid",
                "Async/Event Loop",
                "Browser APIs",
                "Responsive Design",
            ],
        ),
        CompetencyWeight(
            competency_area="Modern UI Frameworks (React/Vue/Next.js)",
            importance_weight=0.30,
            required_concepts=[
                "Component Lifecycle",
                "State Management",
                "React Hooks",
                "Virtual DOM",
                "SSR/SSG (Next.js)",
                "Client-Side Routing",
            ],
        ),
        CompetencyWeight(
            competency_area="Web Performance & Core Vitals",
            importance_weight=0.15,
            required_concepts=[
                "LCP/FID/CLS Optimization",
                "Code Splitting & Lazy Loading",
                "Asset & Bundle Optimization",
                "Browser Caching & Service Workers",
            ],
        ),
        CompetencyWeight(
            competency_area="Client-Side Architecture & State",
            importance_weight=0.15,
            required_concepts=[
                "Redux/Zustand/Context API",
                "Immutability Patterns",
                "Data Fetching (React Query/SWR)",
                "Client-Side Cache Invalidation",
            ],
        ),
        CompetencyWeight(
            competency_area="Testing & Web Security",
            importance_weight=0.15,
            required_concepts=[
                "Unit Testing (Jest/React Testing Library)",
                "E2E Testing (Cypress/Playwright)",
                "XSS & CSRF Prevention",
                "CORS & Content Security Policy (CSP)",
            ],
        ),
    ],
    StandardRole.BACKEND_ENGINEER: [
        CompetencyWeight(
            competency_area="API Design & Microservices",
            importance_weight=0.25,
            required_concepts=[
                "RESTful API Design",
                "GraphQL & gRPC",
                "API Versioning & Documentation (OpenAPI)",
                "Rate Limiting & Throttling",
                "Authentication & JWT/OAuth2",
            ],
        ),
        CompetencyWeight(
            competency_area="Database Architecture & Query Optimization",
            importance_weight=0.25,
            required_concepts=[
                "Relational Databases (PostgreSQL/MySQL)",
                "Document Databases (MongoDB)",
                "Indexing Strategies & Execution Plans",
                "Transactions & ACID Guarantees",
                "Connection Pooling & Sharding",
            ],
        ),
        CompetencyWeight(
            competency_area="Concurrency, Async & Performance",
            importance_weight=0.20,
            required_concepts=[
                "Async I/O & Event Loops (Asyncio/Node.js)",
                "Multithreading & Multiprocessing",
                "In-Memory Caching (Redis/Memcached)",
                "Throughput & Latency Optimization",
            ],
        ),
        CompetencyWeight(
            competency_area="Distributed Systems & Messaging",
            importance_weight=0.15,
            required_concepts=[
                "Message Brokers (Kafka/RabbitMQ)",
                "Event-Driven Architecture",
                "CAP Theorem & Consistency Models",
                "Idempotency & Distributed Locks",
            ],
        ),
        CompetencyWeight(
            competency_area="Backend Security & Reliability",
            importance_weight=0.15,
            required_concepts=[
                "SQL/NoSQL Injection Mitigation",
                "Error Handling & Structured Logging",
                "Circuit Breakers & Graceful Degradation",
                "Health Checks & Telemetry",
            ],
        ),
    ],
    StandardRole.FULLSTACK_ENGINEER: [
        CompetencyWeight(
            competency_area="Frontend Architecture & UI Frameworks",
            importance_weight=0.25,
            required_concepts=[
                "React/Next.js/Vue",
                "State Management & Data Flow",
                "Responsive UI & CSS Layouts",
                "Client-Side Performance",
            ],
        ),
        CompetencyWeight(
            competency_area="Backend Systems & REST/GraphQL APIs",
            importance_weight=0.25,
            required_concepts=[
                "FastAPI/Node.js/Express/Django",
                "REST & GraphQL Endpoint Design",
                "Middleware & Request Pipelines",
                "Authentication, Authorization & Session Management",
            ],
        ),
        CompetencyWeight(
            competency_area="Database Design & ORM/ODM Integration",
            importance_weight=0.20,
            required_concepts=[
                "Relational & NoSQL Data Modeling",
                "ORM/ODM (SQLAlchemy/Prisma/Beanie)",
                "Schema Migrations",
                "Query Optimization & Indexing",
            ],
        ),
        CompetencyWeight(
            competency_area="DevOps, CI/CD & Deployment",
            importance_weight=0.15,
            required_concepts=[
                "Docker Containerization",
                "CI/CD Pipeline Automation",
                "Cloud Hosting (AWS/Vercel/DigitalOcean)",
                "Environment & Secret Management",
            ],
        ),
        CompetencyWeight(
            competency_area="Fullstack Security & Testing",
            importance_weight=0.15,
            required_concepts=[
                "End-to-End & Integration Testing",
                "OWASP Top 10 Security Practices",
                "CORS, CSRF & XSS Protection",
                "Input Sanitization & Validation",
            ],
        ),
    ],
    StandardRole.DEVOPS_ENGINEER: [
        CompetencyWeight(
            competency_area="Infrastructure as Code & Cloud Platforms",
            importance_weight=0.30,
            required_concepts=[
                "Terraform & CloudFormation",
                "Cloud Providers (AWS/GCP/Azure)",
                "VPC, Subnets & Cloud Networking",
                "IAM Roles & Least Privilege",
            ],
        ),
        CompetencyWeight(
            competency_area="Containerization & Orchestration",
            importance_weight=0.25,
            required_concepts=[
                "Docker & Multi-Stage Builds",
                "Kubernetes (K8s) Architecture",
                "Helm Charts & Package Management",
                "Ingress, Service Meshes & Auto-scaling",
            ],
        ),
        CompetencyWeight(
            competency_area="CI/CD Automation & Release Engineering",
            importance_weight=0.20,
            required_concepts=[
                "GitHub Actions & GitLab CI",
                "Automated Build & Test Pipelines",
                "Blue-Green & Canary Deployments",
                "Artifact Registries & Release Tagging",
            ],
        ),
        CompetencyWeight(
            competency_area="Observability, Monitoring & Alerting",
            importance_weight=0.15,
            required_concepts=[
                "Prometheus, Grafana & Metrics Exporters",
                "Log Aggregation (ELK/Loki)",
                "Distributed Tracing (OpenTelemetry/Jaeger)",
                "SLA, SLO & Error Budget Tracking",
            ],
        ),
        CompetencyWeight(
            competency_area="DevSecOps & Site Reliability (SRE)",
            importance_weight=0.10,
            required_concepts=[
                "Container Vulnerability Scanning",
                "Secrets Management (HashiCorp Vault/AWS KMS)",
                "Disaster Recovery & Backup Automation",
                "Incident Response & Post-Mortem Practices",
            ],
        ),
    ],
    StandardRole.DATA_ENGINEER: [
        CompetencyWeight(
            competency_area="Data Pipeline Engineering (ETL/ELT)",
            importance_weight=0.30,
            required_concepts=[
                "Batch ETL Pipelines",
                "Stream Processing (Apache Kafka/Flink)",
                "Workflow Orchestration (Airflow/Prefect/Dagster)",
                "Data Ingestion & Change Data Capture (CDC)",
            ],
        ),
        CompetencyWeight(
            competency_area="Big Data & Distributed Computing",
            importance_weight=0.25,
            required_concepts=[
                "Apache Spark & PySpark",
                "Distributed Storage & Partitioning",
                "MapReduce & Distributed Aggregations",
                "Cluster Resource Management",
            ],
        ),
        CompetencyWeight(
            competency_area="Data Warehousing & Modeling",
            importance_weight=0.20,
            required_concepts=[
                "Cloud Data Warehouses (Snowflake/BigQuery/Redshift)",
                "Dimensional Modeling (Star/Snowflake Schema)",
                "Data Lakehouse Architecture (Delta Lake/Iceberg)",
                "Columnar Formats (Parquet/ORC)",
            ],
        ),
        CompetencyWeight(
            competency_area="Database Internals & SQL Mastery",
            importance_weight=0.15,
            required_concepts=[
                "Advanced SQL & Window Functions",
                "Query Execution Plan Optimization",
                "Data Sharding, Clustering & Indexing",
                "NoSQL & Wide-Column Stores (Cassandra/HBase)",
            ],
        ),
        CompetencyWeight(
            competency_area="Data Governance & Quality",
            importance_weight=0.10,
            required_concepts=[
                "Data Lineage & Metadata Catalogs",
                "Automated Data Quality Testing (Great Expectations)",
                "Schema Evolution & Compatibility",
                "Data Privacy & Compliance (GDPR/HIPAA)",
            ],
        ),
    ],
    StandardRole.ML_ENGINEER: [
        CompetencyWeight(
            competency_area="Machine Learning Fundamentals & Algorithms",
            importance_weight=0.25,
            required_concepts=[
                "Supervised & Unsupervised Learning",
                "Loss Functions & Gradient Descent Optimization",
                "Feature Engineering & Selection",
                "Evaluation Metrics (ROC/AUC, Precision/Recall, F1)",
                "Cross-Validation & Regularization",
            ],
        ),
        CompetencyWeight(
            competency_area="Deep Learning & Neural Architectures",
            importance_weight=0.25,
            required_concepts=[
                "PyTorch & TensorFlow",
                "Transformer Models & Self-Attention",
                "Computer Vision (CNNs, MediaPipe, OpenCV)",
                "Natural Language Processing (BERT, Tokenizers)",
            ],
        ),
        CompetencyWeight(
            competency_area="MLOps & Model Deployment Pipelines",
            importance_weight=0.20,
            required_concepts=[
                "Model Serving (FastAPI, Triton, TorchServe)",
                "Experiment Tracking (MLflow, W&B)",
                "Feature Stores (Feast)",
                "Model Registry & CI/CD for Machine Learning",
            ],
        ),
        CompetencyWeight(
            competency_area="Large Language Models & Generative AI",
            importance_weight=0.15,
            required_concepts=[
                "LLM Fine-Tuning (LoRA, QLoRA, PEFT)",
                "Retrieval-Augmented Generation (RAG)",
                "Vector Databases (Milvus, Qdrant, Pinecone)",
                "Embeddings & Semantic Search",
            ],
        ),
        CompetencyWeight(
            competency_area="Data Processing & Model Evaluation",
            importance_weight=0.15,
            required_concepts=[
                "Data Drift & Concept Drift Detection",
                "Model Latency & Throughput Optimization (ONNX/TensorRT)",
                "Model Quantization & Pruning",
                "A/B Testing & Production Monitoring",
            ],
        ),
    ],
    StandardRole.QA_AUTOMATION_ENGINEER: [
        CompetencyWeight(
            competency_area="Test Automation Frameworks & Scripting",
            importance_weight=0.30,
            required_concepts=[
                "Selenium, Playwright & Cypress",
                "PyTest, JUnit & TestNG",
                "Page Object Model (POM) Design Pattern",
                "Data-Driven & Keyword-Driven Testing",
                "Parallel Test Execution & Grid",
            ],
        ),
        CompetencyWeight(
            competency_area="API & Backend Testing",
            importance_weight=0.25,
            required_concepts=[
                "RESTful & GraphQL API Validation",
                "Postman, Newman & REST Assured",
                "Contract Testing (Pact)",
                "Mocking, Stubbing & Service Virtualization",
                "Payload Validation & Response Schema Checking",
            ],
        ),
        CompetencyWeight(
            competency_area="Performance, Load & Stress Testing",
            importance_weight=0.15,
            required_concepts=[
                "JMeter, k6 & Locust",
                "Latency, Throughput & Bottleneck Analysis",
                "Spike, Soak & Stress Testing",
                "Resource Monitoring during Load Tests",
            ],
        ),
        CompetencyWeight(
            competency_area="CI/CD & DevOps Test Integration",
            importance_weight=0.15,
            required_concepts=[
                "Pipeline Test Automation (GitHub Actions, Jenkins)",
                "Test Reporting & Dashboards (Allure)",
                "Dockerized Test Execution",
                "Automated Regression & Smoke Test Gates",
            ],
        ),
        CompetencyWeight(
            competency_area="Quality Engineering, Test Strategy & Bug Triage",
            importance_weight=0.15,
            required_concepts=[
                "Test Case Design & Equivalence Partitioning",
                "Boundary Value Analysis",
                "Risk-Based Testing & Coverage Analysis",
                "Defect Lifecycle & Root Cause Analysis (RCA)",
            ],
        ),
    ],
}

ROLE_METADATA_REGISTRY: Dict[StandardRole, Dict[str, str]] = {
    StandardRole.FRONTEND_ENGINEER: {
        "title": "Frontend Engineer",
        "description": "Specializes in interactive web client development, React/Next.js frameworks, responsive CSS, and web performance optimization.",
    },
    StandardRole.BACKEND_ENGINEER: {
        "title": "Backend Engineer",
        "description": "Specializes in scalable server-side systems, REST/gRPC API architectures, relational/NoSQL databases, and distributed messaging.",
    },
    StandardRole.FULLSTACK_ENGINEER: {
        "title": "Fullstack Engineer",
        "description": "Bridges frontend user interfaces with robust backend services, end-to-end database integrations, and containerized deployment.",
    },
    StandardRole.DEVOPS_ENGINEER: {
        "title": "DevOps / SRE Engineer",
        "description": "Focuses on infrastructure as code, Kubernetes orchestration, CI/CD automation pipelines, observability, and cloud security.",
    },
    StandardRole.DATA_ENGINEER: {
        "title": "Data Engineer",
        "description": "Specializes in distributed data pipelines, ETL/ELT batch and streaming systems (Kafka, Spark), and cloud data warehouses.",
    },
    StandardRole.ML_ENGINEER: {
        "title": "Machine Learning Engineer",
        "description": "Develops production machine learning models, deep learning architectures, MLOps deployment pipelines, and Generative AI / LLM solutions.",
    },
    StandardRole.QA_AUTOMATION_ENGINEER: {
        "title": "QA Automation Engineer",
        "description": "Designs automated testing frameworks (Playwright, Selenium, PyTest), API regression suites, and CI/CD quality verification gates.",
    },
}


def get_role_competency_matrix(role: StandardRole) -> List[CompetencyWeight]:
    """Retrieve the defined competency weights and required concepts for a role."""
    return ROLE_COMPETENCY_MATRICES.get(role, [])


def get_all_standard_roles() -> List[StandardRole]:
    """Return all supported standardized roles."""
    return list(StandardRole)


def parse_standard_role(role_str: Optional[str]) -> StandardRole:
    """Robustly parse and normalize any role string, display title, or synonym into a StandardRole enum."""
    if not role_str:
        return StandardRole.BACKEND_ENGINEER

    if isinstance(role_str, StandardRole):
        return role_str

    raw = str(role_str).strip()
    norm = raw.lower().replace("-", "_").replace(" ", "_")

    # 1. Exact value match
    for role in StandardRole:
        if role.value == norm or role.value == raw.lower():
            return role

    # 2. Modern Full-Stack & Framework Stacks
    norm_text = raw.lower()
    if any(k in norm_text for k in ["mern", "mean", "mevn", "pern", "lamp", "jamstack", "fullstack", "full stack", "full_stack", "full-stack"]):
        return StandardRole.FULLSTACK_ENGINEER

    # 3. Frontend & Mobile Stacks
    if any(k in norm_text for k in ["front", "react", "vue", "angular", "svelte", "nextjs", "next.js", "ui", "web dev", "frontend", "flutter", "react native", "react_native", "ios", "android", "mobile"]):
        return StandardRole.FRONTEND_ENGINEER

    # 4. DevOps, Cloud & SRE
    if any(k in norm_text for k in ["devops", "cloud", "sre", "infra", "infrastructure", "kubernetes", "k8s", "terraform", "platform", "aws", "gcp", "azure", "docker"]):
        return StandardRole.DEVOPS_ENGINEER

    # 5. Data Engineering & Big Data
    if any(k in norm_text for k in ["data engineer", "data_engineer", "big data", "etl", "spark", "warehouse", "snowflake", "databricks", "airflow", "kafka", "data pipeline"]):
        return StandardRole.DATA_ENGINEER

    # 6. ML / AI / Data Science
    if any(k in norm_text for k in ["ml", "machine learning", "machine_learning", "ai engineer", "deep learning", "nlp", "computer vision", "llm", "genai", "generative ai", "data scientist", "data science"]):
        return StandardRole.ML_ENGINEER

    # 7. QA & Test Automation
    if any(k in norm_text for k in ["qa", "test", "quality", "sdet", "automation engineer", "playwright", "cypress", "selenium"]):
        return StandardRole.QA_AUTOMATION_ENGINEER

    # 8. Backend & Server-Side Systems
    if any(k in norm_text for k in ["back", "server", "api", "backend", "python", "django", "fastapi", "flask", "golang", "go engineer", "java", "spring", "spring boot", "node", "express", "ruby", "rails", ".net", "dotnet", "c#", "csharp", "php", "rust"]):
        return StandardRole.BACKEND_ENGINEER

    return StandardRole.BACKEND_ENGINEER


def detect_specialized_stack(role_str: Optional[str], skills: Optional[List[str]] = None) -> tuple[str, List[str]]:
    """
    Detects specialized tech stack tags and suggested core skills from role title and skills.
    Prioritizes role title domain first, then explicit skills.
    Returns (stack_key, default_stack_skills).
    """
    r_str = str(role_str or "").lower()
    s_str = " ".join(skills or []).lower()

    # 1. Check role title first to avoid cross-domain false positives (e.g. DevOps getting MERN because candidate has React on CV)
    if any(k in r_str for k in ["devops", "cloud", "sre", "infrastructure", "kubernetes", "k8s", "terraform", "platform engineer", "docker", "site reliability"]):
        return "devops_cloud", ["Docker", "Kubernetes", "Terraform", "CI/CD (GitHub Actions)", "AWS/GCP", "Prometheus/Grafana"]
    if any(k in r_str for k in ["data engineer", "data_engineer", "etl", "spark", "airflow", "data pipeline"]):
        return "data_pipeline", ["Apache Spark", "Python/PySpark", "SQL", "Airflow", "Data Warehousing (Snowflake/BigQuery)", "Kafka"]
    if any(k in r_str for k in ["ml", "machine learning", "ai engineer", "deep learning", "nlp", "computer vision", "llm", "genai", "data scientist"]):
        return "ml_ai", ["PyTorch/TensorFlow", "Transformers", "RAG & Vector DBs", "MLOps", "Model Serving", "Python"]
    if any(k in r_str for k in ["qa", "quality assurance", "test automation", "sdet", "automation engineer"]):
        return "qa_automation", ["Playwright/Cypress", "Python/TypeScript", "API Testing", "CI/CD Integration", "Page Object Model"]
    if any(k in r_str for k in ["blockchain", "web3", "smart contract", "solidity", "crypto", "defi"]):
        return "blockchain_web3", ["Solidity", "Smart Contracts", "EVM", "Hardhat/Foundry", "Web3.js/Ethers.js", "Reentrancy & Gas Optimization"]
    if any(k in r_str for k in ["flutter", "dart"]):
        return "flutter", ["Flutter", "Dart", "State Management (Bloc/Provider)", "REST APIs", "Mobile UI", "Offline Caching"]
    if "react native" in r_str or "react_native" in r_str:
        return "react_native", ["React Native", "JavaScript/TypeScript", "Redux/Zustand", "Native Modules", "Mobile Performance"]
    if re.search(r"\b(spring|springboot|jvm|hibernate)\b", r_str) or (re.search(r"\bjava\b", r_str) and "javascript" not in r_str):
        return "java_backend", ["Java", "Spring Boot", "Hibernate/JPA", "Microservices", "PostgreSQL", "REST APIs"]
    if "django" in r_str or "flask" in r_str or "fastapi" in r_str or (re.search(r"\bpython\b", r_str) and ("backend" in r_str or "api" in r_str)):
        return "python_backend", ["Python", "Django/FastAPI", "PostgreSQL", "ORM", "Asyncio", "REST APIs", "Celery"]
    if "mern" in r_str:
        return "mern", ["MongoDB", "Express.js", "React.js", "Node.js", "REST APIs", "JWT Authentication"]
    if "mean" in r_str:
        return "mean", ["MongoDB", "Express.js", "Angular", "Node.js", "TypeScript", "REST APIs"]
    if "pern" in r_str:
        return "pern", ["PostgreSQL", "Express.js", "React.js", "Node.js", "SQL", "REST APIs"]
    if "lamp" in r_str:
        return "lamp", ["Linux", "Apache", "MySQL", "PHP", "MVC", "OOP"]
    if "vue" in r_str or "nuxt" in r_str:
        return "vue", ["Vue.js", "Nuxt.js", "Pinia/Vuex", "TypeScript", "Component Design", "Vite"]
    if "next" in r_str or ("react" in r_str and "native" not in r_str):
        return "react_next", ["React.js", "Next.js", "TypeScript", "Tailwind CSS", "State Management", "SSR/SSG"]

    # 2. Check combined text when role title is generic (e.g. 'Software Engineer', 'Fullstack Engineer')
    raw = f"{r_str} {s_str}".strip()

    if any(k in raw for k in ["k8s", "kubernetes", "terraform", "devops", "docker", "ci/cd", "aws", "gcp", "azure"]) and not any(k in r_str for k in ["front", "react"]):
        if any(k in s_str for k in ["kubernetes", "k8s", "terraform", "docker", "ansible", "helm"]) and ("react" not in r_str and "node" not in r_str):
            return "devops_cloud", ["Docker", "Kubernetes", "Terraform", "CI/CD (GitHub Actions)", "AWS/GCP", "Prometheus/Grafana"]

    if "mern" in raw or (("react" in raw or "next" in raw) and ("node" in raw or "express" in raw or "mongo" in raw)):
        return "mern", ["MongoDB", "Express.js", "React.js", "Node.js", "REST APIs", "JWT Authentication"]
    if "mean" in raw or ("angular" in raw and ("node" in raw or "express" in raw or "mongo" in raw)):
        return "mean", ["MongoDB", "Express.js", "Angular", "Node.js", "TypeScript", "REST APIs"]
    if "pern" in raw:
        return "pern", ["PostgreSQL", "Express.js", "React.js", "Node.js", "SQL", "REST APIs"]
    if "lamp" in raw:
        return "lamp", ["Linux", "Apache", "MySQL", "PHP", "MVC", "OOP"]
    if "django" in raw or "flask" in raw or "fastapi" in raw or (re.search(r"\bpython\b", raw) and ("backend" in raw or "api" in raw or "django" in raw or "fastapi" in raw)):
        return "python_backend", ["Python", "Django/FastAPI", "PostgreSQL", "ORM", "Asyncio", "REST APIs", "Celery"]
    if re.search(r"\b(spring|springboot|jvm|hibernate)\b", raw) or (re.search(r"\bjava\b", raw) and "javascript" not in raw):
        return "java_backend", ["Java", "Spring Boot", "Hibernate/JPA", "Microservices", "PostgreSQL", "REST APIs"]
    if "flutter" in raw or "dart" in raw:
        return "flutter", ["Flutter", "Dart", "State Management (Bloc/Provider)", "REST APIs", "Mobile UI", "Offline Caching"]
    if "react native" in raw or "react_native" in raw:
        return "react_native", ["React Native", "JavaScript/TypeScript", "Redux/Zustand", "Native Modules", "Mobile Performance"]
    if "next" in raw or "react" in raw:
        return "react_next", ["React.js", "Next.js", "TypeScript", "Tailwind CSS", "State Management", "SSR/SSG"]
    if "vue" in raw or "nuxt" in raw:
        return "vue", ["Vue.js", "Nuxt.js", "Pinia/Vuex", "TypeScript", "Component Design", "Vite"]
    if any(k in raw for k in ["k8s", "kubernetes", "terraform", "devops", "docker", "ci/cd"]):
        return "devops_cloud", ["Docker", "Kubernetes", "Terraform", "CI/CD (GitHub Actions)", "AWS/GCP", "Prometheus/Grafana"]
    if any(k in raw for k in ["spark", "etl", "airflow", "data engineer", "snowflake", "bigquery"]):
        return "data_pipeline", ["Apache Spark", "Python/PySpark", "SQL", "Airflow", "Data Warehousing (Snowflake/BigQuery)", "Kafka"]
    if any(k in raw for k in ["llm", "rag", "deep learning", "machine learning", "pytorch", "tensorflow"]):
        return "ml_ai", ["PyTorch/TensorFlow", "Transformers", "RAG & Vector DBs", "MLOps", "Model Serving", "Python"]
    if any(k in raw for k in ["playwright", "cypress", "selenium", "qa", "pytest"]):
        return "qa_automation", ["Playwright/Cypress", "Python/TypeScript", "API Testing", "CI/CD Integration", "Page Object Model"]
    if any(k in raw for k in ["solidity", "smart contract", "blockchain", "web3", "evm", "crypto", "defi"]):
        return "blockchain_web3", ["Solidity", "Smart Contracts", "EVM", "Hardhat/Foundry", "Web3.js/Ethers.js", "Reentrancy & Gas Optimization"]
    
    return "general", []


def parse_seniority_level(
    difficulty_or_seniority: Optional[str],
    experience_years: Optional[int] = None,
) -> SeniorityLevel:
    """Parse candidate-selected difficulty or seniority level string with fallback to experience inference."""
    if isinstance(difficulty_or_seniority, SeniorityLevel):
        return difficulty_or_seniority

    if difficulty_or_seniority and isinstance(difficulty_or_seniority, str):
        val = difficulty_or_seniority.strip().lower()
        if any(k in val for k in ["lead", "principal", "staff", "architect", "expert"]):
            return SeniorityLevel.LEAD
        if any(k in val for k in ["senior", "advanced", "hard", "sr"]):
            return SeniorityLevel.SENIOR
        if any(k in val for k in ["entry", "junior", "beginner", "easy", "intern", "assoc", "graduate", "fresher"]):
            return SeniorityLevel.ENTRY
        if any(k in val for k in ["mid", "intermediate", "medium", "middle", "experienced"]):
            return SeniorityLevel.MID

    # Experience-based inference fallback
    if experience_years is None or experience_years <= 2:
        return SeniorityLevel.ENTRY
    elif experience_years <= 5:
        return SeniorityLevel.MID
    elif experience_years <= 8:
        return SeniorityLevel.SENIOR
    else:
        return SeniorityLevel.LEAD


