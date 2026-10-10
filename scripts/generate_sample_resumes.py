"""Generate realistic resumes dataset for matching evaluation and benchmarking.

Produces data/raw/resumes.csv with resume text and category labels across canonical domains:
- Backend Developer (Python Developer, Java Developer, Backend Developer)
- Frontend Developer (Web Designing, React Developer, Frontend Developer)
- ML Engineer (Data Science, Machine Learning, ML Engineer)
- Data Analyst (Business Analyst, Data Analyst)
- DevOps Engineer (DevOps, Cloud Engineer, DevOps Engineer)
- Product Manager (Product Manager, Project Manager, Operations Manager)
"""

import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_FILE = BASE_DIR / "data" / "raw" / "resumes.csv"
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

RESUMES_DATA = [
    # --- Backend Developer / Python Developer (10 resumes) ---
    (
        "Python Developer",
        "John Miller - Senior Python Developer\n\n"
        "Summary:\nExperienced backend software developer with 5+ years building distributed web applications and RESTful APIs using Python, FastAPI, and Django.\n\n"
        "Skills:\nLanguages: Python, SQL, Bash\nFrameworks: FastAPI, Flask, Django\nDatabases: PostgreSQL, Redis, MySQL\nTools: Docker, Git, Linux, CI/CD\n\n"
        "Experience:\nSenior Backend Engineer at CloudSystems (2020 - Present)\n"
        "- Designed and implemented scalable microservices using FastAPI and PostgreSQL.\n"
        "- Integrated Redis caching layers to reduce database query latency by 45%.\n"
        "- Built automated CI/CD deployment pipelines using Docker and GitHub Actions.\n\n"
        "Education:\nB.S. in Computer Science, State University",
    ),
    (
        "Backend Developer",
        "Sarah Jenkins - Backend Software Engineer\n\n"
        "Summary:\nBackend engineer specializing in high-concurrency microservices architecture and relational database optimization.\n\n"
        "Skills:\nPython, FastAPI, PostgreSQL, Redis, Docker, RabbitMQ, REST APIs, Git, Linux, SQLAlchemy.\n\n"
        "Experience:\nBackend Developer at DataFlow Corp (2021 - Present)\n"
        "- Developed REST APIs with Python and FastAPI serving 2M daily requests.\n"
        "- Optimized PostgreSQL database schemas and complex analytical queries.\n"
        "- Managed containerized services with Docker.\n\n"
        "Education:\nB.Tech in Information Technology",
    ),
    (
        "Python Developer",
        "David Clark - Python Backend Engineer\n\n"
        "Summary:\nSoftware engineer with focus on Python server-side development, asynchronous programming, and cloud integrations.\n\n"
        "Skills:\nPython, Django, Flask, SQL, PostgreSQL, Docker, Git, REST API, Celery, Linux.\n\n"
        "Experience:\nPython Engineer at WebScale Inc (2019 - 2023)\n"
        "- Built core business logic in Django and Celery for background job processing.\n"
        "- Containerized applications using Docker and deployed on Linux cloud servers.\n"
        "- Collaborated with frontend teams to define RESTful API contracts.\n\n"
        "Education:\nB.S. Computer Engineering",
    ),
    (
        "Backend Developer",
        "Elena Rostova - Backend API Developer\n\n"
        "Summary:\n4 years experience building reliable web backends, integrating third-party APIs, and maintaining relational databases.\n\n"
        "Skills:\nPython, FastAPI, SQL, PostgreSQL, Redis, Docker, Git, CI/CD, Microservices.\n\n"
        "Experience:\nSoftware Developer at FinApp (2022 - Present)\n"
        "- Created financial transaction processing pipelines using Python and PostgreSQL.\n"
        "- Implemented caching with Redis and set up unit testing with pytest.\n\n"
        "Education:\nB.S. Software Engineering",
    ),
    (
        "Python Developer",
        "Alex Rivera - Python & Cloud Backend Developer\n\n"
        "Summary:\nBackend developer proficient in Python, SQL, and container technologies.\n\n"
        "Skills:\nPython, FastAPI, Docker, SQL, PostgreSQL, Linux, Git, REST API, CI/CD.\n\n"
        "Experience:\nBackend Engineer at LogiTech (2020 - Present)\n"
        "- Designed internal tooling and microservices using Python and Docker.\n"
        "- Wrote database migration scripts and optimized SQL indexes in PostgreSQL.\n\n"
        "Education:\nB.S. in Computer Science",
    ),
    (
        "Backend Developer",
        "Marcus Vance - Junior Backend Developer\n\n"
        "Summary:\nPassionate software engineer with solid fundamentals in Python, relational databases, and REST APIs.\n\n"
        "Skills:\nPython, Flask, SQL, PostgreSQL, Git, Linux, Docker, REST APIs.\n\n"
        "Experience:\nJunior Developer at StartupHub (2023 - Present)\n"
        "- Assisted in building Flask REST endpoints and writing PostgreSQL queries.\n"
        "- Automated test suites and participated in agile sprints.\n\n"
        "Education:\nB.S. Computer Science",
    ),
    (
        "Python Developer",
        "Rachel Adams - Backend Systems Engineer\n\n"
        "Summary:\nSpecialist in scalable Python server architectures, microservices, and database tuning.\n\n"
        "Skills:\nPython, FastAPI, Redis, PostgreSQL, Docker, Kubernetes, CI/CD, Git.\n\n"
        "Experience:\nSenior Backend Developer at OmniCloud (2019 - Present)\n"
        "- Re-architected monolithic application into microservices using FastAPI and Docker.\n"
        "- Maintained zero-downtime database migrations in PostgreSQL.\n\n"
        "Education:\nM.S. in Computer Science",
    ),
    (
        "Backend Developer",
        "Kevin Brooks - Server-Side Software Engineer\n\n"
        "Summary:\nBackend developer focused on secure, high-performance API design with Python.\n\n"
        "Skills:\nPython, Django, PostgreSQL, Docker, Git, Linux, REST API, Redis.\n\n"
        "Experience:\nSoftware Engineer at SecureNet (2021 - Present)\n"
        "- Built authentication and user management services in Django.\n"
        "- Used Redis for session caching and rate-limiting.\n\n"
        "Education:\nB.S. Information Systems",
    ),
    (
        "Python Developer",
        "Liam Thorne - Python Developer & Architect\n\n"
        "Summary:\nExperienced engineer designing robust Python services and data processing pipelines.\n\n"
        "Skills:\nPython, FastAPI, SQL, PostgreSQL, Redis, Docker, Git, Linux, CI/CD.\n\n"
        "Experience:\nStaff Engineer at AlphaPlatform (2018 - Present)\n"
        "- Lead developer for payment microservices using FastAPI and PostgreSQL.\n\n"
        "Education:\nB.S. Computer Science",
    ),
    (
        "Backend Developer",
        "Zoe Martinez - Backend Developer\n\n"
        "Summary:\n3 years of hands-on experience building backend APIs and database management with Python.\n\n"
        "Skills:\nPython, Flask, FastAPI, PostgreSQL, SQL, Docker, Git, Linux.\n\n"
        "Experience:\nBackend Developer at MediaTech (2022 - Present)\n"
        "- Implemented content delivery REST APIs with Python and FastAPI.\n\n"
        "Education:\nB.S. Computing",
    ),

    # --- Data Analyst / Business Analyst (10 resumes) ---
    (
        "Data Analyst",
        "Emily Watson - Senior Data Analyst\n\n"
        "Summary:\nData Analyst with 5+ years of experience transforming complex datasets into actionable business insights using SQL, Tableau, and Excel.\n\n"
        "Skills:\nSQL, Tableau, Excel, Power BI, Python, Data Visualization, Statistical Analysis, A/B Testing, Data Analytics, Pandas.\n\n"
        "Experience:\nLead Data Analyst at RetailMetrics (2020 - Present)\n"
        "- Designed executive dashboards in Tableau tracking KPI performance and retention.\n"
        "- Wrote advanced SQL queries involving window functions and multi-table joins.\n"
        "- Conducted A/B testing and statistical analysis to guide marketing strategy.\n\n"
        "Education:\nB.S. in Statistics, State University",
    ),
    (
        "Business Analyst",
        "Brian Taylor - Senior Business Analyst\n\n"
        "Summary:\nBusiness analyst bridging technical teams and executive stakeholders through data-driven reporting and financial modeling.\n\n"
        "Skills:\nSQL, Excel, Tableau, Data Visualization, Business Analysis, Stakeholder Management, Power BI, Requirements Gathering.\n\n"
        "Experience:\nBusiness Analyst at Corporate Finance Partners (2019 - Present)\n"
        "- Created quarterly KPI dashboards in Power BI and automated monthly Excel reports.\n"
        "- Collaborated with engineering teams using SQL to extract customer purchase data.\n\n"
        "Education:\nB.A. in Economics & Finance",
    ),
    (
        "Data Analyst",
        "Jessica Lee - Product Data Analyst\n\n"
        "Summary:\nData analyst specializing in product analytics, funnel optimization, and user segmentation.\n\n"
        "Skills:\nSQL, Tableau, Excel, Python, A/B Testing, Google Analytics, Data Visualization, Statistical Analysis.\n\n"
        "Experience:\nProduct Analyst at SaaS Growth (2021 - Present)\n"
        "- Analyzed user conversion funnels and designed A/B tests using Python and SQL.\n"
        "- Built interactive Tableau dashboards for product managers.\n\n"
        "Education:\nB.S. Mathematics",
    ),
    (
        "Business Analyst",
        "Daniel Evans - Business Intelligence Analyst\n\n"
        "Summary:\nAnalytical professional with expertise in SQL reporting, Data Warehousing, and business intelligence reporting.\n\n"
        "Skills:\nSQL, Power BI, Tableau, Excel, Data Warehousing, Snowflake, Business Analysis, ETL.\n\n"
        "Experience:\nBI Analyst at OmniRetail (2020 - Present)\n"
        "- Built enterprise reporting models connecting Snowflake and Power BI.\n"
        "- Optimized SQL queries for automated daily executive dashboards.\n\n"
        "Education:\nB.S. Information Systems",
    ),
    (
        "Data Analyst",
        "Hannah Scott - Quantitative Data Analyst\n\n"
        "Summary:\nQuantitative analyst skilled in statistical modeling, SQL query extraction, and spreadsheet automation.\n\n"
        "Skills:\nSQL, Excel, Tableau, Statistical Analysis, Python, R, Data Analytics, Data Visualization.\n\n"
        "Experience:\nData Analyst at MarketInsight (2021 - Present)\n"
        "- Performed regression analysis and statistical hypothesis testing on survey data.\n"
        "- Automated client reports using Excel macros and SQL scripts.\n\n"
        "Education:\nB.S. Applied Statistics",
    ),
    (
        "Business Analyst",
        "Christopher Hall - Operations & Data Analyst\n\n"
        "Summary:\nOperations analyst improving logistical efficiencies through SQL querying and Excel dashboarding.\n\n"
        "Skills:\nSQL, Excel, Power BI, Tableau, Process Optimization, Data Visualization, Business Analysis.\n\n"
        "Experience:\nOperations Analyst at Global Logistics (2022 - Present)\n"
        "- Monitored delivery metrics and shipment KPIs using Power BI.\n"
        "- Analyzed warehouse throughput data using SQL.\n\n"
        "Education:\nB.S. Industrial Engineering",
    ),
    (
        "Data Analyst",
        "Olivia Green - Marketing Data Analyst\n\n"
        "Summary:\nMarketing analyst measuring campaign ROI, user acquisition channels, and cohort retention.\n\n"
        "Skills:\nSQL, Tableau, Excel, Google Analytics, Python, Data Visualization, A/B Testing.\n\n"
        "Experience:\nMarketing Analyst at AdTech Agency (2021 - Present)\n"
        "- Built cross-channel marketing dashboards in Tableau.\n"
        "- Evaluated campaign effectiveness using SQL and A/B test methodologies.\n\n"
        "Education:\nB.A. Marketing Analytics",
    ),
    (
        "Business Analyst",
        "Andrew Young - Data & Reporting Analyst\n\n"
        "Summary:\nSpecialist in financial reporting, SQL databases, and executive presentation preparation.\n\n"
        "Skills:\nSQL, Excel, Tableau, Power BI, Data Analytics, KPI Management, Business Analysis.\n\n"
        "Experience:\nReporting Analyst at HealthFirst (2020 - Present)\n"
        "- Standardized hospital performance reporting across 12 facilities.\n"
        "- Maintained SQL views and automated reporting delivery schedules.\n\n"
        "Education:\nB.S. Health Informatics",
    ),
    (
        "Data Analyst",
        "Sophia King - Junior Data Analyst\n\n"
        "Summary:\nJunior analyst with solid SQL querying skills and hands-on dashboard design experience.\n\n"
        "Skills:\nSQL, Excel, Tableau, Power BI, Data Visualization, Python.\n\n"
        "Experience:\nJunior Analyst at DataSphere (2023 - Present)\n"
        "- Wrote SQL queries to extract raw data and built Tableau charts.\n\n"
        "Education:\nB.S. Data Science",
    ),
    (
        "Business Analyst",
        "Matthew Wright - Senior BI & Data Analyst\n\n"
        "Summary:\nAnalytical leader delivering corporate intelligence systems using SQL, Snowflake, and Tableau.\n\n"
        "Skills:\nSQL, Tableau, Snowflake, Excel, Data Warehousing, Power BI, Business Analysis.\n\n"
        "Experience:\nLead BI Developer at Apex Group (2019 - Present)\n"
        "- Implemented central analytics warehouse and customer reporting suites.\n\n"
        "Education:\nM.S. Business Analytics",
    ),

    # --- ML Engineer / Data Science (10 resumes) ---
    (
        "Data Science",
        "Dr. Nathan Cole - Senior Machine Learning Engineer\n\n"
        "Summary:\nPh.D. in Computer Science with 6+ years building production deep learning, natural language processing, and computer vision systems.\n\n"
        "Skills:\nMachine Learning, Deep Learning, PyTorch, TensorFlow, Python, scikit-learn, Pandas, NumPy, NLP, Docker, MLOps, MLflow.\n\n"
        "Experience:\nStaff ML Engineer at DeepVision Labs (2020 - Present)\n"
        "- Architected Transformer-based NLP models and deployed inference microservices using FastAPI and Docker.\n"
        "- Trained convolutional vision backbones using PyTorch across multi-GPU clusters.\n"
        "- Established MLOps experiment tracking and model registry using MLflow.\n\n"
        "Education:\nPh.D. in Computer Science, Stanford University",
    ),
    (
        "ML Engineer",
        "Priya Patel - Machine Learning Engineer\n\n"
        "Summary:\nML engineer specializing in predictive modeling, feature engineering, and scalable model serving.\n\n"
        "Skills:\nPython, PyTorch, scikit-learn, Deep Learning, Machine Learning, Docker, FastAPI, XGBoost, Pandas, NumPy, MLflow.\n\n"
        "Experience:\nMachine Learning Engineer at PredictiveAI (2021 - Present)\n"
        "- Built tabular fraud detection models with scikit-learn and XGBoost.\n"
        "- Containerized inference services using Docker and tracked experiments with MLflow.\n\n"
        "Education:\nM.S. in Machine Learning",
    ),
    (
        "Data Science",
        "Lucas Bennett - Data Scientist & ML Practitioner\n\n"
        "Summary:\nApplied Data Scientist experienced in predictive machine learning, statistical inference, and deep neural nets.\n\n"
        "Skills:\nMachine Learning, Python, PyTorch, scikit-learn, TensorFlow, Deep Learning, NLP, Pandas, Docker.\n\n"
        "Experience:\nData Scientist at NeuroTech (2020 - Present)\n"
        "- Developed classification and clustering algorithms using scikit-learn and PyTorch.\n"
        "- Fine-tuned language models with Hugging Face transformers for document summarization.\n\n"
        "Education:\nM.S. Data Science",
    ),
    (
        "ML Engineer",
        "Elena Morozova - Computer Vision & ML Engineer\n\n"
        "Summary:\nSpecialist in deep learning, image segmentation, object detection, and edge deployment.\n\n"
        "Skills:\nComputer Vision, PyTorch, Deep Learning, OpenCV, Python, Docker, Machine Learning, TensorFlow.\n\n"
        "Experience:\nComputer Vision Engineer at AutoDrive Systems (2021 - Present)\n"
        "- Trained real-time object detection models with PyTorch and OpenCV.\n"
        "- Containerized models for deployment on edge devices with Docker.\n\n"
        "Education:\nB.S. Electrical & Computer Engineering",
    ),
    (
        "Data Science",
        "Gabriel Santos - Applied Machine Learning Engineer\n\n"
        "Summary:\nML engineer building production recommendation engines and tabular prediction pipelines.\n\n"
        "Skills:\nPython, Machine Learning, scikit-learn, PyTorch, XGBoost, Pandas, SQL, Docker, FastAPI.\n\n"
        "Experience:\nApplied ML Engineer at StreamMedia (2022 - Present)\n"
        "- Engineered collaborative filtering models serving personalized recommendations.\n"
        "- Deployed low-latency inference endpoints with FastAPI.\n\n"
        "Education:\nB.S. Computer Science",
    ),
    (
        "ML Engineer",
        "Aiden Hughes - NLP & LLM Engineer\n\n"
        "Summary:\nMachine learning engineer focused on natural language processing, transformers, and large language models.\n\n"
        "Skills:\nNatural Language Processing, PyTorch, Python, Deep Learning, Hugging Face, Transformers, Docker, MLOps.\n\n"
        "Experience:\nNLP Engineer at Conversational AI Corp (2022 - Present)\n"
        "- Fine-tuned LLMs on domain-specific datasets and evaluated hallucination rates.\n"
        "- Implemented vector retrieval augmentation using PyTorch.\n\n"
        "Education:\nM.S. Artificial Intelligence",
    ),
    (
        "Data Science",
        "Chloe Ward - Data Scientist\n\n"
        "Summary:\nData scientist with proven background in statistical machine learning, exploratory analysis, and deep neural networks.\n\n"
        "Skills:\nMachine Learning, Python, scikit-learn, PyTorch, Pandas, NumPy, Deep Learning, SQL, Git.\n\n"
        "Experience:\nData Scientist at BioAnalytics (2021 - Present)\n"
        "- Trained predictive biomarker models with scikit-learn and PyTorch.\n\n"
        "Education:\nB.S. Bioinformatics",
    ),
    (
        "ML Engineer",
        "Victor Ramos - MLOps & Machine Learning Engineer\n\n"
        "Summary:\nEngineer bridging the gap between ML research code and automated production deployment pipelines.\n\n"
        "Skills:\nMLOps, Machine Learning, Python, Docker, Kubernetes, PyTorch, MLflow, CI/CD, Linux.\n\n"
        "Experience:\nMLOps Engineer at CloudAI (2020 - Present)\n"
        "- Automated training and continuous evaluation pipelines using MLflow and Docker.\n"
        "- Managed Kubernetes clusters for distributed model inference.\n\n"
        "Education:\nB.S. Software Engineering",
    ),
    (
        "Data Science",
        "Isabella Rossi - AI Research & ML Engineer\n\n"
        "Summary:\nResearch engineer experienced in deep learning architectures, PyTorch, and generative modeling.\n\n"
        "Skills:\nDeep Learning, PyTorch, Python, Machine Learning, TensorFlow, Pandas, NumPy, OpenCV.\n\n"
        "Experience:\nAI Researcher at NextGen Labs (2021 - Present)\n"
        "- Developed generative diffusion models for image synthesis in PyTorch.\n\n"
        "Education:\nM.S. Computer Science",
    ),
    (
        "ML Engineer",
        "Samuel Price - Junior Machine Learning Engineer\n\n"
        "Summary:\nJunior ML practitioner with strong Python, mathematical foundations, and model development skills.\n\n"
        "Skills:\nPython, PyTorch, scikit-learn, Machine Learning, Pandas, NumPy, Git, Docker.\n\n"
        "Experience:\nJunior ML Engineer at SmartData (2023 - Present)\n"
        "- Built baseline classification models and feature extraction pipelines with scikit-learn.\n\n"
        "Education:\nB.S. Data Science",
    ),

    # --- Frontend Developer / Web Designing (10 resumes) ---
    (
        "Web Designing",
        "Samantha Bell - Senior Frontend React Developer\n\n"
        "Summary:\nFrontend developer with 6+ years creating intuitive, responsive web applications using React, TypeScript, and Next.js.\n\n"
        "Skills:\nReact, TypeScript, JavaScript, Next.js, HTML5, CSS3, Tailwind CSS, Redux, Figma, Webpack, Git.\n\n"
        "Experience:\nSenior Frontend Engineer at CreativeWeb Studio (2020 - Present)\n"
        "- Built high-performance single page web applications using React and Next.js.\n"
        "- Styled components using Tailwind CSS and translated Figma designs into accessible code.\n"
        "- Implemented complex application state with Redux Toolkit.\n\n"
        "Education:\nB.A. in Interactive Media & Web Design",
    ),
    (
        "Frontend Developer",
        "Tyler Reed - Frontend Engineer\n\n"
        "Summary:\nUI engineer focused on React component architecture, TypeScript typing, and frontend performance optimization.\n\n"
        "Skills:\nReact, TypeScript, Next.js, JavaScript, HTML5, CSS3, Tailwind CSS, Redux, REST API, Git.\n\n"
        "Experience:\nFrontend Developer at CloudInterface (2021 - Present)\n"
        "- Built responsive customer dashboards with React and TypeScript.\n"
        "- Utilized Next.js for server-side rendering to enhance SEO and initial page loads.\n\n"
        "Education:\nB.S. in Computer Science",
    ),
    (
        "Web Designing",
        "Emma Watson - UI / Frontend Developer\n\n"
        "Summary:\nFront-end specialist with a passion for clean UI design systems, micro-interactions, and modern CSS.\n\n"
        "Skills:\nHTML5, CSS3, JavaScript, React, Figma, Tailwind CSS, Sass, UI Design, Responsive Web Design, Git.\n\n"
        "Experience:\nUI Developer at DesignCraft (2019 - Present)\n"
        "- Created modular component libraries in React following design systems in Figma.\n"
        "- Implemented responsive layouts with HTML5 and CSS3.\n\n"
        "Education:\nB.F.A. in Digital Arts",
    ),
    (
        "Frontend Developer",
        "Jordan Bailey - React / Next.js Engineer\n\n"
        "Summary:\nSoftware engineer specializing in modern React ecosystem, Next.js App Router, and TypeScript.\n\n"
        "Skills:\nReact, Next.js, TypeScript, JavaScript, Redux, Tailwind CSS, HTML5, CSS3, Webpack.\n\n"
        "Experience:\nFrontend Engineer at ScaleApp (2022 - Present)\n"
        "- Led migration from legacy SPA to Next.js App Router with React and TypeScript.\n"
        "- Integrated REST APIs and optimized web vital metrics.\n\n"
        "Education:\nB.S. Software Engineering",
    ),
    (
        "Web Designing",
        "Morgan Diaz - Web Developer & Designer\n\n"
        "Summary:\nWeb designer and developer delivering accessible, cross-browser web interfaces.\n\n"
        "Skills:\nJavaScript, React, HTML5, CSS3, Figma, Tailwind CSS, Git, Sass, UI/UX Design.\n\n"
        "Experience:\nWeb Developer at Studio7 (2021 - Present)\n"
        "- Designed mockups in Figma and coded frontend interfaces using React and Tailwind.\n\n"
        "Education:\nB.S. Web Development",
    ),
    (
        "Frontend Developer",
        "Caleb Foster - Client-Side Software Engineer\n\n"
        "Summary:\nFrontend developer with strong expertise in TypeScript, React, and state management.\n\n"
        "Skills:\nReact, TypeScript, Redux, JavaScript, HTML5, CSS3, Webpack, Git, REST API.\n\n"
        "Experience:\nFrontend Developer at FintechPortal (2020 - Present)\n"
        "- Developed trading dashboards using React, Redux, and TypeScript.\n\n"
        "Education:\nB.S. Computer Science",
    ),
    (
        "Web Designing",
        "Kayla Ortiz - Frontend UI Specialist\n\n"
        "Summary:\nFrontend engineer building clean web applications with React, Next.js, and CSS modules.\n\n"
        "Skills:\nReact, Next.js, TypeScript, HTML5, CSS3, Tailwind CSS, Figma, Git.\n\n"
        "Experience:\nUI Engineer at AppWorks (2021 - Present)\n"
        "- Built interactive marketing websites and customer dashboards.\n\n"
        "Education:\nB.A. Graphic & Web Design",
    ),
    (
        "Frontend Developer",
        "Justin Cooper - Junior Frontend Developer\n\n"
        "Summary:\nJunior developer with solid grounding in React, JavaScript, HTML5, and CSS3.\n\n"
        "Skills:\nJavaScript, React, HTML5, CSS3, Tailwind CSS, Git, TypeScript.\n\n"
        "Experience:\nJunior Web Developer at Launchpad Labs (2023 - Present)\n"
        "- Assisted in building responsive web components with React.\n\n"
        "Education:\nB.S. Information Technology",
    ),
    (
        "Web Designing",
        "Brooke Campbell - Design Systems & React Developer\n\n"
        "Summary:\nSpecialist in scalable web design systems, Tailwind CSS, and React component libraries.\n\n"
        "Skills:\nReact, Tailwind CSS, Figma, TypeScript, HTML5, CSS3, Design Systems, Git.\n\n"
        "Experience:\nFrontend Developer at DesignScale (2020 - Present)\n"
        "- Maintained unified design system across 4 enterprise applications in React.\n\n"
        "Education:\nB.S. Digital Media",
    ),
    (
        "Frontend Developer",
        "Trevor Walsh - React & TypeScript Developer\n\n"
        "Summary:\n4 years building customer-facing web applications with React and Next.js.\n\n"
        "Skills:\nReact, TypeScript, Next.js, JavaScript, Redux, HTML5, CSS3, Git.\n\n"
        "Experience:\nFrontend Software Engineer at MediaPortal (2021 - Present)\n"
        "- Implemented interactive video playback UI with React and TypeScript.\n\n"
        "Education:\nB.S. Computer Science",
    ),

    # --- DevOps Engineer / DevOps (10 resumes) ---
    (
        "DevOps",
        "Robert Garcia - Senior DevOps Engineer\n\n"
        "Summary:\nDevOps and Infrastructure Engineer with 7+ years automating CI/CD pipelines, orchestrating Kubernetes clusters, and managing AWS cloud infrastructure.\n\n"
        "Skills:\nKubernetes, Docker, CI/CD, Linux, AWS, Amazon Web Services, Terraform, Ansible, Prometheus, Git, Bash.\n\n"
        "Experience:\nLead DevOps Engineer at CloudSphere (2019 - Present)\n"
        "- Managed production Kubernetes clusters running 200+ microservices on AWS.\n"
        "- Automated infrastructure deployment using Terraform and Ansible.\n"
        "- Built CI/CD automated deployment pipelines reducing build times by 60%.\n\n"
        "Education:\nB.S. in Computer Engineering",
    ),
    (
        "DevOps Engineer",
        "Amber Lewis - Site Reliability & DevOps Engineer\n\n"
        "Summary:\nSRE / DevOps engineer ensuring 99.99% system availability through automated monitoring, containerization, and IaC.\n\n"
        "Skills:\nKubernetes, Docker, Linux, CI/CD, Terraform, Amazon Web Services, Prometheus, Grafana, Git, Python.\n\n"
        "Experience:\nDevOps Engineer at InfraScale (2021 - Present)\n"
        "- Provisioned cloud resources on AWS using Terraform.\n"
        "- Configured Prometheus and Grafana alerts for Kubernetes microservices.\n\n"
        "Education:\nB.S. Information Systems",
    ),
    (
        "DevOps",
        "Sean Murphy - Cloud & DevOps Specialist\n\n"
        "Summary:\nCloud infrastructure engineer experienced with Docker containerization, Kubernetes orchestration, and continuous integration.\n\n"
        "Skills:\nDocker, Kubernetes, CI/CD, Amazon Web Services, Linux, Bash, Terraform, Git, Jenkins.\n\n"
        "Experience:\nCloud Engineer at EnterpriseNet (2020 - Present)\n"
        "- Maintained Jenkins and GitHub Actions pipelines for automated testing.\n"
        "- Deployed scalable container clusters on AWS with Kubernetes.\n\n"
        "Education:\nB.S. Computer Science",
    ),
    (
        "DevOps Engineer",
        "Danielle Jenkins - DevOps Automation Engineer\n\n"
        "Summary:\nAutomation engineer focused on infrastructure-as-code, Linux server hardening, and container management.\n\n"
        "Skills:\nKubernetes, Docker, Linux, CI/CD, Ansible, Terraform, Git, Bash, AWS.\n\n"
        "Experience:\nDevOps Engineer at SaaSPlatform (2021 - Present)\n"
        "- Wrote Ansible playbooks for automated server provisioning and patching.\n"
        "- Maintained Kubernetes staging and production environments.\n\n"
        "Education:\nB.S. Software Engineering",
    ),
    (
        "DevOps",
        "Kyle Simmons - Platform & Infrastructure Engineer\n\n"
        "Summary:\nInfrastructure specialist experienced in multi-region cloud deployments on AWS and container security.\n\n"
        "Skills:\nKubernetes, Docker, AWS, Linux, CI/CD, Prometheus, Terraform, Git, Cloud Security.\n\n"
        "Experience:\nPlatform Engineer at DataCloud (2020 - Present)\n"
        "- Architected multi-region Kubernetes deployments on AWS using Terraform.\n\n"
        "Education:\nB.S. Computer Systems",
    ),
    (
        "DevOps Engineer",
        "Melissa Cox - DevOps & Release Engineer\n\n"
        "Summary:\nRelease engineer automating deployment workflows and managing containerized services.\n\n"
        "Skills:\nDocker, CI/CD, Kubernetes, Linux, Git, Jenkins, AWS, Bash.\n\n"
        "Experience:\nRelease Engineer at AppCorp (2022 - Present)\n"
        "- Maintained automated CI/CD release pipelines and container builds.\n\n"
        "Education:\nB.S. Information Technology",
    ),
    (
        "DevOps",
        "Brandon Howard - Kubernetes & Cloud Engineer\n\n"
        "Summary:\nKubernetes administrator with deep expertise in cloud networking, Linux administration, and Helm packaging.\n\n"
        "Skills:\nKubernetes, Docker, Linux, Helm, Amazon Web Services, CI/CD, Terraform, Prometheus.\n\n"
        "Experience:\nDevOps Engineer at ScaleOps (2019 - Present)\n"
        "- Managed 50+ Kubernetes namespaces and automated Helm deployments.\n\n"
        "Education:\nB.S. Network Engineering",
    ),
    (
        "DevOps Engineer",
        "Angela Ross - Cloud Infrastructure Engineer\n\n"
        "Summary:\nSpecialist in automated cloud provisioning, Linux systems, and Docker orchestration.\n\n"
        "Skills:\nKubernetes, Docker, Linux, AWS, CI/CD, Terraform, Git, Bash.\n\n"
        "Experience:\nInfrastructure Engineer at FinOps (2021 - Present)\n"
        "- Provisioned cloud resources using Terraform and maintained Docker workloads.\n\n"
        "Education:\nB.S. Computer Science",
    ),
    (
        "DevOps",
        "Eric Griffin - Junior DevOps Engineer\n\n"
        "Summary:\nJunior DevOps engineer with solid skills in Linux, Docker containerization, and Git version control.\n\n"
        "Skills:\nDocker, Linux, Git, CI/CD, Bash, Kubernetes, Python.\n\n"
        "Experience:\nJunior DevOps Engineer at StartupOps (2023 - Present)\n"
        "- Maintained GitHub Actions runners and wrote Bash automation scripts.\n\n"
        "Education:\nB.S. Information Systems",
    ),
    (
        "DevOps Engineer",
        "Heather Ward - Senior Systems & DevOps Engineer\n\n"
        "Summary:\nSenior engineer with 8 years managing mission-critical Linux servers and Kubernetes clusters.\n\n"
        "Skills:\nKubernetes, Docker, Linux, CI/CD, Terraform, Amazon Web Services, Ansible, Prometheus.\n\n"
        "Experience:\nSenior DevOps Engineer at GlobalTech (2018 - Present)\n"
        "- Led migration of legacy on-prem infrastructure to containerized Kubernetes on AWS.\n\n"
        "Education:\nB.S. Computer Engineering",
    ),

    # --- Product Manager / Operations Manager (10 resumes) ---
    (
        "Operations Manager",
        "Gregory King - Technical Product Manager\n\n"
        "Summary:\nProduct leader with 6+ years driving software roadmap strategy, agile execution, and cross-functional team delivery.\n\n"
        "Skills:\nProduct Management, Agile Methodology, Scrum, Stakeholder Management, Product Strategy, User Research, KPI Management, Communication, Business Analysis.\n\n"
        "Experience:\nSenior Product Manager at SoftwareVentures (2019 - Present)\n"
        "- Led cross-functional team of 12 engineers and designers using Agile and Scrum.\n"
        "- Defined product vision, roadmap, and quarterly KPI milestones.\n"
        "- Conducted customer user research interviews and market opportunity analysis.\n\n"
        "Education:\nMBA, Business School; B.S. Engineering",
    ),
    (
        "Product Manager",
        "Victoria Gray - Product Manager\n\n"
        "Summary:\nProduct manager focused on B2B SaaS growth, sprint backlog prioritization, and feature discovery.\n\n"
        "Skills:\nProduct Management, Agile Methodology, Scrum, Stakeholder Management, User Research, Roadmapping, Product Strategy, KPI Management.\n\n"
        "Experience:\nProduct Manager at SaaSWorks (2021 - Present)\n"
        "- Managed end-to-end product lifecycle from discovery through release.\n"
        "- Partnered with UX researchers and data analysts to evaluate feature adoption.\n\n"
        "Education:\nB.A. in Management Information Systems",
    ),
    (
        "Operations Manager",
        "Craig Peterson - Agile Product Owner & Operations Manager\n\n"
        "Summary:\nCertified Scrum Product Owner aligning business priorities with technical execution.\n\n"
        "Skills:\nAgile Methodology, Scrum, Product Management, Stakeholder Management, Business Analysis, Process Optimization, Communication.\n\n"
        "Experience:\nProduct Owner at EnterpriseSolutions (2020 - Present)\n"
        "- Maintained sprint backlogs, wrote user stories, and led sprint planning sessions.\n"
        "- Facilitated communication between executive stakeholders and engineering teams.\n\n"
        "Education:\nB.S. Business Administration",
    ),
    (
        "Product Manager",
        "Diana Price - Senior Digital Product Manager\n\n"
        "Summary:\nProduct strategist launching consumer mobile and web applications with data-informed iteration.\n\n"
        "Skills:\nProduct Management, Product Strategy, Agile Methodology, Scrum, Stakeholder Management, KPI Management, User Research.\n\n"
        "Experience:\nSenior PM at ConsumerApps (2019 - Present)\n"
        "- Defined feature specifications and KPIs for consumer product releases.\n"
        "- Collaborated with engineering leads to ensure agile delivery.\n\n"
        "Education:\nB.S. Human-Computer Interaction",
    ),
    (
        "Operations Manager",
        "Bradley Watson - Operations & Technical Project Manager\n\n"
        "Summary:\nOperations manager skilled in agile delivery frameworks, operational workflows, and stakeholder communication.\n\n"
        "Skills:\nAgile Methodology, Scrum, Project Management, Stakeholder Management, KPI Management, Communication, Business Analysis.\n\n"
        "Experience:\nOperations Project Manager at OmniCorp (2020 - Present)\n"
        "- Managed project delivery timelines across multi-disciplinary teams.\n\n"
        "Education:\nB.S. Industrial Management",
    ),
    (
        "Product Manager",
        "Kelly Sanders - Associate Product Manager\n\n"
        "Summary:\nProduct manager with strong user research, analytical, and agile sprint coordination abilities.\n\n"
        "Skills:\nProduct Management, Agile Methodology, Scrum, User Research, Communication, Stakeholder Management, SQL.\n\n"
        "Experience:\nAssociate PM at TechStart (2022 - Present)\n"
        "- Conducted customer feedback surveys and user interview sessions.\n"
        "- Created user stories and tracked sprint progress in Jira.\n\n"
        "Education:\nB.A. Economics",
    ),
    (
        "Operations Manager",
        "Douglas Barnes - Technical Program & Product Manager\n\n"
        "Summary:\nProgram manager aligning product roadmaps with corporate strategic objectives.\n\n"
        "Skills:\nProduct Management, Agile Methodology, Scrum, Stakeholder Management, Product Strategy, KPI Management, Communication.\n\n"
        "Experience:\nTechnical Program Manager at ScaleTech (2018 - Present)\n"
        "- Coordinated engineering delivery schedules for 3 major product lines.\n\n"
        "Education:\nM.S. Technology Management",
    ),
    (
        "Product Manager",
        "Natalie Brooks - Growth Product Manager\n\n"
        "Summary:\nGrowth-focused product manager optimizing conversion funnels and user onboarding flows.\n\n"
        "Skills:\nProduct Management, Agile Methodology, Scrum, KPI Management, A/B Testing, User Research, Stakeholder Management.\n\n"
        "Experience:\nGrowth PM at WebMedia (2021 - Present)\n"
        "- Led experimental growth initiatives that improved activation rates by 22%.\n\n"
        "Education:\nB.S. Business & Computer Science",
    ),
    (
        "Operations Manager",
        "Russell Henderson - Operations & Delivery Manager\n\n"
        "Summary:\nOperations lead optimizing organizational workflows, cross-departmental delivery, and operational KPIs.\n\n"
        "Skills:\nAgile Methodology, Scrum, Stakeholder Management, Communication, KPI Management, Business Analysis.\n\n"
        "Experience:\nOperations Lead at HealthOps (2020 - Present)\n"
        "- Streamlined cross-departmental workflows and project tracking.\n\n"
        "Education:\nB.S. Operations Management",
    ),
    (
        "Product Manager",
        "Courtney James - Product Manager\n\n"
        "Summary:\nProduct professional with proven track record translating market needs into software roadmaps.\n\n"
        "Skills:\nProduct Management, Agile Methodology, Scrum, Stakeholder Management, Product Strategy, Communication, User Research.\n\n"
        "Experience:\nProduct Manager at AppSphere (2021 - Present)\n"
        "- Authored product requirement documents and managed sprint priorities.\n\n"
        "Education:\nB.A. Business Administration",
    ),
]


def main():
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["category", "resume_text"])
        for cat, text in RESUMES_DATA:
            writer.writerow([cat, text])
    print(f"Generated {len(RESUMES_DATA)} resumes across 6 categories in: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
