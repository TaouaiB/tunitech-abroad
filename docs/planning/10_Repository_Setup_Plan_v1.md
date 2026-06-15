# TuniTech Abroad - Repository Setup Plan v1

<!-- Converted to Markdown for repository/agent context. The original generated PDF/DOCX remains the formatted source-of-truth document. -->


### 1. Document Purpose
This document defines the exact repository setup plan for TuniTech Abroad MVP.
It comes after:
BRD v1
PRD v1
Technical Architecture v1
Database Schema v1
Service Contracts v1
Data Flow / Sequence Diagrams v1
Page + URL + View Map v1
Implementation Roadmap v1
MVP Backlog v1
It comes before:
First Coding Phase
This is the final planning document before implementation.
### 2. Final Stack Decision
The MVP repository will use:
Backend:
- Django
- Django ORM
- PostgreSQL
- Redis
- Celery
- Celery Beat
- django-allauth
Frontend:
- Django templates
- HTMX
- Tailwind CSS
- Alpine.js only where needed
AI:
- OpenRouter
- cached calls
- strict limits
- service-layer access only
CV Parsing:
- PyMuPDF or pdfplumber
- deterministic regex for exact fields
- optional LLM structured extraction
- no OCR in MVP
Not used:
React
Next.js
Angular
FastAPI
MongoDB
SQLAlchemy
SPA architecture

### 3. Repository Name
Recommended repository name:
tunitech-abroad
Project root:
tunitech-abroad/
Django project package:
config/
Local Django apps:
apps/
### 4. High-Level Folder Structure
tunitech-abroad/
  README.md
  .gitignore
  .env.example
  .editorconfig
  pyproject.toml
  requirements/
    base.txt
    local.txt
    production.txt
    test.txt
  docker-compose.yml
  Dockerfile
  Makefile
  manage.py
  config/
    __init__.py
    asgi.py
    wsgi.py
    celery.py
    urls.py
    settings/
      __init__.py
      base.py
      local.py
      production.py
      test.py
  apps/
    __init__.py
    accounts/
    profiles/
    skills/
    jobs/
    cvs/
    matching/
    recommendations/
    llm/
    notifications/
    privacy/
    analytics/
    core/
    dashboard/
  templates/
    base.html
    components/
    core/

account/
    jobs/
    dashboard/
    cvs/
    matching/
    recommendations/
    notifications/
    privacy/
  static/
    src/
      input.css
      app.js
    dist/
  media/
    .gitkeep
  tests/
    __init__.py
    factories/
    integration/
    unit/
    views/
  docs/
    planning/
    architecture/
    operations/
  scripts/
    wait_for_db.py
### 5. App Structure Pattern
Each Django app should follow the same internal pattern where useful.
Example for jobs:
apps/jobs/
  __init__.py
  admin.py
  apps.py
  models.py
  urls.py
  views.py
  forms.py
  tasks.py
  selectors.py
  services/
    __init__.py
    ingestion.py
    fixture_ingestion.py
    normalization.py
    classification.py
    freshness.py
    revalidation.py
    search.py
    query.py
    skill_extraction.py
    france_travail/
      __init__.py
      client.py
  tests/
    __init__.py
    test_models.py
    test_services.py
    test_views.py
For simple apps, not every file is needed immediately.

### 6. Django Apps to Create
Create these apps from the start:
accounts
profiles
skills
jobs
cvs
matching
recommendations
llm
notifications
privacy
analytics
core
dashboard
Reason:
The schema and service layer are already defined.
Creating the app boundaries early prevents messy file movement later.
### 7. Settings Structure
Use split settings:
config/settings/base.py
config/settings/local.py
config/settings/production.py
config/settings/test.py
7.1 base.py
Contains shared config:
INSTALLED_APPS
MIDDLEWARE
TEMPLATES
AUTH_USER_MODEL
DATABASES from env
STATIC settings
MEDIA settings
allauth base settings
Celery settings
logging base
7.2 local.py
Contains local development settings:
DEBUG = True
console email backend
local static/media
local allowed hosts
developer-friendly logging
7.3 production.py
Contains production-safe settings:
DEBUG = False
secure cookies
CSRF secure
allowed hosts from env
email provider settings
static/media production config
security headers

