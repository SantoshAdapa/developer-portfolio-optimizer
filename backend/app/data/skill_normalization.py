"""Skill normalization dictionary.

Maps common abbreviations, synonyms, and alternative spellings to their
canonical form so that matching is consistent across resume text, job
descriptions, and role templates.
"""

# Canonical name → list of known aliases (all lowercase)
SKILL_ALIASES: dict[str, list[str]] = {
    "Machine Learning": [
        "ml",
        "machine learning",
        "machine-learning",
        "machinelearning",
    ],
    "Deep Learning": [
        "dl",
        "deep learning",
        "deep-learning",
        "deeplearning",
    ],
    "Scikit-Learn": [
        "scikit-learn",
        "scikit learn",
        "sklearn",
        "sk-learn",
    ],
    "TensorFlow": [
        "tensorflow",
        "tensor flow",
        "tensor-flow",
        "tf",
    ],
    "PyTorch": [
        "pytorch",
        "py-torch",
        "torch",
        "pytorch lightning",
    ],
    "Natural Language Processing": [
        "nlp",
        "natural language processing",
        "natural-language-processing",
        "text mining",
        "text analysis",
    ],
    "Computer Vision": [
        "computer vision",
        "cv",
        "image recognition",
        "image processing",
        "object detection",
    ],
    "Python": ["python", "python3", "python 3", "cpython"],
    "JavaScript": ["javascript", "js", "ecmascript", "es6", "es2015"],
    "TypeScript": ["typescript", "ts"],
    "Node.js": ["node.js", "nodejs", "node"],
    "React": ["react", "react.js", "reactjs"],
    "Next.js": ["next.js", "nextjs", "next"],
    "Vue": ["vue", "vue.js", "vuejs"],
    "Angular": ["angular", "angular.js", "angularjs"],
    "Express.js": ["express.js", "expressjs", "express"],
    "FastAPI": ["fastapi", "fast api", "fast-api"],
    "Django": ["django"],
    "Flask": ["flask"],
    "Spring Boot": ["spring boot", "spring-boot", "springboot"],
    "Ruby on Rails": ["ruby on rails", "rails", "ror"],
    "Docker": ["docker", "dockerfile", "docker-compose"],
    "Kubernetes": ["kubernetes", "k8s", "kube"],
    "AWS": ["aws", "amazon web services", "amazon cloud"],
    "GCP": ["gcp", "google cloud", "google cloud platform"],
    "Azure": ["azure", "microsoft azure", "ms azure"],
    "CI/CD": [
        "ci/cd",
        "cicd",
        "ci cd",
        "continuous integration",
        "continuous deployment",
        "continuous delivery",
        "github actions",
        "gitlab ci",
        "jenkins",
        "circleci",
    ],
    "PostgreSQL": ["postgresql", "postgres", "psql"],
    "MySQL": ["mysql", "my-sql"],
    "MongoDB": ["mongodb", "mongo"],
    "Redis": ["redis"],
    "Elasticsearch": ["elasticsearch", "elastic search", "elastic"],
    "SQL": ["sql", "structured query language"],
    "Git": ["git", "github", "gitlab", "bitbucket", "version control"],
    "Linux": ["linux", "unix", "ubuntu", "debian", "centos", "rhel"],
    "Pandas": ["pandas"],
    "NumPy": ["numpy", "np"],
    "Matplotlib": ["matplotlib", "mpl"],
    "Seaborn": ["seaborn"],
    "SciPy": ["scipy"],
    "OpenCV": ["opencv", "cv2", "open cv"],
    "Keras": ["keras"],
    "XGBoost": ["xgboost", "xg boost", "xg-boost"],
    "LightGBM": ["lightgbm", "light gbm", "lgbm"],
    "Hugging Face": [
        "hugging face",
        "huggingface",
        "hf",
        "transformers",
    ],
    "LangChain": ["langchain", "lang chain", "lang-chain"],
    "spaCy": ["spacy", "spa-cy"],
    "NLTK": ["nltk"],
    "Statistics": [
        "statistics",
        "statistical analysis",
        "stat",
        "stats",
        "data analysis",
        "data science",
    ],
    "Feature Engineering": [
        "feature engineering",
        "feature extraction",
        "feature selection",
    ],
    "Data Processing": [
        "data processing",
        "data pipeline",
        "etl",
        "data wrangling",
        "data munging",
        "data cleaning",
    ],
    "MLOps": ["mlops", "ml ops", "ml-ops", "model deployment"],
    "Terraform": ["terraform", "tf infra", "iac"],
    "Monitoring": [
        "monitoring",
        "prometheus",
        "grafana",
        "datadog",
        "observability",
    ],
    "Testing": [
        "testing",
        "unit testing",
        "pytest",
        "jest",
        "mocha",
        "selenium",
        "cypress",
        "test automation",
    ],
    "Apache Spark": ["apache spark", "spark", "pyspark"],
    "Kafka": ["kafka", "apache kafka"],
    "REST API": ["rest api", "rest", "restful", "restful api"],
    "GraphQL": ["graphql", "graph ql"],
    "gRPC": ["grpc", "g-rpc"],
    "Microservices": ["microservices", "micro services", "micro-services"],
    "Reinforcement Learning": [
        "reinforcement learning",
        "rl",
        "reinforcement-learning",
    ],
    "Neural Networks": [
        "neural networks",
        "neural network",
        "ann",
        "artificial neural network",
        "cnn",
        "rnn",
        "lstm",
        "gan",
    ],
    "Responsive Design": [
        "responsive design",
        "responsive web design",
        "mobile-first",
    ],
    "Tailwind CSS": ["tailwindcss", "tailwind css", "tailwind"],
    "Bootstrap": ["bootstrap"],
    "Material UI": ["material ui", "material-ui", "mui"],
    "Redux": ["redux", "react-redux"],
    "Sass": ["sass", "scss"],
    "Webpack": ["webpack"],
    "Vite": ["vite"],
    "Java": ["java"],
    "C++": ["c++", "cpp"],
    "C#": ["c#", "csharp", "c sharp"],
    "Go": ["go", "golang"],
    "Rust": ["rust"],
    "Ruby": ["ruby"],
    "PHP": ["php"],
    "Swift": ["swift"],
    "Kotlin": ["kotlin"],
    "R": ["r language", "r programming", "r-lang"],
    "Scala": ["scala"],
    "Bash": ["bash", "shell", "shell scripting", "sh"],
    "Tableau": ["tableau"],
    "Power BI": ["power bi", "powerbi", "power-bi"],
    "Excel": ["excel", "microsoft excel", "ms excel"],
    "Figma": ["figma"],
    "Data Visualization": [
        "data visualization",
        "data viz",
        "data visualisation",
    ],
    "Model Training": ["model training", "model building", "model development"],
    "Streamlit": ["streamlit"],
    "Gradio": ["gradio"],
    "DynamoDB": ["dynamodb", "dynamo db", "dynamo"],
    "Cassandra": ["cassandra", "apache cassandra"],
    "Neo4j": ["neo4j"],
    "Firebase": ["firebase"],
    "Supabase": ["supabase"],
    "Svelte": ["svelte", "sveltekit"],
    "NestJS": ["nestjs", "nest.js", "nest"],
    "ASP.NET": ["asp.net", "aspnet", ".net"],
    "Gatsby": ["gatsby"],
    "Nuxt.js": ["nuxt.js", "nuxtjs", "nuxt"],
    "Framer Motion": ["framer motion", "framer-motion"],
    "React Native": ["react native", "react-native", "rn"],
    "Flutter": ["flutter"],
    "Styled Components": ["styled-components", "styled components"],
    "SQLAlchemy": ["sqlalchemy", "sql alchemy"],
    "Prisma": ["prisma"],
    "RabbitMQ": ["rabbitmq", "rabbit mq"],
    "Plotly": ["plotly"],
}

# Build reverse lookup: alias_lowercase → canonical name
_ALIAS_TO_CANONICAL: dict[str, str] = {}
for canonical, aliases in SKILL_ALIASES.items():
    for alias in aliases:
        _ALIAS_TO_CANONICAL[alias.lower()] = canonical
    # Also map the canonical name itself
    _ALIAS_TO_CANONICAL[canonical.lower()] = canonical


def normalize_skill(name: str) -> str:
    """Return the canonical skill name for a given string, or title-case it."""
    return _ALIAS_TO_CANONICAL.get(name.strip().lower(), name.strip().title())


def normalize_skills(names: list[str]) -> list[str]:
    """Normalize a list of skill names, deduplicating by canonical form."""
    seen: set[str] = set()
    result: list[str] = []
    for name in names:
        canonical = normalize_skill(name)
        key = canonical.lower()
        if key not in seen:
            seen.add(key)
            result.append(canonical)
    return result
