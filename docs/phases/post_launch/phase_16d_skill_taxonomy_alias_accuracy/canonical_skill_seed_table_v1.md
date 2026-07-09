# Phase 16D — Canonical Skill Seed and Alias Table v1

## Purpose

This file prevents the implementation agent from inventing the taxonomy from scratch. Use it as the baseline for Phase 16D seed/alias work.

Rules:

```text
Use canonical Skill rows as stable labels.
Use SkillAlias rows for spelling, punctuation, language, and framework variants.
Do not auto-create canonical skills from unknown extracted text.
Unknowns go to UnmatchedSkillCandidate.
Seed command must be idempotent.
If the existing database already has a richer taxonomy, merge this table without destructive replacement.
```

## Canonical design decisions

### .NET ecosystem

Use separate canonical skills for broad ecosystem and major frameworks:

```text
.NET
ASP.NET Core
Entity Framework Core
C#
```

Mapping rule:

```text
"dotnet", ".net", ".net core" can map to .NET.
"asp.net core", "asp net core" maps to ASP.NET Core.
"ef core", "entity framework core" maps to Entity Framework Core.
"c sharp", "csharp" maps to C#.
```

Scoring rule later:

```text
ASP.NET Core required + candidate has ASP.NET Core = full match.
ASP.NET Core required + candidate has .NET + C# only = partial/related signal later, not full match.
```

## Seed table

