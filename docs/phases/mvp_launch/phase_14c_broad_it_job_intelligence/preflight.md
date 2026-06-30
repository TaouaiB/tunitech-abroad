# Preflight

Run before coding:

```bash
cd ~/Projects/tunitech-abroad
source .venv/bin/activate

git branch --show-current
git status --short
git diff --stat

python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py test apps.jobs apps.skills apps.matching apps.recommendations --settings=config.settings.local
```

Inspect current job data:

```bash
python manage.py shell --settings=config.settings.local -c "
from apps.jobs.models import NormalizedJob
from apps.jobs.services.relevance import JobITRelevanceService

for job in NormalizedJob.objects.filter(status='active').order_by('-published_at')[:30]:
    rel = JobITRelevanceService.assess(job)
    print('---')
    print(job.id, job.title, job.company_name)
    print('family/current relevance=', rel.is_relevant, rel.score, rel.reasons)
    print('required=', job.required_skills_json)
    print('optional=', job.optional_skills_json)
    print('job_skills=', list(job.job_skills.select_related('skill').values_list('skill__canonical_name','skill__category','requirement_type'))[:20])
    print('desc=', (job.description or '')[:250].replace('\n',' '))
"
```

Clean accidental root junk before final report:

```bash
rm -f scratch_cv.py scratch_extractor.py verify.py
find . -path './.venv' -prune -o -type d -name '__pycache__' -exec rm -rf {} +
find . -path './.venv' -prune -o -type f -name '*.pyc' -delete
```
