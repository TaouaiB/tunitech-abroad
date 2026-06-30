# Test Plan — Phase 14B.3R

## Automated tests

### CV extractor tests

Create or update tests under `apps/cvs/tests/`.

Test:

- URL extraction and normalization
- no false URLs from skill names
- location extraction
- target roles extraction
- language extraction
- years experience estimate if supported
- raw skill cleanup
- incomplete CV does not hallucinate missing fields

### CV parsing/profile tests

Test:

- empty profile populated from CV
- partial profile gets only empty fields filled
- name conflict does not overwrite
- stale bad website URL cleaned when CV has valid portfolio
- ProfileSkill rows created
- profile completion recalculated

### Profile completion tests

Test:

- empty profile low score
- CV partial profile realistic score
- complete profile high score
- `completion_percentage` and `profile_completion_score` do not contradict

### Recommendation tests

Test:

- incomplete profile => blocked state + missing fields
- no active jobs => no jobs state
- complete profile + jobs => recommendations > 0
- failed generation => failed state
- no fake success with zero recommendations on incomplete profile

## Shell proof after tests

Run:

```bash
python manage.py shell --settings=config.settings.local -c "
from apps.cvs.services.deterministic_extractor import CVDeterministicExtractorService
# Print fixture extraction summary here if useful
"
```

Run user state proof if Baha user exists:

```bash
python manage.py shell --settings=config.settings.local -c "
from django.contrib.auth import get_user_model
from apps.profiles.models import CandidateProfile, ProfileSkill
from apps.cvs.models import CVUpload, CVParsedData
from apps.jobs.models import NormalizedJob
from apps.recommendations.models import JobRecommendation, RecommendationRun
email='baha.edine.taouai@gmail.com'
u=get_user_model().objects.filter(email__iexact=email).first()
print('USER_EXISTS=', bool(u))
if u:
    p=CandidateProfile.objects.filter(user=u).first()
    print('PROFILE=', bool(p))
    if p:
        for f in ['location','linkedin_url','github_url','portfolio_url','website_url','current_level','years_experience','target_country','target_type','target_roles','french_level','english_level','profile_completion_score']:
            print(f, '=', getattr(p,f,None))
        print('completion_percentage=', getattr(p,'completion_percentage',None))
        print('skills=', list(ProfileSkill.objects.filter(profile=p).values_list('raw_name','normalized_name','source')))
    print('active_jobs=', NormalizedJob.objects.filter(status='active').count())
    print('recommendations=', JobRecommendation.objects.filter(user=u).count())
    print('runs=', list(RecommendationRun.objects.filter(user=u).order_by('-created_at').values('status','error_message','created_at')[:5]))
"
```

## Browser/headless checks

Use Django dev server or test client. Browser checks must cover:

- `/dashboard/cv/`
- `/dashboard/profile/`
- `/dashboard/recommendations/`
- `/dashboard/matches/`
- match detail
- `/jobs/`
- job detail
- quick match
- login/signup/password reset
- custom 404 under DEBUG=False

## Manual Baha sign-off

Baha must confirm in Chrome:

- CV extracted data is visible and correct
- profile fields are believable
- no `https://Next.js`
- recommendations show exact blocked reason or offers
- UI looks better than previous screenshots
- mobile width not broken
