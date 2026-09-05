"""Domain models and definitions for standardized role taxonomy and competency matrices."""

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