7.4 test.py
Contains test settings:
fast password hasher
test database
Celery eager mode where useful
console/dummy email backend
### 8. Environment Variables
Create .env.example.
Required variables:
DJANGO_SETTINGS_MODULE=config.settings.local
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
POSTGRES_DB=tunitech_abroad
POSTGRES_USER=tunitech
POSTGRES_PASSWORD=tunitech
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=no-reply@tunitechabroad.local
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
FRANCE_TRAVAIL_CLIENT_ID=
FRANCE_TRAVAIL_CLIENT_SECRET=
FRANCE_TRAVAIL_BASE_URL=
OPENROUTER_API_KEY=
OPENROUTER_DEFAULT_MODEL=
MAX_CV_UPLOAD_SIZE_MB=5
MAX_LLM_CALLS_PER_USER_DAY=10
MAX_MATCH_EXPLANATIONS_PER_USER_DAY=5
Never commit .env.
### 9. Requirements Files
Use requirements split:
requirements/base.txt
requirements/local.txt
requirements/production.txt
requirements/test.txt
9.1 base.txt
Core packages:
Django
psycopg[binary]
django-allauth
celery
redis

python-dotenv
requests
httpx
PyMuPDF
pdfplumber
Pillow
django-htmx
whitenoise
gunicorn
Optional but useful:
django-widget-tweaks
django-filter
9.2 local.txt
Development packages:
-r base.txt
django-debug-toolbar
ipython
9.3 test.txt
Testing packages:
-r base.txt
pytest
pytest-django
pytest-cov
factory-boy
freezegun
responses
9.4 production.txt
Production packages:
-r base.txt
sentry-sdk optional
### 10. Docker Compose
Local services:
postgres
redis
Optional app services later:
web
worker
beat
MVP local-first approach:
Run PostgreSQL and Redis in Docker.
Run Django and Celery from local virtual environment.
Reason:
Simpler debugging on Windows.
Less Docker complexity during early development.
Later, full Docker app services can be added.
### 11. Docker Compose Services

Initial docker-compose.yml should include:
postgres:
  image: postgres
  ports:
    - "5432:5432"
  environment:
    POSTGRES_DB
    POSTGRES_USER
    POSTGRES_PASSWORD
  volumes:
    postgres_data
redis:
  image: redis
  ports:
    - "6379:6379"
Do not include production secrets.
### 12. Celery Setup
Create:
config/celery.py
Pattern:
load Django settings
create Celery app
load config from Django settings
auto-discover tasks
In config/__init__.py:
import celery app
Celery queues for MVP:
default
ingestion
cv
recommendations
email
privacy
llm
Initial tasks:
debug_task
parse_cv
normalize_raw_job_record
extract_job_skills
refresh_user_recommendations
send_weekly_digest
process_account_deletion
### 13. URL Structure
Root config/urls.py should include:
/
accounts/
jobs/
dashboard/
email/
privacy/
terms/
health/
admin/

Include app URLs:
path("", include("apps.core.urls"))
path("accounts/", include("allauth.urls"))
path("jobs/", include("apps.jobs.urls"))
path("dashboard/", include("apps.dashboard.urls"))
path("email/", include("apps.notifications.urls"))
path("", include("apps.privacy.urls"))
path("admin/", admin.site.urls)
### 14. Template Setup
Base template:
templates/base.html
Required components:
templates/components/navbar.html
templates/components/footer.html
templates/components/alerts.html
templates/components/pagination.html
templates/components/badge.html
Dashboard base:
templates/dashboard/base_dashboard.html
All templates should extend either:
base.html
dashboard/base_dashboard.html
### 15. Static Files Setup
Use:
static/src/input.css
static/src/app.js
static/dist/
Tailwind source:
static/src/input.css
Compiled output:
static/dist/styles.css
HTMX can be loaded by:
static vendor file
or CDN for local MVP
Preferred for portfolio/professional project:
vendor static file
### 16. Tailwind Setup
Recommended simple setup:
npm init
install tailwindcss
tailwind.config.js
Content paths:
templates/**/*.html

apps/**/*.py
Build commands:
npm run dev
npm run build
Package scripts:
"dev": "tailwindcss -i ./static/src/input.css -o ./static/dist/styles.css --watch"
"build": "tailwindcss -i ./static/src/input.css -o ./static/dist/styles.css --minify"
### 17. HTMX Setup
Install:
django-htmx
Middleware:
django_htmx.middleware.HtmxMiddleware
Use HTMX only for:
quick match
save/unsave job
CV parse status polling
match explanation
recommendation status refresh
email preference toggles
HTMX endpoints return partial templates only.
### 18. Authentication Setup
Use:
django-allauth
Required:
email/password signup
email verification
Google login
GitHub login
Important settings to verify during implementation:
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_UNIQUE_EMAIL = True
LOGIN_REDIRECT_URL = "/dashboard/"
ACCOUNT_LOGOUT_REDIRECT_URL = "/"
Social account behavior should support safe linking by verified email if available.
Do not add:
Facebook login
LinkedIn login
phone OTP
in MVP.
### 19. Custom User Model
Create custom User before first migration.
File:

