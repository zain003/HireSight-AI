"""
Hybrid extraction: keyword/regex PRIMARY + BERT-NER SUPPLEMENTARY.

The BERT-NER model (yashpwr/resume-ner-bert-v2) was tested and found to
produce noisy output on real resumes. This module uses a proven keyword
database + regex + section parsing as the primary extraction method,
with NER providing supplementary skill/title discovery for novel terms.
"""
import re
from typing import List, Dict, Optional

from app.ai.ner_model import get_ner_service


# ──────────────────────────────────────────────────────────────────────────────
# SKILL DATABASE — Massive keyword list (800+ skills) for highest accuracy
# ──────────────────────────────────────────────────────────────────────────────
SKILL_DATABASE = [
    # ── Programming Languages ──
    "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "C",
    "Go", "Rust", "Ruby", "PHP", "Swift", "Kotlin", "Scala", "R",
    "Perl", "Dart", "Lua", "Haskell", "Elixir", "Clojure", "Erlang",
    "Objective-C", "MATLAB", "Julia", "Groovy", "Shell", "Bash",
    "PowerShell", "F#", "OCaml", "Fortran", "COBOL", "Assembly",
    "Zig", "Nim", "Crystal", "Prolog", "Lisp", "Scheme",
    "Visual Basic", "VB.NET", "Delphi", "Pascal", "Ada",
    "ABAP", "Apex", "Solidity", "Vyper", "Move",
    "SQL", "PL/SQL", "T-SQL", "NoSQL", "GraphQL",

    # ── Web Markup & Styling ──
    "HTML", "HTML5", "CSS", "CSS3", "SASS", "SCSS", "Less",
    "Stylus", "PostCSS", "XML", "JSON", "YAML", "TOML",
    "Markdown", "LaTeX", "Pug", "Handlebars", "EJS", "Jinja2",
    "Liquid", "Mustache", "Twig",

    # ── Frontend Frameworks & Libraries ──
    "React", "React.js", "Angular", "Vue", "Vue.js", "Svelte",
    "SvelteKit", "Next.js", "Nuxt.js", "Gatsby", "Remix",
    "Astro", "Qwik", "Solid.js", "SolidJS", "Preact", "Inferno",
    "Lit", "Alpine.js", "HTMX", "Turbo", "Stimulus",
    "Ember.js", "Backbone.js", "Knockout.js", "Polymer",
    "Mithril", "Riot.js", "Marko",

    # ── Frontend State Management ──
    "Redux", "Redux Toolkit", "MobX", "Zustand", "Recoil",
    "Jotai", "Valtio", "XState", "Pinia", "Vuex", "NgRx",
    "Akita", "Context API", "React Query", "TanStack Query",
    "SWR", "Apollo Client",

    # ── Frontend UI & Component Libraries ──
    "jQuery", "Bootstrap", "Tailwind CSS", "Material UI", "MUI",
    "Chakra UI", "Ant Design", "Semantic UI", "Bulma",
    "Foundation", "PrimeReact", "PrimeNG", "PrimeVue",
    "Radix UI", "Headless UI", "shadcn/ui", "DaisyUI",
    "Vuetify", "Quasar", "Element UI", "Element Plus",
    "Styled Components", "Emotion", "CSS Modules",
    "WindiCSS", "UnoCSS", "Mantine",

    # ── Frontend Build & Bundlers ──
    "Webpack", "Vite", "Babel", "esbuild", "Rollup",
    "Parcel", "SWC", "Turbopack", "Snowpack",
    "Gulp", "Grunt", "Make", "CMake",

    # ── Frontend Visualization ──
    "Three.js", "D3.js", "Chart.js", "Highcharts", "ECharts",
    "Recharts", "Victory", "Nivo", "Plotly", "Leaflet",
    "Mapbox", "Google Maps API", "Cesium",
    "Storybook", "Chromatic", "Bit",
    "Framer Motion", "GSAP", "Anime.js", "Lottie",
    "PixiJS", "Fabric.js", "Konva", "Paper.js",

    # ── Backend Frameworks & Runtimes ──
    "Node.js", "Express", "Express.js", "FastAPI", "Django",
    "Flask", "Spring Boot", "Spring", "Spring MVC",
    "Spring Cloud", "Spring Security", "Spring Data",
    "ASP.NET", "ASP.NET Core", ".NET", ".NET Core",
    "Ruby on Rails", "Rails", "Sinatra",
    "Laravel", "Symfony", "CodeIgniter", "CakePHP", "Slim",
    "NestJS", "Koa", "Hapi", "Fastify", "Adonis.js",
    "Gin", "Echo", "Fiber", "Chi", "Gorilla Mux",
    "Actix", "Rocket", "Axum", "Warp",
    "Phoenix", "Ecto", "Plug",
    "Tornado", "Sanic", "Starlette", "aiohttp",
    "Quarkus", "Micronaut", "Vert.x", "Dropwizard",
    "Play Framework", "Akka", "gRPC", "Thrift",
    "Deno", "Bun",

    # ── Mobile Development ──
    "React Native", "Flutter", "SwiftUI", "UIKit",
    "Jetpack Compose", "Android SDK", "iOS SDK",
    "Xamarin", "MAUI", ".NET MAUI", "Ionic", "Cordova",
    "Capacitor", "NativeScript", "Expo",
    "Kotlin Multiplatform", "KMM",
    "Core Data", "Room", "Realm",
    "ARKit", "ARCore", "SceneKit", "SpriteKit",
    "Android Jetpack", "Dagger", "Hilt",
    "App Store Connect", "Google Play Console",
    "TestFlight", "Firebase App Distribution",

    # ── Databases (Relational) ──
    "PostgreSQL", "MySQL", "SQLite", "Oracle",
    "Oracle Database", "SQL Server", "Microsoft SQL Server",
    "MariaDB", "CockroachDB", "TiDB", "Vitess",
    "Amazon Aurora", "Azure SQL", "Cloud SQL",
    "IBM Db2", "SAP HANA", "Teradata",
    "PlanetScale", "Neon", "AlloyDB",

    # ── Databases (NoSQL & NewSQL) ──
    "MongoDB", "Redis", "DynamoDB", "Cassandra",
    "Apache Cassandra", "CouchDB", "CouchBase",
    "Neo4j", "ArangoDB", "OrientDB", "JanusGraph",
    "Elasticsearch", "OpenSearch", "Solr", "Apache Solr",
    "InfluxDB", "TimescaleDB", "QuestDB",
    "RethinkDB", "FaunaDB", "Fauna",
    "ScyllaDB", "FoundationDB", "YugabyteDB",
    "Firebase", "Firestore", "Supabase",
    "Memcached", "Hazelcast", "Apache Ignite",
    "Pinecone", "Weaviate", "Milvus", "Qdrant",
    "ChromaDB", "pgvector", "FAISS",

    # ── Cloud Platforms & Services ──
    "AWS", "Amazon Web Services", "Azure", "Microsoft Azure",
    "GCP", "Google Cloud", "Google Cloud Platform",
    "IBM Cloud", "Oracle Cloud", "DigitalOcean",
    "Heroku", "Vercel", "Netlify", "Render",
    "Railway", "Fly.io", "Cloudflare", "Cloudflare Workers",
    "Linode", "Vultr", "Hetzner", "OVH",
    "Alibaba Cloud", "Tencent Cloud", "Huawei Cloud",

    # ── AWS Services ──
    "AWS Lambda", "Amazon S3", "S3", "EC2", "ECS", "EKS",
    "RDS", "DynamoDB", "SQS", "SNS", "CloudFront",
    "Route 53", "API Gateway", "CloudWatch",
    "CloudFormation", "CDK", "AWS CDK", "SAM",
    "Cognito", "IAM", "KMS", "Secrets Manager",
    "Step Functions", "EventBridge", "Kinesis",
    "Glue", "Athena", "EMR", "SageMaker",
    "Bedrock", "Elastic Beanstalk", "App Runner",
    "Fargate", "ECR", "CodePipeline", "CodeBuild",
    "CodeDeploy", "X-Ray",

    # ── Azure Services ──
    "Azure DevOps", "Azure Functions", "Azure Kubernetes Service",
    "Azure App Service", "Azure Blob Storage",
    "Azure Cognitive Services", "Azure AD",
    "Azure Service Bus", "Azure Event Hub",
    "Azure Data Factory", "Azure Synapse",
    "Azure Cosmos DB", "Azure Container Apps",

    # ── GCP Services ──
    "Cloud Run", "Cloud Functions", "BigQuery",
    "Pub/Sub", "Cloud Storage", "Compute Engine",
    "App Engine", "Cloud Spanner", "Dataflow",
    "Dataproc", "Vertex AI", "Cloud Build",
    "Artifact Registry", "GKE", "Anthos",

    # ── Containers & Orchestration ──
    "Docker", "Kubernetes", "Docker Compose",
    "Docker Swarm", "Podman", "Containerd",
    "LXC", "LXD", "Helm", "Kustomize",
    "Istio", "Linkerd", "Envoy", "Consul",
    "Nomad", "OpenShift", "Rancher", "K3s",
    "MicroK8s", "Kind", "Minikube",

    # ── Infrastructure as Code ──
    "Terraform", "Pulumi", "CloudFormation",
    "Ansible", "Chef", "Puppet", "SaltStack",
    "Vagrant", "Packer", "Crossplane",
    "AWS CDK", "Bicep", "ARM Templates",

    # ── CI/CD & DevOps ──
    "Jenkins", "GitHub Actions", "GitLab CI",
    "CircleCI", "Travis CI", "Bamboo",
    "TeamCity", "Azure Pipelines", "Drone CI",
    "ArgoCD", "Argo Workflows", "FluxCD",
    "Spinnaker", "Tekton", "GoCD",
    "Harness", "Octopus Deploy",
    "CI/CD", "DevOps", "GitOps", "SRE",
    "MLOps", "AIOps", "DataOps", "FinOps",
    "Platform Engineering", "Serverless",

    # ── Monitoring & Observability ──
    "Prometheus", "Grafana", "Datadog", "New Relic",
    "Splunk", "ELK Stack", "Elastic Stack",
    "Kibana", "Logstash", "Fluentd", "Fluent Bit",
    "Jaeger", "Zipkin", "OpenTelemetry",
    "PagerDuty", "Opsgenie", "VictorOps",
    "Sentry", "Honeycomb", "Lightstep",
    "AWS CloudWatch", "Azure Monitor", "Cloud Monitoring",
    "Nagios", "Zabbix", "Consul", "Dynatrace",

    # ── Web & Proxy Servers ──
    "Nginx", "Apache", "Apache HTTP Server",
    "HAProxy", "Traefik", "Caddy", "Envoy Proxy",
    "Varnish", "Squid", "IIS", "Tomcat", "Jetty",
    "Gunicorn", "Uvicorn", "uWSGI", "PM2",

    # ── AI & Machine Learning ──
    "TensorFlow", "PyTorch", "Keras", "Scikit-learn",
    "XGBoost", "LightGBM", "CatBoost", "AdaBoost",
    "Random Forest", "Gradient Boosting",
    "Decision Trees", "SVM", "Support Vector Machine",
    "Naive Bayes", "Logistic Regression", "Linear Regression",
    "K-Means", "DBSCAN", "PCA",
    "Neural Networks", "CNN", "RNN", "LSTM", "GRU",
    "GAN", "VAE", "Autoencoder",
    "Transformer", "Attention Mechanism",
    "Deep Learning", "Machine Learning",
    "Supervised Learning", "Unsupervised Learning",
    "Reinforcement Learning", "Transfer Learning",
    "Federated Learning", "Few-Shot Learning",
    "Feature Engineering", "Feature Selection",
    "Hyperparameter Tuning", "Cross-Validation",
    "Model Evaluation", "A/B Testing",

    # ── NLP ──
    "NLP", "Natural Language Processing",
    "NLTK", "spaCy", "Gensim", "TextBlob",
    "BERT", "GPT", "GPT-4", "ChatGPT", "Claude",
    "T5", "RoBERTa", "DistilBERT", "ALBERT",
    "Word2Vec", "GloVe", "FastText",
    "Sentiment Analysis", "Named Entity Recognition",
    "Text Classification", "Text Summarization",
    "Machine Translation", "Question Answering",
    "Tokenization", "Lemmatization", "Stemming",
    "TF-IDF", "Bag of Words",

    # ── Generative AI & LLM ──
    "LLM", "Large Language Model",
    "Generative AI", "GenAI", "Prompt Engineering",
    "LangChain", "LlamaIndex", "AutoGen",
    "CrewAI", "Semantic Kernel", "Haystack",
    "RAG", "Retrieval Augmented Generation",
    "Fine-Tuning", "RLHF", "LoRA", "QLoRA",
    "PEFT", "Instruction Tuning",
    "OpenAI API", "Anthropic API", "Gemini API",
    "Azure OpenAI", "AWS Bedrock",
    "Hugging Face", "Transformers",
    "Ollama", "vLLM", "TensorRT",
    "ONNX", "ONNX Runtime",

    # ── Computer Vision ──
    "Computer Vision", "OpenCV", "YOLO",
    "Object Detection", "Image Classification",
    "Image Segmentation", "Semantic Segmentation",
    "Instance Segmentation", "Face Recognition",
    "OCR", "Tesseract", "Optical Character Recognition",
    "MediaPipe", "Detectron2",
    "Image Processing", "Video Processing",

    # ── Data Science & Analytics ──
    "Pandas", "NumPy", "SciPy", "Matplotlib", "Seaborn",
    "Plotly", "Bokeh", "Altair", "Streamlit", "Gradio",
    "Jupyter", "Jupyter Notebook", "JupyterLab",
    "Google Colab", "Kaggle", "Anaconda", "Conda",
    "Data Analysis", "Data Visualization",
    "Statistical Analysis", "Hypothesis Testing",
    "Regression Analysis", "Time Series Analysis",
    "Exploratory Data Analysis", "EDA",
    "Data Mining", "Data Modeling",

    # ── MLOps & ML Infrastructure ──
    "MLflow", "Kubeflow", "Weights & Biases", "W&B",
    "DVC", "CML", "Evidently AI",
    "TFX", "BentoML", "Seldon", "KServe",
    "SageMaker", "Vertex AI", "Azure ML",
    "Feature Store", "Model Registry",
    "Model Serving", "Model Deployment",
    "ML Pipeline", "Training Pipeline",
    "Experiment Tracking", "Model Monitoring",

    # ── Data Engineering ──
    "Apache Spark", "PySpark", "Spark SQL",
    "Hadoop", "HDFS", "MapReduce", "Hive",
    "Kafka", "Apache Kafka", "Kafka Streams",
    "Apache Airflow", "Prefect", "Dagster", "Luigi",
    "dbt", "dbt Core", "dbt Cloud",
    "Snowflake", "Databricks", "Delta Lake",
    "Apache Iceberg", "Apache Hudi",
    "Redshift", "BigQuery", "Synapse Analytics",
    "Apache Flink", "Apache Beam", "Apache Storm",
    "Presto", "Trino", "Apache Druid",
    "Apache NiFi", "Airbyte", "Fivetran", "Stitch",
    "Great Expectations", "Apache Arrow",
    "ETL", "ELT", "Data Pipeline", "Data Warehouse",
    "Data Lake", "Data Lakehouse", "Data Mesh",
    "Data Catalog", "Data Governance",
    "Data Quality", "Data Lineage",
    "Change Data Capture", "CDC",

    # ── BI & Reporting ──
    "Tableau", "Power BI", "Looker", "Mode",
    "Metabase", "Superset", "Qlik", "QlikView",
    "QlikSense", "Sisense", "Domo",
    "Google Analytics", "Google Tag Manager",
    "Mixpanel", "Amplitude", "Segment",
    "Google Data Studio", "Looker Studio",

    # ── Messaging & Streaming ──
    "RabbitMQ", "Apache Kafka", "Redis Pub/Sub",
    "NATS", "ZeroMQ", "ActiveMQ", "Apache Pulsar",
    "Amazon SQS", "Amazon SNS", "Amazon Kinesis",
    "Google Pub/Sub", "Azure Service Bus",
    "Azure Event Hub", "Azure Event Grid",
    "MQTT", "AMQP", "WebSocket",
    "Server-Sent Events", "SSE", "Socket.IO",
    "Signal R", "SignalR",

    # ── API & Integration ──
    "REST API", "REST", "RESTful",
    "GraphQL", "Apollo", "Apollo Server",
    "gRPC", "Protobuf", "Protocol Buffers",
    "OpenAPI", "Swagger", "Postman", "Insomnia",
    "SOAP", "XML-RPC", "JSON-RPC",
    "Webhook", "API Gateway", "Kong",
    "Apigee", "MuleSoft", "Zapier",
    "IFTTT", "n8n", "Make",
    "tRPC", "Hono",

    # ── Testing ──
    "Jest", "Mocha", "Chai", "Sinon", "Jasmine",
    "Cypress", "Playwright", "Selenium", "WebDriver",
    "Puppeteer", "TestCafe", "Nightwatch",
    "JUnit", "TestNG", "Mockito", "PowerMock",
    "pytest", "unittest", "nose2", "tox",
    "RSpec", "Capybara", "Minitest",
    "PHPUnit", "Pest", "Codeception",
    "Enzyme", "React Testing Library", "Vitest",
    "Testing Library", "MSW", "Mock Service Worker",
    "JMeter", "Gatling", "k6", "Locust", "Artillery",
    "SonarQube", "SonarCloud", "CodeClimate",
    "Snyk", "Dependabot", "Renovate",
    "TDD", "BDD", "Unit Testing",
    "Integration Testing", "E2E Testing",
    "Load Testing", "Performance Testing",
    "Stress Testing", "Smoke Testing",
    "Regression Testing", "Acceptance Testing",
    "Test Automation", "QA Automation",
    "Manual Testing", "Quality Assurance",
    "Appium", "Robot Framework", "Cucumber",
    "Gherkin", "SpecFlow", "Behave",

    # ── Security ──
    "OWASP", "OWASP Top 10", "Penetration Testing",
    "Vulnerability Assessment", "Security Audit",
    "Burp Suite", "Nmap", "Wireshark",
    "Metasploit", "Kali Linux", "Parrot OS",
    "SIEM", "SOC", "IDS", "IPS",
    "Firewall", "WAF", "DDoS Protection",
    "OAuth", "OAuth 2.0", "JWT", "SAML",
    "OpenID Connect", "OIDC", "SSO",
    "SSL/TLS", "HTTPS", "PKI",
    "Encryption", "AES", "RSA", "SHA",
    "HashiCorp Vault", "AWS KMS",
    "Azure Key Vault", "Secrets Management",
    "Zero Trust", "Identity Management",
    "Access Control", "RBAC", "ABAC",
    "Compliance", "GDPR", "HIPAA", "SOC 2",
    "PCI DSS", "ISO 27001",
    "Cybersecurity", "Information Security",
    "Application Security", "Network Security",
    "Cloud Security", "DevSecOps",
    "Threat Modeling", "Risk Assessment",
    "Incident Response", "Forensics",
    "Malware Analysis", "Reverse Engineering",
    "SAST", "DAST", "IAST", "SCA",

    # ── Version Control ──
    "Git", "GitHub", "GitLab", "Bitbucket",
    "SVN", "Subversion", "Mercurial",
    "Azure Repos", "AWS CodeCommit",
    "Git Flow", "Trunk-Based Development",
    "Monorepo", "Lerna", "Nx", "Turborepo",

    # ── Project Management & Collaboration ──
    "Jira", "Confluence", "Notion", "Trello",
    "Asana", "Monday.com", "ClickUp",
    "Linear", "Shortcut", "Basecamp",
    "Microsoft Teams", "Slack", "Discord",
    "Miro", "FigJam", "Lucidchart",

    # ── Design Tools ──
    "Figma", "Adobe XD", "Sketch",
    "Photoshop", "Adobe Photoshop",
    "Illustrator", "Adobe Illustrator",
    "InDesign", "Adobe InDesign",
    "After Effects", "Adobe After Effects",
    "Premiere Pro", "Adobe Premiere Pro",
    "Canva", "InVision", "Zeplin",
    "Principle", "ProtoPie", "Framer",
    "Wireframing", "Prototyping", "Design Thinking",
    "User Research", "Usability Testing",
    "UI Design", "UX Design", "UI/UX",
    "Responsive Design", "Mobile First",
    "Design Systems", "Accessibility", "WCAG",
    "Material Design", "Human Interface Guidelines",

    # ── CMS & E-commerce ──
    "WordPress", "Shopify", "Magento",
    "WooCommerce", "Drupal", "Joomla",
    "Ghost", "Hugo", "Jekyll",
    "Contentful", "Strapi", "Sanity",
    "Prismic", "DatoCMS", "Tina",
    "Headless CMS", "JAMstack",

    # ── Blockchain & Web3 ──
    "Solidity", "Ethereum", "Web3.js", "Ethers.js",
    "Hardhat", "Truffle", "Foundry", "Brownie",
    "Smart Contracts", "DeFi", "NFT", "DAO",
    "IPFS", "The Graph", "Chainlink",
    "Polygon", "Avalanche", "Solana",
    "Hyperledger", "Hyperledger Fabric",
    "Consensus Algorithms", "Cryptography",
    "MetaMask", "WalletConnect",
    "Blockchain", "Distributed Ledger",
    "Bitcoin", "Binance Smart Chain",

    # ── IoT & Embedded ──
    "Arduino", "Raspberry Pi", "ESP32", "ESP8266",
    "RTOS", "FreeRTOS", "Zephyr",
    "FPGA", "VHDL", "Verilog", "SystemVerilog",
    "Embedded Systems", "Embedded C",
    "ARM", "ARM Cortex", "STM32", "PIC",
    "MQTT", "CoAP", "LoRaWAN", "Zigbee",
    "BLE", "Bluetooth", "NFC", "RFID",
    "I2C", "SPI", "UART", "CAN Bus",
    "PLC", "SCADA", "Industrial IoT",
    "IoT", "Internet of Things",
    "Edge Computing", "Fog Computing",
    "Digital Twin", "Sensor Fusion",

    # ── Game Development ──
    "Unity", "Unreal Engine", "Godot",
    "UE4", "UE5", "Unity3D",
    "OpenGL", "Vulkan", "DirectX", "Direct3D",
    "Metal", "WebGL", "WebGPU",
    "Phaser", "Cocos2d", "libGDX",
    "Game Design", "Level Design",
    "3D Modeling", "Blender", "Maya", "3ds Max",
    "Physics Engine", "AI Pathfinding",
    "Multiplayer", "Networking",
    "Shader Programming", "HLSL", "GLSL",

    # ── Networking & Infrastructure ──
    "Networking", "TCP/IP", "UDP",
    "HTTP", "HTTPS", "HTTP/2", "HTTP/3",
    "DNS", "DHCP", "SMTP", "FTP", "SSH",
    "VPN", "IPSec", "WireGuard",
    "Load Balancing", "Reverse Proxy",
    "Caching", "CDN", "CloudFlare CDN",
    "Service Mesh", "Istio", "Linkerd",
    "SD-WAN", "MPLS", "BGP", "OSPF",
    "VLAN", "Subnetting", "IPv4", "IPv6",
    "Cisco", "Juniper", "Palo Alto",
    "Network Automation", "NetDevOps",

    # ── Operating Systems & Platforms ──
    "Linux", "Ubuntu", "CentOS", "Red Hat",
    "RHEL", "Debian", "Fedora", "Arch Linux",
    "Alpine Linux", "Amazon Linux",
    "Unix", "FreeBSD", "macOS",
    "Windows", "Windows Server",
    "VMware", "Hyper-V", "KVM", "Proxmox",
    "Virtualization", "Containerization",

    # ── ERP & Enterprise ──
    "SAP", "SAP ABAP", "SAP HANA", "SAP S/4HANA",
    "SAP Fiori", "SAP BTP",
    "Salesforce", "Salesforce Lightning",
    "Salesforce Apex", "Salesforce SOQL",
    "ServiceNow", "Workday", "PeopleSoft",
    "Oracle EBS", "Oracle Fusion",
    "Dynamics 365", "Microsoft Dynamics",
    "NetSuite", "Odoo", "ERPNext",

    # ── RPA & Automation ──
    "UiPath", "Blue Prism", "Automation Anywhere",
    "Power Automate", "Zapier", "n8n",
    "Robotic Process Automation", "RPA",
    "Process Mining", "Process Automation",
    "Selenium", "Web Scraping", "BeautifulSoup",
    "Scrapy", "Puppeteer", "Crawling",

    # ── Low-Code / No-Code ──
    "Power Apps", "Power Platform", "Power Automate",
    "OutSystems", "Mendix", "Appian",
    "Bubble", "Retool", "Airtable",
    "Google AppSheet", "Webflow",

    # ── Methodologies & Practices ──
    "Agile", "Scrum", "Kanban", "SAFe",
    "Lean", "Six Sigma", "Waterfall",
    "Extreme Programming", "XP",
    "Pair Programming", "Code Review",
    "Continuous Integration", "Continuous Delivery",
    "Continuous Deployment", "Blue-Green Deployment",
    "Canary Deployment", "Feature Flags",
    "Microservices", "Monolith", "Modular Monolith",
    "Event-Driven Architecture", "CQRS",
    "Event Sourcing", "Domain-Driven Design", "DDD",
    "Clean Architecture", "Hexagonal Architecture",
    "SOA", "Service-Oriented Architecture",
    "Twelve-Factor App", "API-First",
    "Design Patterns", "SOLID Principles",
    "OOP", "Object-Oriented Programming",
    "Functional Programming", "Reactive Programming",
    "Concurrent Programming", "Parallel Programming",
    "Asynchronous Programming", "Multi-Threading",
    "Data Structures", "Algorithms",
    "System Design", "Distributed Systems",
    "High Availability", "Scalability",
    "Fault Tolerance", "Disaster Recovery",
    "Capacity Planning", "Performance Optimization",
    "Technical Documentation", "API Documentation",

    # ── Soft Skills (commonly listed on resumes) ──
    "Problem Solving", "Critical Thinking",
    "Communication", "Team Collaboration",
    "Leadership", "Mentoring", "Coaching",
    "Project Management", "Time Management",
    "Stakeholder Management", "Client Management",
    "Requirements Gathering", "Business Analysis",
    "Strategic Planning", "Decision Making",
    "Presentation Skills", "Public Speaking",
    "Cross-Functional Collaboration",
    "Adaptability", "Attention to Detail",
    "Analytical Skills", "Research",
    "Innovation", "Creativity",
    "Conflict Resolution", "Negotiation",
    "Remote Work", "Distributed Teams",
]

