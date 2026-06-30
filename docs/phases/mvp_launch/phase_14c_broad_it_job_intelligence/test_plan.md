# Test Plan

## Unit tests

### Classification service

Test each family:

- software_development
- web_mobile
- data_ai_bi
- devops_cloud_sre
- cybersecurity
- qa_testing
- systems_network
- database
- erp_crm
- it_support
- it_project_product_analysis
- it_training_apprenticeship
- non_it

Assertions:

```text
family
is_it
confidence
reasons
negative_reasons
```

### Confidence mapping service/logic

Test exact mapping from `confidence_mapping.md`:

- Data Scientist with optional/detected Python/Machine Learning/Pandas and no required skills => `low_confidence`.
- Generic Web Developer with no skills and weak description => `unavailable`.
- Photography seller/commercial developer => `unavailable`.
- Real Java/Spring/Angular or C#/.NET with required skills => `reliable`.
- Generic FT competence only => not `reliable`.

### Skill extraction service

Use real-style payload fixtures.

Assert:

- specific stack terms become canonical skills.
- required/optional classification is sensible.
- generic FT competences are not treated as exact stack.
- unmatched true technical terms become review candidates if no alias exists.

### Recommendation service

Assert:

- reliable jobs rank before low-confidence jobs.
- unavailable jobs excluded.
- broad IT families can be recommended.
- non-IT jobs excluded.
- IT apprenticeship/alternance positive case included when technical.
- non-technical support and non-technical project/business-analysis negative cases excluded.

### Matching service

Assert:

- reliable jobs show normal score.
- low-confidence jobs show low confidence.
- unavailable jobs hide normal fit score.

## Integration proof command

Run after implementation:

```bash
python manage.py shell --settings=config.settings.local -c "
from apps.jobs.models import NormalizedJob
from apps.jobs.services.relevance import JobITRelevanceService

terms = [
    'Data Scientist',
    'Web Developer',
    'photographie',
    'SALESFORCE',
    'Flutter',
    'AS400',
    'DevOps',
    'QA',
    'cyber',
    'Sage',
    'PeopleSoft',
    'alternance',
    'support informatique',
    'support client commercial',
]

for term in terms:
    job = NormalizedJob.objects.filter(title__icontains=term).first() or NormalizedJob.objects.filter(description__icontains=term).first()
    print('---', term)
    if not job:
        print('NOT FOUND')
        continue
    rel = JobITRelevanceService.assess(job)
    print('title=', job.title)
    print('required=', job.required_skills_json)
    print('optional=', job.optional_skills_json)
    print('job_skills=', list(job.job_skills.select_related('skill').values_list('skill__canonical_name','skill__category','requirement_type'))[:20])
    print('relevance=', rel)
"
```

## Browser/manual tests

Open:

```text
/jobs/
/job detail for Data Scientist
/job detail for DevOps/cloud
/job detail for ERP/CRM
/job detail for photography seller if present
/dashboard/recommendations/
/dashboard/matches/
```

Expected:

- broad IT jobs are recognized.
- non-IT jobs are not recommended.
- weak jobs say weak/unavailable.
- no misleading “you have all required skills” when required skills are absent.