apps/accounts/models.py
Recommended:
class User(AbstractUser):
    email = EmailField(unique=True)
Keep username if simpler with allauth, but make email unique.
Set:
AUTH_USER_MODEL = "accounts.User"
### 20. Services Folder Pattern
Each service module should expose clear service classes or functions.
Example:
apps/matching/services/scoring.py
Contains:
MatchScoringService
FitScoreResult
Rule:
Services can import models.
Views import services.
Tasks import services.
Models do not import services unless absolutely harmless.
### 21. Selectors Pattern
For read-heavy reusable queries, use selectors.
Example:
apps/jobs/selectors.py
Purpose:
centralize complex querysets
avoid duplicating filters in views/services
Examples:
get_active_jobs()
get_public_job_by_id(public_id)
get_user_saved_jobs(user)
get_user_recommendations(user)
Do not overuse at the start. Add selectors when query reuse appears.
### 22. Management Commands
Create management commands for seed and operations.
Required:
seed_system_settings
seed_skills
seed_job_sources
load_job_fixtures
rebuild_job_search_vectors
cleanup_expired_quick_matches

Later:
sync_france_travail_jobs
retry_failed_normalizations
refresh_recommendations_for_active_users
Command location example:
apps/skills/management/commands/seed_skills.py
apps/core/management/commands/seed_system_settings.py
apps/jobs/management/commands/load_job_fixtures.py
### 23. Test Structure
Use pytest.
Root:
tests/
App-level tests are also acceptable:
apps/jobs/tests/
apps/cvs/tests/
apps/matching/tests/
Recommended practical structure:
tests/
  conftest.py
  factories/
    users.py
    profiles.py
    skills.py
    jobs.py
    cvs.py
  unit/
    test_skill_normalizer.py
    test_job_classification.py
    test_match_scoring.py
  integration/
    test_job_fixture_ingestion.py
    test_cv_parsing_flow.py
    test_recommendation_refresh.py
  views/
    test_public_jobs.py
    test_dashboard_auth.py
### 24. Factory Setup
Use factory-boy.
Factories:
UserFactory
CandidateProfileFactory
SkillFactory
SkillAliasFactory
JobSourceFactory
RawJobRecordFactory
NormalizedJobFactory
CVUploadFactory
MatchResultFactory
JobRecommendationFactory
Factories are important because this project has many related models.

