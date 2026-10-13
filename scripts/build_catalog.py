"""Build the technology and skills catalog (700+ entries) and synchronize with skills taxonomy.

Categories (in exact required order):
1. languages
2. hosting_cloud
3. frameworks_libraries
4. servers_runtime
5. databases_orm
6. design_tools
7. ml_dl_data
8. cicd_vcs
9. testing
10. data_bi_analytics
11. mobile
12. security_networking
13. os_systems
14. other_tools
15. soft_skills

Ensures:
- No duplicate IDs.
- Every alias is globally unique across the entire catalog and does not clash with any skill ID.
- Every taxonomy_id resolves to a valid key in data/processed/skills.json.
- Rebuilds skill embeddings and taxonomy if new skills are introduced.
"""

from __future__ import annotations

import json
import logging
import random
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

# Path configuration
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import settings
from ml.taxonomy import is_ambiguous_skill, normalize_skill_name

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

CATALOG_FILE = settings.DATA_DIR / "processed" / "tech_catalog.json"

# Exact category list in order
CATEGORIES = [
    {"id": "languages", "name": "Languages"},
    {"id": "hosting_cloud", "name": "Hosting, SaaS & Cloud"},
    {"id": "frameworks_libraries", "name": "Frameworks, Platforms & Libraries"},
    {"id": "servers_runtime", "name": "Servers & Runtime"},
    {"id": "databases_orm", "name": "Databases & ORM"},
    {"id": "design_tools", "name": "Design Tools"},
    {"id": "ml_dl_data", "name": "Machine Learning, Deep Learning & Data"},
    {"id": "cicd_vcs", "name": "CI/CD & Version Control"},
    {"id": "testing", "name": "Testing & QA"},
    {"id": "data_bi_analytics", "name": "Data, BI & Analytics"},
    {"id": "mobile", "name": "Mobile Development"},
    {"id": "security_networking", "name": "Security & Networking"},
    {"id": "os_systems", "name": "Operating Systems & Systems"},
    {"id": "other_tools", "name": "Other Tools & Utilities"},
    {"id": "soft_skills", "name": "Soft Skills & Professional Practices"},
]

