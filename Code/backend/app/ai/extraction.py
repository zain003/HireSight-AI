"""
AI-powered information extraction from resume text.
Handles skill extraction, experience detection, domain classification,
job title extraction, education parsing, project extraction, and certification detection.
"""
import re
from typing import List, Dict, Optional
import json

from app.ai.embeddings import get_embedding_service


# ──────────────────────────────────────────────────────────────────────────────
# SKILL DATABASE
# ──────────────────────────────────────────────────────────────────────────────
SKILL_DATABASE = [
    # ── Programming Languages (40+) ──
    "Python", "Java", "JavaScript", "TypeScript", "C", "C++", "C#", "Go", "Rust",
    "Ruby", "PHP", "Swift", "Kotlin", "Scala", "R", "MATLAB", "SQL", "Perl",
    "Haskell", "Lua", "Dart", "Objective-C", "Shell", "Bash", "PowerShell",
    "Assembly", "Groovy", "Elixir", "Clojure", "F#", "Julia", "Solidity",
    "Visual Basic", "VBA", "COBOL", "Fortran", "Erlang", "OCaml", "Zig",
    "Crystal", "Nim", "Ada", "Prolog", "Lisp", "Scheme", "Racket",
    "CoffeeScript", "ActionScript", "ABAP", "Apex", "PL/SQL", "T-SQL",

    # ── Web Frontend (50+) ──
    "React", "React.js", "Angular", "Angular.js", "AngularJS", "Vue.js", "Vue",
    "Svelte", "SvelteKit", "Next.js", "Nuxt.js", "Remix", "Astro",
    "Gatsby", "Ember.js", "Backbone.js", "Alpine.js", "Lit", "Solid.js",
    "HTML", "HTML5", "CSS", "CSS3", "SASS", "SCSS", "LESS", "PostCSS",
    "Tailwind CSS", "Bootstrap", "Bulma", "Foundation",
    "Material UI", "Chakra UI", "Ant Design", "Radix UI", "Shadcn",
    "jQuery", "Webpack", "Vite", "Babel", "ESLint", "Prettier",
    "esbuild", "Rollup", "Parcel", "Turbopack", "SWC",
    "Redux", "Redux Toolkit", "MobX", "Zustand", "Recoil", "Jotai", "XState",
    "React Query", "TanStack Query", "SWR", "Apollo Client",
    "Styled Components", "Emotion", "CSS Modules", "Stitches",
    "Three.js", "D3.js", "Chart.js", "Highcharts", "ECharts", "Recharts",
    "WebGL", "Canvas API", "SVG", "WebAssembly", "WASM",
    "Framer Motion", "GSAP", "Lottie", "Anime.js",
    "Storybook", "Chromatic", "Bit",
    "Progressive Web Apps", "PWA", "Service Workers",
    "Responsive Design", "Web Accessibility", "WCAG", "ARIA",
    "Web Components", "Shadow DOM", "Custom Elements",
    "Electron", "Tauri",

    # ── Web Backend / Frameworks (40+) ──
    "Node.js", "Express", "Express.js", "Django", "Flask", "FastAPI",
    "Spring", "Spring Boot", "Spring MVC", "Spring Security", "Spring Data",
    "ASP.NET", "ASP.NET Core", ".NET", ".NET Core", ".NET Framework",
    "Ruby on Rails", "Rails", "Sinatra",
    "Laravel", "Symfony", "CodeIgniter", "CakePHP", "Yii", "Slim",
    "NestJS", "Koa", "Hapi", "Fastify", "Adonis.js",
    "Gin", "Echo", "Fiber", "Chi", "Gorilla Mux",
    "Phoenix", "Rocket", "Actix Web", "Axum", "Warp",
    "Strapi", "KeystoneJS", "Directus", "Payload CMS",
    "Prisma", "TypeORM", "Sequelize", "SQLAlchemy", "Hibernate",
    "Drizzle ORM", "Mongoose", "Knex.js", "MikroORM",
    "GraphQL Yoga", "Mercurius", "Strawberry",

    # ── Databases (40+) ──
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "Cassandra",
    "Oracle", "Oracle Database", "SQL Server", "Microsoft SQL Server",
    "SQLite", "DynamoDB", "MariaDB", "CouchDB", "CouchBase",
    "Neo4j", "ArangoDB", "OrientDB", "JanusGraph",
    "InfluxDB", "TimescaleDB", "QuestDB", "Prometheus TSDB",
    "Firebase", "Firestore", "Firebase Realtime Database",
    "Supabase", "PlanetScale", "Neon", "CockroachDB", "TiDB", "YugabyteDB",
    "Amazon RDS", "Amazon Aurora", "Amazon Redshift",
    "Azure SQL", "Azure Cosmos DB", "Cloud SQL", "Cloud Spanner",
    "Memcached", "etcd", "Hazelcast",
    "ClickHouse", "Apache Druid", "Apache Pinot",
    "Milvus", "Qdrant", "Faiss",

    # ── Cloud Platforms & Services (60+) ──
    "AWS", "Amazon Web Services", "Azure", "Microsoft Azure",
    "GCP", "Google Cloud", "Google Cloud Platform",
    "Heroku", "DigitalOcean", "Vercel", "Netlify", "Cloudflare",
    "Linode", "Vultr", "Fly.io", "Railway", "Render",
    "AWS Lambda", "S3", "EC2", "ECS", "EKS", "EBS", "ECR",
    "SQS", "SNS", "SES", "Step Functions", "EventBridge",
    "API Gateway", "CloudFormation", "CloudWatch", "CloudTrail",
    "AWS IAM", "AWS VPC", "Route 53", "CloudFront",
    "AWS Glue", "AWS Athena", "AWS EMR", "AWS Kinesis",
    "AWS CodePipeline", "AWS CodeBuild", "AWS CodeDeploy",
    "Azure Functions", "Azure DevOps", "Azure Pipelines",
    "Azure App Service", "Azure Kubernetes Service", "Azure Container Instances",
    "Azure Blob Storage", "Azure Event Hub", "Azure Service Bus",
    "Azure Active Directory", "Azure Monitor", "Azure Logic Apps",
    "Cloud Functions", "BigQuery", "Cloud Run", "Cloud Build",
    "Google Kubernetes Engine", "App Engine", "Pub/Sub",
    "Cloud Storage", "Vertex AI", "Dataflow", "Dataproc",
    "IBM Cloud", "Oracle Cloud", "Alibaba Cloud",

    # ── DevOps & Infrastructure (50+) ──
    "Docker", "Docker Compose", "Docker Swarm", "Podman", "Containerd",
    "Kubernetes", "K8s", "OpenShift", "Rancher", "K3s", "Minikube",
    "Jenkins", "GitLab CI", "GitHub Actions", "CircleCI", "Travis CI",
    "Azure Pipelines", "Bamboo", "TeamCity", "Drone CI", "Concourse",
    "Terraform", "Pulumi", "CloudFormation", "Crossplane", "CDK",
    "Ansible", "Puppet", "Chef", "SaltStack",
    "CI/CD", "Continuous Integration", "Continuous Deployment",
    "Helm", "Kustomize", "ArgoCD", "Flux", "Spinnaker",
    "Prometheus", "Grafana", "Datadog", "New Relic", "Splunk",
    "ELK Stack", "Elastic Stack", "Logstash", "Kibana", "Fluentd", "Loki",
    "PagerDuty", "OpsGenie", "VictorOps",
    "Nginx", "Apache", "HAProxy", "Traefik", "Caddy", "Envoy",
    "Istio", "Linkerd", "Consul", "Vault", "Nomad",
    "SonarQube", "Snyk", "Trivy", "Aqua Security",
    "Nexus", "Artifactory", "Harbor",
    "Packer", "Vagrant", "Multipass",
    "Terragrunt", "Checkov", "Sentinel",

    # ── Version Control ──
    "Git", "GitHub", "GitLab", "Bitbucket", "SVN", "Mercurial",
    "Git Flow", "Trunk Based Development", "Conventional Commits",

    # ── Data Science & ML (60+) ──
    "Machine Learning", "Deep Learning", "TensorFlow", "TensorFlow Lite",
    "PyTorch", "PyTorch Lightning", "Keras",
    "Scikit-learn", "Pandas", "NumPy", "SciPy", "Polars", "Dask",
    "Matplotlib", "Seaborn", "Plotly", "Bokeh", "Altair",
    "NLP", "Natural Language Processing", "Computer Vision",
    "Data Analysis", "Data Mining", "Data Visualization",
    "Statistical Modeling", "Statistical Analysis", "A/B Testing",
    "Hypothesis Testing", "Regression Analysis", "Time Series Analysis",
    "Neural Networks", "CNN", "RNN", "LSTM", "GAN",
    "Convolutional Neural Network", "Recurrent Neural Network",
    "Reinforcement Learning", "Transfer Learning",
    "Feature Engineering", "Feature Selection", "Dimensionality Reduction",
    "PCA", "t-SNE", "UMAP",
    "MLOps", "MLflow", "Weights & Biases", "WandB", "Neptune.ai",
    "Kubeflow", "BentoML", "Seldon", "TensorFlow Serving", "TorchServe",
    "Hugging Face", "OpenCV", "NLTK", "SpaCy", "Gensim",
    "XGBoost", "LightGBM", "CatBoost", "Random Forest",
    "SVM", "Support Vector Machine", "Naive Bayes",
    "K-Means", "DBSCAN", "Decision Tree", "Gradient Boosting",
    "Ensemble Methods", "AutoML", "H2O", "TPOT",
    "Jupyter", "Jupyter Notebook", "JupyterLab", "Google Colab",
    "Apache Spark", "PySpark", "Spark MLlib",
    "Hadoop", "MapReduce", "HDFS", "YARN",
    "Hive", "Pig", "Presto", "Trino",
    "Kafka", "Kafka Streams", "Confluent",
    "Airflow", "Apache Airflow", "Prefect", "Dagster", "Luigi",
    "dbt", "dbt Core", "dbt Cloud",
    "Snowflake", "Databricks", "Delta Lake",
    "Tableau", "Power BI", "Looker", "Metabase", "Superset",
    "Google Data Studio", "Qlik", "MicroStrategy",
    "ETL", "ELT", "Data Warehousing", "Data Pipeline", "Data Lake",
    "Data Modeling", "Star Schema", "Snowflake Schema",
    "Great Expectations", "Apache Beam", "Flink",

    # ── AI / LLM (30+) ──
    "Artificial Intelligence", "Generative AI", "LLM", "Large Language Models",
    "GPT", "GPT-4", "GPT-3.5", "ChatGPT", "OpenAI", "OpenAI API",
    "Claude", "Anthropic", "Gemini", "Google Gemini", "Llama", "Mistral",
    "LangChain", "LlamaIndex", "Haystack",
    "RAG", "Retrieval Augmented Generation",
    "Prompt Engineering", "Prompt Tuning",
    "Fine-tuning", "RLHF", "DPO", "LoRA", "QLoRA", "PEFT",
    "Transformers", "BERT", "RoBERTa", "DistilBERT", "ALBERT",
    "T5", "BART", "Whisper", "DALL-E", "Stable Diffusion", "Midjourney",
    "Embeddings", "Sentence Transformers", "SBERT",
    "Vector Databases", "Pinecone", "Weaviate", "ChromaDB", "Milvus", "Qdrant",
    "FAISS", "Annoy",
    "Semantic Search", "Text Generation", "Text Classification",
    "Sentiment Analysis", "Named Entity Recognition", "NER",
    "Question Answering", "Summarization", "Translation",
    "Object Detection", "Image Classification", "Image Segmentation",
    "YOLO", "Detectron2", "SAM",
    "vLLM", "Ollama", "LocalAI",
    "Agents", "AI Agents", "AutoGPT", "CrewAI",

    # ── Mobile Development (20+) ──
    "Android", "Android SDK", "Android Studio",
    "iOS", "iOS SDK", "Xcode",
    "React Native", "Expo",
    "Flutter", "Dart",
    "Xamarin", "MAUI", ".NET MAUI",
    "SwiftUI", "UIKit", "Combine",
    "Jetpack Compose", "Kotlin Multiplatform",
    "Ionic", "Capacitor", "Cordova",
    "App Store", "Google Play", "TestFlight",
    "Firebase Cloud Messaging", "Push Notifications",
    "Mobile Testing", "Appium", "Detox", "XCTest",

    # ── Testing & QA (40+) ──
    "Unit Testing", "Integration Testing", "End-to-End Testing", "E2E Testing",
    "Functional Testing", "Regression Testing", "Smoke Testing",
    "Performance Testing", "Load Testing", "Stress Testing",
    "Security Testing", "Penetration Testing", "API Testing",
    "Acceptance Testing", "UAT", "User Acceptance Testing",
    "Jest", "Mocha", "Chai", "Sinon", "Vitest",
    "Cypress", "Selenium", "Selenium WebDriver", "Playwright", "Puppeteer",
    "WebdriverIO", "TestCafe", "Nightwatch.js",
    "PyTest", "unittest", "Robot Framework",
    "JUnit", "JUnit5", "TestNG", "Mockito", "PowerMock",
    "RSpec", "Minitest", "Capybara",
    "xUnit", "NUnit", "MSTest",
    "Postman", "Insomnia", "HTTPie",
    "TDD", "BDD", "ATDD",
    "Cucumber", "SpecFlow", "Behave", "Gherkin",
    "Test Automation", "Test-Driven Development",
    "JMeter", "Locust", "K6", "Gatling", "Artillery",
    "Appium", "Detox", "Espresso", "XCTest",
    "SonarQube", "Code Coverage", "Istanbul",
    "Contract Testing", "Pact", "Consumer-Driven Contracts",
    "Chaos Engineering", "Chaos Monkey",

    # ── APIs & Communication (30+) ──
    "REST API", "RESTful", "RESTful API",
    "GraphQL", "Apollo GraphQL", "Relay",
    "gRPC", "Protocol Buffers", "Protobuf",
    "WebSocket", "WebSockets", "Socket.io", "SignalR",
    "Server-Sent Events", "SSE",
    "SOAP", "XML-RPC", "JSON-RPC",
    "OAuth", "OAuth2", "OpenID Connect", "OIDC",
    "JWT", "JSON Web Token", "SAML", "PASETO",
    "OpenAPI", "Swagger", "API Blueprint", "Postman Collections",
    "API Design", "API Gateway", "API Management",
    "RabbitMQ", "Apache Kafka", "Amazon SQS", "Azure Service Bus",
    "NATS", "ZeroMQ", "MQTT", "AMQP", "STOMP",
    "Apache ActiveMQ", "Redis Pub/Sub",
    "Webhooks", "Long Polling", "Polling",
    "Rate Limiting", "Throttling", "Circuit Breaker",
    "API Versioning", "HATEOAS",
    "Twilio", "SendGrid", "Stripe API", "PayPal API",

    # ── Architecture & Design Patterns (30+) ──
    "Microservices", "Monolithic", "Modular Monolith",
    "Serverless", "Event-Driven", "Event-Driven Architecture",
    "Domain-Driven Design", "DDD",
    "CQRS", "Event Sourcing", "Saga Pattern",
    "System Design", "Design Patterns", "SOLID",
    "OOP", "Object-Oriented Programming",
    "Functional Programming", "Reactive Programming",
    "Clean Architecture", "Hexagonal Architecture", "Onion Architecture",
    "MVC", "MVP", "MVVM", "MVI",
    "SOA", "Service-Oriented Architecture",
    "Distributed Systems", "High Availability", "Scalability",
    "Load Balancing", "Caching", "CDN",
    "Message Queue", "Pub/Sub Pattern",
    "12-Factor App", "Strangler Fig Pattern",
    "BFF", "Backend for Frontend",
    "API-First Design", "Contract-First Design",
    "KISS", "DRY", "YAGNI",
    "Repository Pattern", "Unit of Work", "Factory Pattern",
    "Observer Pattern", "Strategy Pattern", "Singleton Pattern",

    # ── Security & Compliance (40+) ──
    "Cybersecurity", "Penetration Testing", "Pen Testing",
    "OWASP", "OWASP Top 10",
    "Encryption", "AES", "RSA", "SHA-256",
    "SSL/TLS", "HTTPS", "PKI", "X.509",
    "IAM", "Identity and Access Management",
    "SIEM", "SOC", "Security Operations Center",
    "Vulnerability Assessment", "Vulnerability Scanning",
    "Network Security", "Application Security", "Cloud Security",
    "Authentication", "Authorization", "RBAC", "ABAC",
    "SSO", "Single Sign-On", "MFA", "Multi-Factor Authentication",
    "OAuth", "SAML", "LDAP", "Active Directory",
    "Ethical Hacking", "Bug Bounty",
    "Malware Analysis", "Reverse Engineering",
    "Digital Forensics", "Incident Response",
    "GDPR", "HIPAA", "PCI DSS", "SOC 2", "ISO 27001", "NIST",
    "CCPA", "FERPA", "SOX",
    "Zero Trust", "Defense in Depth",
    "WAF", "Web Application Firewall",
    "IDS", "IPS", "Intrusion Detection",
    "Burp Suite", "Nmap", "Wireshark", "Metasploit", "Kali Linux",
    "Nessus", "Qualys", "CrowdStrike", "Carbon Black",
    "HashiCorp Vault", "AWS KMS", "Azure Key Vault",
    "DevSecOps", "Shift Left Security",

    # ── Networking & OS (30+) ──
    "Linux", "Ubuntu", "Debian", "CentOS", "Fedora", "Arch Linux",
    "Red Hat", "RHEL", "Rocky Linux", "AlmaLinux", "Amazon Linux",
    "Windows", "Windows Server", "macOS",
    "Unix", "FreeBSD", "Solaris",
    "TCP/IP", "DNS", "DHCP", "HTTP", "HTTPS",
    "HTTP/2", "HTTP/3", "QUIC",
    "VPN", "IPSec", "WireGuard", "OpenVPN",
    "VLAN", "Subnetting", "Routing", "Switching",
    "BGP", "OSPF", "MPLS",
    "Active Directory", "LDAP", "Kerberos",
    "SSH", "FTP", "SFTP", "SCP",
    "Cisco", "Juniper", "Palo Alto", "Fortinet",
    "CCNA", "CCNP", "CCIE",
    "SDN", "NFV", "Software-Defined Networking",
    "Load Balancer", "F5", "HAProxy", "Nginx",

    # ── Project & Product Management (20+) ──
    "Agile", "Scrum", "Kanban", "Lean", "SAFe", "XP",
    "Sprint Planning", "Sprint Retrospective", "Daily Standup",
    "Jira", "Confluence", "Trello", "Asana", "Monday.com",
    "Linear", "Notion", "ClickUp", "Shortcut",
    "Project Management", "Product Management",
    "Requirements Analysis", "User Stories", "Epics",
    "Stakeholder Management", "Roadmap", "OKRs",
    "Waterfall", "Prince2", "PMP",
    "Miro", "FigJam", "Lucidchart",

    # ── Soft Skills ──
    "Leadership", "Team Management", "Communication",
    "Problem Solving", "Critical Thinking", "Collaboration",
    "Mentoring", "Coaching", "Code Review", "Technical Writing",
    "Presentation Skills", "Negotiation", "Time Management",
    "Decision Making", "Conflict Resolution", "Adaptability",

    # ── Blockchain & Web3 (20+) ──
    "Blockchain", "Ethereum", "Bitcoin", "Polygon", "Solana", "Avalanche",
    "Smart Contracts", "Solidity", "Vyper", "Rust",
    "Web3", "Web3.js", "Ethers.js", "Hardhat", "Truffle", "Foundry",
    "DeFi", "NFT", "DAO", "DEX",
    "Hyperledger", "Hyperledger Fabric",
    "IPFS", "Chainlink", "The Graph", "OpenZeppelin",

    # ── IoT & Embedded (20+) ──
    "IoT", "Internet of Things", "IIoT",
    "Embedded Systems", "Embedded C", "Embedded Linux",
    "Arduino", "Raspberry Pi", "ESP32", "ESP8266", "STM32",
    "RTOS", "FreeRTOS", "Zephyr",
    "FPGA", "Verilog", "VHDL", "SystemVerilog",
    "Microcontrollers", "Sensors", "Actuators",
    "Edge Computing", "Edge AI",
    "I2C", "SPI", "UART", "CAN Bus", "Modbus",
    "PLC", "SCADA",
    "ROS", "Robot Operating System",
    "ARM", "RISC-V", "MIPS",

    # ── Game Development (20+) ──
    "Unity", "Unity3D", "Unreal Engine", "UE4", "UE5",
    "Godot", "GameMaker", "CryEngine", "Cocos2d",
    "OpenGL", "Vulkan", "DirectX", "DirectX 12", "Metal",
    "Shader", "HLSL", "GLSL",
    "Blender", "3ds Max", "Maya",
    "Game Design", "Level Design", "Game Physics",
    "Multiplayer Networking", "Photon",

    # ── Design Tools (20+) ──
    "Figma", "Adobe XD", "Sketch", "InVision",
    "Photoshop", "Illustrator", "After Effects", "Premiere Pro",
    "Adobe Creative Suite", "Adobe Creative Cloud",
    "Canva", "GIMP", "Inkscape",
    "Framer", "Principle", "ProtoPie",
    "Zeplin", "Balsamiq", "Axure",
    "Design Systems", "Design Tokens",
    "Wireframing", "Prototyping", "User Research",
    "Usability Testing", "A/B Testing",

    # ── CMS & E-commerce ──
    "WordPress", "Drupal", "Joomla",
    "Shopify", "Magento", "WooCommerce", "BigCommerce",
    "Contentful", "Sanity", "Strapi", "Ghost", "Prismic",
    "Headless CMS", "JAMstack",

    # ── ERP, CRM & Enterprise ──
    "SAP", "SAP HANA", "SAP ABAP", "SAP Fiori", "SAP S/4HANA",
    "Salesforce", "Salesforce Lightning", "Apex", "SOQL",
    "ServiceNow", "HubSpot", "Zoho",
    "Oracle ERP", "Microsoft Dynamics", "Dynamics 365",
    "Workday", "PeopleSoft", "NetSuite",

    # ── RPA & Automation ──
    "RPA", "UiPath", "Automation Anywhere", "Blue Prism",
    "Power Automate", "Zapier", "Make", "n8n",

    # ── Communication & Collaboration ──
    "Slack", "Microsoft Teams", "Zoom", "Discord",
    "Confluence", "Notion", "Obsidian",

    # ── IDEs & Developer Tools ──
    "VS Code", "Visual Studio", "IntelliJ IDEA", "WebStorm", "PyCharm",
    "Eclipse", "NetBeans", "Vim", "Neovim", "Emacs",
    "Android Studio", "Xcode",
    "Cursor", "Copilot", "GitHub Copilot",
]