### 25. Initial Git Branch Strategy
Simple solo-dev branch strategy:
main
dev
feature/*
Recommended:
main = stable
dev = active integration
feature/phase-0-setup
feature/phase-1-auth
Do not overcomplicate with release branches.
### 26. First Commit Sequence
Recommended commits:
commit 1: initialize repository
commit 2: create Django project skeleton
commit 3: add settings split and env example
commit 4: add Docker Compose for PostgreSQL and Redis
commit 5: add Celery base config
commit 6: add custom User model
commit 7: add django-allauth base setup
commit 8: add base templates and homepage
This gives a clean professional history.
### 27. Makefile Commands
Add a Makefile for common commands.
Recommended commands:
make run
make migrate
make migrations
make shell
make test
make worker
make beat
make seed
make tailwind
make docker-up
make docker-down
make lint
Example behavior:
make docker-up -> starts postgres and redis
make run -> starts Django dev server
make worker -> starts Celery worker
make beat -> starts Celery Beat
make test -> runs pytest
### 28. Local Development Commands
Expected local setup flow:
git clone <repo>
cd tunitech-abroad
python -m venv .venv

source .venv/bin/activate
pip install -r requirements/local.txt
cp .env.example .env
docker compose up -d
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
On Windows PowerShell:
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements/local.txt
copy .env.example .env
docker compose up -d
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
### 29. Local Runtime Commands
Run Django:
python manage.py runserver
Run Celery worker:
celery -A config worker -l info
Run Celery Beat:
celery -A config beat -l info
Run Tailwind watcher:
npm run dev
### 30. Logging Setup
Minimum logging channels:
django
apps.jobs
apps.cvs
apps.matching
apps.recommendations
apps.llm
apps.notifications
apps.privacy
Log:
task started
task completed
counts
status
duration
error summary
model IDs
Do not log:
full CV text
raw CV file content
API secrets
OAuth tokens
OpenRouter key
France Travail credentials
full email bodies

### 31. Security Baseline
From the start:
CSRF enabled
session auth enabled
admin protected
DEBUG from env
SECRET_KEY from env
ALLOWED_HOSTS from env
no secrets committed
private CV media
public routes use UUID public_id
Before production:
secure cookies
HTTPS
CSRF trusted origins
HSTS if applicable
production email provider
production database backup
### 32. Private Media Rule
CV files must not be publicly served.
Local development can store files under:
media/private/cvs/
But access must go through owner/admin checks.
Do not expose:
/media/private/cvs/<file>
as public URL.
Future production storage can use private object storage.
### 33. Database Setup
Use PostgreSQL from the beginning.
Database name:
tunitech_abroad
Local user:
tunitech
Required PostgreSQL features:
full-text search
GIN index on NormalizedJob.search_vector
optional pg_trgm later
Do not start with SQLite because:
PostgreSQL search behavior matters.
JSON fields and indexes matter.
Production will use PostgreSQL anyway.
### 34. Initial Seed Data

After migrations, seed:
system settings
skill taxonomy
skill aliases
job source: france_travail
prompt versions
sample jobs from fixtures
Initial commands:
python manage.py seed_system_settings
python manage.py seed_skills
python manage.py seed_job_sources
python manage.py load_job_fixtures
### 35. Fixture Data
Create:
fixtures/jobs/france_travail_sample_jobs.json
Purpose:
allow job ingestion and normalization development before live API
Fixture rules:
same path as real ingestion
RawJobRecord created
NormalizedJob created
NormalizedJobSkill created later
No separate fake logic.
### 36. First Coding Phase Scope
The first coding phase is Phase 0: Repository and Local Environment.
It includes only:
repository creation
Django skeleton
settings split
Docker Compose PostgreSQL/Redis
Celery base
.env.example
README
basic run confirmation
It does not include:
auth
models
jobs
CV parsing
matching
UI polish
LLM
email
Reason:
Build the foundation first.
Avoid creating business code before environment is stable.
### 37. Phase 0 Definition of Done

Phase 0 is done when:
Repository exists.
Django project starts.
PostgreSQL runs locally.
Redis runs locally.
Django connects to PostgreSQL.
Celery worker starts.
Celery Beat starts.
.env.example exists.
README setup instructions exist.
python manage.py check passes.
python manage.py migrate passes.
### 38. Recommended First Files to Create
README.md
.gitignore
.env.example
docker-compose.yml
requirements/base.txt
requirements/local.txt
requirements/test.txt
requirements/production.txt
manage.py
config/settings/base.py
config/settings/local.py
config/settings/production.py
config/settings/test.py
config/celery.py
config/urls.py
apps/__init__.py
### 39. README Minimum Content
README should include:
Project name
Project purpose
Tech stack
Local setup
Environment variables
Run commands
Celery commands
Test commands
Seed commands
Project structure
Keep README practical, not marketing-heavy.
### 40. .gitignore Requirements
Must ignore:
.venv/
.env
__pycache__/
*.pyc
db.sqlite3
media/
staticfiles/
node_modules/
.coverage
htmlcov/
.pytest_cache/
.DS_Store

.vscode/
.idea/
Do not ignore:
.env.example
media/.gitkeep
static/src/
static/dist/.gitkeep
### 41. Coding Start Rule
After this repository setup plan is accepted, coding starts.
First coding instruction should be:
Start Phase 0: create repository foundation for TuniTech Abroad.
The first implementation should not jump to models or features.
### 42. Documentation Status
After this document:
Planning documentation is complete.
Completed planning set:
BRD v1
PRD v1
Technical Architecture v1
Database Schema v1
Service Contracts v1
Data Flow / Sequence Diagrams v1
Page + URL + View Map v1
Implementation Roadmap v1
MVP Backlog v1
Repository Setup Plan v1
Next:
First Coding Phase
### 43. Final Repository Setup Decision
Use a clean modular Django monolith:
config for project settings
apps for business domains
services for business logic
tasks as thin Celery wrappers
templates for server-rendered UI
PostgreSQL as source of truth
Redis for queues and short-lived state
Django Admin for operations
This setup is strong enough for MVP and clean enough to expand later into:
multi-country jobs
training center dashboard
recruiter dashboard
paid reports
advanced analytics