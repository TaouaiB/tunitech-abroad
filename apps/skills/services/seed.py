from django.db import transaction
from django.utils.text import slugify
from apps.skills.models import Skill, SkillAlias, SkillCategory
from typing import TypedDict, List, Tuple
from apps.skills.services.normalizer import normalize_skill_text
from apps.skills.services.phase_15d_decisions import approved_taxonomy_decisions

class SkillSeedItem(TypedDict):
    canonical: str
    category: str
    aliases: List[str]

class SkillSeedService:
    @classmethod
    def seed_initial_taxonomy(cls) -> dict:
        """
        Seeds initial canonical skills and their aliases.
        Returns a dict with counts: {'skills_created': x, 'aliases_created': y}
        """
        seed_data: List[SkillSeedItem] = [
            # Programming Languages
            {"canonical": "Python", "category": SkillCategory.PROGRAMMING_LANGUAGE.value, "aliases": ["Python", "Python3", "Python 3", "py", "python2", "py2", "py3"]},
            {"canonical": "JavaScript", "category": SkillCategory.PROGRAMMING_LANGUAGE.value, "aliases": ["JavaScript", "JS", "ECMAScript", "ES6"]},
            {"canonical": "TypeScript", "category": SkillCategory.PROGRAMMING_LANGUAGE.value, "aliases": ["TypeScript", "TS"]},
            {"canonical": "Java", "category": SkillCategory.PROGRAMMING_LANGUAGE.value, "aliases": ["Java", "Java 8", "Java 11", "Java 17", "Java 21", "Core Java", "J2EE"]},
            {"canonical": "C#", "category": SkillCategory.PROGRAMMING_LANGUAGE.value, "aliases": ["C#", "C Sharp", "CSharp", ".NET C#"]},
            {"canonical": "C++", "category": SkillCategory.PROGRAMMING_LANGUAGE.value, "aliases": ["C++", "CPP", "C Plus Plus", "cxx"]},
            {"canonical": "C", "category": SkillCategory.PROGRAMMING_LANGUAGE.value, "aliases": ["C", "C Language"]},
            {"canonical": "Go", "category": SkillCategory.PROGRAMMING_LANGUAGE.value, "aliases": ["Go", "Golang"]},
            {"canonical": "Rust", "category": SkillCategory.PROGRAMMING_LANGUAGE.value, "aliases": ["Rust", "Rustlang"]},
            {"canonical": "PHP", "category": SkillCategory.PROGRAMMING_LANGUAGE.value, "aliases": ["PHP", "PHP 7", "PHP 8"]},
            {"canonical": "Ruby", "category": SkillCategory.PROGRAMMING_LANGUAGE.value, "aliases": ["Ruby"]},
            {"canonical": "Swift", "category": SkillCategory.PROGRAMMING_LANGUAGE.value, "aliases": ["Swift", "SwiftUI"]},
            {"canonical": "Kotlin", "category": SkillCategory.PROGRAMMING_LANGUAGE.value, "aliases": ["Kotlin"]},
            {"canonical": "Dart", "category": SkillCategory.PROGRAMMING_LANGUAGE.value, "aliases": ["Dart"]},
            {"canonical": "Scala", "category": SkillCategory.PROGRAMMING_LANGUAGE.value, "aliases": ["Scala"]},
            {"canonical": "R", "category": SkillCategory.PROGRAMMING_LANGUAGE.value, "aliases": ["R", "R Language"]},
            {"canonical": "Objective-C", "category": SkillCategory.PROGRAMMING_LANGUAGE.value, "aliases": ["Objective-C", "Obj-C"]},
            {"canonical": "Shell Scripting", "category": SkillCategory.PROGRAMMING_LANGUAGE.value, "aliases": ["Shell Scripting", "Bash", "Shell", "Sh"]},

            # Frontend
            {"canonical": "React", "category": SkillCategory.FRONTEND.value, "aliases": ["React", "ReactJS", "React.js", "React JS", "React.JS"]},
            {"canonical": "Vue.js", "category": SkillCategory.FRONTEND.value, "aliases": ["Vue", "Vue.js", "VueJS", "Vue 3", "Vue2"]},
            {"canonical": "Angular", "category": SkillCategory.FRONTEND.value, "aliases": ["Angular", "AngularJS", "Angular 2+", "Angular 14"]},
            {"canonical": "Svelte", "category": SkillCategory.FRONTEND.value, "aliases": ["Svelte"]},
            {"canonical": "HTML5", "category": SkillCategory.FRONTEND.value, "aliases": ["HTML5", "HTML", "HTML 5"]},
            {"canonical": "CSS3", "category": SkillCategory.FRONTEND.value, "aliases": ["CSS3", "CSS", "CSS 3"]},
            {"canonical": "Tailwind CSS", "category": SkillCategory.FRONTEND.value, "aliases": ["Tailwind CSS", "Tailwind", "TailwindCSS"]},
            {"canonical": "Bootstrap", "category": SkillCategory.FRONTEND.value, "aliases": ["Bootstrap", "Bootstrap 4", "Bootstrap 5", "Twitter Bootstrap"]},
            {"canonical": "Sass", "category": SkillCategory.FRONTEND.value, "aliases": ["Sass", "SCSS", "SASS/SCSS"]},
            {"canonical": "Next.js", "category": SkillCategory.FRONTEND.value, "aliases": ["Next.js", "NextJS", "Next", "Next JS"]},
            {"canonical": "Nuxt.js", "category": SkillCategory.FRONTEND.value, "aliases": ["Nuxt.js", "NuxtJS", "Nuxt", "Nuxt JS"]},
            {"canonical": "Gatsby", "category": SkillCategory.FRONTEND.value, "aliases": ["Gatsby", "GatsbyJS"]},
            {"canonical": "jQuery", "category": SkillCategory.FRONTEND.value, "aliases": ["jQuery"]},
            {"canonical": "Redux", "category": SkillCategory.FRONTEND.value, "aliases": ["Redux"]},
            {"canonical": "Vuex", "category": SkillCategory.FRONTEND.value, "aliases": ["Vuex"]},
            {"canonical": "Pinia", "category": SkillCategory.FRONTEND.value, "aliases": ["Pinia"]},
            {"canonical": "Webpack", "category": SkillCategory.FRONTEND.value, "aliases": ["Webpack"]},
            {"canonical": "Vite", "category": SkillCategory.FRONTEND.value, "aliases": ["Vite"]},

            # Backend
            {"canonical": "Node.js", "category": SkillCategory.BACKEND.value, "aliases": ["Node.js", "Node", "NodeJS", "Node JS"]},
            {"canonical": "Express.js", "category": SkillCategory.BACKEND.value, "aliases": ["Express.js", "Express", "ExpressJS"]},
            {"canonical": "NestJS", "category": SkillCategory.BACKEND.value, "aliases": ["NestJS", "Nest"]},
            {"canonical": "Django", "category": SkillCategory.BACKEND.value, "aliases": ["Django", "Django Rest Framework", "DRF", "Django Web Framework"]},
            {"canonical": "Flask", "category": SkillCategory.BACKEND.value, "aliases": ["Flask"]},
            {"canonical": "FastAPI", "category": SkillCategory.BACKEND.value, "aliases": ["FastAPI"]},
            {"canonical": "Spring Boot", "category": SkillCategory.BACKEND.value, "aliases": ["Spring Boot", "Spring", "SpringBoot", "Spring Framework"]},
            {"canonical": ".NET Core", "category": SkillCategory.BACKEND.value, "aliases": [".NET Core", ".NET", "DotNet", "Dot Net", "ASP.NET Core"]},
            {"canonical": "ASP.NET", "category": SkillCategory.BACKEND.value, "aliases": ["ASP.NET"]},
            {"canonical": "Laravel", "category": SkillCategory.BACKEND.value, "aliases": ["Laravel"]},
            {"canonical": "Symfony", "category": SkillCategory.BACKEND.value, "aliases": ["Symfony"]},
            {"canonical": "Ruby on Rails", "category": SkillCategory.BACKEND.value, "aliases": ["Ruby on Rails", "Rails", "RoR"]},
            {"canonical": "GraphQL", "category": SkillCategory.BACKEND.value, "aliases": ["GraphQL"]},
            {"canonical": "REST API", "category": SkillCategory.BACKEND.value, "aliases": ["REST API", "REST", "RESTful APIs", "RESTful"]},
            {"canonical": "gRPC", "category": SkillCategory.BACKEND.value, "aliases": ["gRPC"]},
            {"canonical": "Microservices", "category": SkillCategory.BACKEND.value, "aliases": ["Microservices", "Microservices Architecture"]},

            # Database
            {"canonical": "PostgreSQL", "category": SkillCategory.DATABASE.value, "aliases": ["PostgreSQL", "Postgres", "psql", "Postgres DB"]},
            {"canonical": "MySQL", "category": SkillCategory.DATABASE.value, "aliases": ["MySQL", "My SQL"]},
            {"canonical": "MariaDB", "category": SkillCategory.DATABASE.value, "aliases": ["MariaDB"]},
            {"canonical": "SQLite", "category": SkillCategory.DATABASE.value, "aliases": ["SQLite"]},
            {"canonical": "Oracle DB", "category": SkillCategory.DATABASE.value, "aliases": ["Oracle DB", "Oracle"]},
            {"canonical": "SQL Server", "category": SkillCategory.DATABASE.value, "aliases": ["SQL Server", "MSSQL", "Microsoft SQL Server"]},
            {"canonical": "MongoDB", "category": SkillCategory.DATABASE.value, "aliases": ["MongoDB", "Mongo", "Mongo DB"]},
            {"canonical": "Redis", "category": SkillCategory.DATABASE.value, "aliases": ["Redis"]},
            {"canonical": "Elasticsearch", "category": SkillCategory.DATABASE.value, "aliases": ["Elasticsearch", "Elastic Search", "Elastic"]},
            {"canonical": "Cassandra", "category": SkillCategory.DATABASE.value, "aliases": ["Cassandra", "Apache Cassandra"]},
            {"canonical": "DynamoDB", "category": SkillCategory.DATABASE.value, "aliases": ["DynamoDB", "AWS DynamoDB"]},
            {"canonical": "Neo4j", "category": SkillCategory.DATABASE.value, "aliases": ["Neo4j"]},
            {"canonical": "Firebase", "category": SkillCategory.DATABASE.value, "aliases": ["Firebase", "Firestore"]},
            {"canonical": "SQL", "category": SkillCategory.DATABASE.value, "aliases": ["SQL"]},

            # DevOps / Cloud
            {"canonical": "Docker Compose", "category": SkillCategory.DEVOPS.value, "aliases": ["Docker Compose", "docker-compose"]},
            {"canonical": "Docker", "category": SkillCategory.DEVOPS.value, "aliases": ["Docker", "Docker Container"]},
            {"canonical": "Kubernetes", "category": SkillCategory.DEVOPS.value, "aliases": ["Kubernetes", "K8s", "Kube"]},
            {"canonical": "Jenkins", "category": SkillCategory.DEVOPS.value, "aliases": ["Jenkins"]},
            {"canonical": "GitLab CI/CD", "category": SkillCategory.DEVOPS.value, "aliases": ["GitLab CI/CD", "GitLab CI"]},
            {"canonical": "GitHub Actions", "category": SkillCategory.DEVOPS.value, "aliases": ["GitHub Actions"]},
            {"canonical": "Terraform", "category": SkillCategory.DEVOPS.value, "aliases": ["Terraform"]},
            {"canonical": "Ansible", "category": SkillCategory.DEVOPS.value, "aliases": ["Ansible"]},
            {"canonical": "AWS", "category": SkillCategory.CLOUD.value, "aliases": ["AWS", "Amazon Web Services", "Amazon AWS"]},
            {"canonical": "Azure", "category": SkillCategory.CLOUD.value, "aliases": ["Azure", "Microsoft Azure", "MS Azure"]},
            {"canonical": "Google Cloud", "category": SkillCategory.CLOUD.value, "aliases": ["Google Cloud", "GCP", "Google Cloud Platform"]},
            {"canonical": "Linux", "category": SkillCategory.DEVOPS.value, "aliases": ["Linux", "GNU/Linux", "Linux OS"]},
            {"canonical": "Ubuntu", "category": SkillCategory.DEVOPS.value, "aliases": ["Ubuntu"]},
            {"canonical": "CentOS", "category": SkillCategory.DEVOPS.value, "aliases": ["CentOS"]},
            {"canonical": "Nginx", "category": SkillCategory.DEVOPS.value, "aliases": ["Nginx"]},
            {"canonical": "Apache", "category": SkillCategory.DEVOPS.value, "aliases": ["Apache", "Apache HTTP Server"]},
            {"canonical": "Prometheus", "category": SkillCategory.DEVOPS.value, "aliases": ["Prometheus"]},
            {"canonical": "Grafana", "category": SkillCategory.DEVOPS.value, "aliases": ["Grafana"]},
            {"canonical": "Datadog", "category": SkillCategory.DEVOPS.value, "aliases": ["Datadog"]},
            {"canonical": "CI/CD", "category": SkillCategory.DEVOPS.value, "aliases": ["CI/CD", "Continuous Integration", "Continuous Deployment", "CI CD"]},

            # Mobile
            {"canonical": "React Native", "category": SkillCategory.MOBILE.value, "aliases": ["React Native", "RN"]},
            {"canonical": "Flutter", "category": SkillCategory.MOBILE.value, "aliases": ["Flutter"]},
            {"canonical": "iOS Development", "category": SkillCategory.MOBILE.value, "aliases": ["iOS Development", "iOS"]},
            {"canonical": "Android Development", "category": SkillCategory.MOBILE.value, "aliases": ["Android Development", "Android"]},
            {"canonical": "Xamarin", "category": SkillCategory.MOBILE.value, "aliases": ["Xamarin"]},
            {"canonical": "Ionic", "category": SkillCategory.MOBILE.value, "aliases": ["Ionic"]},

            # Data/AI
            {"canonical": "Machine Learning", "category": SkillCategory.DATA_AI.value, "aliases": ["Machine Learning", "ML", "Machine Learning (ML)"]},
            {"canonical": "Deep Learning", "category": SkillCategory.DATA_AI.value, "aliases": ["Deep Learning", "DL"]},
            {"canonical": "Data Science", "category": SkillCategory.DATA_AI.value, "aliases": ["Data Science"]},
            {"canonical": "Artificial Intelligence", "category": SkillCategory.DATA_AI.value, "aliases": ["Artificial Intelligence", "AI", "AI/ML"]},
            {"canonical": "TensorFlow", "category": SkillCategory.DATA_AI.value, "aliases": ["TensorFlow"]},
            {"canonical": "PyTorch", "category": SkillCategory.DATA_AI.value, "aliases": ["PyTorch"]},
            {"canonical": "Pandas", "category": SkillCategory.DATA_AI.value, "aliases": ["Pandas"]},
            {"canonical": "NumPy", "category": SkillCategory.DATA_AI.value, "aliases": ["NumPy"]},
            {"canonical": "Scikit-Learn", "category": SkillCategory.DATA_AI.value, "aliases": ["Scikit-Learn", "sklearn"]},
            {"canonical": "Keras", "category": SkillCategory.DATA_AI.value, "aliases": ["Keras"]},
            {"canonical": "Hadoop", "category": SkillCategory.DATA_AI.value, "aliases": ["Hadoop"]},
            {"canonical": "Spark", "category": SkillCategory.DATA_AI.value, "aliases": ["Spark", "Apache Spark"]},
            {"canonical": "Kafka", "category": SkillCategory.DATA_AI.value, "aliases": ["Kafka", "Apache Kafka"]},
            {"canonical": "Power BI", "category": SkillCategory.DATA_AI.value, "aliases": ["Power BI", "PowerBI"]},
            {"canonical": "Tableau", "category": SkillCategory.DATA_AI.value, "aliases": ["Tableau"]},

            # Testing
            {"canonical": "Jest", "category": SkillCategory.TESTING.value, "aliases": ["Jest"]},
            {"canonical": "Mocha", "category": SkillCategory.TESTING.value, "aliases": ["Mocha"]},
            {"canonical": "Cypress", "category": SkillCategory.TESTING.value, "aliases": ["Cypress"]},
            {"canonical": "Selenium", "category": SkillCategory.TESTING.value, "aliases": ["Selenium"]},
            {"canonical": "JUnit", "category": SkillCategory.TESTING.value, "aliases": ["JUnit"]},
            {"canonical": "PyTest", "category": SkillCategory.TESTING.value, "aliases": ["PyTest"]},
            {"canonical": "RSpec", "category": SkillCategory.TESTING.value, "aliases": ["RSpec"]},
            {"canonical": "Unit Testing", "category": SkillCategory.TESTING.value, "aliases": ["Unit Testing", "TDD"]},

            # Tools & Methodology
            {"canonical": "Git", "category": SkillCategory.TOOLS.value, "aliases": ["Git", "Git Version Control"]},
            {"canonical": "GitHub", "category": SkillCategory.TOOLS.value, "aliases": ["GitHub"]},
            {"canonical": "GitLab", "category": SkillCategory.TOOLS.value, "aliases": ["GitLab"]},
            {"canonical": "Bitbucket", "category": SkillCategory.TOOLS.value, "aliases": ["Bitbucket"]},
            {"canonical": "Jira", "category": SkillCategory.TOOLS.value, "aliases": ["Jira"]},
            {"canonical": "Confluence", "category": SkillCategory.TOOLS.value, "aliases": ["Confluence"]},
            {"canonical": "Agile", "category": SkillCategory.METHODOLOGY.value, "aliases": ["Agile", "Agile Methodology", "Agile Software Development"]},
            {"canonical": "Scrum", "category": SkillCategory.METHODOLOGY.value, "aliases": ["Scrum", "Scrum Framework", "Scrum Master"]},
            {"canonical": "Kanban", "category": SkillCategory.METHODOLOGY.value, "aliases": ["Kanban"]},
            {"canonical": "Figma", "category": SkillCategory.TOOLS.value, "aliases": ["Figma"]},

            # Soft Skills
            {"canonical": "Communication", "category": SkillCategory.SOFT_SKILL.value, "aliases": ["Communication", "Good Communication"]},
            {"canonical": "Teamwork", "category": SkillCategory.SOFT_SKILL.value, "aliases": ["Teamwork", "Collaboration"]},
            {"canonical": "Problem Solving", "category": SkillCategory.SOFT_SKILL.value, "aliases": ["Problem Solving", "Problem-Solving"]},
            {"canonical": "Leadership", "category": SkillCategory.SOFT_SKILL.value, "aliases": ["Leadership"]},
            {"canonical": "Time Management", "category": SkillCategory.SOFT_SKILL.value, "aliases": ["Time Management"]},

            # Security
            {"canonical": "Cybersecurity", "category": SkillCategory.SECURITY.value, "aliases": ["Cybersecurity", "Cyber Security"]},
            {"canonical": "Penetration Testing", "category": SkillCategory.SECURITY.value, "aliases": ["Penetration Testing", "Pentesting"]},
            {"canonical": "Cryptography", "category": SkillCategory.SECURITY.value, "aliases": ["Cryptography"]},
            {"canonical": "Network Security", "category": SkillCategory.SECURITY.value, "aliases": ["Network Security"]},
            {"canonical": "OWASP", "category": SkillCategory.SECURITY.value, "aliases": ["OWASP"]},
        ]

        extra_skills: List[Tuple[str, str, List[str]]] = [
            ("Celery", SkillCategory.BACKEND.value, ["Celery"]),
            ("RabbitMQ", SkillCategory.DEVOPS.value, ["RabbitMQ"]),
            ("Vagrant", SkillCategory.DEVOPS.value, ["Vagrant"]),
            ("Puppet", SkillCategory.DEVOPS.value, ["Puppet"]),
            ("Chef", SkillCategory.DEVOPS.value, ["Chef"]),
            ("Istio", SkillCategory.DEVOPS.value, ["Istio"]),
            ("CircleCI", SkillCategory.DEVOPS.value, ["CircleCI"]),
            ("Travis CI", SkillCategory.DEVOPS.value, ["Travis CI", "Travis"]),
            ("Bitrise", SkillCategory.DEVOPS.value, ["Bitrise"]),
            ("DigitalOcean", SkillCategory.CLOUD.value, ["DigitalOcean", "DO"]),
            ("Heroku", SkillCategory.CLOUD.value, ["Heroku"]),
            ("Vercel", SkillCategory.CLOUD.value, ["Vercel"]),
            ("Netlify", SkillCategory.CLOUD.value, ["Netlify"]),
            ("Linode", SkillCategory.CLOUD.value, ["Linode"]),
            ("Supabase", SkillCategory.DATABASE.value, ["Supabase"]),
            ("Auth0", SkillCategory.BACKEND.value, ["Auth0"]),
            ("Stripe API", SkillCategory.BACKEND.value, ["Stripe", "Stripe API"]),
            ("Twilio API", SkillCategory.BACKEND.value, ["Twilio", "Twilio API"]),
            ("SendGrid", SkillCategory.BACKEND.value, ["SendGrid"]),
            ("Postman", SkillCategory.TOOLS.value, ["Postman"]),
            ("Swagger", SkillCategory.TOOLS.value, ["Swagger", "OpenAPI"]),
            ("SOAP", SkillCategory.BACKEND.value, ["SOAP"]),
            ("XML", SkillCategory.BACKEND.value, ["XML"]),
            ("JSON", SkillCategory.BACKEND.value, ["JSON"]),
            ("YAML", SkillCategory.DEVOPS.value, ["YAML"]),
            ("Markdown", SkillCategory.TOOLS.value, ["Markdown", "MD"]),
            ("GraphQL Apollo", SkillCategory.FRONTEND.value, ["Apollo", "Apollo GraphQL"]),
            ("TypeORM", SkillCategory.BACKEND.value, ["TypeORM"]),
            ("Sequelize", SkillCategory.BACKEND.value, ["Sequelize"]),
            ("Prisma", SkillCategory.BACKEND.value, ["Prisma"]),
            ("Mongoose", SkillCategory.BACKEND.value, ["Mongoose"]),
            ("Hibernate", SkillCategory.BACKEND.value, ["Hibernate"]),
            ("Entity Framework", SkillCategory.BACKEND.value, ["Entity Framework", "EF", "EF Core"]),
            ("JPA", SkillCategory.BACKEND.value, ["JPA"]),
            ("Django ORM", SkillCategory.BACKEND.value, ["Django ORM"]),
            ("SQLAlchemy", SkillCategory.BACKEND.value, ["SQLAlchemy"]),
            ("Boto3", SkillCategory.BACKEND.value, ["Boto3"]),
            ("Babel", SkillCategory.FRONTEND.value, ["Babel"]),
            ("ESLint", SkillCategory.FRONTEND.value, ["ESLint"]),
            ("Prettier", SkillCategory.FRONTEND.value, ["Prettier"]),
            ("Husky", SkillCategory.TOOLS.value, ["Husky"]),
            ("PWA", SkillCategory.FRONTEND.value, ["PWA", "Progressive Web Apps"]),
            ("WebSockets", SkillCategory.BACKEND.value, ["WebSockets", "Socket.io"]),
            ("WebRTC", SkillCategory.FRONTEND.value, ["WebRTC"]),
            ("Three.js", SkillCategory.FRONTEND.value, ["Three.js", "ThreeJS"]),
            ("D3.js", SkillCategory.FRONTEND.value, ["D3", "D3.js"]),
            ("Chart.js", SkillCategory.FRONTEND.value, ["Chart.js", "ChartJS"]),
            ("Highcharts", SkillCategory.FRONTEND.value, ["Highcharts"]),
            ("RxJS", SkillCategory.FRONTEND.value, ["RxJS"]),
            ("NgRx", SkillCategory.FRONTEND.value, ["NgRx"]),
            ("Vue Router", SkillCategory.FRONTEND.value, ["Vue Router"]),
            ("React Router", SkillCategory.FRONTEND.value, ["React Router"]),
            ("Styled Components", SkillCategory.FRONTEND.value, ["Styled Components"]),
            ("Emotion", SkillCategory.FRONTEND.value, ["Emotion"]),
            ("Less", SkillCategory.FRONTEND.value, ["Less"]),
            ("Stylus", SkillCategory.FRONTEND.value, ["Stylus"]),
            ("Material UI", SkillCategory.FRONTEND.value, ["Material UI", "MUI"]),
            ("Ant Design", SkillCategory.FRONTEND.value, ["Ant Design", "AntD"]),
            ("Chakra UI", SkillCategory.FRONTEND.value, ["Chakra UI"]),
            ("Bulma", SkillCategory.FRONTEND.value, ["Bulma"]),
            ("Foundation", SkillCategory.FRONTEND.value, ["Foundation"]),
            ("Semantic UI", SkillCategory.FRONTEND.value, ["Semantic UI"]),
            ("Storybook", SkillCategory.FRONTEND.value, ["Storybook"]),
            ("Lerna", SkillCategory.TOOLS.value, ["Lerna"]),
            ("Nx", SkillCategory.TOOLS.value, ["Nx"]),
            ("Turborepo", SkillCategory.TOOLS.value, ["Turborepo"]),
            ("Packer", SkillCategory.DEVOPS.value, ["Packer"]),
            ("Nomad", SkillCategory.DEVOPS.value, ["Nomad"]),
            ("Consul", SkillCategory.DEVOPS.value, ["Consul"]),
            ("Vault", SkillCategory.SECURITY.value, ["Vault", "HashiCorp Vault"]),
            ("Splunk", SkillCategory.DEVOPS.value, ["Splunk"]),
            ("Logstash", SkillCategory.DEVOPS.value, ["Logstash"]),
            ("Kibana", SkillCategory.DEVOPS.value, ["Kibana"]),
            ("New Relic", SkillCategory.DEVOPS.value, ["New Relic"]),
            ("AppDynamics", SkillCategory.DEVOPS.value, ["AppDynamics"]),
            ("Sentry", SkillCategory.DEVOPS.value, ["Sentry"]),
            ("Rollbar", SkillCategory.DEVOPS.value, ["Rollbar"]),
            ("Nagios", SkillCategory.DEVOPS.value, ["Nagios"]),
            ("Zabbix", SkillCategory.DEVOPS.value, ["Zabbix"]),
            ("Icinga", SkillCategory.DEVOPS.value, ["Icinga"]),
            ("Cloudflare", SkillCategory.CLOUD.value, ["Cloudflare"]),
            ("Akamai", SkillCategory.CLOUD.value, ["Akamai"]),
            ("Fastly", SkillCategory.CLOUD.value, ["Fastly"]),
            ("Nvidia CUDA", SkillCategory.DATA_AI.value, ["CUDA"]),
            ("OpenCV", SkillCategory.DATA_AI.value, ["OpenCV"]),
            ("NLTK", SkillCategory.DATA_AI.value, ["NLTK"]),
            ("Spacy", SkillCategory.DATA_AI.value, ["Spacy"]),
            ("Gensim", SkillCategory.DATA_AI.value, ["Gensim"]),
            ("Hugging Face", SkillCategory.DATA_AI.value, ["Hugging Face", "Transformers"]),
            ("MLflow", SkillCategory.DATA_AI.value, ["MLflow"]),
            ("Kubeflow", SkillCategory.DATA_AI.value, ["Kubeflow"]),
            ("Airflow", SkillCategory.DATA_AI.value, ["Airflow", "Apache Airflow"]),
            ("Luigi", SkillCategory.DATA_AI.value, ["Luigi"]),
            ("Snowflake", SkillCategory.DATABASE.value, ["Snowflake"]),
            ("Redshift", SkillCategory.DATABASE.value, ["Redshift", "AWS Redshift"]),
            ("BigQuery", SkillCategory.DATABASE.value, ["BigQuery", "Google BigQuery"]),
            ("Athena", SkillCategory.DATABASE.value, ["Athena", "AWS Athena"]),
            ("HBase", SkillCategory.DATABASE.value, ["HBase", "Apache HBase"]),
            ("CouchDB", SkillCategory.DATABASE.value, ["CouchDB", "Apache CouchDB"]),
            ("Couchbase", SkillCategory.DATABASE.value, ["Couchbase"]),
            ("ArangoDB", SkillCategory.DATABASE.value, ["ArangoDB"]),
            ("Memcached", SkillCategory.DATABASE.value, ["Memcached"]),
            ("ActiveMQ", SkillCategory.DEVOPS.value, ["ActiveMQ"]),
            ("ZeroMQ", SkillCategory.DEVOPS.value, ["ZeroMQ"]),
            ("NATS", SkillCategory.DEVOPS.value, ["NATS"]),
            ("Thrift", SkillCategory.BACKEND.value, ["Thrift"]),
            ("Protobuf", SkillCategory.BACKEND.value, ["Protobuf", "Protocol Buffers"]),
            ("Avro", SkillCategory.DATA_AI.value, ["Avro"]),
            ("Parquet", SkillCategory.DATA_AI.value, ["Parquet"]),
            ("ORC", SkillCategory.DATA_AI.value, ["ORC"]),
            ("Jupyter", SkillCategory.DATA_AI.value, ["Jupyter", "Jupyter Notebooks"]),
            ("Zeppelin", SkillCategory.DATA_AI.value, ["Zeppelin"]),
            ("Metabase", SkillCategory.DATA_AI.value, ["Metabase"]),
            ("Superset", SkillCategory.DATA_AI.value, ["Superset", "Apache Superset"]),
            ("Looker", SkillCategory.DATA_AI.value, ["Looker"]),
            ("Qlik", SkillCategory.DATA_AI.value, ["Qlik", "QlikView", "Qlik Sense"]),
            ("MicroStrategy", SkillCategory.DATA_AI.value, ["MicroStrategy"]),
            ("IBM Cognos", SkillCategory.DATA_AI.value, ["Cognos", "IBM Cognos"]),
            ("SAP BusinessObjects", SkillCategory.DATA_AI.value, ["BusinessObjects", "SAP BO"]),
            ("Excel", SkillCategory.TOOLS.value, ["Excel", "Microsoft Excel"]),
            ("Google Sheets", SkillCategory.TOOLS.value, ["Google Sheets", "GSheets"]),
            ("VBA", SkillCategory.PROGRAMMING_LANGUAGE.value, ["VBA", "Visual Basic for Applications"]),
            ("MATLAB", SkillCategory.PROGRAMMING_LANGUAGE.value, ["MATLAB"]),
            ("Mathematica", SkillCategory.PROGRAMMING_LANGUAGE.value, ["Mathematica"]),
            ("SAS", SkillCategory.DATA_AI.value, ["SAS"]),
            ("SPSS", SkillCategory.DATA_AI.value, ["SPSS"]),
            ("Stata", SkillCategory.DATA_AI.value, ["Stata"]),
            ("EViews", SkillCategory.DATA_AI.value, ["EViews"]),
            ("Minitab", SkillCategory.DATA_AI.value, ["Minitab"]),
            ("JMP", SkillCategory.DATA_AI.value, ["JMP"]),
            ("RapidMiner", SkillCategory.DATA_AI.value, ["RapidMiner"]),
            ("KNIME", SkillCategory.DATA_AI.value, ["KNIME"]),
            ("Alteryx", SkillCategory.DATA_AI.value, ["Alteryx"]),
            ("Dataiku", SkillCategory.DATA_AI.value, ["Dataiku"]),
            ("Databricks", SkillCategory.DATA_AI.value, ["Databricks"]),
            ("Cloudera", SkillCategory.DATA_AI.value, ["Cloudera"]),
            ("Hortonworks", SkillCategory.DATA_AI.value, ["Hortonworks"]),
            ("MapR", SkillCategory.DATA_AI.value, ["MapR"]),
            ("Solr", SkillCategory.DATABASE.value, ["Solr", "Apache Solr"]),
            ("Sphinx", SkillCategory.DATABASE.value, ["Sphinx"]),
            ("Algolia", SkillCategory.DATABASE.value, ["Algolia"]),
            ("Meilisearch", SkillCategory.DATABASE.value, ["Meilisearch"]),
            ("Typesense", SkillCategory.DATABASE.value, ["Typesense"]),
            ("Redisearch", SkillCategory.DATABASE.value, ["Redisearch"]),
            ("Zookeeper", SkillCategory.DEVOPS.value, ["Zookeeper", "Apache Zookeeper"]),
            ("Etcd", SkillCategory.DEVOPS.value, ["Etcd"]),
            ("CoreOS", SkillCategory.DEVOPS.value, ["CoreOS"]),
            ("Alpine Linux", SkillCategory.DEVOPS.value, ["Alpine Linux", "Alpine"]),
            ("Debian", SkillCategory.DEVOPS.value, ["Debian"]),
            ("Red Hat", SkillCategory.DEVOPS.value, ["Red Hat", "RHEL"]),
            ("Fedora", SkillCategory.DEVOPS.value, ["Fedora"]),
            ("Arch Linux", SkillCategory.DEVOPS.value, ["Arch Linux", "Arch"]),
            ("macOS", SkillCategory.DEVOPS.value, ["macOS", "Mac OS X", "OSX"]),
            ("Windows Server", SkillCategory.DEVOPS.value, ["Windows Server"]),
            ("IIS", SkillCategory.DEVOPS.value, ["IIS", "Internet Information Services"]),
            ("Tomcat", SkillCategory.DEVOPS.value, ["Tomcat", "Apache Tomcat"]),
            ("Jetty", SkillCategory.DEVOPS.value, ["Jetty"]),
            ("GlassFish", SkillCategory.DEVOPS.value, ["GlassFish"]),
            ("WildFly", SkillCategory.DEVOPS.value, ["WildFly", "JBoss"]),
            ("WebSphere", SkillCategory.DEVOPS.value, ["WebSphere", "IBM WebSphere"]),
            ("WebLogic", SkillCategory.DEVOPS.value, ["WebLogic", "Oracle WebLogic"]),
            ("WordPress", SkillCategory.FRONTEND.value, ["WordPress", "WP"]),
            ("Drupal", SkillCategory.FRONTEND.value, ["Drupal"]),
            ("Joomla", SkillCategory.FRONTEND.value, ["Joomla"]),
            ("Magento", SkillCategory.FRONTEND.value, ["Magento"]),
            ("Shopify", SkillCategory.FRONTEND.value, ["Shopify"]),
            ("WooCommerce", SkillCategory.FRONTEND.value, ["WooCommerce"]),
            ("PrestaShop", SkillCategory.FRONTEND.value, ["PrestaShop"]),
            ("Salesforce", SkillCategory.TOOLS.value, ["Salesforce", "SFDC"]),
            ("HubSpot", SkillCategory.TOOLS.value, ["HubSpot"]),
            ("Zendesk", SkillCategory.TOOLS.value, ["Zendesk"]),
            ("ServiceNow", SkillCategory.TOOLS.value, ["ServiceNow"]),
            ("SAP ERP", SkillCategory.TOOLS.value, ["SAP", "SAP ERP"]),
            ("Oracle ERP", SkillCategory.TOOLS.value, ["Oracle ERP"]),
            ("NetSuite", SkillCategory.TOOLS.value, ["NetSuite"]),
            ("Microsoft Dynamics", SkillCategory.TOOLS.value, ["Microsoft Dynamics", "Dynamics 365"]),
            ("Odoo", SkillCategory.TOOLS.value, ["Odoo"]),
            ("Zoho", SkillCategory.TOOLS.value, ["Zoho"]),
            ("Trello", SkillCategory.TOOLS.value, ["Trello", "Trello Board"]),
            ("Asana", SkillCategory.TOOLS.value, ["Asana", "Asana Task Management"]),
            ("Notion", SkillCategory.TOOLS.value, ["Notion"]),
            ("Slack", SkillCategory.TOOLS.value, ["Slack", "Slack API"]),
        ]

        phase_15b_aliases = [
            # Security / cyber
            ("Cybersecurity", "Cybersécurité", SkillCategory.SECURITY.value),
            ("Cybersecurity", "Cybersecurité", SkillCategory.SECURITY.value),
            ("Cybersecurity", "Sécurité informatique", SkillCategory.SECURITY.value),
            ("Cybersecurity", "Security", SkillCategory.SECURITY.value),
            ("Cybersecurity", "Fondamentaux de sécurité", SkillCategory.SECURITY.value),
            ("Cybersecurity", "Frameworks de sécurité", SkillCategory.SECURITY.value),
            ("Cybersecurity", "Architecture de sécurité", SkillCategory.SECURITY.value),
            ("Cybersecurity", "Sécurité des Systèmes d'Information", SkillCategory.SECURITY.value),
            ("Cybersecurity", "Sécurité système", SkillCategory.SECURITY.value),
            ("Network Security", "Sécurité réseau", SkillCategory.SECURITY.value),
            ("Network Security", "Réseau sécurisé", SkillCategory.SECURITY.value),
            ("Network Security", "Réseaux", SkillCategory.SECURITY.value),
            ("Network Security", "Réseau", SkillCategory.SECURITY.value),
            ("Network Security", "Networking", SkillCategory.SECURITY.value),
            ("Application Security", "Sécurité des applications", SkillCategory.SECURITY.value),
            ("Database Security", "Sécurité des bases de données", SkillCategory.SECURITY.value),
            ("Cloud Security", "Sécurité cloud", SkillCategory.SECURITY.value),
            ("Vulnerability Management", "Gestion des vulnérabilités", SkillCategory.SECURITY.value),
            ("Vulnerability Management", "Analyse de vulnérabilités", SkillCategory.SECURITY.value),
            ("Risk Analysis", "Analyse de risques", SkillCategory.SECURITY.value),
            ("Risk Analysis", "Évaluation des risques", SkillCategory.SECURITY.value),
            ("Cryptography", "Cryptographie", SkillCategory.SECURITY.value),
            ("GRC", "Gouvernance, Risques et Conformité (GRC)", SkillCategory.SECURITY.value),
            ("GRC", "GRC", SkillCategory.SECURITY.value),
            ("ISO 27001", "ISO 27001", SkillCategory.SECURITY.value),
            ("ISO 27005", "ISO 27005", SkillCategory.SECURITY.value),
            ("NIS2", "NIS2", SkillCategory.SECURITY.value),
            ("IAM", "IAM", SkillCategory.SECURITY.value),
            ("SIEM", "SIEM", SkillCategory.SECURITY.value),
            ("Entra ID", "Entra ID", SkillCategory.SECURITY.value),
            ("Active Directory", "Active Directory", SkillCategory.SECURITY.value),
            # Systems / network / support
            ("Windows", "Windows", SkillCategory.TOOLS.value),
            ("PowerShell", "PowerShell", SkillCategory.TOOLS.value),
            ("Microsoft 365", "Microsoft 365", SkillCategory.TOOLS.value),
            ("Office 365", "Office 365", SkillCategory.TOOLS.value),
            ("TCP/IP", "TCP/IP", SkillCategory.SECURITY.value),
            ("LAN", "LAN", SkillCategory.SECURITY.value),
            ("WAN", "WAN", SkillCategory.SECURITY.value),
            ("VLAN", "VLAN", SkillCategory.SECURITY.value),
            ("VPN", "VPN", SkillCategory.SECURITY.value),
            ("Firewall", "Firewall", SkillCategory.SECURITY.value),
            ("Troubleshooting", "Troubleshooting", SkillCategory.TOOLS.value),
            ("GLPI", "GLPI", SkillCategory.TOOLS.value),
            # DevOps / cloud
            ("DevOps", "DevOps", SkillCategory.DEVOPS.value),
            ("Cloud", "Cloud", SkillCategory.CLOUD.value),
            ("OpenShift", "OpenShift", SkillCategory.DEVOPS.value),
            ("Azure DevOps", "Azure DevOps", SkillCategory.DEVOPS.value),
            ("Infrastructure as Code", "Infrastructure as Code", SkillCategory.DEVOPS.value),
            ("Argo CD", "ArgoCD", SkillCategory.DEVOPS.value),
            ("Helm", "Helm", SkillCategory.DEVOPS.value),
            ("Dynatrace", "Dynatrace", SkillCategory.DEVOPS.value),
            ("VMware", "VmWare", SkillCategory.DEVOPS.value),
            ("Monitoring", "Monitoring", SkillCategory.DEVOPS.value),
            ("Scripting", "Scripting", SkillCategory.DEVOPS.value),
            # API / software engineering
            ("REST API", "API REST", SkillCategory.BACKEND.value),
            ("API", "API", SkillCategory.BACKEND.value),
            ("Software Testing", "Tests unitaires", SkillCategory.TESTING.value),
            ("Automated Testing", "Automated Testing", SkillCategory.TESTING.value),
            ("Software Quality", "Software Quality", SkillCategory.TESTING.value),
            ("Design Patterns", "Design Patterns", SkillCategory.BACKEND.value),
            ("Object-Oriented Programming", "Programmation Orientée Objet", SkillCategory.PROGRAMMING_LANGUAGE.value),
            ("Object-Oriented Programming", "Object-Oriented Programming", SkillCategory.PROGRAMMING_LANGUAGE.value),
            ("Debugging", "Debugging", SkillCategory.TOOLS.value),
            ("Code Review", "Code review", SkillCategory.METHODOLOGY.value),
            ("UML", "UML", SkillCategory.METHODOLOGY.value),
            # Data / AI
            ("Data Modeling", "Data Modeling", SkillCategory.DATA_AI.value),
            ("Data Engineering", "Data Engineering", SkillCategory.DATA_AI.value),
            ("ETL", "ETL", SkillCategory.DATA_AI.value),
            ("dbt", "dbt", SkillCategory.DATA_AI.value),
            ("NoSQL", "NoSQL", SkillCategory.DATABASE.value),
            ("Azure Data Factory", "Azure Data Factory", SkillCategory.DATA_AI.value),
            ("PySpark", "PySpark", SkillCategory.DATA_AI.value),
            ("Prompt Engineering", "Prompt Engineering", SkillCategory.DATA_AI.value),
            ("RAG", "RAG (Retrieval Augmented Generation)", SkillCategory.DATA_AI.value),
            ("RAG", "RAG (Retrieval-Augmented Generation)", SkillCategory.DATA_AI.value),
            ("Azure OpenAI", "Azure OpenAI", SkillCategory.DATA_AI.value),
            ("Copilot Studio", "Copilot Studio", SkillCategory.DATA_AI.value),
            ("Power Automate", "Power Automate", SkillCategory.TOOLS.value),
            ("Power Platform", "Power Platform", SkillCategory.TOOLS.value),
            # ERP / legacy / SAP
            ("ERP", "ERP", SkillCategory.TOOLS.value),
            ("ABAP", "ABAP", SkillCategory.PROGRAMMING_LANGUAGE.value),
            ("SAP ECC6", "SAP ECC6", SkillCategory.TOOLS.value),
            ("SAP S/4HANA", "SAP S/4HANA", SkillCategory.TOOLS.value),
            ("SAP Fiori", "SAP Fiori", SkillCategory.FRONTEND.value),
            ("SAP UI5", "SAP UI5", SkillCategory.FRONTEND.value),
            ("COBOL", "COBOL", SkillCategory.PROGRAMMING_LANGUAGE.value),
            ("Mainframe", "Mainframe", SkillCategory.TOOLS.value),
            ("JCL", "JCL", SkillCategory.PROGRAMMING_LANGUAGE.value),
            ("CICS", "CICS", SkillCategory.TOOLS.value),
            ("IBM Mainframe", "IBM Mainframe", SkillCategory.TOOLS.value),
            # Embedded / industrial
            ("Embedded Systems", "systèmes embarqués", SkillCategory.OTHER.value),
            ("Embedded Linux", "Linux embarqué", SkillCategory.OTHER.value),
            ("RTOS", "RTOS", SkillCategory.OTHER.value),
            ("Yocto Project", "Yocto Project", SkillCategory.OTHER.value),
            ("Buildroot", "Buildroot", SkillCategory.OTHER.value),
            ("SPI", "SPI", SkillCategory.OTHER.value),
            ("I2C", "I2C", SkillCategory.OTHER.value),
            ("UDP", "UDP", SkillCategory.OTHER.value),
            ("Ethernet", "Ethernet", SkillCategory.OTHER.value),
            # Software delivery
            ("Software Development", "développement logiciel", SkillCategory.BACKEND.value),
            ("Software Development", "Développer un logiciel, un système d'informations, une application", SkillCategory.BACKEND.value),
            ("Software Analysis", "analyse et conception", SkillCategory.BACKEND.value),
            ("Software Architecture", "Conception d'architecture logicielle", SkillCategory.BACKEND.value),
            ("Software Architecture", "Conception d'architecture système", SkillCategory.BACKEND.value),
            ("Software Testing", "tests et qualité", SkillCategory.TESTING.value),
            ("Software Deployment", "déploiement et maintenance", SkillCategory.DEVOPS.value),
            ("Software Deployment", "Optimisation de développement", SkillCategory.DEVOPS.value),
            ("Technical Documentation", "Documentation technique", SkillCategory.METHODOLOGY.value),
            ("Technical Documentation", "Documentation de support", SkillCategory.METHODOLOGY.value),
            ("Requirements Analysis", "Analyse des besoins", SkillCategory.METHODOLOGY.value),
            ("Technical Watch", "Veille technologique", SkillCategory.METHODOLOGY.value),
            ("Specifications Writing", "Rédaction de cahier des charges", SkillCategory.METHODOLOGY.value),
            ("Digital Project Management", "Gestion de projet numérique", SkillCategory.METHODOLOGY.value),
            ("Technology Selection", "Sélection de technologies", SkillCategory.METHODOLOGY.value),
            # Data / automation
            ("Data Modeling", "Modélisation de données", SkillCategory.DATA_AI.value),
            ("Data Warehouse", "Architecture d'entrepôts de données décisionnelles", SkillCategory.DATA_AI.value),
            ("RPA", "RPA", SkillCategory.TOOLS.value),
            ("Automation", "Surveillance des systèmes automatisés", SkillCategory.TOOLS.value),
            ("Blockchain", "Blockchain", SkillCategory.TOOLS.value),
            # IT support / technician
            ("IT Support", "Assistance technique", SkillCategory.TOOLS.value),
            ("IT Support", "Support aux utilisateurs", SkillCategory.TOOLS.value),
            ("System and Network Administration", "Systèmes et Réseaux", SkillCategory.SECURITY.value),
            ("IT Asset Management", "Gestion de parc informatique", SkillCategory.TOOLS.value),
            ("IT Asset Management", "Gestion des consommables", SkillCategory.TOOLS.value),
            ("Hardware Maintenance", "Maintenance matériel", SkillCategory.TOOLS.value),
            ("Hardware Troubleshooting", "Diagnostic de pannes matérielles et logicielles", SkillCategory.TOOLS.value),
            ("Hardware Repair", "Réparation de composants", SkillCategory.TOOLS.value),
            ("Operating System Installation", "Installation et configuration de systèmes d'exploitation", SkillCategory.TOOLS.value),
            ("Software Installation", "Installation et configuration de logiciels", SkillCategory.TOOLS.value),
            ("Workstation Deployment", "Préparation de postes informatiques", SkillCategory.TOOLS.value),
            ("IT Deployment", "Déploiement informatique", SkillCategory.DEVOPS.value),
            ("IT Inventory Management", "Gestion des stocks de matériel informatique", SkillCategory.TOOLS.value),
            ("Intervention Tracking", "Suivi des interventions", SkillCategory.TOOLS.value),
            # Security ops / audit / recovery
            ("Security Planning", "Security Plan Development", SkillCategory.SECURITY.value),
            ("Security Implementation", "Security Solution Implementation", SkillCategory.SECURITY.value),
            ("Security Audit", "Organizational Audits", SkillCategory.SECURITY.value),
            ("Security Audit", "Technical Audits", SkillCategory.SECURITY.value),
            ("Disaster Recovery", "Disaster Recovery Plan (DRP) Definition", SkillCategory.SECURITY.value),
            ("Disaster Recovery", "Disaster Recovery Plan (DRP) Deployment", SkillCategory.SECURITY.value),
            ("Disaster Recovery", "Disaster Recovery Plan (PRA)", SkillCategory.SECURITY.value),
            # Rail / safety software
            ("ERTMS", "ERTMS", SkillCategory.TESTING.value),
            ("EN 50128", "EN 50128", SkillCategory.TESTING.value),
            ("SIL4", "SIL4", SkillCategory.TESTING.value),
            # Data center / infrastructure-adjacent
            ("Data Center Operations", "Data Center Operations", SkillCategory.DEVOPS.value),
            ("Root Cause Analysis", "Root Cause Analysis (RCA)", SkillCategory.METHODOLOGY.value),
            ("Root Cause Analysis", "Analyse des causes racines", SkillCategory.METHODOLOGY.value),
            ("SLA Management", "SLA Management", SkillCategory.METHODOLOGY.value),
            ("SOP Development", "Standard Operating Procedure (SOP) Development", SkillCategory.METHODOLOGY.value),
            ("Safety Procedures", "Safety Procedures", SkillCategory.METHODOLOGY.value),
            ("CMMS", "CMMS", SkillCategory.TOOLS.value),
            ("Preventive Maintenance", "Maintenance préventive", SkillCategory.TOOLS.value),
            ("Corrective Maintenance", "Maintenance corrective", SkillCategory.TOOLS.value),
            ("Diagnostic", "Diagnostic", SkillCategory.TOOLS.value),
            ("Troubleshooting", "Dépannage", SkillCategory.TOOLS.value),
        ]

        for name, category, aliases in extra_skills:
            seed_data.append(SkillSeedItem(canonical=name, category=category, aliases=aliases))

        phase_15b_grouped = {}
        for canonical, alias, cat in phase_15b_aliases:
            if canonical not in phase_15b_grouped:
                phase_15b_grouped[canonical] = {"category": cat, "aliases": set()}
            phase_15b_grouped[canonical]["aliases"].add(alias)

        for canonical, data in phase_15b_grouped.items():
            seed_data.append(SkillSeedItem(
                canonical=canonical,
                category=data["category"],
                aliases=sorted(data["aliases"])
            ))

        phase_15d_grouped = {}
        for decision in approved_taxonomy_decisions():
            canonical = decision.target_canonical_skill
            category = decision.target_category or SkillCategory.OTHER.value
            if canonical not in phase_15d_grouped:
                phase_15d_grouped[canonical] = {"category": category, "aliases": set()}
            phase_15d_grouped[canonical]["aliases"].add(decision.raw_skill_text)

        for canonical, data in phase_15d_grouped.items():
            seed_data.append(SkillSeedItem(
                canonical=canonical,
                category=data["category"],
                aliases=sorted(data["aliases"])
            ))

        skills_created = 0
        aliases_created = 0
        alias_conflicts = []

        with transaction.atomic():
            for item in seed_data:
                canonical: str = item["canonical"]
                safe_canonical: str = canonical.replace('#', 'sharp').replace('+', 'plus').replace('.', 'dot')
                slug = slugify(safe_canonical)
                if not slug:
                    slug = normalize_skill_text(canonical).replace(' ', '-')

                skill, created = Skill.objects.get_or_create(
                    canonical_name=canonical,
                    defaults={
                        'slug': slug,
                        'category': item["category"],
                        'source': 'seed'
                    }
                )
                if created:
                    skills_created += 1

                aliases: List[str] = item["aliases"]
                for alias_text in aliases:
                    normalized = normalize_skill_text(alias_text)
                    if normalized:
                        alias_obj = SkillAlias.objects.filter(normalized_alias=normalized).first()
                        if alias_obj:
                            if alias_obj.skill_id != skill.id:
                                conflict = {
                                    "alias": alias_text,
                                    "normalized_alias": normalized,
                                    "existing_skill": alias_obj.skill.canonical_name,
                                    "requested_skill": skill.canonical_name,
                                }
                                alias_conflicts.append(conflict)
                                print(
                                    "Conflict: "
                                    f"Alias '{normalized}' maps to '{alias_obj.skill.canonical_name}' "
                                    f"but tried to map to '{skill.canonical_name}'"
                                )
                        else:
                            SkillAlias.objects.create(
                                skill=skill,
                                alias=alias_text,
                                normalized_alias=normalized,
                                language='unknown'
                            )
                            aliases_created += 1

        return {
            "skills_created": skills_created,
            "aliases_created": aliases_created,
            "alias_conflicts": alias_conflicts,
        }