# Raw seed items for each category: (id, name, [aliases])
RAW_CATALOG_DATA: Dict[str, List[Tuple[str, str, List[str]]]] = {
    "languages": [
        ("python", "Python", ["py", "python3", "python2"]),
        ("javascript", "JavaScript", ["js", "ecmascript"]),
        ("typescript", "TypeScript", ["ts"]),
        ("java", "Java", ["java17", "java21", "java8", "java11"]),
        ("c++", "C++", ["cpp", "cplusplus"]),
        ("c", "C", ["clang", "ansi c"]),
        ("c#", "C#", ["csharp", "dotnet c#"]),
        ("rust", "Rust", ["rustlang"]),
        ("go", "Go", ["golang"]),
        ("kotlin", "Kotlin", ["kt"]),
        ("swift", "Swift", ["swiftlang"]),
        ("ruby", "Ruby", ["ruby on rails language"]),
        ("php", "PHP", ["php8", "php7"]),
        ("sql", "SQL", ["structured query language", "ansi sql"]),
        ("html", "HTML", ["html5"]),
        ("css", "CSS", ["css3"]),
        ("r", "R", ["rlang"]),
        ("scala", "Scala", []),
        ("dart", "Dart", ["dartlang"]),
        ("shell", "Shell Scripting", ["bash script", "sh script"]),
        ("bash", "Bash", ["bourne again shell"]),
        ("powershell", "PowerShell", ["pwsh", "posh"]),
        ("perl", "Perl", ["perl5"]),
        ("haskell", "Haskell", []),
        ("elixir", "Elixir", ["elixirlang"]),
        ("erlang", "Erlang", []),
        ("clojure", "Clojure", []),
        ("lua", "Lua", []),
        ("julia", "Julia", ["julialang"]),
        ("groovy", "Groovy", []),
        ("f#", "F#", ["fsharp"]),
        ("ocaml", "OCaml", []),
        ("matlab", "MATLAB", []),
        ("solidity", "Solidity", []),
        ("assembly", "Assembly", ["asm", "x86 asm", "arm asm"]),
        ("fortran", "Fortran", []),
        ("cobol", "COBOL", []),
        ("visual_basic", "Visual Basic .NET", ["vb.net", "vba"]),
        ("apex", "Apex", ["salesforce apex"]),
        ("objective_c", "Objective-C", ["obj-c", "objc"]),
        ("plsql", "PL/SQL", ["oracle plsql"]),
        ("tsql", "T-SQL", ["transact-sql"]),
        ("sas", "SAS", ["sas programming"]),
        ("racket", "Racket", []),
        ("scheme", "Scheme", []),
        ("common_lisp", "Common Lisp", ["lisp"]),
        ("elm", "Elm", []),
        ("purescript", "PureScript", []),
        ("coffeescript", "CoffeeScript", []),
        ("crystal", "Crystal", ["crystallang"]),
        ("d_lang", "D", ["dlang"]),
        ("actionscript", "ActionScript", ["as3"]),
        ("hack", "Hack", ["hhvm hack"]),
        ("abap", "ABAP", ["sap abap"]),
        ("ada", "Ada", []),
        ("pascal", "Pascal", ["delphi pascal"]),
        ("delphi", "Delphi", []),
        ("scratch", "Scratch", []),
        ("vhdl", "VHDL", []),
        ("verilog", "Verilog", ["systemverilog"]),
        ("zig", "Zig", ["ziglang"]),
        ("nim", "Nim", ["nimlang"]),
        ("v_lang", "V", ["vlang"]),
        ("vyper", "Vyper", []),
        ("hcl", "HCL", ["hashicorp configuration language"]),
    ],
    "hosting_cloud": [
        ("aws", "Amazon Web Services", ["amazon aws"]),
        ("azure", "Microsoft Azure", ["ms azure"]),
        ("gcp", "Google Cloud Platform", ["google cloud", "gcloud"]),
        ("vercel", "Vercel", ["zeit"]),
        ("netlify", "Netlify", []),
        ("render", "Render", ["render.com"]),
        ("heroku", "Heroku", []),
        ("digitalocean", "DigitalOcean", ["digital ocean", "do droplets"]),
        ("cloudflare", "Cloudflare", []),
        ("linode", "Linode", ["akamai linode"]),
        ("fly_io", "Fly.io", ["flyio"]),
        ("railway", "Railway", ["railway.app"]),
        ("supabase", "Supabase", []),
        ("firebase", "Firebase", ["google firebase"]),
        ("oracle_cloud", "Oracle Cloud Infrastructure", ["oci"]),
        ("ibm_cloud", "IBM Cloud", []),
        ("alibaba_cloud", "Alibaba Cloud", ["aliyun"]),
        ("hetzner", "Hetzner", ["hetzner cloud"]),
        ("ovhcloud", "OVHcloud", ["ovh"]),
        ("scaleway", "Scaleway", []),
        ("aws_ec2", "AWS EC2", ["elastic compute cloud", "ec2"]),
        ("aws_s3", "AWS S3", ["simple storage service", "s3 bucket"]),
        ("aws_lambda", "AWS Lambda", ["lambda serverless"]),
        ("aws_ecs", "AWS ECS", ["elastic container service"]),
        ("aws_eks", "AWS EKS", ["elastic kubernetes service"]),
        ("aws_cloudfront", "AWS CloudFront", ["cloudfront cdn"]),
        ("aws_rds", "AWS RDS", ["relational database service"]),
        ("aws_dynamodb", "AWS DynamoDB", ["dynamodb service"]),
        ("aws_iam", "AWS IAM", ["identity and access management"]),
        ("aws_cloudwatch", "AWS CloudWatch", ["cloudwatch logs"]),
        ("aws_sns", "AWS SNS", ["simple notification service"]),
        ("aws_sqs", "AWS SQS", ["simple queue service"]),
        ("aws_route53", "AWS Route 53", ["route53 dns"]),
        ("azure_app_service", "Azure App Service", []),
        ("azure_functions", "Azure Functions", []),
        ("azure_blob_storage", "Azure Blob Storage", ["azure blob"]),
        ("azure_devops", "Azure DevOps", ["vsts", "azure pipelines"]),
        ("azure_vms", "Azure Virtual Machines", ["azure vm"]),
        ("gcp_compute_engine", "Google Compute Engine", ["gce"]),
        ("gcp_cloud_run", "Google Cloud Run", ["cloud run"]),
        ("gcp_cloud_functions", "Google Cloud Functions", ["gcf"]),
        ("gcp_gke", "Google Kubernetes Engine", ["gke"]),
        ("gcp_bigquery", "Google BigQuery Cloud", []),
        ("cloudflare_workers", "Cloudflare Workers", []),
        ("cloudflare_pages", "Cloudflare Pages", []),
        ("backblaze_b2", "Backblaze B2", ["b2 cloud storage"]),
        ("wasabi", "Wasabi Hot Cloud Storage", []),
        ("upcloud", "UpCloud", []),
        ("pythonanywhere", "PythonAnywhere", []),
        ("glitch", "Glitch", ["glitch.com"]),
        ("replit", "Replit", ["repl.it"]),
        ("planetscale", "PlanetScale", []),
        ("neon_db", "Neon Serverless Postgres", ["neon.tech"]),
        ("faunadb", "FaunaDB", ["fauna"]),
        ("datadog_cloud", "Datadog Cloud Monitoring", []),
        ("new_relic", "New Relic", []),
        ("fastly", "Fastly", ["fastly cdn"]),
    ],
    "frameworks_libraries": [
        ("react", "React", ["reactjs", "react.js"]),
        ("nextjs", "Next.js", ["next.js", "next"]),
        ("vue", "Vue.js", ["vuejs", "vue 3", "vue 2"]),
        ("nuxtjs", "Nuxt.js", ["nuxt", "nuxt.js"]),
        ("angular", "Angular", ["angularjs", "angular 2+"]),
        ("svelte", "Svelte", ["sveltejs"]),
        ("sveltekit", "SvelteKit", []),
        ("django", "Django", ["django framework"]),
        ("fastapi", "FastAPI", ["fastapi framework"]),
        ("flask", "Flask", ["flask framework"]),
        ("spring_boot", "Spring Boot", ["springboot", "spring framework"]),
        ("aspnet_core", "ASP.NET Core", ["asp.net core", ".net core web"]),
        ("express", "Express.js", ["expressjs", "express framework"]),
        ("nestjs", "NestJS", ["nest.js"]),
        ("remix", "Remix", ["remix.run"]),
        ("astro", "Astro", ["astro.build"]),
        ("gatsby", "Gatsby", ["gatsbyjs"]),
        ("solidjs", "SolidJS", ["solid.js"]),
        ("alpinejs", "Alpine.js", []),
        ("lit", "Lit", ["lit-html", "lit-element"]),
        ("ember", "Ember.js", ["emberjs"]),
        ("ruby_on_rails", "Ruby on Rails", ["rails", "ror"]),
        ("laravel", "Laravel", ["laravel framework"]),
        ("symfony", "Symfony", []),
        ("gin", "Gin", ["gin-gonic"]),
        ("echo", "Echo", ["echo web framework"]),
        ("fiber", "Fiber", ["go fiber"]),
        ("actix_web", "Actix Web", ["actix"]),
        ("axum", "Axum", ["rust axum"]),
        ("rocket", "Rocket", ["rocket.rs"]),
        ("tornado", "Tornado", ["tornado web"]),
        ("sanic", "Sanic", []),
        ("bottle", "Bottle", ["bottle.py"]),
        ("phoenix", "Phoenix", ["elixir phoenix"]),
        ("sinatra", "Sinatra", ["ruby sinatra"]),
        ("koa", "Koa", ["koajs"]),
        ("fastify", "Fastify", []),
        ("hono", "Hono", ["honojs"]),
        ("hapi", "Hapi", ["hapijs"]),
        ("quasar", "Quasar Framework", ["quasar"]),
        ("preact", "Preact", []),
        ("redux", "Redux", []),
        ("redux_toolkit", "Redux Toolkit", ["rtk"]),
        ("mobx", "MobX", []),
        ("zustand", "Zustand", []),
        ("recoil", "Recoil", []),
        ("jotai", "Jotai", []),
        ("tanstack_query", "TanStack Query", ["react query"]),
        ("swr", "SWR", ["vercel swr"]),
        ("tailwind_css", "Tailwind CSS", ["tailwindcss", "tailwind"]),
        ("bootstrap", "Bootstrap", ["bootstrap 5", "bootstrap 4"]),
        ("material_ui", "Material-UI", ["mui"]),
        ("ant_design", "Ant Design", ["antd"]),
        ("chakra_ui", "Chakra UI", []),
        ("radix_ui", "Radix UI", ["radix primitives"]),
        ("shadcn_ui", "shadcn/ui", ["shadcn"]),
        ("styled_components", "styled-components", ["styled components"]),
        ("emotion", "Emotion", ["emotion css"]),
        ("sass", "Sass", ["scss", "syntactically awesome stylesheets"]),
        ("less", "Less", ["less css"]),
        ("postcss", "PostCSS", []),
        ("jquery", "jQuery", []),
        ("lodash", "Lodash", []),
        ("rxjs", "RxJS", ["reactive extensions for javascript"]),
        ("threejs", "Three.js", ["three.js"]),
        ("d3js", "D3.js", ["d3", "data-driven documents"]),
        ("chartjs", "Chart.js", []),
        ("gsap", "GSAP", ["greensock"]),
        ("htmx", "HTMX", []),
        ("electron", "Electron", ["electronjs"]),
        ("tauri", "Tauri", ["tauriapp"]),
    ],
    "servers_runtime": [
        ("nodejs", "Node.js", ["node", "node js"]),
        ("deno", "Deno", []),
        ("bun", "Bun", ["bun runtime"]),
        ("nginx", "Nginx", ["engine x"]),
        ("apache_http", "Apache HTTP Server", ["httpd", "apache web server"]),
        ("caddy", "Caddy", ["caddy server"]),
        ("haproxy", "HAProxy", []),
        ("envoy", "Envoy Proxy", ["envoy"]),
        ("traefik", "Traefik", ["traefik proxy"]),
        ("uvicorn", "Uvicorn", []),
        ("gunicorn", "Gunicorn", ["green unicorn"]),
        ("tomcat", "Apache Tomcat", ["tomcat"]),
        ("jetty", "Eclipse Jetty", ["jetty"]),
        ("netty", "Netty", []),
        ("wildfly", "WildFly", ["jboss as"]),
        ("kestrel", "Kestrel", ["kestrel web server"]),
        ("iis", "Microsoft IIS", ["internet information services"]),
        ("asgi", "ASGI", ["asynchronous server gateway interface"]),
        ("wsgi", "WSGI", ["web server gateway interface"]),
        ("puma", "Puma", ["puma web server"]),
        ("unicorn_server", "Unicorn", ["unicorn rack server"]),
        ("thin", "Thin", ["thin ruby server"]),
        ("phusion_passenger", "Phusion Passenger", ["mod_passenger"]),
        ("openresty", "OpenResty", []),
        ("lighttpd", "Lighttpd", []),
        ("hypercorn", "Hypercorn", []),
        ("gevent", "Gevent", []),
        ("eventlet", "Eventlet", []),
        ("tokio", "Tokio", ["tokio runtime"]),
        ("libuv", "libuv", []),
        ("pm2", "PM2", ["process manager 2"]),
        ("forever", "Forever", ["forever npm"]),
        ("supervisord", "Supervisord", ["supervisor process manager"]),
        ("systemd", "Systemd", ["systemctl"]),
        ("openssl", "OpenSSL", []),
        ("kong_gateway", "Kong Gateway", ["kong api gateway"]),
        ("apache_apisix", "Apache APISIX", ["apisix"]),
        ("krakend", "KrakenD", []),
        ("istio", "Istio", ["istio service mesh"]),
        ("linkerd", "Linkerd", []),
        ("consul", "HashiCorp Consul", ["consul service mesh"]),
        ("envoy_gateway", "Envoy Gateway", []),
        ("caddy_ingress", "Caddy Ingress Controller", []),
        ("nginx_ingress", "NGINX Ingress Controller", []),
        ("coredns", "CoreDNS", []),
    ],
    "databases_orm": [
        ("postgresql", "PostgreSQL", ["postgres", "pgsql"]),
        ("mysql", "MySQL", []),
        ("mariadb", "MariaDB", []),
        ("sqlite", "SQLite", ["sqlite3"]),
        ("mssql", "Microsoft SQL Server", ["sql server", "ms sql"]),
        ("oracle_db", "Oracle Database", ["oracle rdbms"]),
        ("mongodb", "MongoDB", ["mongo", "mongodb atlas"]),
        ("redis", "Redis", ["redis cache"]),
        ("cassandra", "Apache Cassandra", ["cassandra"]),
        ("dynamodb", "DynamoDB", ["amazon dynamodb"]),
        ("elasticsearch", "Elasticsearch", ["es search"]),
        ("neo4j", "Neo4j", ["neo4j graph"]),
        ("couchdb", "Apache CouchDB", ["couchdb"]),
        ("couchbase", "Couchbase", []),
        ("cockroachdb", "CockroachDB", []),
        ("clickhouse", "ClickHouse", []),
        ("scylladb", "ScyllaDB", []),
        ("tidb", "TiDB", []),
        ("influxdb", "InfluxDB", []),
        ("timescaledb", "TimescaleDB", []),
        ("duckdb", "DuckDB", []),
        ("chroma_db", "Chroma DB", ["chromadb"]),
        ("pinecone", "Pinecone", ["pinecone vector db"]),
        ("weaviate", "Weaviate", []),
        ("milvus", "Milvus", []),
        ("qdrant", "Qdrant", []),
        ("memcached", "Memcached", []),
        ("arangodb", "ArangoDB", []),
        ("realm", "Realm Database", ["realm db"]),
        ("firestore", "Google Cloud Firestore", ["cloud firestore"]),
        ("rocksdb", "RocksDB", []),
        ("leveldb", "LevelDB", []),
        ("rethinkdb", "RethinkDB", []),
        ("ravendb", "RavenDB", []),
        ("dgraph", "Dgraph", []),
        ("orientdb", "OrientDB", []),
        ("sqlalchemy", "SQLAlchemy", []),
        ("prisma", "Prisma", ["prisma orm"]),
        ("hibernate", "Hibernate", ["hibernate orm"]),
        ("entity_framework", "Entity Framework Core", ["ef core", "entity framework"]),
        ("mongoose", "Mongoose", ["mongoose odm"]),
        ("typeorm", "TypeORM", []),
        ("drizzle_orm", "Drizzle ORM", ["drizzle"]),
        ("sequelize", "Sequelize", []),
        ("peewee", "Peewee", []),
        ("tortoise_orm", "Tortoise ORM", []),
        ("gorm", "GORM", ["go gorm"]),
        ("diesel", "Diesel", ["diesel orm"]),
        ("seaorm", "SeaORM", []),
        ("active_record", "Active Record", ["rails active record"]),
        ("django_orm", "Django ORM", []),
        ("knex", "Knex.js", ["knex"]),
        ("objection_js", "Objection.js", []),
        ("waterline", "Waterline", []),
        ("mikro_orm", "MikroORM", []),
        ("exposed_orm", "Exposed ORM", ["kotlin exposed"]),
        ("jooq", "jOOQ", []),
        ("mybatis", "MyBatis", []),
        ("flyway", "Flyway", []),
        ("liquibase", "Liquibase", []),
    ],
    "design_tools": [
        ("figma", "Figma", []),
        ("sketch", "Sketch", ["sketch app"]),
        ("adobe_xd", "Adobe XD", ["xd"]),
        ("photoshop", "Adobe Photoshop", ["photoshop", "ps"]),
        ("illustrator", "Adobe Illustrator", ["illustrator", "ai design"]),
        ("indesign", "Adobe InDesign", ["indesign"]),
        ("after_effects", "Adobe After Effects", ["after effects", "ae"]),
        ("premiere_pro", "Adobe Premiere Pro", ["premiere pro", "premiere"]),
        ("canva", "Canva", []),
        ("blender", "Blender", ["blender 3d"]),
        ("invision", "InVision", []),
        ("zeplin", "Zeplin", []),
        ("framer", "Framer", ["framer motion tool"]),
        ("protopie", "ProtoPie", []),
        ("axure_rp", "Axure RP", ["axure"]),
        ("balsamiq", "Balsamiq", ["balsamiq mockups"]),
        ("marvel_app", "Marvel App", []),
        ("coreldraw", "CorelDRAW", []),
        ("affinity_designer", "Affinity Designer", []),
        ("affinity_photo", "Affinity Photo", []),
        ("cinema_4d", "Cinema 4D", ["c4d"]),
        ("maya", "Autodesk Maya", ["maya 3d"]),
        ("3ds_max", "Autodesk 3ds Max", ["3ds max"]),
        ("zbrush", "ZBrush", []),
        ("procreate", "Procreate", []),
        ("penpot", "Penpot", []),
        ("lunacy", "Lunacy", ["icons8 lunacy"]),
        ("gravit_designer", "Gravit Designer", []),
        ("principle", "Principle", ["principle for mac"]),
        ("whimsical", "Whimsical", []),
        ("miro", "Miro", ["realtimeboard"]),
        ("mural", "Mural", []),
        ("figjam", "FigJam", []),
        ("lucidchart", "Lucidchart", []),
        ("draw_io", "Draw.io", ["diagrams.net"]),
        ("vectornator", "Vectornator", ["linearity curve"]),
        ("tinkercad", "Tinkercad", []),
        ("autocad", "AutoCAD", []),
        ("solidworks", "SolidWorks", []),
        ("spline", "Spline 3D", ["spline design"]),
        ("midjourney", "Midjourney", []),
        ("dall_e", "DALL-E", ["dalle 3"]),
        ("stable_diffusion_webui", "Stable Diffusion WebUI", ["automatic1111"]),
        ("davinci_resolve", "DaVinci Resolve", []),
        ("lightroom", "Adobe Lightroom", ["lightroom cc"]),
    ],
    "ml_dl_data": [
        ("pytorch", "PyTorch", ["torch"]),
        ("tensorflow", "TensorFlow", ["tf", "tf2"]),
        ("keras", "Keras", []),
        ("scikit_learn", "scikit-learn", ["sklearn"]),
        ("xgboost", "XGBoost", []),
        ("lightgbm", "LightGBM", []),
        ("catboost", "CatBoost", []),
        ("pandas", "pandas", []),
        ("numpy", "NumPy", []),
        ("scipy", "SciPy", []),
        ("huggingface_transformers", "Hugging Face Transformers", ["transformers library"]),
        ("langchain", "LangChain", []),
        ("llamaindex", "LlamaIndex", ["gpt index"]),
        ("spacy", "spaCy", []),
        ("nltk", "NLTK", ["natural language toolkit"]),
        ("opencv", "OpenCV", ["cv2"]),
        ("fastai", "fastai", []),
        ("jax", "JAX", ["google jax"]),
        ("mxnet", "Apache MXNet", ["mxnet"]),
        ("pytorch_lightning", "PyTorch Lightning", ["lightning"]),
        ("onnx", "ONNX", ["open neural network exchange"]),
        ("tensorrt", "TensorRT", ["nvidia tensorrt"]),
        ("triton_server", "Triton Inference Server", []),
        ("vllm", "vLLM", []),
        ("ollama", "Ollama", []),
        ("deepspeed", "DeepSpeed", ["microsoft deepspeed"]),
        ("ray", "Ray", ["ray core", "ray tune"]),
        ("ludwig", "Ludwig AI", []),
        ("mlflow", "MLflow", []),
        ("wandb", "Weights & Biases", ["wandb"]),
        ("dvc", "DVC", ["data version control"]),
        ("clearml", "ClearML", []),
        ("neptune_ai", "Neptune.ai", []),
        ("comet_ml", "Comet ML", []),
        ("kubeflow", "Kubeflow", ["kubeflow pipelines"]),
        ("optuna", "Optuna", []),
        ("hyperopt", "Hyperopt", []),
        ("albumentations", "Albumentations", []),
        ("torchvision", "Torchvision", []),
        ("torchaudio", "Torchaudio", []),
        ("whisper_ai", "Whisper", ["openai whisper"]),
        ("stable_diffusion", "Stable Diffusion", ["sdxl"]),
        ("yolo", "YOLO", ["yolov8", "yolov5"]),
        ("medpy", "MedPy", []),
        ("gensim", "Gensim", []),
        ("pattern_nlp", "Pattern NLP", []),
        ("stanza", "Stanza", ["stanford stanza"]),
        ("allennlp", "AllenNLP", []),
        ("textblob", "TextBlob", []),
        ("polars", "Polars", ["polars dataframe"]),
        ("dask", "Dask", []),
        ("vaex", "Vaex", []),
        ("modin", "Modin", []),
        ("pyarrow", "PyArrow", ["apache arrow python"]),
        ("openvino", "OpenVINO", ["intel openvino"]),
        ("mediapipe", "MediaPipe", ["google mediapipe"]),
        ("tesseract", "Tesseract OCR", ["pytesseract"]),
        ("pytorch_geometric", "PyTorch Geometric", ["pyg"]),
        ("networkx", "NetworkX", []),
        ("autogluon", "AutoGluon", []),
        ("flaml", "FLAML", []),
        ("tpot", "TPOT", []),
        ("sentence_transformers", "Sentence-Transformers", ["sbert"]),
        ("peft", "PEFT", ["parameter efficient fine tuning", "lora"]),
    ],
    "cicd_vcs": [
        ("git", "Git", []),
        ("github", "GitHub", []),
        ("gitlab", "GitLab", []),
        ("bitbucket", "Bitbucket", []),
        ("github_actions", "GitHub Actions", ["gha"]),
        ("gitlab_ci", "GitLab CI/CD", ["gitlab ci"]),
        ("jenkins", "Jenkins", ["jenkins ci"]),
        ("travis_ci", "Travis CI", []),
        ("circleci", "CircleCI", []),
        ("teamcity", "TeamCity", []),
        ("bamboo", "Bamboo", ["atlassian bamboo"]),
        ("argo_cd", "Argo CD", ["argocd"]),
        ("flux_cd", "Flux CD", ["flux v2"]),
        ("tekton", "Tekton", ["tekton pipelines"]),
        ("spinnaker", "Spinnaker", []),
        ("drone_ci", "Drone CI", []),
        ("woodpecker_ci", "Woodpecker CI", []),
        ("buildkite", "Buildkite", []),
        ("octopus_deploy", "Octopus Deploy", []),
        ("docker", "Docker", ["docker engine"]),
        ("docker_compose", "Docker Compose", []),
        ("podman", "Podman", []),
        ("buildah", "Buildah", []),
        ("kaniko", "Kaniko", []),
        ("containerd", "containerd", []),
        ("kubernetes", "Kubernetes", ["k8s"]),
        ("helm", "Helm", ["helm charts"]),
        ("kustomize", "Kustomize", []),
        ("terraform", "Terraform", ["tf infra"]),
        ("terragrunt", "Terragrunt", []),
        ("pulumi", "Pulumi", []),
        ("ansible", "Ansible", ["ansible playbooks"]),
        ("puppet", "Puppet", []),
        ("chef", "Chef", ["chef infra"]),
        ("saltstack", "SaltStack", ["salt"]),
        ("vagrant", "Vagrant", []),
        ("packer", "Packer", ["hashicorp packer"]),
        ("cloudformation", "AWS CloudFormation", ["cfn"]),
        ("aws_cdk", "AWS CDK", ["cloud development kit"]),
        ("serverless_framework", "Serverless Framework", ["sls"]),
        ("skaffold", "Skaffold", []),
        ("tilt", "Tilt", ["tilt dev"]),
        ("minikube", "Minikube", []),
        ("kind_k8s", "Kind", ["kubernetes in docker"]),
        ("harbor", "Harbor Registry", []),
    ],
    "testing": [
        ("pytest", "Pytest", ["py.test"]),
        ("unittest", "Unittest", ["python unittest"]),
        ("jest", "Jest", ["jest js"]),
        ("mocha", "Mocha", ["mochajs"]),
        ("chai", "Chai", ["chai assertion library"]),
        ("jasmine", "Jasmine", []),
        ("vitest", "Vitest", []),
        ("cypress", "Cypress", ["cypress.io"]),
        ("playwright", "Playwright", ["microsoft playwright"]),
        ("selenium", "Selenium", ["selenium webdriver"]),
        ("puppeteer", "Puppeteer", []),
        ("junit", "JUnit", ["junit 5", "junit 4"]),
        ("testng", "TestNG", []),
        ("nunit", "NUnit", []),
        ("xunit", "xUnit.net", ["xunit"]),
        ("mstest", "MSTest", []),
        ("rspec", "RSpec", []),
        ("capybara", "Capybara", []),
        ("phpunit", "PHPUnit", []),
        ("mockito", "Mockito", []),
        ("pytest_mock", "pytest-mock", []),
        ("unittest_mock", "unittest.mock", []),
        ("sinon", "Sinon.js", ["sinon"]),
        ("karma", "Karma", ["karma test runner"]),
        ("storybook", "Storybook", ["storybook.js"]),
        ("postman", "Postman", ["postman api testing"]),
        ("newman", "Newman", ["postman newman"]),
        ("insomnia", "Insomnia", ["insomnia rest client"]),
        ("jmeter", "Apache JMeter", ["jmeter"]),
        ("k6", "k6", ["grafana k6"]),
        ("gatling", "Gatling", []),
        ("locust", "Locust", ["locust.io"]),
        ("artillery", "Artillery", ["artillery.io"]),
        ("robot_framework", "Robot Framework", []),
        ("cucumber", "Cucumber", ["cucumber bdd"]),
        ("behave", "Behave", ["behave bdd"]),
        ("specflow", "SpecFlow", []),
        ("detox", "Detox", ["wix detox"]),
        ("appium", "Appium", []),
        ("espresso_test", "Espresso", ["android espresso"]),
        ("xcuitest", "XCUITest", []),
        ("sonarqube", "SonarQube", ["sonar"]),
        ("coverage_py", "Coverage.py", ["pytest coverage"]),
        ("istanbul_nyc", "Istanbul / nyc", ["nyc coverage"]),
        ("pact", "Pact", ["consumer driven contract testing"]),
    ],
    "data_bi_analytics": [
        ("power_bi", "Power BI", ["powerbi", "ms power bi"]),
        ("tableau", "Tableau", ["tableau desktop"]),
        ("looker", "Looker", ["lookml"]),
        ("looker_studio", "Looker Studio", ["google data studio"]),
        ("qlik_sense", "Qlik Sense", []),
        ("qlikview", "QlikView", []),
        ("apache_superset", "Apache Superset", ["superset"]),
        ("metabase", "Metabase", []),
        ("redash", "Redash", []),
        ("grafana", "Grafana", []),
        ("kibana", "Kibana", ["elk kibana"]),
        ("databricks", "Databricks", ["databricks lakehouse"]),
        ("apache_spark", "Apache Spark", ["spark"]),
        ("pyspark", "PySpark", []),
        ("apache_flink", "Apache Flink", ["flink"]),
        ("apache_kafka", "Apache Kafka", ["kafka"]),
        ("apache_pulsar", "Apache Pulsar", []),
        ("rabbitmq", "RabbitMQ", []),
        ("celery", "Celery", ["celery task queue"]),
        ("apache_airflow", "Apache Airflow", ["airflow"]),
        ("prefect", "Prefect", []),
        ("dagster", "Dagster", []),
        ("luigi", "Luigi", ["spotify luigi"]),
        ("apache_nifi", "Apache NiFi", ["nifi"]),
        ("apache_beam", "Apache Beam", []),
        ("dbt", "dbt", ["data build tool"]),
        ("great_expectations", "Great Expectations", []),
        ("snowflake", "Snowflake", ["snowflake data warehouse"]),
        ("google_bigquery", "Google BigQuery", ["bigquery"]),
        ("amazon_redshift", "Amazon Redshift", ["redshift"]),
        ("azure_synapse", "Azure Synapse Analytics", ["synapse"]),
        ("presto", "Presto", ["prestodb"]),
        ("trino", "Trino", ["prestosql"]),
        ("apache_hive", "Apache Hive", ["hive"]),
        ("apache_hadoop", "Apache Hadoop", ["hadoop", "hdfs"]),
        ("apache_druid", "Apache Druid", []),
        ("talend", "Talend", []),
        ("informatica", "Informatica", []),
        ("stitch_data", "Stitch Data", []),
        ("fivetran", "Fivetran", []),
        ("google_analytics", "Google Analytics", ["ga4"]),
        ("mixpanel", "Mixpanel", []),
        ("amplitude", "Amplitude", []),
        ("segment", "Segment", ["twilio segment"]),
        ("heap", "Heap Analytics", []),
    ],
    "mobile": [
        ("react_native", "React Native", ["rn"]),
        ("flutter", "Flutter", ["flutter sdk"]),
        ("swiftui", "SwiftUI", []),
        ("jetpack_compose", "Jetpack Compose", ["compose android"]),
        ("android_sdk", "Android SDK", ["android development"]),
        ("ios_sdk", "iOS SDK", ["ios development"]),
        ("xcode", "Xcode", []),
        ("android_studio", "Android Studio", []),
        ("expo", "Expo", ["expo cli"]),
        ("capacitor", "Capacitor", ["ionic capacitor"]),
        ("cordova", "Apache Cordova", ["phonegap"]),
        ("ionic", "Ionic", ["ionic framework"]),
        ("xamarin", "Xamarin", ["xamarin forms"]),
        ("dotnet_maui", ".NET MAUI", ["maui"]),
        ("nativescript", "NativeScript", []),
        ("fastlane", "Fastlane", []),
        ("cocoapods", "CocoaPods", []),
        ("gradle_android", "Gradle for Android", ["android gradle"]),
        ("carthage", "Carthage", []),
        ("swift_package_manager", "Swift Package Manager", ["spm"]),
        ("retrofit", "Retrofit", ["square retrofit"]),
        ("okhttp", "OkHttp", []),
        ("room_db", "Room Database", ["android room"]),
        ("core_data", "Core Data", ["apple core data"]),
        ("alamofire", "Alamofire", []),
        ("combine_framework", "Combine", ["apple combine"]),
        ("rxswift", "RxSwift", []),
        ("rxjava", "RxJava", []),
        ("koin", "Koin", ["koin di"]),
        ("dagger_hilt", "Dagger Hilt", ["hilt di"]),
        ("kotlin_coroutines", "Kotlin Coroutines", []),
        ("viewbinding", "ViewBinding", ["android data binding"]),
        ("apns", "Apple Push Notification service", ["apns push"]),
        ("fcm", "Firebase Cloud Messaging", ["fcm push"]),
        ("flutter_bloc", "Flutter BLoC", ["bloc pattern"]),
        ("provider_flutter", "Provider for Flutter", []),
        ("riverpod", "Riverpod", []),
        ("lottie_mobile", "Lottie", ["airbnb lottie"]),
        ("flutter_getx", "GetX", []),
        ("arkit", "ARKit", ["apple arkit"]),
        ("arcore", "ARCore", ["google arcore"]),
    ],
    "security_networking": [
        ("oauth2", "OAuth 2.0", ["oauth", "oauth2"]),
        ("openid_connect", "OpenID Connect", ["oidc"]),
        ("jwt", "JSON Web Tokens", ["jwt token"]),
        ("saml", "SAML", ["saml 2.0"]),
        ("keycloak", "Keycloak", []),
        ("auth0", "Auth0", []),
        ("okta", "Okta", []),
        ("firebase_auth", "Firebase Authentication", []),
        ("hashicorp_vault", "HashiCorp Vault", ["vault"]),
        ("cyberark", "CyberArk", []),
        ("nmap", "Nmap", ["network mapper"]),
        ("wireshark", "Wireshark", []),
        ("metasploit", "Metasploit", ["metasploit framework"]),
        ("burp_suite", "Burp Suite", ["burp"]),
        ("owasp_zap", "OWASP ZAP", ["zed attack proxy"]),
        ("nessus", "Nessus", ["tenable nessus"]),
        ("snort", "Snort", []),
        ("suricata", "Suricata", []),
        ("kali_linux", "Kali Linux", []),
        ("tor", "Tor Network", ["the onion router"]),
        ("openvpn", "OpenVPN", []),
        ("wireguard", "WireGuard", []),
        ("ipsec", "IPsec", []),
        ("ssh", "SSH", ["secure shell", "openssh"]),
        ("ssl_tls", "SSL / TLS", ["tls", "https certificates"]),
        ("https", "HTTPS", ["http secure"]),
        ("dns", "DNS", ["domain name system"]),
        ("dhcp", "DHCP", []),
        ("tcp_ip", "TCP/IP", ["transmission control protocol"]),
        ("bgp", "BGP", ["border gateway protocol"]),
        ("ospf", "OSPF", []),
        ("vlan", "VLAN", ["virtual local area network"]),
        ("subnetting", "Subnetting / CIDR", ["cidr"]),
        ("reverse_proxy", "Reverse Proxy", []),
        ("forward_proxy", "Forward Proxy", []),
        ("waf", "Web Application Firewall", ["waf security"]),
        ("cloudflare_waf", "Cloudflare WAF", []),
        ("aws_waf", "AWS WAF", []),
        ("modsecurity", "ModSecurity", []),
        ("siem", "SIEM", ["security information and event management"]),
        ("splunk", "Splunk", ["splunk enterprise"]),
        ("elastic_security", "Elastic Security", []),
        ("crowdstrike", "CrowdStrike Falcon", ["crowdstrike"]),
        ("ossec", "OSSEC", []),
        ("wazuh", "Wazuh", []),
        ("iam", "Identity & Access Management", ["iam identity"]),
        ("rbac", "Role-Based Access Control", ["rbac"]),
        ("abac", "Attribute-Based Access Control", ["abac"]),
        ("zero_trust", "Zero Trust Architecture", ["zero trust"]),
        ("cryptography", "Cryptography", ["encryption"]),
        ("aes", "AES Encryption", ["advanced encryption standard"]),
        ("rsa", "RSA Algorithm", ["rsa encryption"]),
        ("sha256", "SHA-256", ["sha2 hashing"]),
        ("pgp_gpg", "PGP / GPG", ["pretty good privacy", "gnupg"]),
        ("penetration_testing", "Penetration Testing", ["pen testing", "ethical hacking"]),
        ("vulnerability_assessment", "Vulnerability Assessment", ["vapt"]),
    ],
    "os_systems": [
        ("linux", "Linux", ["gnu linux"]),
        ("ubuntu", "Ubuntu", ["ubuntu linux"]),
        ("debian", "Debian", ["debian gnu"]),
        ("centos", "CentOS", ["centos stream"]),
        ("rhel", "Red Hat Enterprise Linux", ["rhel"]),
        ("fedora", "Fedora", ["fedora linux"]),
        ("arch_linux", "Arch Linux", ["arch"]),
        ("alpine_linux", "Alpine Linux", ["alpine"]),
        ("rocky_linux", "Rocky Linux", []),
        ("almalinux", "AlmaLinux", []),
        ("suse", "SUSE Linux", ["opensuse"]),
        ("macos", "macOS", ["os x", "apple macos"]),
        ("windows_os", "Windows", ["windows 11", "windows 10"]),
        ("windows_server", "Windows Server", ["winserver"]),
        ("freebsd", "FreeBSD", []),
        ("openbsd", "OpenBSD", []),
        ("netbsd", "NetBSD", []),
        ("android_os", "Android OS", ["android platform"]),
        ("ios_os", "iOS", ["apple ios"]),
        ("posix", "POSIX Standards", ["posix compliance"]),
        ("zsh", "Zsh", ["z shell", "oh-my-zsh"]),
        ("fish_shell", "Fish Shell", ["fish shell scripting"]),
        ("linux_kernel", "Linux Kernel", ["kernel modules"]),
        ("ebpf", "eBPF", ["extended bpf"]),
        ("cron", "Cron", ["crontab"]),
        ("syslog", "Syslog", ["rsyslog"]),
        ("virtualbox", "VirtualBox", ["oracle virtualbox"]),
        ("vmware_esxi", "VMware ESXi", ["vsphere"]),
        ("vmware_workstation", "VMware Workstation", []),
        ("kvm", "KVM", ["kernel-based virtual machine"]),
        ("qemu", "QEMU", []),
        ("hyper_v", "Hyper-V", ["microsoft hyper-v"]),
        ("wsl", "WSL", ["windows subsystem for linux", "wsl2"]),
        ("grub", "GRUB Bootloader", ["grub2"]),
        ("chroot", "Chroot", []),
        ("cgroups", "cgroups", ["control groups linux"]),
        ("ipc", "Inter-Process Communication", ["ipc shared memory"]),
        ("socket_programming", "Socket Programming", ["unix domain sockets"]),
        ("multithreading", "Multithreading", ["concurrency", "thread synchronization"]),
        ("memory_management", "Memory Management", ["virtual memory", "mmap"]),
    ],
    "other_tools": [
        ("vscode", "Visual Studio Code", ["vs code", "vscode"]),
        ("intellij_idea", "IntelliJ IDEA", ["intellij"]),
        ("pycharm", "PyCharm", []),
        ("webstorm", "WebStorm", []),
        ("eclipse_ide", "Eclipse IDE", ["eclipse"]),
        ("netbeans", "NetBeans", []),
        ("sublime_text", "Sublime Text", ["sublime"]),
        ("vim", "Vim", ["vi editor"]),
        ("neovim", "Neovim", ["nvim"]),
        ("emacs", "Emacs", ["gnu emacs"]),
        ("nano", "GNU nano", ["nano editor"]),
        ("jira", "Jira", ["atlassian jira"]),
        ("confluence", "Confluence", ["atlassian confluence"]),
        ("trello", "Trello", []),
        ("asana", "Asana", []),
        ("monday_com", "Monday.com", ["monday"]),
        ("linear", "Linear", ["linear.app"]),
        ("notion", "Notion", []),
        ("obsidian", "Obsidian", ["obsidian md"]),
        ("slack", "Slack", []),
        ("microsoft_teams", "Microsoft Teams", ["ms teams"]),
        ("zoom", "Zoom", ["zoom meetings"]),
        ("loom", "Loom", ["loom video"]),
        ("basecamp", "Basecamp", []),
        ("clickup", "ClickUp", []),
        ("airtable", "Airtable", []),
        ("google_workspace", "Google Workspace", ["g suite"]),
        ("microsoft_365", "Microsoft 365", ["office 365"]),
        ("dbeaver", "DBeaver", ["dbeaver universal"]),
        ("pgadmin", "pgAdmin", ["pgadmin 4"]),
        ("mysql_workbench", "MySQL Workbench", []),
        ("mongodb_compass", "MongoDB Compass", ["compass gui"]),
        ("tableplus", "TablePlus", []),
        ("charles_proxy", "Charles Proxy", []),
        ("fiddler", "Fiddler", ["telerik fiddler"]),
        ("regex", "Regular Expressions", ["regexp"]),
        ("markdown", "Markdown", ["commonmark", "gfm"]),
        ("latex", "LaTeX", ["tex formatting"]),
        ("swagger", "Swagger / OpenAPI", ["openapi 3", "swagger ui"]),
        ("graphql", "GraphQL", ["graphql schema"]),
        ("grpc", "gRPC", ["protocol buffers", "protobuf"]),
        ("json", "JSON", ["json format"]),
        ("xml", "XML", ["xml parsing"]),
        ("yaml", "YAML", ["yaml configuration"]),
        ("toml", "TOML", ["toml format"]),
    ],
    "soft_skills": [
        ("communication", "Communication", ["verbal communication", "written communication"]),
        ("problem_solving", "Problem Solving", ["troubleshooting mindset"]),
        ("critical_thinking", "Critical Thinking", []),
        ("teamwork", "Teamwork", ["team player"]),
        ("collaboration", "Collaboration", ["cross-team collaboration"]),
        ("leadership", "Leadership", ["team leadership"]),
        ("adaptability", "Adaptability", ["flexibility"]),
        ("time_management", "Time Management", ["deadline management"]),
        ("conflict_resolution", "Conflict Resolution", []),
        ("empathy", "Empathy", ["compassion"]),
        ("active_listening", "Active Listening", []),
        ("emotional_intelligence", "Emotional Intelligence", ["eq"]),
        ("mentorship", "Mentorship", ["coaching", "mentoring junior developers"]),
        ("negotiation", "Negotiation", []),
        ("presentation_skills", "Presentation Skills", ["demo presentation"]),
        ("public_speaking", "Public Speaking", []),
        ("analytical_thinking", "Analytical Thinking", []),
        ("decision_making", "Decision Making", []),
        ("ownership", "Ownership & Accountability", ["extreme ownership"]),
        ("attention_to_detail", "Attention to Detail", ["thoroughness"]),
        ("work_ethic", "Strong Work Ethic", ["dedication"]),
        ("prioritization", "Prioritization", ["task prioritization"]),
        ("project_management", "Project Management", ["pmp principles"]),
        ("agile", "Agile Methodologies", ["agile delivery"]),
        ("scrum", "Scrum", ["scrum ceremonies"]),
        ("kanban", "Kanban", ["kanban boards"]),
        ("sprint_planning", "Sprint Planning", ["backlog grooming"]),
        ("root_cause_analysis", "Root Cause Analysis", ["5 whys", "rca"]),
        ("stakeholder_management", "Stakeholder Management", ["client management"]),
        ("customer_focus", "Customer Focus", ["customer centricity"]),
        ("strategic_thinking", "Strategic Thinking", []),
        ("continuous_learning", "Continuous Learning", ["growth mindset"]),
        ("creativity", "Creativity", ["innovative thinking"]),
        ("stress_management", "Stress Management", ["working under pressure"]),
        ("interpersonal_skills", "Interpersonal Skills", []),
        ("feedback_reception", "Receptive to Feedback", ["constructive criticism"]),
        ("cross_functional", "Cross-Functional Collaboration", []),
        ("remote_collaboration", "Remote Work & Collaboration", ["async communication"]),
        ("technical_writing", "Technical Writing", ["documentation skills"]),
        ("code_review_culture", "Code Review & Quality Mindset", ["peer review"]),
        ("pair_programming", "Pair Programming", []),
        ("facilitation", "Meeting Facilitation", []),
        ("delegation", "Delegation", ["effective delegation"]),
        ("resilience", "Resilience", ["grit"]),
        ("change_management", "Change Management", []),
    ],
}