| Category | Canonical skill | Required aliases |
|---|---|---|
| programming_language | Python | python, python3, py |
| programming_language | JavaScript | javascript, js, ecmascript |
| programming_language | TypeScript | typescript, ts |
| programming_language | Java | java, core java |
| programming_language | C# | c#, c sharp, csharp, c-sharp |
| programming_language | C++ | c++, cpp, c plus plus |
| programming_language | C | c language, langage c |
| programming_language | PHP | php |
| programming_language | Ruby | ruby |
| programming_language | Go | go, golang |
| programming_language | Rust | rust |
| programming_language | Kotlin | kotlin |
| programming_language | Swift | swift |
| programming_language | SQL | sql, structured query language |
| frontend | HTML | html, html5 |
| frontend | CSS | css, css3 |
| frontend | React | react, reactjs, react.js |
| frontend | Vue.js | vue, vuejs, vue.js |
| frontend | Angular | angular, angular2, angular 2+ |
| frontend | Svelte | svelte |
| frontend | Next.js | next, nextjs, next.js |
| frontend | Nuxt | nuxt, nuxtjs, nuxt.js |
| frontend | Tailwind CSS | tailwind, tailwindcss, tailwind css |
| frontend | Bootstrap | bootstrap, bootstrap css |
| frontend | Redux | redux, redux toolkit |
| frontend | jQuery | jquery, j query |
| backend | Django | django, django framework |
| backend | Django REST Framework | drf, django rest framework, django rest |
| backend | Flask | flask |
| backend | FastAPI | fastapi, fast api |
| backend | Node.js | node, nodejs, node.js, node js |
| backend | Express.js | express, expressjs, express.js |
| backend | NestJS | nest, nestjs, nest.js |
| backend | Spring Boot | spring boot, springboot |
| backend | Spring | spring framework, spring |
| backend | Laravel | laravel |
| backend | Symfony | symfony |
| backend | Ruby on Rails | rails, ruby on rails, ror |
| backend | .NET | .net, dotnet, dot net, .net core, dotnet core |
| backend | ASP.NET Core | asp.net core, asp net core, aspnet core, asp.net |
| backend | Entity Framework Core | entity framework core, ef core, entityframeworkcore |
| database | PostgreSQL | postgresql, postgres, postgre sql, pgsql |
| database | MySQL | mysql, my sql |
| database | MariaDB | mariadb, maria db |
| database | SQLite | sqlite, sqlite3 |
| database | SQL Server | sql server, microsoft sql server, mssql, ms sql |
| database | Oracle Database | oracle, oracle db, oracle database |
| database | MongoDB | mongodb, mongo, mongo db |
| database | Redis | redis |
| database | Elasticsearch | elasticsearch, elastic search, elk search |
| database | OpenSearch | opensearch, open search |
| database | DynamoDB | dynamodb, dynamo db |
| database | Cassandra | cassandra, apache cassandra |
| devops | Docker | docker, dockerfile |
| devops | Docker Compose | docker compose, docker-compose, compose |
| devops | Kubernetes | kubernetes, k8s |
| devops | Helm | helm, helm charts |
| devops | GitHub Actions | github actions, gh actions |
| devops | GitLab CI | gitlab ci, gitlab-ci, gitlab pipelines |
| devops | Jenkins | jenkins |
| devops | CI/CD | ci/cd, cicd, continuous integration, continuous delivery, continuous deployment |
| devops | Linux | linux, gnu linux |
| devops | Bash | bash, shell scripting, shell script |
| devops | Nginx | nginx |
| devops | Caddy | caddy, caddy server |
| devops | Apache HTTP Server | apache, apache httpd, httpd |
| devops | Terraform | terraform, tf |
| devops | Ansible | ansible |
| devops | Prometheus | prometheus |
| devops | Grafana | grafana |
| cloud | AWS | aws, amazon web services |
| cloud | Azure | azure, microsoft azure |
| cloud | Google Cloud | gcp, google cloud, google cloud platform |
| cloud | OVHcloud | ovh, ovhcloud, ovh cloud |
| cloud | Cloudflare | cloudflare |
| cloud | Heroku | heroku |
| cloud | DigitalOcean | digitalocean, digital ocean |
| testing | Pytest | pytest, py test |
| testing | unittest | python unittest, unittest |
| testing | Jest | jest |
| testing | Cypress | cypress |
| testing | Playwright | playwright |
| testing | Selenium | selenium |
| testing | JUnit | junit |
| testing | Postman | postman |
| data_ai | Pandas | pandas |
| data_ai | NumPy | numpy |
| data_ai | scikit-learn | sklearn, scikit learn, scikit-learn |
| data_ai | TensorFlow | tensorflow, tensor flow |
| data_ai | PyTorch | pytorch, torch |
| data_ai | LangChain | langchain, lang chain |
| data_ai | OpenAI API | openai, openai api |
| data_ai | OpenRouter | openrouter, open router |
| data_ai | NLP | nlp, natural language processing |
| data_ai | Machine Learning | machine learning, ml |
| data_ai | Deep Learning | deep learning, dl |
| mobile | React Native | react native, reactnative |
| mobile | Flutter | flutter, dart flutter |
| mobile | Android | android |
| mobile | iOS | ios, iphone app |
| tools | Git | git |
| tools | GitHub | github |
| tools | GitLab | gitlab |
| tools | Jira | jira |
| tools | Confluence | confluence |
| tools | Figma | figma |
| tools | VS Code | vscode, visual studio code |
| tools | Visual Studio | visual studio |
| tools | Power BI | power bi, powerbi |
| tools | Excel | excel, microsoft excel |
| methodology | Agile | agile |
| methodology | Scrum | scrum |
| methodology | Kanban | kanban |
| methodology | REST API | rest, restful api, rest api |
| methodology | GraphQL | graphql, graph ql |
| methodology | Microservices | microservices, micro services |
| methodology | MVC | mvc |
| methodology | OOP | oop, object oriented programming, object-oriented programming |
| methodology | TDD | tdd, test driven development |
| soft_skill | Communication | communication, communication skills |
| soft_skill | Teamwork | teamwork, team work |
| soft_skill | Problem Solving | problem solving, problem-solving |
| soft_skill | Leadership | leadership |
| soft_skill | Customer Support | customer support, technical support |

## Required regression mappings

Phase 16D tests must cover at minimum:

```text
".NET Core" -> .NET
"dotnet" -> .NET
"ASP.NET Core" -> ASP.NET Core
"EF Core" -> Entity Framework Core
"C sharp" -> C#
"csharp" -> C#
"Node.js" -> Node.js
"node js" -> Node.js
"ReactJS" -> React
"Postgres" -> PostgreSQL
"postgresql" -> PostgreSQL
"JS" -> JavaScript
"TS" -> TypeScript
"C++" -> C++
"CI/CD" -> CI/CD
"Docker Compose" -> Docker Compose
"GitHub Actions" -> GitHub Actions
```

## Future extension policy

When an unmatched candidate occurs frequently, map it to an existing Skill first. Create a new canonical Skill only when:

```text
it represents a distinct market-relevant capability
it is not just spelling/punctuation/language variation
it is useful for matching or missing-skill explanation
it has clear category and aliases
owner/admin approves it
```