# Skill aliases — 120+ variations → canonical name
SKILL_ALIASES = {
    # Languages
    "js": "JavaScript", "ts": "TypeScript", "py": "Python",
    "c sharp": "C#", "csharp": "C#", "cpp": "C++",
    "golang": "Go", "obj-c": "Objective-C", "objective c": "Objective-C",
    "vb": "Visual Basic", "vb.net": "Visual Basic",
    "plsql": "PL/SQL", "tsql": "T-SQL",

    # Frontend
    "reactjs": "React", "react js": "React", "react.js": "React",
    "angularjs": "Angular", "angular js": "Angular", "angular.js": "Angular",
    "vuejs": "Vue.js", "vue js": "Vue.js",
    "nextjs": "Next.js", "next js": "Next.js",
    "nuxtjs": "Nuxt.js", "nuxt js": "Nuxt.js",
    "sveltejs": "Svelte", "sveltekit": "SvelteKit",
    "tailwindcss": "Tailwind CSS", "tailwind": "Tailwind CSS",
    "material-ui": "Material UI", "mui": "Material UI",
    "antd": "Ant Design", "ant-design": "Ant Design",
    "redux toolkit": "Redux Toolkit", "rtk": "Redux Toolkit",
    "tanstack query": "TanStack Query", "react-query": "React Query",
    "chartjs": "Chart.js", "chart.js": "Chart.js",
    "threejs": "Three.js", "d3js": "D3.js",
    "wasm": "WebAssembly", "web assembly": "WebAssembly",

    # Backend
    "node": "Node.js", "nodejs": "Node.js", "node js": "Node.js",
    "expressjs": "Express.js", "express js": "Express.js",
    "nestjs": "NestJS", "nest js": "NestJS", "nest.js": "NestJS",
    "fastify": "Fastify", "adonisjs": "Adonis.js",
    "asp.net": "ASP.NET", "aspnet": "ASP.NET",
    "aspnet core": "ASP.NET Core", "asp.net core": "ASP.NET Core",
    "dotnet": ".NET", "dot net": ".NET", ".net core": ".NET Core",
    "ror": "Ruby on Rails", "ruby on rails": "Ruby on Rails",
    "spring mvc": "Spring MVC", "spring framework": "Spring",
    "typeorm": "TypeORM", "sequelizejs": "Sequelize",
    "sqlalchemy": "SQLAlchemy",

    # Databases
    "postgres": "PostgreSQL", "psql": "PostgreSQL",
    "mongo": "MongoDB", "mongodb atlas": "MongoDB",
    "mssql": "SQL Server", "ms sql": "SQL Server",
    "dynamodb": "DynamoDB", "dynamo db": "DynamoDB",
    "couchbase": "CouchBase", "couch base": "CouchBase",
    "cockroachdb": "CockroachDB", "cockroach db": "CockroachDB",
    "planetscale": "PlanetScale",
    "elastic search": "Elasticsearch", "opensearch": "Elasticsearch",

    # Cloud
    "amazon web services": "AWS",
    "google cloud platform": "GCP", "google cloud": "GCP",
    "microsoft azure": "Azure",
    "rds": "Amazon RDS", "aurora": "Amazon Aurora",
    "lambda": "AWS Lambda",
    "azure ad": "Azure Active Directory",

    # DevOps
    "k8s": "Kubernetes", "kube": "Kubernetes",
    "docker-compose": "Docker Compose",
    "tf": "Terraform",
    "ci cd": "CI/CD", "cicd": "CI/CD",
    "ci/cd pipelines": "CI/CD",
    "github action": "GitHub Actions", "gha": "GitHub Actions",
    "gitlab-ci": "GitLab CI", "gitlab ci/cd": "GitLab CI",
    "circle ci": "CircleCI",
    "elk": "ELK Stack", "elastic stack": "Elastic Stack",

    # Data/ML
    "ml": "Machine Learning", "dl": "Deep Learning",
    "ai": "Artificial Intelligence",
    "sklearn": "Scikit-learn", "scikit learn": "Scikit-learn",
    "opencv": "OpenCV", "open cv": "OpenCV",
    "tf lite": "TensorFlow Lite", "tflite": "TensorFlow Lite",
    "pytorch lightning": "PyTorch Lightning",
    "wandb": "Weights & Biases", "weights and biases": "Weights & Biases",
    "pyspark": "PySpark", "spark": "Apache Spark",
    "huggingface": "Hugging Face", "hf": "Hugging Face",
    "gen ai": "Generative AI", "genai": "Generative AI",
    "llms": "LLM", "large language model": "LLM",
    "chatgpt": "ChatGPT", "chat gpt": "ChatGPT",
    "langchain": "LangChain", "llamaindex": "LlamaIndex",
    "sbert": "Sentence Transformers",

    # APIs
    "rest": "REST API", "restful api": "REST API", "restful apis": "REST API",
    "graphql api": "GraphQL",
    "grpc": "gRPC",
    "rabbit mq": "RabbitMQ", "rabbitmq": "RabbitMQ",
    "websockets": "WebSocket", "web socket": "WebSocket",
    "socket.io": "Socket.io", "socketio": "Socket.io",
    "oauth 2.0": "OAuth2", "oauth2.0": "OAuth2",
    "json web token": "JWT", "json web tokens": "JWT",
    "openid connect": "OpenID Connect",

    # Architecture
    "oop": "Object-Oriented Programming",
    "fp": "Functional Programming",
    "ddd": "Domain-Driven Design",
    "tdd": "TDD", "bdd": "BDD",
    "soa": "SOA",

    # Testing
    "e2e": "End-to-End Testing", "e2e testing": "End-to-End Testing",
    "selenium webdriver": "Selenium WebDriver",

    # BI & Analytics
    "power bi": "Power BI", "powerbi": "Power BI",
    "google data studio": "Google Data Studio",

    # Mobile
    "rn": "React Native", "react-native": "React Native",

    # Other
    "gh copilot": "GitHub Copilot", "copilot": "GitHub Copilot",
    "vscode": "VS Code", "vs code": "VS Code",
    "intellij": "IntelliJ IDEA",
}