def build_catalog() -> Tuple[Dict[str, Any], int]:
    """Assemble and validate catalog, synchronize with skills.json taxonomy."""
    # 1. Load existing taxonomy
    if not settings.SKILLS_FILE.exists():
        raise FileNotFoundError(f"Taxonomy skills file not found at {settings.SKILLS_FILE}")

    with open(settings.SKILLS_FILE, "r", encoding="utf-8") as f:
        skills_taxonomy: Dict[str, Dict[str, Any]] = json.load(f)

    logger.info("Loaded initial taxonomy with %d skills.", len(skills_taxonomy))

    # Reverse lookup for taxonomy (by normalized name and alias)
    tax_name_map: Dict[str, str] = {}
    tax_alias_map: Dict[str, str] = {}
    for sid, sdata in skills_taxonomy.items():
        tax_name_map[normalize_skill_name(sdata["name"])] = sid
        tax_name_map[sid] = sid
        for a in sdata.get("aliases", []):
            tax_alias_map[normalize_skill_name(a)] = sid

    # Category mapping from catalog category to valid settings.SKILL_CATEGORIES
    cat_to_tax_category = {
        "languages": "programming",
        "hosting_cloud": "cloud",
        "frameworks_libraries": "web",
        "servers_runtime": "devops",
        "databases_orm": "data",
        "design_tools": "design",
        "ml_dl_data": "ml",
        "cicd_vcs": "devops",
        "testing": "tools",
        "data_bi_analytics": "data",
        "mobile": "programming",
        "security_networking": "tools",
        "os_systems": "devops",
        "other_tools": "tools",
        "soft_skills": "soft skills",
    }

    # Tracking sets to enforce global uniqueness
    claimed_ids: Set[str] = set()
    claimed_aliases: Dict[str, str] = {}  # alias -> skill_id

    # Canonical names map across taxonomy to prevent alias-name collision
    canonical_names: Dict[str, str] = {}
    tax_name_map: Dict[str, str] = {}
    tax_alias_map: Dict[str, str] = {}

    for sid, sdata in skills_taxonomy.items():
        norm_sname = normalize_skill_name(sdata["name"])
        norm_sid = normalize_skill_name(sid)
        canonical_names[norm_sname] = sid
        canonical_names[norm_sid] = sid
        tax_name_map[norm_sname] = sid
        tax_name_map[norm_sid] = sid
        for a in sdata.get("aliases", []):
            tax_alias_map[normalize_skill_name(a)] = sid

    categories_out: List[Dict[str, Any]] = []
    total_skills_count = 0
    new_taxonomy_skills_count = 0

    # Process categories in defined order
    for cat_meta in CATEGORIES:
        cat_id = cat_meta["id"]
        cat_name = cat_meta["name"]
        raw_skills = RAW_CATALOG_DATA.get(cat_id, [])

        cat_skills_out: List[Dict[str, Any]] = []

        for skill_id, skill_name, aliases in raw_skills:
            norm_id = normalize_skill_name(skill_id)
            if norm_id in claimed_ids:
                raise ValueError(f"Duplicate catalog skill ID found: '{norm_id}' in category '{cat_id}'")
            claimed_ids.add(norm_id)

            # Clean and deduplicate aliases globally
            clean_aliases: List[str] = []
            for a in aliases:
                norm_a = normalize_skill_name(a)
                if not norm_a or norm_a == norm_id:
                    continue
                # Check uniqueness against all claimed IDs
                if norm_a in claimed_ids:
                    logger.debug("Skipping alias '%s' for skill '%s' because it clashes with an ID", norm_a, norm_id)
                    continue
                # Check uniqueness against already claimed aliases
                if norm_a in claimed_aliases:
                    prev_id = claimed_aliases[norm_a]
                    logger.debug("Skipping alias '%s' for skill '%s' (already claimed by '%s')", norm_a, norm_id, prev_id)
                    continue

                claimed_aliases[norm_a] = norm_id
                clean_aliases.append(norm_a)

            # Determine taxonomy linkage
            tax_id: Optional[str] = None
            if norm_id in skills_taxonomy:
                tax_id = norm_id
            elif normalize_skill_name(skill_name) in tax_name_map:
                tax_id = tax_name_map[normalize_skill_name(skill_name)]
            elif norm_id in tax_alias_map:
                tax_id = tax_alias_map[norm_id]
            elif normalize_skill_name(skill_name) in tax_alias_map:
                tax_id = tax_alias_map[normalize_skill_name(skill_name)]
            else:
                for ca in clean_aliases:
                    if ca in tax_name_map:
                        tax_id = tax_name_map[ca]
                        break
                    if ca in tax_alias_map:
                        tax_id = tax_alias_map[ca]
                        break

            # If not in taxonomy, add it so the analyzer and builder use ONE vocabulary
            if not tax_id:
                tax_id = norm_id
                safe_tax_aliases = [
                    ca for ca in clean_aliases
                    if ca not in canonical_names and ca not in tax_name_map
                ]
                skills_taxonomy[tax_id] = {
                    "name": skill_name,
                    "aliases": safe_tax_aliases,
                    "category": cat_to_tax_category.get(cat_id, "tools"),
                    "ambiguous": is_ambiguous_skill(skill_name, safe_tax_aliases),
                }
                tax_name_map[normalize_skill_name(skill_name)] = tax_id
                tax_name_map[tax_id] = tax_id
                canonical_names[normalize_skill_name(skill_name)] = tax_id
                canonical_names[tax_id] = tax_id
                for sa in safe_tax_aliases:
                    tax_alias_map[sa] = tax_id
                new_taxonomy_skills_count += 1
            else:
                # Merge safe missing aliases into the taxonomy
                existing_aliases = set(skills_taxonomy[tax_id].get("aliases", []))
                for ca in clean_aliases:
                    if (ca not in existing_aliases and
                            ca not in canonical_names and
                            ca not in tax_name_map and
                            ca not in tax_alias_map):
                        skills_taxonomy[tax_id].setdefault("aliases", []).append(ca)
                        tax_alias_map[ca] = tax_id

            skill_entry = {
                "id": norm_id,
                "name": skill_name,
                "aliases": clean_aliases,
                "taxonomy_id": tax_id,
            }
            cat_skills_out.append(skill_entry)
            total_skills_count += 1

        categories_out.append({
            "id": cat_id,
            "name": cat_name,
            "skills": cat_skills_out,
        })

    # Save catalog
    catalog_payload = {"categories": categories_out}
    CATALOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CATALOG_FILE, "w", encoding="utf-8") as f:
        json.dump(catalog_payload, f, indent=2, ensure_ascii=False)

    logger.info("Saved tech catalog with %d categories and %d total skills to %s", len(categories_out), total_skills_count, CATALOG_FILE)

    # Save updated taxonomy if new skills were introduced
    if new_taxonomy_skills_count > 0:
        logger.info("Added %d new skills to taxonomy. Updating %s...", new_taxonomy_skills_count, settings.SKILLS_FILE)
        with open(settings.SKILLS_FILE, "w", encoding="utf-8") as f:
            json.dump(skills_taxonomy, f, indent=2, ensure_ascii=False)

        # Rebuild embeddings
        rebuild_taxonomy_embeddings(skills_taxonomy)
    else:
        logger.info("Taxonomy already complete (0 new skills added).")

    return catalog_payload, total_skills_count