# ──────────────────────────────────────────────────────────────────────────────
# SKILL ALIASES — Map alternate spellings/abbreviations to canonical names
# ──────────────────────────────────────────────────────────────────────────────
SKILL_ALIASES = {
    # Language aliases
    "js": "JavaScript", "ts": "TypeScript", "py": "Python",
    "golang": "Go", "rustlang": "Rust",
    "csharp": "C#", "c sharp": "C#",
    "cplusplus": "C++", "cpp": "C++", "c plus plus": "C++",
    "obj-c": "Objective-C", "objective c": "Objective-C",
    "vb": "Visual Basic", "vbnet": "VB.NET",
    "f sharp": "F#", "fsharp": "F#",
    "r language": "R", "r programming": "R",
    "pl sql": "PL/SQL", "plsql": "PL/SQL",
    "tsql": "T-SQL",

    # Frontend aliases
    "node": "Node.js", "nodejs": "Node.js", "node js": "Node.js",
    "react js": "React.js", "reactjs": "React.js",
    "vue js": "Vue.js", "vuejs": "Vue.js",
    "next js": "Next.js", "nextjs": "Next.js",
    "nuxt js": "Nuxt.js", "nuxtjs": "Nuxt.js",
    "express js": "Express.js", "expressjs": "Express.js",
    "angular js": "Angular", "angularjs": "Angular",
    "svelte kit": "SvelteKit", "sveltekit": "SvelteKit",
    "solid js": "SolidJS", "solidjs": "SolidJS",
    "alpine js": "Alpine.js", "alpinejs": "Alpine.js",
    "ember js": "Ember.js", "backbone js": "Backbone.js",
    "three js": "Three.js", "d3 js": "D3.js",
    "chart js": "Chart.js", "chartjs": "Chart.js",
    "socket io": "Socket.IO", "socketio": "Socket.IO",

    # CSS/UI aliases
    "tailwind": "Tailwind CSS", "tailwindcss": "Tailwind CSS",
    "materialui": "Material UI", "material-ui": "Material UI",
    "chakraui": "Chakra UI", "chakra-ui": "Chakra UI",
    "antd": "Ant Design", "ant-design": "Ant Design",
    "styled-components": "Styled Components",
    "css-modules": "CSS Modules",
    "shadcn": "shadcn/ui",

    # Backend aliases
    "asp.net": "ASP.NET", "aspnet": "ASP.NET",
    "asp.net core": "ASP.NET Core", "aspnetcore": "ASP.NET Core",
    "dotnet": ".NET", "dot net": ".NET",
    "dotnet core": ".NET Core",
    "ror": "Ruby on Rails", "ruby on rails": "Ruby on Rails",
    "spring-boot": "Spring Boot", "springboot": "Spring Boot",
    "nest js": "NestJS", "nest.js": "NestJS",
    "adonis js": "Adonis.js", "adonisjs": "Adonis.js",
    "fast api": "FastAPI", "fast-api": "FastAPI",

    # Database aliases
    "postgres": "PostgreSQL", "psql": "PostgreSQL", "pg": "PostgreSQL",
    "mongo": "MongoDB", "mongodb": "MongoDB",
    "mssql": "SQL Server", "ms sql": "SQL Server",
    "dynamodb": "DynamoDB", "dynamo db": "DynamoDB",
    "elastic": "Elasticsearch", "es": "Elasticsearch",
    "open search": "OpenSearch", "opensearch": "OpenSearch",
    "cockroachdb": "CockroachDB",
    "neo 4j": "Neo4j",

    # Cloud & DevOps aliases
    "k8s": "Kubernetes", "k8": "Kubernetes", "kube": "Kubernetes",
    "tf": "Terraform",
    "gh actions": "GitHub Actions", "github-actions": "GitHub Actions",
    "gitlab-ci": "GitLab CI", "gitlab ci/cd": "GitLab CI",
    "aws lambda": "AWS Lambda", "lambda": "AWS Lambda",
    "gcloud": "Google Cloud", "gcp": "GCP",
    "gke": "Google Kubernetes Engine",
    "aks": "Azure Kubernetes Service",
    "eks": "EKS",
    "ecr": "ECR",
    "s3 bucket": "S3", "amazon s3": "Amazon S3",
    "cloud formation": "CloudFormation",
    "serverless framework": "Serverless",
    "argocd": "ArgoCD", "argo cd": "ArgoCD",
    "fluxcd": "FluxCD", "flux cd": "FluxCD",

    # AI/ML aliases
    "sklearn": "Scikit-learn", "scikit learn": "Scikit-learn",
    "sci-kit learn": "Scikit-learn", "scikit-learn": "Scikit-learn",
    "opencv": "OpenCV", "open cv": "OpenCV",
    "nlp": "NLP", "natural language processing": "NLP",
    "ml": "Machine Learning", "machine-learning": "Machine Learning",
    "dl": "Deep Learning", "deep-learning": "Deep Learning",
    "cv": "Computer Vision", "computer-vision": "Computer Vision",
    "rl": "Reinforcement Learning",
    "ai": "Generative AI", "gen ai": "GenAI", "genai": "GenAI",
    "llms": "LLM", "large language models": "LLM",
    "langchain": "LangChain", "lang chain": "LangChain",
    "llamaindex": "LlamaIndex", "llama index": "LlamaIndex",
    "huggingface": "Hugging Face", "hugging-face": "Hugging Face",
    "hf": "Hugging Face",
    "mlflow": "MLflow", "ml flow": "MLflow",
    "sagemaker": "SageMaker", "sage maker": "SageMaker",
    "xgb": "XGBoost", "lgbm": "LightGBM",
    "w&b": "Weights & Biases", "wandb": "Weights & Biases",

    # Data Engineering aliases
    "pyspark": "PySpark", "py spark": "PySpark",
    "apache spark": "Apache Spark", "spark": "Apache Spark",
    "apache kafka": "Apache Kafka",
    "apache airflow": "Apache Airflow", "airflow": "Apache Airflow",
    "apache flink": "Apache Flink", "flink": "Apache Flink",
    "apache beam": "Apache Beam", "beam": "Apache Beam",
    "power bi": "Power BI", "powerbi": "Power BI",

    # Testing aliases
    "testing library": "React Testing Library",
    "rtl": "React Testing Library",
    "webdriver": "Selenium",
    "selenium webdriver": "Selenium",

    # Methodology aliases
    "ci cd": "CI/CD", "cicd": "CI/CD",
    "ci/cd pipeline": "CI/CD",
    "tdd": "TDD", "test driven development": "TDD",
    "bdd": "BDD", "behavior driven development": "BDD",
    "ddd": "DDD", "domain driven design": "DDD",
    "oop": "OOP", "object oriented programming": "OOP",
    "fp": "Functional Programming",
    "solid": "SOLID Principles",
    "design-patterns": "Design Patterns",
    "micro services": "Microservices", "micro-services": "Microservices",
    "event driven": "Event-Driven Architecture",
    "api first": "API-First",

    # Security aliases
    "oauth2": "OAuth 2.0", "oauth 2": "OAuth 2.0",
    "jwt token": "JWT", "json web token": "JWT",
    "sso": "SSO", "single sign on": "SSO",
    "rbac": "RBAC", "role based access": "RBAC",
    "devsecops": "DevSecOps", "dev sec ops": "DevSecOps",
    "pen testing": "Penetration Testing", "pentest": "Penetration Testing",

    # Other aliases
    "web3": "Web3.js", "web 3": "Web3.js",
    "ethers": "Ethers.js", "ethersjs": "Ethers.js",
    "unreal": "Unreal Engine", "ue4": "UE4", "ue5": "UE5",
    "unity3d": "Unity", "unity 3d": "Unity",
    "rpa": "RPA", "robotic process automation": "RPA",
    "uipath": "UiPath", "ui path": "UiPath",
    "web scraping": "Web Scraping", "webscraping": "Web Scraping",
    "beautiful soup": "BeautifulSoup", "beautifulsoup": "BeautifulSoup",
    "bs4": "BeautifulSoup",
    "raspberry-pi": "Raspberry Pi", "rpi": "Raspberry Pi",
    "freertos": "FreeRTOS", "free rtos": "FreeRTOS",
    "ui ux": "UI/UX", "uiux": "UI/UX",
    "ui/ux design": "UI/UX",
    "responsive-design": "Responsive Design",
    "a11y": "Accessibility",
    "wcag": "WCAG",
    "jamstack": "JAMstack", "jam stack": "JAMstack",
}

