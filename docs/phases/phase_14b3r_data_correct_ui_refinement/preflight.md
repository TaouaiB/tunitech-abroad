# Preflight — Phase 14B.3R

Run before editing.

```bash
cd ~/Projects/tunitech-abroad
source .venv/bin/activate

git branch --show-current
git status --short
git diff --stat

docker compose up -d postgres redis || true

python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
python manage.py seed_demo_data --settings=config.settings.local
python manage.py test --settings=config.settings.local
```

Capture current failing state:

```bash
python manage.py shell --settings=config.settings.local -c "
from django.contrib.auth import get_user_model
from apps.profiles.models import CandidateProfile, ProfileSkill
from apps.cvs.models import CVUpload, CVParsedData
from apps.recommendations.models import JobRecommendation, RecommendationRun
from apps.jobs.models import NormalizedJob

email='baha.edine.taouai@gmail.com'
User=get_user_model()
u=User.objects.filter(email__iexact=email).first()
print('USER_EXISTS=', bool(u))
if u:
    p=CandidateProfile.objects.filter(user=u).first()
    print('PROFILE_EXISTS=', bool(p))
    if p:
        for f in ['full_name','phone','location','linkedin_url','github_url','portfolio_url','website_url','current_level','years_experience','target_country','target_type','target_roles','french_level','english_level','relocation_preference','remote_preference','profile_completion_score']:
            print(f, '=', getattr(p, f, None))
        print('completion_percentage=', getattr(p,'completion_percentage',None))
        print('skills=', list(ProfileSkill.objects.filter(profile=p).values_list('raw_name','normalized_name','source')))
    cv=CVUpload.all_objects.filter(user=u).order_by('-uploaded_at').first()
    print('CV=', cv.original_filename if cv else None, cv.parse_status if cv else None)
    if cv:
        parsed=CVParsedData.objects.filter(cv_upload=cv).first()
        print('PARSED=', bool(parsed))
        if parsed:
            for f in ['extracted_name','extracted_email','extracted_phone','extracted_location','extracted_linkedin_url','extracted_github_url','extracted_portfolio_url','extraction_method','warnings_json']:
                print(f, '=', getattr(parsed, f, None))
    print('active_jobs=', NormalizedJob.objects.filter(status='active').count())
    print('recommendations=', JobRecommendation.objects.filter(user=u).count())
    print('runs=', list(RecommendationRun.objects.filter(user=u).order_by('-created_at').values('status','error_message','created_at')[:5]))
"
```

Fresh extractor proof:

```bash
python manage.py shell --settings=config.settings.local -c "
from django.contrib.auth import get_user_model
from apps.cvs.models import CVUpload, CVParsedData
from apps.cvs.services.deterministic_extractor import CVDeterministicExtractorService
email='baha.edine.taouai@gmail.com'
u=get_user_model().objects.filter(email__iexact=email).first()
if not u:
    print('NO USER')
else:
    cv=CVUpload.all_objects.filter(user=u).order_by('-uploaded_at').first()
    if not cv:
        print('NO CV')
    else:
        parsed=CVParsedData.objects.get(cv_upload=cv)
        result=CVDeterministicExtractorService.extract(parsed.raw_text)
        for k in sorted(result.keys()):
            print(k, '=', result[k])
"
```