def rebuild_taxonomy_embeddings(skills: Dict[str, Dict[str, Any]]) -> None:
    """Recompute sentence embeddings for the updated taxonomy."""
    from sentence_transformers import SentenceTransformer

    logger.info("Recomputing embeddings for %d taxonomy skills...", len(skills))
    model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
    skill_ids_list = list(skills.keys())
    texts_to_embed = [
        f"{skills[sid]['name']} ({skills[sid].get('category', 'technical')})"
        for sid in skill_ids_list
    ]

    embeddings = model.encode(texts_to_embed, normalize_embeddings=True, show_progress_bar=False)
    embeddings = np.asarray(embeddings, dtype=np.float32)

    np.save(settings.SKILL_EMBEDDINGS_FILE, embeddings)
    with open(settings.SKILL_IDS_FILE, "w", encoding="utf-8") as f:
        json.dump(skill_ids_list, f, indent=2)

    logger.info(
        "Successfully updated embeddings at %s (shape: %s) and IDs at %s.",
        settings.SKILL_EMBEDDINGS_FILE,
        embeddings.shape,
        settings.SKILL_IDS_FILE,
    )


if __name__ == "__main__":
    catalog, count = build_catalog()
    print(f"\nSuccessfully built Tech Catalog with {count} total entries across {len(catalog['categories'])} categories.")