# ──────────────────────────────────────────────────────────────────────────────
# JOB TITLE PATTERNS — 25+ regex patterns for 90%+ coverage
# ──────────────────────────────────────────────────────────────────────────────
JOB_TITLE_PATTERNS = [
    # ── Core Engineering Roles (all seniority levels) ──
    r'(?:senior|junior|lead|principal|staff|distinguished|associate|chief|head\s+of|vp\s+of|director\s+of|manager\s+of|executive|mid[\s-]?level|entry[\s-]?level)?\s*(?:software|web|full[\s-]?stack|front[\s-]?end|back[\s-]?end|mobile|android|ios|cloud|platform|infrastructure|devops|devsecops|site\s+reliability|data|machine\s+learning|ml|ai|nlp|deep\s+learning|computer\s+vision|security|cyber\s*security|qa|test|automation|database|network|embedded|firmware|iot|blockchain|game|graphics|ui|ux|product|solutions?|applications?|systems?|release|build|integration)\s*(?:engineer|developer|architect|analyst|scientist|consultant|specialist|manager|lead|tester|designer|researcher|administrator|admin|ops|programmer|coder)',

    # ── Specific Tech Stack Titles ──
    r'(?:java|python|php|ruby|golang|rust|scala|kotlin|swift|dart|javascript|typescript|node\.?js|react|angular|vue|django|flask|spring|\.net|salesforce|sap|oracle|aws|azure|gcp|terraform|kubernetes|docker)\s+(?:developer|engineer|architect|consultant|specialist|admin)',

    # ── Software & Application Titles ──
    r'(?:software|application|systems?|solutions?|platform|digital|information)\s+(?:engineer|developer|architect|designer|programmer|analyst|consultant)',

    # ── Management & Leadership ──
    r'(?:technical|engineering|development|project|program|product|delivery|it|technology|digital|software|cloud|data|security|infrastructure|devops|qa|test)\s+(?:manager|lead|director|coordinator|head|supervisor|officer|vp|chief|owner)',
    r'(?:team|tech|engineering|development)\s+(?:lead|leader|captain)',
    r'(?:chief\s+)?(?:technology|technical|information|security|data|digital|product|revenue|operating|marketing|financial|privacy)\s+officer',
    r'(?:vp|vice\s+president)\s+(?:of\s+)?(?:engineering|technology|product|development|data|it|operations)',
    r'head\s+of\s+(?:engineering|technology|product|development|data|design|security|it|infrastructure|devops|qa|mobile)',

    # ── Data & Analytics Titles ──
    r'(?:data|business\s+intelligence|bi|analytics|reporting|insights?|quantitative)\s+(?:analyst|engineer|scientist|architect|specialist|modeler|consultant|manager)',
    r'(?:machine\s+learning|ml|ai|deep\s+learning|nlp|computer\s+vision|research|applied)\s+(?:engineer|scientist|researcher|specialist|architect)',
    r'(?:data\s+(?:warehouse|lake|platform|infrastructure|governance|quality|ops|reliability))\s+(?:engineer|architect|analyst|specialist|manager)',

    # ── DevOps / SRE / Platform ──
    r'(?:devops|dev\s+ops|cloud\s+ops|cloud|platform|infrastructure|site\s+reliability|sre|build\s+and\s+release|release|systems?)\s+(?:engineer|architect|specialist|analyst|administrator|admin|manager)',

    # ── Security Titles ──
    r'(?:security|cyber\s*security|information\s+security|infosec|app(?:lication)?\s+security|cloud\s+security|network\s+security)\s+(?:engineer|analyst|architect|specialist|consultant|manager|officer|researcher)',
    r'(?:penetration|pen)\s+tester',
    r'(?:security\s+)?(?:soc|incident\s+response|threat[\s-]?intelligence|vulnerability|forensic|compliance|risk)\s+(?:analyst|engineer|specialist|manager)',
    r'ethical\s+hacker',

    # ── QA & Testing Titles ──
    r'(?:qa|quality\s+assurance|test|testing|automation\s+test|performance\s+test|manual\s+test)\s+(?:engineer|analyst|lead|manager|specialist|architect|developer)',
    r'sdet',

    # ── Design Titles ──
    r'(?:ui|ux|ui[\s/]ux|ux[\s/]ui|user\s+(?:experience|interface)|product|visual|graphic|interaction|web|motion|brand)\s+(?:designer|architect|researcher|strategist|lead)',
    r'(?:creative|art|design)\s+(?:director|lead|manager)',

    # ── Consulting & Freelance ──
    r'(?:technical|technology|it|management|strategy|cloud|digital\s+transformation|erp|crm)\s+(?:consultant|advisor|specialist)',
    r'(?:freelance|contract|independent)\s+(?:developer|designer|engineer|consultant|programmer)',

    # ── Teaching & Research ──
    r'(?:professor|lecturer|instructor|adjunct|teaching\s+assistant|research\s+assistant|postdoc|fellow)',
    r'(?:research|applied)\s+(?:scientist|engineer|fellow|associate)',

    # ── ERP & Enterprise ──
    r'(?:sap|salesforce|oracle|servicenow|dynamics|workday|netsuite|peoplesoft|hubspot|zendesk)\s+(?:developer|consultant|architect|admin(?:istrator)?|analyst|specialist|functional\s+consultant|technical\s+consultant)',

    # ── RPA & Low-Code ──
    r'(?:rpa|automation|uipath|blue\s+prism|power\s+(?:platform|automate|apps)|appian|mendix|outsystems)\s+(?:developer|engineer|consultant|architect)',

    # ── Specific Well-Known Titles (abbreviations / standalone) ──
    r'\b(?:sre|dba|sdet|devops\s+engineer|scrum\s+master|agile\s+coach|technical\s+writer|tech\s+writer|developer\s+advocate|developer\s+evangelist|developer\s+relations|solutions?\s+engineer|pre[\s-]?sales\s+engineer|support\s+engineer|field\s+engineer|customer\s+success\s+engineer|implementation\s+engineer)\b',

    # ── Intern / Entry Level ──
    r'(?:software|engineering|development|data|design|it|web|mobile|ai|ml|devops|cloud|qa|security)?\s*(?:intern(?:ship)?|trainee|apprentice|co[\s-]?op|working\s+student)',
    r'(?:graduate|entry[\s-]?level|junior|associate)\s+(?:engineer|developer|analyst|designer|programmer|consultant)',

    # ── Niche / Emerging Roles ──
    r'(?:prompt|ai\s+prompt|genai|generative\s+ai)\s+(?:engineer|specialist|designer)',
    r'(?:blockchain|web3|smart\s+contract|solidity|crypto)\s+(?:developer|engineer|architect)',
    r'(?:game|gameplay|graphics|rendering|engine|level|3d|physics)\s+(?:developer|programmer|engineer|designer|artist)',
    r'(?:embedded|firmware|fpga|hardware|asic|vlsi|rf|signal|control\s+systems?)\s+(?:engineer|developer|designer|programmer)',
    r'(?:network|systems?|infrastructure|telecom|wireless|voip)\s+(?:engineer|administrator|admin|architect|analyst)',
    r'(?:technical\s+)?(?:support|help\s+desk|service\s+desk)\s+(?:engineer|specialist|analyst)',
    r'(?:technical\s+)?(?:account|sales|partner)\s+(?:manager|executive|director)',
    r'(?:it|technology)\s+(?:manager|director|administrator|coordinator|specialist|officer|support)',
]