# ──────────────────────────────────────────────────────────────────────────────
# JOB TITLE DATABASE — 120+ patterns for accurate role detection
# ──────────────────────────────────────────────────────────────────────────────
JOB_TITLE_PATTERNS = [
    # ── Software Engineering (General) ──
    r"(?:senior|junior|lead|principal|staff|sr\.?|jr\.?)?\s*software\s+engineer(?:ing)?",
    r"(?:senior|junior|lead|principal|staff|sr\.?|jr\.?)?\s*software\s+developer",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*full[\s\-]?stack\s+(?:developer|engineer)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*application\s+(?:developer|engineer)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*web\s+(?:developer|engineer)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*api\s+(?:developer|engineer)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*solutions?\s+(?:developer|engineer)",
    r"programmer",
    r"coder",

    # ── Frontend ──
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*front[\s\-]?end\s+(?:developer|engineer)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*(?:react|angular|vue|next\.?js)\s+(?:developer|engineer)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*ui\s+(?:developer|engineer)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*javascript\s+(?:developer|engineer)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*typescript\s+(?:developer|engineer)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*wordpress\s+developer",

    # ── Backend ──
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*back[\s\-]?end\s+(?:developer|engineer)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*(?:java|python|php|ruby|golang|go|node\.?js|\.net|c\+\+|c#|scala|rust)\s+(?:developer|engineer)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*server[\s\-]?side\s+(?:developer|engineer)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*microservices?\s+(?:developer|engineer)",

    # ── Mobile ──
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*mobile\s+(?:developer|engineer|application\s+developer)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*android\s+(?:developer|engineer)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*ios\s+(?:developer|engineer)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*(?:flutter|react\s+native|xamarin|ionic|swift|kotlin)\s+(?:developer|engineer)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*cross[\s\-]?platform\s+(?:developer|engineer)",

    # ── Data Science & AI / ML ──
    r"(?:senior|junior|lead|principal|sr\.?|jr\.?)?\s*data\s+scientist",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*(?:machine|deep)\s+learning\s+engineer",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*(?:ml|ai|nlp|cv|computer\s+vision)\s+engineer",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*ai\s+(?:researcher|scientist|developer)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*research\s+(?:engineer|scientist|assistant)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*applied\s+scientist",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*(?:data|ml)\s+(?:ops|operations)\s+engineer",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*prompt\s+engineer",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*llm\s+engineer",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*generative\s+ai\s+engineer",

    # ── Data Engineering & Analytics ──
    r"(?:senior|junior|lead|principal|sr\.?|jr\.?)?\s*data\s+engineer",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*data\s+analyst",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*(?:data|analytics)\s+architect",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*(?:bi|business\s+intelligence)\s+(?:developer|analyst|engineer)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*business\s+analyst",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*etl\s+developer",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*(?:data\s+)?warehouse\s+(?:developer|engineer|architect)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*reporting\s+(?:analyst|developer|engineer)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*visualization\s+(?:analyst|engineer)",

    # ── DevOps, SRE & Infrastructure ──
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*devops\s+(?:engineer|architect|specialist|consultant)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*site\s+reliability\s+engineer",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*sre\b",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*platform\s+engineer",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*infrastructure\s+(?:engineer|architect)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*(?:build|release)\s+engineer",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*(?:ci[\s/]cd|automation)\s+engineer",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*systems?\s+(?:engineer|administrator|admin)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*linux\s+(?:engineer|administrator|admin)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*configuration\s+management\s+engineer",

    # ── Cloud Engineering ──
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*cloud\s+(?:engineer|architect|developer|consultant|specialist)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*(?:aws|azure|gcp|google\s+cloud)\s+(?:engineer|architect|developer|specialist|consultant)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*cloud\s+(?:native|infrastructure)\s+engineer",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*serverless\s+(?:engineer|architect)",

    # ── Network & Telecom ──
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*network\s+(?:engineer|architect|administrator|admin|specialist)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*telecom(?:munications?)?\s+engineer",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*wireless\s+engineer",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*voip\s+engineer",

    # ── Security & Cybersecurity ──
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*(?:cyber)?security\s+(?:engineer|analyst|architect|consultant|specialist|officer)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*(?:information|infosec|itsec)\s+security\s+(?:engineer|analyst|officer|manager)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*penetration\s+tester",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*(?:soc|security\s+operations)\s+analyst",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*threat\s+(?:analyst|intelligence\s+analyst|hunter)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*(?:application|appsec)\s+security\s+engineer",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*ethical\s+hacker",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*(?:grc|governance)\s+(?:analyst|specialist)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*(?:ciso|chief\s+information\s+security\s+officer)",

    # ── QA & Testing ──
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*qa\s+(?:engineer|analyst|lead|manager|specialist|tester|automation)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*quality\s+(?:assurance|control)\s+(?:engineer|analyst|manager)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*test\s+(?:engineer|automation\s+engineer|lead|manager|analyst)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*sdet\b",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*performance\s+(?:test|testing)\s+engineer",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*manual\s+tester",

    # ── Database ──
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*database\s+(?:administrator|engineer|architect|developer)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*dba\b",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*(?:sql|oracle|mysql|postgresql|mongodb)\s+(?:developer|administrator|engineer)",

    # ── Architecture ──
    r"(?:senior|principal|chief|lead)?\s*(?:solutions?|software|enterprise|systems?|technical|data|cloud)\s+architect",

    # ── Management & Leadership ──
    r"(?:engineering|technical|tech|software|development)\s+(?:manager|lead|director|head)",
    r"(?:team|tech|development)\s+lead(?:er)?",
    r"(?:vp|vice\s+president)\s+(?:of\s+)?(?:engineering|technology|product)",
    r"(?:cto|cio|cso)\b",
    r"chief\s+(?:technology|information|security)\s+officer",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*(?:project|program|delivery)\s+manager",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*(?:product|technical\s+product)\s+(?:manager|owner)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*scrum\s+master",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*agile\s+(?:coach|lead|master)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*release\s+manager",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*it\s+(?:manager|director|coordinator)",

    # ── Design (UI/UX) ──
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*(?:ui[\s/]ux|ux[\s/]ui)\s+(?:designer|developer|engineer)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*ux\s+(?:designer|researcher|engineer|strategist|writer)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*ui\s+(?:designer|developer|engineer)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*(?:product|visual|interaction|graphic|motion)\s+designer",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*(?:web|digital)\s+designer",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*design\s+(?:lead|manager|director)",

    # ── Game Development ──
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*game\s+(?:developer|programmer|engineer|designer)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*(?:unity|unreal)\s+(?:developer|engineer)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*gameplay\s+(?:programmer|engineer)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*(?:3d|graphics)\s+(?:programmer|engineer|artist)",

    # ── Embedded & Hardware ──
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*embedded\s+(?:software\s+)?(?:engineer|developer)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*firmware\s+engineer",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*(?:iot|internet\s+of\s+things)\s+(?:engineer|developer)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*hardware\s+engineer",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*(?:fpga|vhdl|verilog)\s+(?:engineer|developer)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*(?:robotics|autonomous)\s+(?:engineer|developer)",

    # ── Blockchain & Web3 ──
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*blockchain\s+(?:developer|engineer)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*(?:smart\s+contract|solidity|web3)\s+(?:developer|engineer)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*(?:defi|nft|crypto)\s+(?:developer|engineer)",

    # ── Technical Writing & Consulting ──
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*technical\s+(?:writer|author|editor|documenter)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*(?:technical|it|technology)\s+(?:consultant|advisor)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*(?:pre[\s\-]?sales|sales)\s+engineer",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*(?:support|customer)\s+engineer",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*developer\s+(?:advocate|evangelist|relations)",

    # ── Other / General ──
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*it\s+(?:specialist|engineer|analyst|support|administrator)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*(?:erp|sap|salesforce|crm)\s+(?:developer|consultant|analyst)",
    r"(?:senior|junior|lead|sr\.?|jr\.?)?\s*(?:rpa|automation)\s+(?:developer|engineer)",
    r"teaching\s+assistant",
    r"(?:software|development|engineering|web|mobile|data|ml|ai|cloud|devops|qa|security)?\s*intern(?:ship)?",
    r"(?:software|development|engineering|it)?\s*trainee",
    r"graduate\s+(?:engineer|developer|trainee|assistant)",
    r"(?:associate|apprentice)\s+(?:engineer|developer|analyst)",
]

# ──────────────────────────────────────────────────────────────────────────────
# DOMAIN KEYWORDS — Weighted scoring with comprehensive indicators
# ──────────────────────────────────────────────────────────────────────────────
DOMAIN_KEYWORDS = {
    "software_engineering": {
        "title_patterns": [
            "software engineer", "software developer", "full stack", "fullstack",
            "web developer", "web engineer", "application developer", "application engineer",
            "solutions developer", "solutions engineer", "api developer", "api engineer",
            "programmer", "coder",
        ],
        "keywords": [
            "software", "development", "engineering", "programming", "coding",
            "full stack", "fullstack", "developer", "web application", "crud",
            "backend", "frontend", "full-stack", "object oriented", "design patterns",
            "software development life cycle", "sdlc", "agile development",
        ],
        "skill_indicators": [
            "react", "angular", "vue", "node.js", "django", "flask", "fastapi",
            "spring boot", "express", "rest api", "graphql", "html", "css",
            "javascript", "typescript", "python", "java", "c#", "c++", "go",
            "ruby", "php", "rust", "next.js", "nuxt.js", ".net", "laravel",
            "postgresql", "mongodb", "mysql", "redis", "docker", "git",
            "microservices", "clean architecture", "mvc", "solid",
        ]
    },
    "frontend": {
        "title_patterns": [
            "frontend", "front-end", "front end", "ui developer", "ui engineer",
            "react developer", "react engineer", "angular developer", "vue developer",
            "javascript developer", "typescript developer", "wordpress developer",
            "web designer",
        ],
        "keywords": [
            "frontend", "front-end", "ui", "ux", "user interface", "user experience",
            "web design", "responsive design", "single page application", "spa",
            "progressive web app", "pwa", "component", "state management", "dom",
            "browser", "accessibility", "wcag", "cross-browser", "pixel perfect",
        ],
        "skill_indicators": [
            "react", "angular", "vue", "svelte", "html", "html5", "css", "css3",
            "tailwind", "bootstrap", "sass", "scss", "less", "webpack", "vite",
            "next.js", "nuxt.js", "gatsby", "redux", "mobx", "zustand",
            "styled components", "material ui", "chakra ui", "ant design",
            "three.js", "d3.js", "framer motion", "gsap", "storybook",
            "responsive design", "web accessibility", "jquery", "babel",
        ]
    },
    "backend": {
        "title_patterns": [
            "backend", "back-end", "back end", "server side",
            "java developer", "python developer", "php developer",
            "node developer", ".net developer", "golang developer",
            "ruby developer", "api developer", "microservices engineer",
        ],
        "keywords": [
            "backend", "back-end", "server", "api", "microservices", "api design",
            "server side", "middleware", "authentication", "authorization",
            "database design", "orm", "caching", "message queue", "webhook",
            "scalability", "high availability", "concurrency", "multithreading",
        ],
        "skill_indicators": [
            "node.js", "django", "flask", "fastapi", "spring boot", "spring",
            "express", ".net", "asp.net", "laravel", "symfony", "rails",
            "nestjs", "koa", "gin", "echo", "fiber", "phoenix",
            "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
            "rest api", "graphql", "grpc", "rabbitmq", "kafka", "websocket",
            "docker", "jwt", "oauth", "prisma", "sqlalchemy",
        ]
    },
    "data_science": {
        "title_patterns": [
            "data scientist", "ml engineer", "machine learning engineer",
            "ai engineer", "ai researcher", "ai scientist", "ai developer",
            "nlp engineer", "cv engineer", "computer vision engineer",
            "deep learning engineer", "applied scientist", "research scientist",
            "research engineer", "prompt engineer", "llm engineer",
            "generative ai engineer", "mlops engineer",
        ],
        "keywords": [
            "data science", "machine learning", "deep learning", "analytics",
            "statistics", "neural network", "artificial intelligence",
            "natural language processing", "computer vision", "reinforcement learning",
            "supervised learning", "unsupervised learning", "model training",
            "feature engineering", "hyperparameter tuning", "model deployment",
            "research", "experiment", "llm", "large language model",
            "generative ai", "prompt engineering", "fine-tuning",
            "transfer learning", "transformer", "attention mechanism",
        ],
        "skill_indicators": [
            "tensorflow", "pytorch", "keras", "scikit-learn", "pandas", "numpy",
            "scipy", "matplotlib", "seaborn", "jupyter", "google colab",
            "nlp", "computer vision", "hugging face", "opencv", "nltk", "spacy",
            "xgboost", "lightgbm", "catboost", "random forest",
            "deep learning", "neural networks", "bert", "gpt", "transformers",
            "langchain", "llamaindex", "rag", "pinecone", "chromadb",
            "mlops", "mlflow", "wandb", "openai", "stable diffusion",
        ]
    },
    "data_engineering": {
        "title_patterns": [
            "data engineer", "etl developer", "bi developer", "bi engineer",
            "bi analyst", "data architect", "analytics engineer",
            "data warehouse engineer", "data warehouse architect",
            "data platform engineer", "data ops engineer",
            "reporting analyst", "visualization engineer",
        ],
        "keywords": [
            "data engineering", "etl", "elt", "data pipeline", "data warehouse",
            "big data", "data lake", "data mesh", "data modeling",
            "data integration", "data quality", "data governance",
            "batch processing", "stream processing", "real-time data",
            "data infrastructure", "olap", "oltp", "dimensional modeling",
        ],
        "skill_indicators": [
            "apache spark", "pyspark", "hadoop", "hive", "kafka", "airflow",
            "dbt", "snowflake", "databricks", "bigquery", "redshift",
            "azure data factory", "aws glue", "fivetran", "nifi",
            "data pipeline", "etl", "data warehousing",
            "tableau", "power bi", "looker", "metabase",
            "sql", "postgresql", "mysql", "mongodb", "cassandra",
            "parquet", "avro", "delta lake", "iceberg",
        ]
    },
    "devops": {
        "title_patterns": [
            "devops engineer", "devops architect", "devops specialist",
            "sre", "site reliability", "platform engineer",
            "infrastructure engineer", "infrastructure architect",
            "build engineer", "release engineer", "automation engineer",
            "ci/cd engineer", "systems engineer", "systems administrator",
            "linux administrator", "linux engineer",
            "configuration management engineer",
        ],
        "keywords": [
            "devops", "infrastructure", "deployment", "automation",
            "site reliability", "continuous integration", "continuous deployment",
            "continuous delivery", "infrastructure as code", "iac",
            "container orchestration", "monitoring", "observability",
            "incident management", "on-call", "uptime", "sla",
            "configuration management", "provisioning", "scaling",
        ],
        "skill_indicators": [
            "docker", "kubernetes", "terraform", "ansible", "puppet", "chef",
            "jenkins", "github actions", "gitlab ci", "circleci", "travis ci",
            "ci/cd", "helm", "argocd", "spinnaker",
            "prometheus", "grafana", "datadog", "new relic", "splunk",
            "elk stack", "nginx", "apache", "haproxy",
            "istio", "envoy", "consul", "vault",
            "linux", "bash", "shell", "vagrant", "packer",
        ]
    },
    "mobile": {
        "title_patterns": [
            "mobile developer", "mobile engineer", "mobile application developer",
            "android developer", "android engineer",
            "ios developer", "ios engineer",
            "flutter developer", "flutter engineer",
            "react native developer", "react native engineer",
            "swift developer", "kotlin developer",
            "cross-platform developer", "cross platform engineer",
        ],
        "keywords": [
            "mobile", "android", "ios", "app development", "mobile application",
            "app store", "play store", "mobile ui", "responsive", "native app",
            "hybrid app", "cross-platform", "push notification", "mobile sdk",
        ],
        "skill_indicators": [
            "react native", "flutter", "swift", "swiftui", "kotlin",
            "jetpack compose", "ionic", "xamarin", "cordova",
            "android", "ios", "objective-c", "dart",
            "firebase", "mobile development", "app development",
        ]
    },
    "cloud_engineering": {
        "title_patterns": [
            "cloud engineer", "cloud architect", "cloud developer",
            "cloud consultant", "cloud specialist",
            "aws engineer", "aws architect", "aws developer",
            "azure engineer", "azure architect", "azure developer",
            "gcp engineer", "google cloud engineer",
            "cloud native engineer", "cloud infrastructure engineer",
            "serverless engineer", "serverless architect",
        ],
        "keywords": [
            "cloud", "cloud engineer", "cloud architect", "cloud infrastructure",
            "cloud computing", "cloud native", "cloud migration", "multi-cloud",
            "hybrid cloud", "serverless", "iaas", "paas", "saas",
            "cloud security", "cloud cost optimization", "finops",
        ],
        "skill_indicators": [
            "aws", "azure", "gcp", "google cloud",
            "cloudformation", "ec2", "s3", "ecs", "eks", "sqs", "sns",
            "api gateway", "cloudwatch", "lambda", "aws lambda",
            "azure functions", "azure devops", "azure sql",
            "cloud functions", "bigquery", "cloud run",
            "terraform", "cloudflare", "vercel", "heroku",
        ]
    },
    "security": {
        "title_patterns": [
            "security engineer", "security analyst", "security architect",
            "security consultant", "security specialist", "security officer",
            "cybersecurity engineer", "cybersecurity analyst",
            "information security", "infosec", "itsec",
            "penetration tester", "ethical hacker",
            "soc analyst", "threat analyst", "threat intelligence",
            "application security", "appsec", "devsecops",
            "grc analyst", "governance analyst",
            "ciso", "chief information security officer",
        ],
        "keywords": [
            "security", "cybersecurity", "penetration testing", "encryption",
            "infosec", "information security", "vulnerability", "compliance",
            "threat", "malware", "forensics", "incident response",
            "risk assessment", "security audit", "security operations",
            "identity management", "access control", "zero trust",
            "gdpr", "pci dss", "soc 2", "iso 27001", "nist", "hipaa",
            "devsecops", "secure coding", "security by design",
        ],
        "skill_indicators": [
            "owasp", "penetration testing", "vulnerability assessment",
            "siem", "firewall", "encryption", "ssl/tls",
            "iam", "rbac", "sso", "saml", "oauth",
            "burp suite", "nmap", "wireshark", "metasploit", "kali linux",
            "ethical hacking", "malware analysis", "forensics",
            "cybersecurity", "network security", "application security",
        ]
    },
    "qa_testing": {
        "title_patterns": [
            "qa engineer", "qa analyst", "qa lead", "qa manager",
            "qa automation", "qa specialist", "qa tester",
            "test engineer", "test automation engineer", "test lead",
            "test manager", "test analyst",
            "quality assurance engineer", "quality control engineer",
            "sdet", "performance test engineer", "manual tester",
        ],
        "keywords": [
            "quality assurance", "testing", "qa", "test automation",
            "manual testing", "automated testing", "regression testing",
            "smoke testing", "integration testing", "end-to-end testing",
            "unit testing", "performance testing", "load testing",
            "stress testing", "acceptance testing", "test plan",
            "test case", "bug tracking", "defect management",
            "test coverage", "test strategy",
        ],
        "skill_indicators": [
            "selenium", "cypress", "playwright", "jest", "pytest",
            "junit", "testng", "jmeter", "locust", "k6",
            "tdd", "bdd", "mocha", "chai", "postman",
            "test automation", "load testing", "unit testing",
            "appium", "robot framework", "cucumber", "specflow",
        ]
    },
    "network_engineering": {
        "title_patterns": [
            "network engineer", "network architect", "network administrator",
            "network specialist", "telecom engineer",
            "wireless engineer", "voip engineer",
        ],
        "keywords": [
            "networking", "network infrastructure", "routing", "switching",
            "firewall", "load balancer", "vpn", "vlan", "lan", "wan",
            "tcp/ip", "dns", "dhcp", "bgp", "ospf",
            "network security", "network monitoring", "sdn",
            "telecommunications", "wireless",
        ],
        "skill_indicators": [
            "cisco", "ccna", "ccnp", "juniper", "arista",
            "tcp/ip", "dns", "dhcp", "vpn", "vlan",
            "routing", "switching", "firewall", "load balancing",
            "wireshark", "snmp", "nagios", "zabbix",
            "active directory", "ldap",
        ]
    },
    "game_development": {
        "title_patterns": [
            "game developer", "game programmer", "game engineer",
            "game designer", "unity developer", "unreal developer",
            "gameplay programmer", "graphics programmer", "3d programmer",
        ],
        "keywords": [
            "game development", "game design", "game engine", "gameplay",
            "level design", "game mechanics", "game physics",
            "3d rendering", "shader programming", "graphics programming",
        ],
        "skill_indicators": [
            "unity", "unreal engine", "godot", "c++", "c#",
            "opengl", "vulkan", "directx", "webgl", "shader",
            "blender", "3d modeling", "game design",
        ]
    },
    "embedded_systems": {
        "title_patterns": [
            "embedded engineer", "embedded developer", "firmware engineer",
            "iot engineer", "hardware engineer", "robotics engineer",
            "fpga engineer", "vhdl engineer",
        ],
        "keywords": [
            "embedded systems", "firmware", "iot", "rtos",
            "microcontroller", "hardware", "pcb", "circuit",
            "real-time", "signal processing", "robotics",
        ],
        "skill_indicators": [
            "embedded systems", "arduino", "raspberry pi", "rtos",
            "fpga", "verilog", "vhdl", "microcontrollers",
            "c", "c++", "assembly", "iot", "sensors",
            "edge computing", "arm", "stm32", "esp32",
        ]
    },
    "blockchain": {
        "title_patterns": [
            "blockchain developer", "blockchain engineer",
            "smart contract developer", "solidity developer",
            "web3 developer", "web3 engineer",
            "defi developer", "crypto developer",
        ],
        "keywords": [
            "blockchain", "decentralized", "smart contract", "web3",
            "cryptocurrency", "defi", "nft", "token", "consensus",
            "distributed ledger",
        ],
        "skill_indicators": [
            "blockchain", "ethereum", "solidity", "web3",
            "smart contracts", "defi", "nft", "hardhat", "truffle",
            "hyperledger", "rust", "go",
        ]
    },
    "design": {
        "title_patterns": [
            "ui designer", "ux designer", "ui/ux designer", "ux/ui designer",
            "product designer", "visual designer", "interaction designer",
            "graphic designer", "motion designer", "web designer",
            "ux researcher", "ux strategist", "ux writer",
            "design lead", "design manager", "design director",
        ],
        "keywords": [
            "design", "user experience", "user interface", "usability",
            "wireframe", "prototype", "mockup", "design system",
            "information architecture", "user research", "design thinking",
            "typography", "color theory", "visual design",
        ],
        "skill_indicators": [
            "figma", "adobe xd", "sketch", "invision",
            "photoshop", "illustrator", "after effects",
            "framer", "principle", "zeplin",
            "design thinking", "wireframing", "prototyping",
        ]
    },
}


class ExtractionService:
    """Service for extracting structured information from resume text"""

    def __init__(self):
        self.embedding_service = get_embedding_service()
        self._skill_lookup = {s.lower(): s for s in SKILL_DATABASE}
        self._alias_lookup = {a.lower(): c for a, c in SKILL_ALIASES.items()}

    # ── Skills ────────────────────────────────────────────────────────────────

    def extract_skills(self, text: str, use_embeddings: bool = True) -> List[str]:
        """Extract skills from resume text using keyword, alias, and embedding matching."""
        skills = set()
        text_lower = text.lower()

        # Method 1: Keyword matching (word-boundary for short terms)
        for skill in SKILL_DATABASE:
            sl = skill.lower()
            if len(skill) <= 3:
                if re.search(r'\b' + re.escape(sl) + r'\b', text_lower):
                    skills.add(skill)
            else:
                if sl in text_lower:
                    skills.add(skill)

        # Method 2: Alias matching
        for alias, canonical in self._alias_lookup.items():
            if len(alias) <= 3:
                if re.search(r'\b' + re.escape(alias) + r'\b', text_lower):
                    skills.add(canonical)
            else:
                if alias in text_lower:
                    skills.add(canonical)

        # Method 3: Skill-section parsing
        section_patterns = [
            r'(?:skills|technologies|tools|tech stack|technical skills|proficienc(?:y|t))[:\s]*([^\n]+(?:\n(?!\n)[^\n]*)*)',
            r'(?:languages|frameworks|platforms)[:\s]*([^\n]+)',
        ]
        for pat in section_patterns:
            for match in re.findall(pat, text_lower, re.IGNORECASE):
                candidates = re.split(r'[,|•·▪►→\-–—/\\]|\s{2,}', match)
                for c in candidates:
                    c = c.strip().strip('.')
                    if 2 <= len(c) <= 30:
                        if c in self._skill_lookup:
                            skills.add(self._skill_lookup[c])
                        elif c in self._alias_lookup:
                            skills.add(self._alias_lookup[c])

        # Method 4: Embedding-based similarity
        if use_embeddings:
            try:
                potential = re.findall(r'\b[A-Z][a-zA-Z+#.]*(?:\s+[A-Z][a-zA-Z+#.]*){0,2}\b', text)
                ctx_pats = [
                    r'(?:experience\s+(?:with|in|using)|proficient\s+in|knowledge\s+of|familiar\s+with|worked\s+with|expertise\s+in)\s+([^\n.]+)',
                ]
                for p in ctx_pats:
                    for m in re.findall(p, text, re.IGNORECASE):
                        potential.extend([i.strip() for i in re.split(r'[,;]|\band\b', m)])

                seen = set()
                unique = []
                for ph in potential:
                    ph = ph.strip()
                    pl = ph.lower()
                    if pl not in seen and 2 <= len(ph) <= 30 and pl not in self._skill_lookup:
                        seen.add(pl)
                        unique.append(ph)

                for ph in unique[:80]:
                    similar = self.embedding_service.find_similar_skills(ph, SKILL_DATABASE, threshold=0.78)
                    if similar:
                        skills.add(similar[0][0])
            except Exception as e:
                print(f"Embedding extraction failed: {e}")

        return sorted(list(skills))

    # ── Job Titles ────────────────────────────────────────────────────────────

    # Reference job titles for SBERT similarity matching — 200+ titles
    _JOB_TITLES_REFERENCE = [
        # ── Software Engineering ──
        "Software Engineer", "Software Developer", "Full Stack Developer",
        "Full Stack Engineer", "Web Developer", "Web Engineer",
        "Application Developer", "Application Engineer", "API Developer",
        "API Engineer", "Solutions Engineer", "Solutions Developer",
        "Programmer", "Coder",
        "Senior Software Engineer", "Staff Software Engineer",
        "Principal Software Engineer", "Lead Software Engineer",
        "Junior Software Developer", "Associate Software Engineer",
        # ── Frontend ──
        "Frontend Developer", "Frontend Engineer", "UI Developer",
        "UI Engineer", "React Developer", "React Engineer",
        "Angular Developer", "Vue Developer", "Next.js Developer",
        "JavaScript Developer", "TypeScript Developer",
        "WordPress Developer", "Web Designer",
        "Senior Frontend Developer", "Lead Frontend Engineer",
        # ── Backend ──
        "Backend Developer", "Backend Engineer", "Server Side Developer",
        "Java Developer", "Python Developer", "PHP Developer",
        "Node.js Developer", ".NET Developer", "Go Developer",
        "Golang Developer", "Ruby Developer", "Rust Developer",
        "Scala Developer", "C++ Developer", "C# Developer",
        "Microservices Developer", "Microservices Engineer",
        "Senior Backend Developer", "Lead Backend Engineer",
        # ── Mobile ──
        "Mobile Developer", "Mobile Engineer", "Mobile Application Developer",
        "Android Developer", "Android Engineer",
        "iOS Developer", "iOS Engineer",
        "Flutter Developer", "Flutter Engineer",
        "React Native Developer", "React Native Engineer",
        "Swift Developer", "Kotlin Developer",
        "Cross Platform Developer", "Cross Platform Engineer",
        # ── Data Science & AI/ML ──
        "Data Scientist", "Data Analyst", "Data Engineer",
        "Machine Learning Engineer", "ML Engineer", "AI Engineer",
        "NLP Engineer", "Computer Vision Engineer", "Deep Learning Engineer",
        "AI Researcher", "AI Scientist", "AI Developer",
        "Research Scientist", "Research Engineer", "Applied Scientist",
        "Prompt Engineer", "LLM Engineer", "Generative AI Engineer",
        "MLOps Engineer", "DataOps Engineer",
        "BI Developer", "BI Analyst", "BI Engineer",
        "Business Analyst", "Business Intelligence Analyst",
        "Analytics Engineer", "Data Architect", "Data Modeler",
        "ETL Developer", "Data Warehouse Engineer",
        "Reporting Analyst", "Visualization Engineer",
        "Senior Data Scientist", "Lead ML Engineer",
        "Principal Data Engineer", "Staff Data Scientist",
        # ── DevOps, SRE & Infrastructure ──
        "DevOps Engineer", "DevOps Architect", "DevOps Specialist",
        "Site Reliability Engineer", "SRE",
        "Platform Engineer", "Infrastructure Engineer", "Infrastructure Architect",
        "Cloud Engineer", "Cloud Architect", "Cloud Developer",
        "Cloud Consultant", "Cloud Specialist",
        "AWS Engineer", "AWS Architect", "AWS Developer",
        "Azure Engineer", "Azure Architect", "Azure Developer",
        "GCP Engineer", "Google Cloud Engineer",
        "Systems Engineer", "Systems Administrator", "System Admin",
        "Linux Engineer", "Linux Administrator",
        "Build Engineer", "Release Engineer", "Automation Engineer",
        "CI/CD Engineer", "Configuration Management Engineer",
        "Senior DevOps Engineer", "Lead Platform Engineer",
        "Serverless Engineer", "Serverless Architect",
        # ── Security & Cybersecurity ──
        "Security Engineer", "Security Analyst", "Security Architect",
        "Security Consultant", "Security Specialist",
        "Cybersecurity Engineer", "Cybersecurity Analyst",
        "Penetration Tester", "Ethical Hacker",
        "SOC Analyst", "Threat Analyst", "Threat Intelligence Analyst",
        "Application Security Engineer", "AppSec Engineer",
        "Information Security Officer", "CISO",
        "DevSecOps Engineer", "Cloud Security Engineer",
        "GRC Analyst", "Compliance Analyst",
        "Senior Security Engineer", "Lead Security Architect",
        # ── QA & Testing ──
        "QA Engineer", "QA Analyst", "QA Lead", "QA Automation Engineer",
        "Test Engineer", "Test Automation Engineer", "Test Lead",
        "SDET", "Quality Assurance Engineer", "Quality Control Engineer",
        "Performance Test Engineer", "Manual Tester",
        "Senior QA Engineer", "Lead Test Engineer",
        # ── Database ──
        "Database Administrator", "DBA",
        "Database Engineer", "Database Architect", "Database Developer",
        "SQL Developer", "Oracle DBA", "MongoDB Developer",
        # ── Architecture ──
        "Solutions Architect", "Software Architect", "Enterprise Architect",
        "Technical Architect", "Systems Architect",
        "Data Architect", "Cloud Architect", "Security Architect",
        "Principal Architect", "Chief Architect",
        # ── Management & Leadership ──
        "Engineering Manager", "Technical Lead", "Team Lead", "Tech Lead",
        "Development Manager", "Software Development Manager",
        "Director of Engineering", "VP of Engineering",
        "Head of Engineering", "Head of Technology",
        "CTO", "CIO", "CSO",
        "Chief Technology Officer", "Chief Information Officer",
        "Project Manager", "Program Manager", "Delivery Manager",
        "Product Manager", "Product Owner", "Technical Product Manager",
        "Scrum Master", "Agile Coach", "Release Manager",
        "IT Manager", "IT Director", "IT Coordinator",
        # ── Design (UI/UX) ──
        "UI/UX Designer", "UX Designer", "UI Designer",
        "UX Researcher", "UX Strategist", "UX Writer",
        "Product Designer", "Visual Designer", "Interaction Designer",
        "Graphic Designer", "Motion Designer", "Web Designer",
        "Design Lead", "Design Manager", "Design Director",
        "Senior Product Designer", "Lead UX Designer",
        # ── Network & Telecom ──
        "Network Engineer", "Network Architect", "Network Administrator",
        "Network Specialist", "Telecom Engineer",
        "Wireless Engineer", "VoIP Engineer",
        "Senior Network Engineer",
        # ── Game Development ──
        "Game Developer", "Game Programmer", "Game Engineer",
        "Game Designer", "Level Designer",
        "Unity Developer", "Unreal Developer",
        "Gameplay Programmer", "Graphics Programmer",
        "3D Developer", "3D Artist",
        # ── Embedded & IoT ──
        "Embedded Engineer", "Embedded Developer",
        "Embedded Software Engineer", "Firmware Engineer",
        "IoT Engineer", "IoT Developer",
        "Hardware Engineer", "FPGA Engineer",
        "Robotics Engineer", "Autonomous Systems Engineer",
        # ── Blockchain & Web3 ──
        "Blockchain Developer", "Blockchain Engineer",
        "Smart Contract Developer", "Solidity Developer",
        "Web3 Developer", "Web3 Engineer",
        "DeFi Developer", "Crypto Developer",
        # ── Technical Writing & Consulting ──
        "Technical Writer", "Technical Author",
        "Technical Consultant", "IT Consultant", "Technology Consultant",
        "Pre-Sales Engineer", "Sales Engineer",
        "Customer Engineer", "Support Engineer",
        "Developer Advocate", "Developer Evangelist", "Developer Relations",
        # ── ERP & Enterprise ──
        "SAP Developer", "SAP Consultant", "SAP Architect",
        "Salesforce Developer", "Salesforce Consultant", "Salesforce Architect",
        "ServiceNow Developer", "Oracle Developer",
        "ERP Developer", "ERP Consultant",
        "CRM Developer", "CRM Consultant",
        "Dynamics 365 Developer", "NetSuite Developer",
        # ── RPA & Automation ──
        "RPA Developer", "RPA Engineer",
        "Automation Developer", "Automation Engineer",
        "UiPath Developer", "Power Automate Developer",
        # ── Other / Niche ──
        "IT Specialist", "IT Analyst", "IT Support Engineer",
        "IT Administrator", "Help Desk Technician",
        "FinOps Engineer", "SaaS Engineer",
        "Reliability Engineer", "Performance Engineer",
        "Integration Engineer", "Middleware Engineer",
        "API Architect", "Microservices Architect",
        "Teaching Assistant", "Research Assistant",
        "Graduate Engineer", "Graduate Developer",
        "Associate Engineer", "Associate Developer",
        "Intern", "Software Engineering Intern",
        "Trainee Developer", "Trainee Engineer",
    ]

    def extract_job_titles(self, text: str) -> List[str]:
        """
        Extract job titles/roles from resume text.
        Uses regex patterns first, then SBERT similarity as fallback
        for novel/unusual titles.
        """
        titles = []
        text_lower = text.lower()

        # Method 1: Regex pattern matching (120+ patterns)
        for pattern in JOB_TITLE_PATTERNS:
            matches = re.finditer(pattern, text_lower)
            for m in matches:
                title = m.group(0).strip()
                title = title.title()
                if title not in titles:
                    titles.append(title)

        # Method 2: Experience section format matching
        # "Software Engineer at Google" or "Software Engineer | Google"
        exp_title_pat = r'(?:^|\n)\s*([A-Z][A-Za-z\s/\-]+?)\s*(?:at|@|\||-|–|—|,)\s*[A-Z]'
        for m in re.finditer(exp_title_pat, text):
            candidate = m.group(1).strip()
            if 5 <= len(candidate) <= 60:
                cl = candidate.lower()
                for tp in JOB_TITLE_PATTERNS:
                    if re.search(tp, cl):
                        if candidate.title() not in titles:
                            titles.append(candidate.title())
                        break

        # Method 3: SBERT embedding similarity fallback
        # Catches novel/unusual titles that regex misses
        try:
            # Extract candidate phrases from experience sections
            candidates = []

            # Look for role-like phrases near company indicators
            role_pats = [
                r'(?:^|\n)\s*([A-Z][A-Za-z\s/\-&]+?)\s*(?:at|@|\||–|—)\s+',
                r'(?:role|position|title|designation)[:\s]+([^\n,]+)',
                r'(?:worked\s+as|serving\s+as|working\s+as|currently)\s+(?:a\s+)?([^\n,]+?)(?:\s+at|\s+in|\s+for|\.|,|\n)',
            ]
            for rp in role_pats:
                for m in re.finditer(rp, text, re.IGNORECASE):
                    c = m.group(1).strip().rstrip(',.- ')
                    if 5 <= len(c) <= 60:
                        candidates.append(c)

            # Deduplicate and filter already-found titles
            seen_lower = {t.lower() for t in titles}
            unique_candidates = []
            for c in candidates:
                cl = c.lower()
                if cl not in seen_lower and len(c.split()) <= 6:
                    seen_lower.add(cl)
                    unique_candidates.append(c)

            # Match against reference titles using SBERT
            for candidate in unique_candidates[:20]:
                similar = self.embedding_service.find_similar_skills(
                    candidate, self._JOB_TITLES_REFERENCE, threshold=0.82
                )
                if similar:
                    matched_title = candidate.title()
                    if matched_title not in titles:
                        titles.append(matched_title)
        except Exception as e:
            print(f"SBERT job title matching failed: {e}")

        return titles[:10]  # Limit to 10

    # ── Education ─────────────────────────────────────────────────────────────

    def extract_education(self, text: str) -> List[Dict[str, str]]:
        """Extract education details using degree keyword patterns only.
        
        NOTE: Section-based fallback removed because PDF text lacks proper
        newlines, causing cross-contamination with other sections.
        Uses precise degree keyword patterns that work on any text.
        """
        education = []

        # Pattern 1: "Degree in/from/at Institution (Year)"
        degree_patterns = [
            r'((?:Bachelor|Master|Doctor|PhD|B\.?S\.?c?|M\.?S\.?c?|B\.?A\.?|M\.?A\.?|B\.?E\.?|M\.?E\.?|B\.?Tech|M\.?Tech|MBA|BBA|BS|MS|BE|ME|Associate|Diploma)[\w\s,.]{{0,60}}?)(?:\s+(?:from|at|in)\s+)([\w\s,.\-\']+?)(?:\s*[\(,\|]\s*(\d{{4}})\s*[\),\|]|\s+(\d{{4}})|\s*(?:\n|$))',
        ]

        for pat in degree_patterns:
            for m in re.finditer(pat, text, re.IGNORECASE | re.MULTILINE):
                degree = m.group(1).strip().rstrip(',.- ')
                institution = m.group(2).strip().rstrip(',.- ') if m.group(2) else ""
                year = m.group(3) or (m.group(4) if len(m.groups()) > 3 else None)

                # Validate: degree must be short, institution must be real
                if len(degree) > 3 and len(degree) < 100 and len(institution) > 2 and len(institution) < 80:
                    entry = {"degree": degree, "institution": institution}
                    if year:
                        entry["year"] = year
                    if not any(e["degree"].lower() == degree.lower() for e in education):
                        education.append(entry)

        # Pattern 2: Standalone degree keywords with year nearby
        if not education:
            standalone_pat = r'((?:Bachelor|Master|Doctor|PhD|B\.?S\.?c?|M\.?S\.?c?|B\.?A\.?|M\.?A\.?|B\.?E\.?|M\.?E\.?|B\.?Tech|M\.?Tech|MBA|BBA|Diploma|Associate)\s+(?:of|in)\s+[\w\s]+?)(?:\s*[,\(\|]\s*(\d{4})|\s+(\d{4})|\s*(?:\n|$))'
            for m in re.finditer(standalone_pat, text, re.IGNORECASE):
                degree = m.group(1).strip().rstrip(',.- ')
                year = m.group(2) or m.group(3)
                if 5 < len(degree) < 100:
                    entry = {"degree": degree, "institution": "", "year": year or ""}
                    if not any(e["degree"].lower() == degree.lower() for e in education):
                        education.append(entry)

        return education[:5]

    # ── Projects ──────────────────────────────────────────────────────────────

    def extract_projects(self, text: str) -> List[Dict[str, str]]:
        """Extract project names from resume using pattern matching.
        
        NOTE: Section-based parsing removed because PDF text lacks proper
        newlines, causing cross-contamination. Uses keyword patterns instead.
        """
        projects = []

        # Pattern 1: Lines that look like project titles with descriptions
        # "ProjectName – Description" or "ProjectName: Description"
        proj_pats = [
            r'(?:^|\n)\s*[•▪►→\-\*]?\s*([A-Z][\w\s\-./]{2,50}?)\s*[–—:\|]\s*([^\n]{10,200})',
        ]

        # Only look in what seems like a projects area
        # Find "Projects" keyword and take text after it (limited)
        proj_area_match = re.search(
            r'(?:projects?|personal\s+projects?|key\s+projects?|academic\s+projects?|side\s+projects?)\s*[:\n\r]',
            text, re.IGNORECASE
        )

        if proj_area_match:
            # Take up to 2000 chars after the "Projects" heading
            start = proj_area_match.end()
            proj_area = text[start:start + 2000]

            # Split into potential entries by looking for capitalized lines or bullets
            entries = re.split(r'\n\s*(?=[A-Z•▪►→\-\*\d])', proj_area)
            for entry in entries:
                entry = entry.strip()
                if not entry or len(entry) < 5:
                    continue

                # Check if it's a section header (means we've left projects)
                if re.match(r'(?:education|experience|skills|certif|awards?|achievements?|references?|hobbies|interests)\b', entry, re.IGNORECASE):
                    break

                # Extract title (first line or first part before description)
                title_match = re.match(r'^[•▪►→\-\*\d.)\s]*([A-Z][\w\s\-./&]{2,60}?)(?:\s*[–—:\|]\s*(.+)|$)', entry)
                if title_match:
                    title = title_match.group(1).strip().rstrip(',.- ')
                    desc = title_match.group(2) or ""
                    if 3 <= len(title) <= 80:
                        projects.append({"name": title, "description": desc.strip()[:200]})

        return projects[:8]

    # ── Certifications ────────────────────────────────────────────────────────

    def extract_certifications(self, text: str) -> List[str]:
        """Extract certifications from resume using pattern matching only.
        
        NOTE: Section-based parsing is intentionally disabled because
        PDF-extracted text often lacks proper newlines, causing the section
        parser to capture garbled body text as certifications.
        Instead, we rely solely on precise regex patterns for known
        certification families, which never produce false positives.
        """
        certs = []

        # Pattern-match 25+ certification families anywhere in text
        cert_patterns = [
            # AWS (30+ certs)
            r'(AWS\s+Certified[\w\s\-]+)',
            r'(AWS\s+(?:Solutions?\s+Architect|Developer|SysOps|DevOps|Data\s+Analytics|Machine\s+Learning|Security|Database|Networking|SAP|Advanced Networking)[\w\s\-]*)',
            # Azure (20+ certs)
            r'(Azure\s+(?:Fundamentals|Administrator|Developer|Solutions?\s+Architect|Security|Data|AI|DevOps)[\w\s\-]*)',
            r'(Microsoft\s+Certified[:\s][\w\s\-]+)',
            r'(AZ-\d{3}|DP-\d{3}|AI-\d{3}|SC-\d{3}|MS-\d{3}|PL-\d{3})',
            # Google Cloud (15+ certs)
            r'(Google\s+Cloud\s+(?:Certified|Professional|Associate)[\w\s\-]*)',
            r'(Google\s+(?:Professional|Associate)\s+(?:Cloud|Data|Machine\s+Learning|Network|Security|DevOps)[\w\s\-]*)',
            # Kubernetes
            r'((?:CKA|CKAD|CKS|Certified\s+Kubernetes)[\w\s\-]*)',
            # Scrum / Agile
            r'((?:Certified\s+Scrum\s+(?:Master|Product\s+Owner|Developer)|CSM|CSPO|CSD|PSM|PSPO|PMI-ACP|SAFe\s+Agilist)[\w\s\-]*)',
            # PMI
            r'((?:PMP|CAPM|PMI-RMP|PMI-SP|PgMP|PfMP|Project\s+Management\s+Professional)[\w\s\-]*)',
            # ISC2
            r'((?:CISSP|CCSP|CSSLP|SSCP|CAP|Certified\s+Information\s+Systems\s+Security)[\w\s\-]*)',
            # EC-Council
            r'((?:CEH|Certified\s+Ethical\s+Hacker|CHFI|ECSA|LPT)[\w\s\-]*)',
            # CompTIA
            r'(CompTIA\s+(?:A\+|Network\+|Security\+|Cloud\+|Linux\+|Server\+|CySA\+|PenTest\+|CASP\+|Data\+|ITF\+)[\w\s\-]*)',
            # Cisco
            r'((?:CCNA|CCNP|CCIE|CCDA|CCDP|Cisco\s+Certified)[\w\s\-]*)',
            # Oracle
            r'(Oracle\s+Certified[\w\s\-]+)',
            r'(OCA|OCP|OCM|Oracle\s+(?:Database|Java|Cloud)[\w\s\-]*)',
            # Salesforce
            r'(Salesforce\s+Certified[\w\s\-]+)',
            r'(Salesforce\s+(?:Administrator|Developer|Architect|Consultant)[\w\s\-]*)',
            # HashiCorp
            r'(HashiCorp\s+Certified[:\s][\w\s\-]+)',
            r'(Terraform\s+(?:Associate|Professional)[\w\s\-]*)',
            # Linux
            r'((?:LFCS|LFCE|RHCSA|RHCE|RHCA|Linux\s+Foundation\s+Certified)[\w\s\-]*)',
            r'(Red\s+Hat\s+Certified[\w\s\-]+)',
            # ITIL
            r'(ITIL[\w\s\-v]*(?:Foundation|Practitioner|Expert|Master)?)',
            # Data
            r'((?:Databricks|Snowflake|Confluent|MongoDB)\s+Certified[\w\s\-]*)',
            r'((?:Tableau|Power\s+BI)\s+(?:Desktop\s+)?(?:Certified|Specialist|Associate)[\w\s\-]*)',
            # Six Sigma
            r'((?:Six\s+Sigma|Lean\s+Six\s+Sigma)\s+(?:Green|Black|Yellow|White)\s+Belt[\w\s\-]*)',
            # ISTQB
            r'(ISTQB[\w\s\-]*)',
        ]

        for pat in cert_patterns:
            for m in re.finditer(pat, text, re.IGNORECASE):
                cert = m.group(1).strip()
                if cert not in certs and len(cert) > 3:
                    certs.append(cert)

        return certs[:15]  # Limit to 15

    # ── Experience ────────────────────────────────────────────────────────────

    def extract_experience(self, text: str) -> Dict[str, any]:
        """Extract experience information: years, summary, and companies.
        
        IMPORTANT: Date range calculation only looks inside the Experience
        section to avoid picking up education or project dates.
        """
        from datetime import datetime as dt

        experience = {
            "years": None,
            "summary": "",
            "companies": []
        }

        # ─── First, find the Experience section text ───
        exp_section_match = re.search(
            r'(?:experience|work\s+history|employment|professional\s+experience|work\s+experience)\s*[:\n\r]?(.*?)(?:(?:education|skills|projects?|certif|awards?|achievements?|hobbies|interests|references?)\b|\Z)',
            text, re.IGNORECASE | re.DOTALL
        )
        exp_text = exp_section_match.group(1) if exp_section_match else ""

        # ─── Method 1: Explicit "X years of experience" (search full text) ───
        years_pats = [
            r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience|exp|work)',
            r'(?:experience|exp)\s*(?:of\s+)?(\d+)\+?\s*(?:years?|yrs?)',
            r'(?:over|more\s+than|approximately|approx|around|nearly|about)\s+(\d+)\s*(?:years?|yrs?)',
        ]
        for yp in years_pats:
            m = re.search(yp, text, re.IGNORECASE)
            if m:
                experience["years"] = int(m.group(1))
                break

        # ─── Method 2: Calculate from date ranges IN EXPERIENCE SECTION ONLY ───
        if experience["years"] is None and exp_text:
            date_range_pats = [
                # "Mon YYYY – Mon YYYY" or "Mon YYYY – Present"
                r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s*[,.]?\s*(\d{4})\s*[-–—to]+\s*(?:(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s*[,.]?\s*)?(\d{4}|[Pp]resent|[Cc]urrent|[Nn]ow|[Oo]ngoing)',
                # "YYYY – YYYY" or "YYYY – Present"
                r'(\d{4})\s*[-–—to]+\s*(\d{4}|[Pp]resent|[Cc]urrent|[Nn]ow|[Oo]ngoing)',
            ]

            all_years = []
            current_year = dt.now().year

            # Only search within Experience section text
            for pat in date_range_pats:
                for m in re.finditer(pat, exp_text, re.IGNORECASE):
                    groups = m.groups()
                    start_year = None
                    end_year = None

                    for g in groups:
                        if g and g.isdigit():
                            yr = int(g)
                            if 1970 <= yr <= current_year + 1:
                                if start_year is None:
                                    start_year = yr
                                else:
                                    end_year = yr
                        elif g and g.lower() in ('present', 'current', 'now', 'ongoing'):
                            end_year = current_year

                    if start_year and end_year:
                        all_years.append((start_year, end_year))
                    elif start_year:
                        all_years.append((start_year, current_year))

            if all_years:
                earliest = min(y[0] for y in all_years)
                latest = max(y[1] for y in all_years)
                total_years = latest - earliest
                if 0 < total_years <= 50:
                    experience["years"] = total_years

        # ─── Experience section summary ───
        if exp_text:
            experience["summary"] = exp_text.strip()[:500]

        # ─── Extract company names ───
        company_patterns = [
            r'(?:at|@)\s+([A-Z][\w\s&.,]+?)(?:\s*[\|\-–—,]|\s+as\s+|\n)',
            r'([A-Z][\w\s&.]+?)\s*[\|\-–—]\s*(?:' + '|'.join(JOB_TITLE_PATTERNS[:15]) + r')',
        ]
        companies = []
        for cp in company_patterns:
            for m in re.finditer(cp, text):
                company = m.group(1).strip().rstrip(',.- ')
                if 2 <= len(company) <= 50 and company not in companies:
                    companies.append(company)

        experience["companies"] = companies[:10]

        return experience

    # ── Domain Detection (FIXED) ──────────────────────────────────────────────

    def detect_domain(self, text: str, skills: List[str], job_titles: List[str]) -> str:
        """
        Detect professional domain using weighted scoring.
        Job titles from the resume are given the HIGHEST weight.
        """
        text_lower = text.lower()
        domain_scores = {}

        for domain, config in DOMAIN_KEYWORDS.items():
            score = 0

            # HIGHEST WEIGHT: Match against actual job titles found in resume
            for title in job_titles:
                title_lower = title.lower()
                for tp in config["title_patterns"]:
                    if tp in title_lower:
                        score += 10  # Very high weight for job title match

            # MEDIUM WEIGHT: Keyword matches in full text
            for keyword in config["keywords"]:
                if keyword.lower() in text_lower:
                    score += 1

            # MEDIUM WEIGHT: Skill indicators
            for skill in skills:
                skill_lower = skill.lower()
                for indicator in config["skill_indicators"]:
                    if indicator in skill_lower or skill_lower in indicator:
                        score += 2

            domain_scores[domain] = score

        if domain_scores:
            best = max(domain_scores, key=domain_scores.get)
            if domain_scores[best] > 0:
                return best

        return "general"

    # ── Extract All ───────────────────────────────────────────────────────────

    def extract_all(self, text: str) -> Dict[str, any]:
        """Extract all structured information from resume text."""
        skills = self.extract_skills(text)
        job_titles = self.extract_job_titles(text)
        experience = self.extract_experience(text)
        education = self.extract_education(text)
        projects = self.extract_projects(text)
        certifications = self.extract_certifications(text)
        domain = self.detect_domain(text, skills, job_titles)

        return {
            "skills": skills,
            "job_titles": job_titles,
            "experience": experience,
            "education": education,
            "projects": projects,
            "certifications": certifications,
            "domain": domain,
            "raw_text_length": len(text),
        }


# Singleton
_extraction_service = None


def get_extraction_service() -> ExtractionService:
    """Get singleton extraction service instance"""
    global _extraction_service
    if _extraction_service is None:
        _extraction_service = ExtractionService()
    return _extraction_service
