# Phase 15F Manual Commands

## Small E2E canary after implementation

```bash
cd ~/Projects/tunitech-abroad
source .venv/bin/activate

python manage.py run_llm_e2e_pipeline   --preset broad_it   --limit-per-keyword 2   --max-total 10   --max-pages-per-keyword 1   --force-llm-count 10   --force-provider-call   --min-llm-success 8   --apply   --settings=config.settings.local
```

## 100-job E2E after small canary passes

```bash
python manage.py run_llm_e2e_pipeline   --preset broad_it   --limit-per-keyword 10   --max-total 100   --max-pages-per-keyword 2   --force-llm-count 100   --force-provider-call   --min-llm-success 95   --apply   --settings=config.settings.local
```

Use a lower `--min-llm-success` if the goal is provider reachability rather than strict success:

```bash
python manage.py run_llm_e2e_pipeline   --preset broad_it   --limit-per-keyword 10   --max-total 100   --max-pages-per-keyword 2   --force-llm-count 100   --force-provider-call   --min-llm-success 80   --apply   --settings=config.settings.local
```

## Inspect latest enrichment statuses

```bash
python manage.py shell --settings=config.settings.local <<'PY'
from django.db.models import Count
from apps.llm.models import JobEnrichment

latest = JobEnrichment.objects.order_by('-created_at')[:100]
ids = [e.id for e in latest]
qs = JobEnrichment.objects.filter(id__in=ids)

print('LATEST 100 STATUS')
for row in qs.values('status').annotate(c=Count('id')).order_by('status'):
    print(row)

print('
LATEST 100 STATUS REASONS')
for row in qs.values('status', 'status_reason').annotate(c=Count('id')).order_by('status', 'status_reason'):
    print(row)

print('
TOKEN GROUPS')
print('reached_provider_tokens_gt_0:', qs.filter(total_tokens__gt=0).count())
print('pre_skipped_tokens_0:', qs.filter(total_tokens=0).count())
PY
```

## Public safety check

```bash
python manage.py shell --settings=config.settings.local <<'PY'
from apps.jobs.models import NormalizedJob
from apps.jobs.services.eligibility import JobEligibilityService

all_jobs = NormalizedJob.objects.all()
public = JobEligibilityService.filter_publicly_visible(all_jobs)
matchable = JobEligibilityService.filter_matchable(all_jobs)

print('PUBLIC_VISIBLE:', public.count())
print('MATCHABLE:', matchable.count())
print('PUBLIC_ZERO:', public.filter(job_skills__isnull=True).distinct().count())
print('MATCHABLE_ZERO:', matchable.filter(job_skills__isnull=True).distinct().count())
PY
```

Required:

```text
PUBLIC_ZERO: 0
MATCHABLE_ZERO: 0
```