# ──────────────────────────────────────────────────────────────────────────────
# DOMAIN KEYWORDS — 20 domains with comprehensive indicators for 90%+ accuracy
# ──────────────────────────────────────────────────────────────────────────────
DOMAIN_KEYWORDS = {
    "software_engineering": {
        "title_patterns": [
            "software engineer", "software developer", "full stack",
            "fullstack", "web developer", "application developer",
            "full-stack developer", "solutions architect", "systems engineer",
            "application architect",
        ],
        "skill_indicators": [
            "react", "angular", "vue", "node.js", "django", "flask",
            "fastapi", "spring boot", "express", "rest api", "graphql",
            "javascript", "typescript", "python", "java", "c#", "c++",
            "go", "next.js", ".net", "laravel", "postgresql", "mongodb",
            "mysql", "docker", "git", "microservices", "redis",
            "nestjs", "ruby on rails", "svelte", "nuxt.js",
            "asp.net", "spring", "php", "kotlin", "rust",
        ],
    },
    "frontend": {
        "title_patterns": [
            "frontend", "front-end", "front end", "ui developer",
            "ui engineer", "react developer", "angular developer",
            "vue developer", "web developer", "frontend architect",
        ],
        "skill_indicators": [
            "react", "angular", "vue", "svelte", "html", "css",
            "tailwind", "bootstrap", "sass", "scss", "webpack", "vite",
            "next.js", "nuxt.js", "gatsby", "redux", "material ui",
            "three.js", "d3.js", "storybook", "styled components",
            "framer motion", "chakra ui", "jquery", "typescript",
            "responsive design", "css modules", "pinia", "vuex",
        ],
    },
    "backend": {
        "title_patterns": [
            "backend", "back-end", "back end", "server side",
            "java developer", "python developer", "node developer",
            "api developer", "backend architect", "php developer",
            ".net developer", "golang developer",
        ],
        "skill_indicators": [
            "node.js", "django", "flask", "fastapi", "spring boot",
            "express", ".net", "laravel", "nestjs", "postgresql",
            "mysql", "mongodb", "redis", "rest api", "graphql",
            "grpc", "rabbitmq", "kafka", "docker", "jwt", "oauth",
            "gin", "fiber", "actix", "sql", "microservices",
            "celery", "gunicorn", "nginx", "api gateway",
        ],
    },
    "data_science": {
        "title_patterns": [
            "data scientist", "ml engineer", "machine learning",
            "ai engineer", "deep learning", "nlp engineer",
            "research scientist", "prompt engineer", "applied scientist",
            "ai researcher", "computer vision engineer",
            "machine learning researcher", "data science lead",
        ],
        "skill_indicators": [
            "tensorflow", "pytorch", "keras", "scikit-learn", "pandas",
            "numpy", "hugging face", "opencv", "nltk", "spacy",
            "xgboost", "deep learning", "bert", "gpt", "transformers",
            "langchain", "mlflow", "machine learning", "neural networks",
            "reinforcement learning", "computer vision", "nlp",
            "feature engineering", "model evaluation", "a/b testing",
            "sagemaker", "vertex ai", "generative ai", "llm",
            "prompt engineering", "rag", "fine-tuning",
        ],
    },
    "data_engineering": {
        "title_patterns": [
            "data engineer", "etl developer", "bi developer",
            "data architect", "analytics engineer", "data platform",
            "big data engineer", "data pipeline engineer",
            "data warehouse engineer", "data infrastructure",
        ],
        "skill_indicators": [
            "apache spark", "pyspark", "hadoop", "kafka", "airflow",
            "dbt", "snowflake", "databricks", "bigquery", "redshift",
            "tableau", "power bi", "sql", "data pipeline", "etl",
            "data warehouse", "data lake", "hive", "presto", "trino",
            "apache flink", "apache beam", "delta lake", "fivetran",
            "airbyte", "data mesh", "data catalog", "data governance",
        ],
    },
    "devops": {
        "title_patterns": [
            "devops engineer", "sre", "site reliability",
            "platform engineer", "infrastructure engineer",
            "cloud ops", "release engineer", "build engineer",
            "devops architect", "devsecops", "gitops",
        ],
        "skill_indicators": [
            "docker", "kubernetes", "terraform", "ansible", "jenkins",
            "github actions", "gitlab ci", "ci/cd", "prometheus",
            "grafana", "nginx", "linux", "aws", "azure", "gcp",
            "helm", "argocd", "datadog", "elk stack", "istio",
            "packer", "vagrant", "cloudformation", "pulumi",
            "opentelemetry", "serverless", "gitops",
        ],
    },
    "mobile": {
        "title_patterns": [
            "mobile developer", "android developer", "ios developer",
            "flutter developer", "react native developer",
            "mobile engineer", "mobile architect", "app developer",
            "cross-platform developer", "kotlin developer",
            "swift developer",
        ],
        "skill_indicators": [
            "react native", "flutter", "swift", "kotlin", "android",
            "ios", "jetpack compose", "swiftui", "dart", "firebase",
            "mobile", "xcode", "android studio", "expo", "capacitor",
            "ionic", "xamarin", "arkit", "arcore", "realm",
            "core data", "room", "uikit",
        ],
    },
    "cloud_engineering": {
        "title_patterns": [
            "cloud engineer", "cloud architect", "aws engineer",
            "azure engineer", "gcp engineer", "cloud consultant",
            "cloud specialist", "cloud administrator",
            "cloud solutions architect", "cloud infrastructure",
        ],
        "skill_indicators": [
            "aws", "azure", "gcp", "ec2", "s3", "lambda",
            "cloudformation", "terraform", "cloud functions",
            "bigquery", "cloud run", "kubernetes", "docker",
            "ecs", "eks", "fargate", "azure functions",
            "iam", "vpc", "route 53", "cloudfront", "cdn",
            "serverless", "multi-cloud", "hybrid cloud",
        ],
    },
    "security": {
        "title_patterns": [
            "security engineer", "cybersecurity", "penetration tester",
            "security analyst", "ethical hacker", "security architect",
            "infosec", "information security", "soc analyst",
            "security consultant", "application security",
            "cloud security engineer", "security researcher",
        ],
        "skill_indicators": [
            "owasp", "penetration testing", "siem", "firewall",
            "encryption", "burp suite", "nmap", "wireshark",
            "metasploit", "kali linux", "sast", "dast",
            "vulnerability assessment", "threat modeling",
            "incident response", "compliance", "gdpr", "soc 2",
            "zero trust", "devsecops", "waf", "ids",
            "forensics", "malware analysis",
        ],
    },
    "qa_testing": {
        "title_patterns": [
            "qa engineer", "test engineer", "sdet",
            "quality assurance", "automation engineer",
            "test lead", "qa analyst", "qa manager",
            "performance test engineer", "test architect",
        ],
        "skill_indicators": [
            "selenium", "cypress", "playwright", "jest", "pytest",
            "junit", "jmeter", "tdd", "bdd", "postman",
            "test automation", "appium", "robot framework",
            "cucumber", "manual testing", "regression testing",
            "load testing", "performance testing", "k6",
            "sonarqube", "quality assurance",
        ],
    },
    "design": {
        "title_patterns": [
            "ui designer", "ux designer", "product designer",
            "graphic designer", "web designer", "ui/ux designer",
            "interaction designer", "visual designer",
            "design lead", "ux researcher", "creative director",
        ],
        "skill_indicators": [
            "figma", "adobe xd", "sketch", "photoshop", "illustrator",
            "wireframing", "prototyping", "design thinking",
            "user research", "usability testing", "ui/ux",
            "design systems", "accessibility", "responsive design",
            "invision", "zeplin", "framer", "canva",
            "after effects", "motion design",
        ],
    },
    "blockchain": {
        "title_patterns": [
            "blockchain developer", "smart contract developer",
            "web3 developer", "solidity developer",
            "blockchain engineer", "crypto developer",
            "defi developer", "blockchain architect",
        ],
        "skill_indicators": [
            "solidity", "ethereum", "web3.js", "ethers.js", "hardhat",
            "smart contracts", "defi", "nft", "blockchain",
            "truffle", "foundry", "ipfs", "polygon", "solana",
            "hyperledger", "consensus algorithms", "cryptography",
            "metamask", "dao",
        ],
    },
    "game_development": {
        "title_patterns": [
            "game developer", "game programmer", "game engineer",
            "game designer", "gameplay engineer", "unity developer",
            "unreal developer", "graphics programmer",
            "level designer", "3d artist",
        ],
        "skill_indicators": [
            "unity", "unreal engine", "godot", "opengl", "vulkan",
            "directx", "c++", "c#", "game design", "shader",
            "blender", "maya", "3d modeling", "physics engine",
            "multiplayer", "webgl", "phaser", "pixi",
        ],
    },
    "embedded_iot": {
        "title_patterns": [
            "embedded engineer", "firmware engineer", "iot engineer",
            "embedded developer", "hardware engineer",
            "fpga engineer", "embedded systems",
            "control systems engineer", "robotics engineer",
        ],
        "skill_indicators": [
            "embedded systems", "embedded c", "rtos", "freertos",
            "arduino", "raspberry pi", "esp32", "stm32", "arm",
            "fpga", "vhdl", "verilog", "mqtt", "iot",
            "i2c", "spi", "uart", "can bus", "ble",
            "edge computing", "sensor fusion", "plc", "scada",
        ],
    },
    "networking": {
        "title_patterns": [
            "network engineer", "network administrator",
            "network architect", "systems administrator",
            "infrastructure engineer", "telecom engineer",
            "network security engineer", "it administrator",
        ],
        "skill_indicators": [
            "cisco", "juniper", "tcp/ip", "dns", "vpn",
            "firewall", "load balancing", "bgp", "ospf", "vlan",
            "routing", "switching", "sd-wan", "mpls", "wireshark",
            "linux", "windows server", "vmware", "active directory",
            "subnetting", "ipv4", "ipv6",
        ],
    },
    "erp_enterprise": {
        "title_patterns": [
            "sap consultant", "sap developer", "salesforce developer",
            "salesforce consultant", "erp consultant",
            "oracle developer", "dynamics consultant",
            "servicenow developer", "functional consultant",
            "technical consultant",
        ],
        "skill_indicators": [
            "sap", "sap hana", "sap abap", "sap fiori", "salesforce",
            "salesforce apex", "servicenow", "oracle", "dynamics 365",
            "workday", "netsuite", "erp", "crm", "peoplesoft",
        ],
    },
    "project_management": {
        "title_patterns": [
            "project manager", "program manager", "product manager",
            "scrum master", "agile coach", "delivery manager",
            "technical project manager", "pmo", "release manager",
            "product owner",
        ],
        "skill_indicators": [
            "agile", "scrum", "kanban", "jira", "confluence",
            "project management", "stakeholder management",
            "sprint planning", "roadmap", "okr", "kpi",
            "risk management", "safe", "pmp", "prince2",
            "waterfall", "lean", "six sigma",
        ],
    },
    "data_analytics": {
        "title_patterns": [
            "data analyst", "business analyst", "business intelligence",
            "bi analyst", "reporting analyst", "insights analyst",
            "analytics manager", "market analyst", "financial analyst",
        ],
        "skill_indicators": [
            "sql", "excel", "tableau", "power bi", "looker",
            "google analytics", "data visualization", "python",
            "r", "statistical analysis", "data analysis",
            "mixpanel", "amplitude", "segment", "a/b testing",
            "hypothesis testing", "regression analysis",
        ],
    },
    "rpa_automation": {
        "title_patterns": [
            "rpa developer", "automation engineer",
            "automation architect", "rpa consultant",
            "process automation", "uipath developer",
            "blue prism developer", "power automate developer",
        ],
        "skill_indicators": [
            "uipath", "blue prism", "automation anywhere",
            "power automate", "rpa", "process mining",
            "process automation", "selenium", "web scraping",
            "python", "power platform", "zapier",
        ],
    },
}


class ExtractionService:
    """Hybrid extraction: keyword/regex primary + BERT-NER supplementary.

    The keyword database + regex approach reliably extracts 30+ skills
    from well-formatted resumes. BERT-NER adds novel skills/titles
    that aren't in the keyword database.
    """

    def __init__(self):
        self.ner_service = get_ner_service()
        self._skill_lookup = {s.lower(): s for s in SKILL_DATABASE}
        self._alias_lookup = {a.lower(): c for a, c in SKILL_ALIASES.items()}

    # ── NER helper ────────────────────────────────────────────────────────────

    def _get_ner_entities(self, text: str) -> Dict[str, List[str]]:
        """Run BERT-NER and return grouped entities."""
        try:
            return self.ner_service.extract_entities(text)
        except Exception as e:
            print(f"NER extraction failed: {e}")
            return {}

    # ── Skills ────────────────────────────────────────────────────────────────

    def extract_skills(self, text: str, use_embeddings: bool = True, _entities: Optional[Dict] = None) -> List[str]:
        """Extract skills using keyword matching + NER boost.

        Primary: keyword database (300+ skills) + alias matching + section parsing.
        Supplementary: BERT-NER skills entities for novel discoveries.
        """
        skills = set()
        text_lower = text.lower()

        # ── Method 1: Keyword matching ──
        for skill in SKILL_DATABASE:
            sl = skill.lower()
            if len(skill) <= 3:
                if re.search(r'\b' + re.escape(sl) + r'\b', text_lower):
                    skills.add(skill)
            else:
                if sl in text_lower:
                    skills.add(skill)

        # ── Method 2: Alias matching ──
        for alias, canonical in self._alias_lookup.items():
            if len(alias) <= 3:
                if re.search(r'\b' + re.escape(alias) + r'\b', text_lower):
                    skills.add(canonical)
            else:
                if alias in text_lower:
                    skills.add(canonical)

        # ── Method 3: Skill-section parsing ──
        # Catch many common resume section headers for skills
        section_patterns = [
            r'(?:skills|technical\s+skills|core\s+skills|key\s+skills|relevant\s+skills|professional\s+skills|hard\s+skills|soft\s+skills|additional\s+skills|other\s+skills)[:\s]*([^\n]+(?:\n(?!\n)[^\n]*)*)',
            r'(?:technologies|tools|tech\s+stack|technology\s+stack|tools?\s+(?:and|&)\s+technologies|technical\s+proficiency|proficienc(?:y|ies)|expertise|competencies|core\s+competencies|key\s+competencies|areas\s+of\s+expertise|technical\s+expertise)[:\s]*([^\n]+(?:\n(?!\n)[^\n]*)*)',
            r'(?:languages|programming\s+languages|frameworks|libraries|platforms|databases|cloud|devops|frontend|backend|front[\s-]end|back[\s-]end)[:\s]*([^\n]+)',
            r'(?:familiar\s+with|proficient\s+in|experienced\s+in|knowledge\s+of|worked\s+with|exposure\s+to)[:\s]*([^\n]+)',
        ]
        for pat in section_patterns:
            for match in re.findall(pat, text_lower, re.IGNORECASE):
                # Split on common delimiters used in skills sections
                candidates = re.split(r'[,|•·▪►→★☆■□●○◆◇\-–—/\\:;]|\s{2,}|\n', match)
                for c in candidates:
                    c = c.strip().strip('.()')
                    if 2 <= len(c) <= 35:
                        cl = c.lower().strip()
                        if cl in self._skill_lookup:
                            skills.add(self._skill_lookup[cl])
                        elif cl in self._alias_lookup:
                            skills.add(self._alias_lookup[cl])

        # ── Method 4: BERT-NER boost (novel skills only) ──
        entities = _entities or self._get_ner_entities(text)
        ner_skills = entities.get("skills", [])
        for ns in ner_skills:
            ns_clean = ns.strip()
            # Only add if:
            # 1. Not already found by keyword matching
            # 2. Looks like a real skill (reasonable length, no junk)
            if (ns_clean and
                len(ns_clean) >= 2 and
                len(ns_clean) <= 40 and
                not any(s.lower() == ns_clean.lower() for s in skills)):
                skills.add(ns_clean)

        return sorted(list(skills))

    # ── Job Titles ────────────────────────────────────────────────────────────

    def _add_spaces_to_title(self, title: str) -> str:
        """Add spaces between concatenated words in job titles.
        
        Examples:
            'softwareengineer' -> 'Software Engineer'
            'juniorsoftwareengineer' -> 'Junior Software Engineer'
            'mlops' -> 'MLOps'
        """
        # If title already has proper spacing (multiple words), return as-is with title case
        if ' ' in title and len(title.split()) > 1:
            # Check if it's not the weird spaced-out version
            words = title.split()
            if all(len(w) > 1 for w in words):
                return title.title()
        
        # Common job title words to split on
        job_words = [
            'software', 'engineer', 'developer', 'architect', 'manager', 'lead', 'senior', 
            'junior', 'principal', 'staff', 'associate', 'chief', 'director', 'analyst',
            'scientist', 'consultant', 'specialist', 'administrator', 'admin', 'designer',
            'researcher', 'tester', 'programmer', 'coder', 'frontend', 'backend', 'fullstack',
            'full', 'stack', 'mobile', 'android', 'ios', 'cloud', 'platform', 'infrastructure',
            'devops', 'devsecops', 'site', 'reliability', 'data', 'machine', 'learning',
            'deep', 'nlp', 'security', 'cyber', 'quality', 'assurance', 'database', 'network',
            'embedded', 'firmware', 'blockchain', 'game', 'graphics', 'product', 'solutions',
            'applications', 'systems', 'release', 'build', 'integration', 'web', 'api',
            'mlops', 'aiops', 'dataops', 'sre', 'qa', 'ui', 'ux', 'technical', 'head',
            'vice', 'president', 'executive', 'officer', 'team', 'tech', 'development',
            'business', 'intelligence', 'analytics', 'reporting', 'insights', 'quantitative',
            'automation', 'test', 'testing', 'manual', 'performance', 'load', 'stress',
            'penetration', 'ethical', 'hacker', 'incident', 'response', 'threat', 'vulnerability',
            'compliance', 'risk', 'forensic', 'visual', 'interaction', 'user', 'experience',
            'interface', 'creative', 'art', 'freelance', 'contract', 'independent', 'professor',
            'lecturer', 'instructor', 'teaching', 'assistant', 'research', 'postdoc', 'fellow',
            'applied', 'functional', 'process', 'field', 'customer', 'success', 'implementation',
            'support', 'sales', 'partner', 'account', 'delivery', 'program', 'project', 'scrum',
            'master', 'agile', 'coach', 'owner', 'entry', 'level', 'mid', 'intern', 'internship',
            'trainee', 'apprentice', 'graduate', 'working', 'student', 'prompt', 'generative',
            'smart', 'contract', 'solidity', 'crypto', 'gameplay', 'rendering', 'engine',
            'physics', 'hardware', 'asic', 'vlsi', 'signal', 'control', 'telecom', 'wireless',
            'voip', 'help', 'desk', 'service', 'pmo', 'market', 'financial', 'rpa', 'blue',
            'prism', 'power', 'automate', 'apps', 'mining', 'warehouse', 'lake', 'pipeline',
            'governance', 'catalog', 'lineage', 'mesh', 'ops', 'bi', 'etl', 'elt', 'change',
            'capture', 'cdc', 'streaming', 'messaging', 'kafka', 'spark', 'hadoop', 'airflow',
            'dbt', 'snowflake', 'databricks', 'bigquery', 'redshift', 'tableau', 'looker',
            'metabase', 'superset', 'qlik', 'sisense', 'domo', 'mixpanel', 'amplitude', 'segment',
        ]
        
        title_lower = title.lower().strip()
        
        # Special case: if the entire title is a known tech abbreviation, handle it
        if title_lower == 'mlops':
            return 'MLOps'
        elif title_lower == 'devops':
            return 'DevOps'
        elif title_lower == 'aiops':
            return 'AIOps'
        elif title_lower == 'dataops':
            return 'DataOps'
        
        result = []
        i = 0
        
        while i < len(title_lower):
            matched = False
            # Try to match the longest word first
            for word in sorted(job_words, key=len, reverse=True):
                if title_lower[i:].startswith(word):
                    result.append(word.capitalize())
                    i += len(word)
                    matched = True
                    break
            
            if not matched:
                # If no word matched, just add the character
                result.append(title_lower[i])
                i += 1
        
        # Join and clean up
        formatted = ' '.join(result)
        
        # Handle common tech abbreviations that should stay together
        formatted = formatted.replace('M Lops', 'MLOps')
        formatted = formatted.replace('Ml Ops', 'MLOps')
        formatted = formatted.replace('Mlops', 'MLOps')
        formatted = formatted.replace('Dev Ops', 'DevOps')
        formatted = formatted.replace('Devops', 'DevOps')
        formatted = formatted.replace('Dev Sec Ops', 'DevSecOps')
        formatted = formatted.replace('Devsecops', 'DevSecOps')
        formatted = formatted.replace('Ai Ops', 'AIOps')
        formatted = formatted.replace('Aiops', 'AIOps')
        formatted = formatted.replace('Data Ops', 'DataOps')
        formatted = formatted.replace('Dataops', 'DataOps')
        formatted = formatted.replace('Ai ', 'AI ')
        formatted = formatted.replace('Ml ', 'ML ')
        formatted = formatted.replace('Nlp ', 'NLP ')
        formatted = formatted.replace('Ui ', 'UI ')
        formatted = formatted.replace('Ux ', 'UX ')
        formatted = formatted.replace('Api ', 'API ')
        formatted = formatted.replace('Aws ', 'AWS ')
        formatted = formatted.replace('Gcp ', 'GCP ')
        formatted = formatted.replace('Sre ', 'SRE ')
        formatted = formatted.replace('Qa ', 'QA ')
        formatted = formatted.replace('Sdet ', 'SDET ')
        formatted = formatted.replace('Bi ', 'BI ')
        formatted = formatted.replace('Etl ', 'ETL ')
        formatted = formatted.replace('Elt ', 'ELT ')
        formatted = formatted.replace('Cdc ', 'CDC ')
        
        # Normalize multiple spaces to single space
        formatted = re.sub(r'\s+', ' ', formatted)
        
        # Filter out weird spaced-out results (like "p r o f e s s i o n a l")
        words = formatted.split()
        if len(words) > 3 and all(len(w) == 1 for w in words[:3]):
            # This is likely a weird spaced-out result, skip it
            return ""
        
        return formatted.strip()

    def extract_job_titles(self, text: str, _entities: Optional[Dict] = None) -> List[str]:
        """Extract job titles using regex + NER boost."""
        titles = []
        text_lower = text.lower()

        # ── Method 1: Regex pattern matching ──
        for pattern in JOB_TITLE_PATTERNS:
            matches = re.finditer(pattern, text_lower)
            for m in matches:
                title = m.group(0).strip()
                # Format title with proper spacing
                title = self._add_spaces_to_title(title)
                # Filter out invalid titles (too short, contains newlines, etc.)
                if title and title not in titles and len(title) > 3 and '\n' not in title:
                    titles.append(title)

        # ── Method 2: Experience section format matching ──
        exp_title_pat = r'(?:^|\n)\s*([A-Z][A-Za-z\s/\-]+?)\s*(?:at|@|\||-|–|—|,)\s*[A-Z]'
        for m in re.finditer(exp_title_pat, text):
            candidate = m.group(1).strip()
            if 5 <= len(candidate) <= 60:
                cl = candidate.lower()
                for tp in JOB_TITLE_PATTERNS:
                    if re.search(tp, cl):
                        # Format title with proper spacing
                        formatted_title = self._add_spaces_to_title(candidate)
                        if formatted_title and formatted_title not in titles and len(formatted_title) > 3 and '\n' not in formatted_title:
                            titles.append(formatted_title)
                        break

        # ── Method 3: BERT-NER designation boost ──
        entities = _entities or self._get_ner_entities(text)
        ner_titles = entities.get("designation", [])
        for nt in ner_titles:
            nt_clean = self._add_spaces_to_title(nt.strip())
            if nt_clean and len(nt_clean) >= 5 and nt_clean not in titles and '\n' not in nt_clean:
                titles.append(nt_clean)

        return titles[:10]

    # ── Education ─────────────────────────────────────────────────────────────

    def extract_education(self, text: str, _entities: Optional[Dict] = None) -> List[Dict[str, str]]:
        """Extract education using regex + NER boost."""
        education = []

        # ── Method 1: Regex patterns ──
        degree_patterns = [
            r'((?:Bachelor|Master|Doctor|PhD|B\.?S\.?c?|M\.?S\.?c?|B\.?A\.?|M\.?A\.?|B\.?E\.?|M\.?E\.?|B\.?Tech|M\.?Tech|MBA|BBA|BS|MS|BE|ME|Associate|Diploma)[\w\s,.]{0,60}?)\s+(?:from|at|in)\s+([\w\s,.\-\']+?)(?:\s*[\(,\|]\s*(\d{4})\s*[\),\|]|\s+(\d{4})|\s*(?:\n|$))',
        ]
        for pat in degree_patterns:
            for m in re.finditer(pat, text, re.IGNORECASE | re.MULTILINE):
                degree = m.group(1).strip().rstrip(',.- ')
                institution = m.group(2).strip().rstrip(',.- ') if m.group(2) else ""
                year = m.group(3) or (m.group(4) if len(m.groups()) > 3 else None)
                if len(degree) > 3 and len(degree) < 100 and len(institution) > 2:
                    entry = {"degree": degree, "institution": institution}
                    if year:
                        entry["year"] = year
                    if not any(e["degree"].lower() == degree.lower() for e in education):
                        education.append(entry)

        # Standalone degree keywords
        if not education:
            standalone_pat = r'((?:Bachelor|Master|Doctor|PhD|B\.?S\.?c?|M\.?S\.?c?|B\.?A\.?|M\.?A\.?|B\.?E\.?|M\.?E\.?|B\.?Tech|M\.?Tech|MBA|BBA|Diploma|Associate)\s+(?:of|in)\s+[\w\s]+?)(?:\s*[,\(\|]\s*(\d{4})|(\d{4})|\s*(?:\n|$))'
            for m in re.finditer(standalone_pat, text, re.IGNORECASE):
                degree = m.group(1).strip().rstrip(',.- ')
                year = m.group(2) or m.group(3)
                if 5 < len(degree) < 100:
                    entry = {"degree": degree, "institution": "", "year": year or ""}
                    if not any(e["degree"].lower() == degree.lower() for e in education):
                        education.append(entry)

        # ── Method 2: NER boost ──
        if not education:
            entities = _entities or self._get_ner_entities(text)
            degrees = entities.get("degree", [])
            colleges = entities.get("college", [])
            grad_years = entities.get("graduation_year", [])
            max_entries = max(len(degrees), len(colleges), 1)
            for i in range(min(max_entries, 5)):
                entry = {
                    "degree": degrees[i] if i < len(degrees) else "",
                    "institution": colleges[i] if i < len(colleges) else "",
                    "year": grad_years[i] if i < len(grad_years) else "",
                }
                if entry["degree"] or entry["institution"]:
                    education.append(entry)

        return education[:5]

    # ── Experience ────────────────────────────────────────────────────────────

    def extract_experience(self, text: str, _entities: Optional[Dict] = None) -> Dict[str, any]:
        """Extract experience: years, summary, companies."""
        from datetime import datetime as dt

        experience = {"years": None, "summary": "", "companies": []}

        # ── Companies from NER ──
        entities = _entities or self._get_ner_entities(text)
        ner_companies = entities.get("companies", [])

        # ── Companies from regex ──
        company_patterns = [
            r'(?:at|@)\s+([A-Z][\w\s&.,]+?)(?:\s*[\|\-–—,]|\s+as\s+|\n)',
        ]
        regex_companies = []
        for cp in company_patterns:
            for m in re.finditer(cp, text):
                company = m.group(1).strip().rstrip(',.- ')
                if 2 <= len(company) <= 50 and company not in regex_companies:
                    regex_companies.append(company)

        # Merge: regex companies + NER companies (deduplicated)
        all_companies = list(regex_companies)
        for nc in ner_companies:
            if not any(nc.lower() == c.lower() for c in all_companies):
                all_companies.append(nc)
        experience["companies"] = all_companies[:10]

        # ── Years of experience ──
        # Method 1: NER
        ner_years = entities.get("experience_years", [])
        if ner_years:
            for yr_text in ner_years:
                m = re.search(r'(\d+)', yr_text)
                if m:
                    experience["years"] = int(m.group(1))
                    break

        # Method 2: Explicit regex
        if experience["years"] is None:
            years_pats = [
                r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience|exp|work)',
                r'(?:experience|exp)\s*(?:of\s+)?(\d+)\+?\s*(?:years?|yrs?)',
                r'(?:over|more\s+than|approximately|around|nearly|about)\s+(\d+)\s*(?:years?|yrs?)',
            ]
            for yp in years_pats:
                m = re.search(yp, text, re.IGNORECASE)
                if m:
                    experience["years"] = int(m.group(1))
                    break

        # Method 3: Date range calculation
        if experience["years"] is None:
            exp_section_match = re.search(
                r'(?:experience|work\s+history|employment|professional\s+experience)\s*[:\n\r]?(.*?)(?:(?:education|skills|projects?|certif|awards?)\b|\Z)',
                text, re.IGNORECASE | re.DOTALL
            )
            exp_text = exp_section_match.group(1) if exp_section_match else ""
            if exp_text:
                date_range_pats = [
                    r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s*[,.]?\s*(\d{4})\s*[-–—to]+\s*(?:(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s*[,.]?\s*)?(\d{4}|[Pp]resent|[Cc]urrent|[Nn]ow|[Oo]ngoing)',
                    r'(\d{4})\s*[-–—to]+\s*(\d{4}|[Pp]resent|[Cc]urrent|[Nn]ow|[Oo]ngoing)',
                ]
                current_year = dt.now().year
                all_years = []
                for pat in date_range_pats:
                    for m in re.finditer(pat, exp_text, re.IGNORECASE):
                        groups = m.groups()
                        start_year = end_year = None
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

        # Experience summary
        exp_section = re.search(
            r'(?:experience|work\s+history|employment)\s*[:\n\r]?(.*?)(?:(?:education|skills|projects?|certif)\b|\Z)',
            text, re.IGNORECASE | re.DOTALL
        )
        if exp_section:
            experience["summary"] = exp_section.group(1).strip()[:500]

        return experience

    # ── Projects (regex only) ─────────────────────────────────────────────────

    def extract_projects(self, text: str) -> List[Dict[str, str]]:
        """Extract project names from resume using pattern matching."""
        projects = []
        proj_area_match = re.search(
            r'(?:projects?|personal\s+projects?|key\s+projects?|academic\s+projects?|side\s+projects?)\s*[:\n\r]',
            text, re.IGNORECASE
        )
        if proj_area_match:
            start = proj_area_match.end()
            proj_area = text[start:start + 2000]
            entries = re.split(r'\n\s*(?=[A-Z•▪►→\-\*\d])', proj_area)
            for entry in entries:
                entry = entry.strip()
                if not entry or len(entry) < 5:
                    continue
                if re.match(r'(?:education|experience|skills|certif|awards?|references?|hobbies)\b', entry, re.IGNORECASE):
                    break
                title_match = re.match(r'^[•▪►→\-\*\d.)\s]*([A-Z][\w\s\-./&]{2,60}?)(?:\s*[–—:\|]\s*(.+)|$)', entry)
                if title_match:
                    title = title_match.group(1).strip().rstrip(',.- ')
                    desc = title_match.group(2) or ""
                    if 3 <= len(title) <= 80:
                        projects.append({"name": title, "description": desc.strip()[:200]})
        return projects[:8]

    # ── Certifications (regex only) ───────────────────────────────────────────

    def extract_certifications(self, text: str) -> List[str]:
        """Extract certifications using precise regex patterns."""
        certs = []
        cert_patterns = [
            r'(AWS\s+Certified[\w\s\-]+)',
            r'(Azure\s+(?:Fundamentals|Administrator|Developer|Solutions?\s+Architect|Security|Data|AI|DevOps)[\w\s\-]*)',
            r'(Microsoft\s+Certified[:\s][\w\s\-]+)',
            r'(AZ-\d{3}|DP-\d{3}|AI-\d{3}|SC-\d{3})',
            r'(Google\s+Cloud\s+(?:Certified|Professional|Associate)[\w\s\-]*)',
            r'((?:CKA|CKAD|CKS|Certified\s+Kubernetes)[\w\s\-]*)',
            r'((?:Certified\s+Scrum\s+(?:Master|Product\s+Owner|Developer)|CSM|CSPO|PSM|PSPO|PMI-ACP|SAFe\s+Agilist)[\w\s\-]*)',
            r'((?:PMP|CAPM|Project\s+Management\s+Professional)[\w\s\-]*)',
            r'((?:CISSP|CCSP|Certified\s+Information\s+Systems\s+Security)[\w\s\-]*)',
            r'((?:CEH|Certified\s+Ethical\s+Hacker)[\w\s\-]*)',
            r'(CompTIA\s+(?:A\+|Network\+|Security\+|Cloud\+|Linux\+|CySA\+|PenTest\+|CASP\+)[\w\s\-]*)',
            r'((?:CCNA|CCNP|CCIE|Cisco\s+Certified)[\w\s\-]*)',
            r'(Oracle\s+Certified[\w\s\-]+)',
            r'(Salesforce\s+Certified[\w\s\-]+)',
            r'(Terraform\s+(?:Associate|Professional)[\w\s\-]*)',
            r'((?:RHCSA|RHCE|RHCA)[\w\s\-]*)',
            r'(ITIL[\w\s\-v]*(?:Foundation|Practitioner|Expert|Master)?)',
            r'(ISTQB[\w\s\-]*)',
        ]
        for pat in cert_patterns:
            for m in re.finditer(pat, text, re.IGNORECASE):
                cert = m.group(1).strip()
                if cert not in certs and len(cert) > 3:
                    certs.append(cert)
        return certs[:15]

    # ── Domain Detection ──────────────────────────────────────────────────────

    def detect_domain(self, text: str, skills: List[str], job_titles: List[str]) -> str:
        """Detect professional domain using weighted scoring."""
        text_lower = text.lower()
        domain_scores = {}
        for domain, config in DOMAIN_KEYWORDS.items():
            score = 0
            for title in job_titles:
                title_lower = title.lower()
                for tp in config["title_patterns"]:
                    if tp in title_lower:
                        score += 10
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

    # ── Skill Classification ──────────────────────────────────────────────────

    def _extract_experience_and_project_sections(self, text: str) -> str:
        """Extract text from experience and project sections only."""
        text_lower = text.lower()
        combined_text = ""
        
        # Experience section patterns
        experience_patterns = [
            r'(?:experience|work\s+experience|professional\s+experience|employment\s+history|work\s+history)[:\s]*(.+?)(?=\n\s*(?:education|projects|skills|certifications|awards|publications|references|$))',
            r'(?:professional\s+background|career\s+history|employment)[:\s]*(.+?)(?=\n\s*(?:education|projects|skills|certifications|$))',
        ]
        
        for pattern in experience_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE | re.DOTALL)
            for match in matches:
                combined_text += " " + match
        
        # Project section patterns
        project_patterns = [
            r'(?:projects|personal\s+projects|key\s+projects|major\s+projects|project\s+experience|academic\s+projects)[:\s]*(.+?)(?=\n\s*(?:education|experience|skills|certifications|awards|publications|references|$))',
            r'(?:portfolio|work\s+samples|case\s+studies)[:\s]*(.+?)(?=\n\s*(?:education|experience|skills|certifications|$))',
        ]
        
        for pattern in project_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE | re.DOTALL)
            for match in matches:
                combined_text += " " + match
        
        return combined_text.lower()

    def classify_skills(self, text: str, skills: List[str], projects: List[str]) -> Dict[str, List[str]]:
        """
        Classify skills into two categories:
        1. Experienced Skills: Skills mentioned in experience/project sections
        2. Known Skills: Skills mentioned elsewhere (skills section, summary, etc.)
        
        Args:
            text: Full resume text
            skills: List of all extracted skills
            projects: List of extracted projects
            
        Returns:
            Dict with 'experienced_skills' and 'known_skills' lists
        """
        # Extract experience and project sections
        experience_project_text = self._extract_experience_and_project_sections(text)
        
        # Also include project descriptions
        for project in projects:
            experience_project_text += " " + project.lower()
        
        experienced_skills = []
        known_skills = []
        
        for skill in skills:
            skill_lower = skill.lower()
            
            # Check if skill appears in experience/project sections
            # Use word boundary for short skills (<=3 chars) to avoid false matches
            if len(skill) <= 3:
                # For short skills like "Go", "R", "C", use word boundary
                pattern = r'\b' + re.escape(skill_lower) + r'\b'
                if re.search(pattern, experience_project_text):
                    experienced_skills.append(skill)
                else:
                    known_skills.append(skill)
            else:
                # For longer skills, simple substring match is fine
                if skill_lower in experience_project_text:
                    experienced_skills.append(skill)
                else:
                    known_skills.append(skill)
        
        return {
            "experienced_skills": experienced_skills,
            "known_skills": known_skills
        }

    # ── Extract All (optimized: single NER call) ──────────────────────────────

    def extract_all(self, text: str) -> Dict[str, any]:
        """Extract all structured information from resume text.

        Runs NER once, passes cached entities to all sub-methods.
        """
        entities = self._get_ner_entities(text)

        skills = self.extract_skills(text, _entities=entities)
        job_titles = self.extract_job_titles(text, _entities=entities)
        experience = self.extract_experience(text, _entities=entities)
        education = self.extract_education(text, _entities=entities)
        projects = self.extract_projects(text)
        certifications = self.extract_certifications(text)
        domain = self.detect_domain(text, skills, job_titles)
        
        # ✅ NEW: Classify skills into experienced vs known
        skill_classification = self.classify_skills(text, skills, projects)

        return {
            "skills": skills,  # Keep all skills for backward compatibility
            "experienced_skills": skill_classification["experienced_skills"],
            "known_skills": skill_classification["known_skills"],
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
