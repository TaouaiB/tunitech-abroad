# Test Plan

## Unit/service tests

Add or update tests for:

### ProfileCompletenessService

- Empty profile returns accurate score and missing fields.
- Profile with phone/location does not list phone/location missing.
- Profile missing only years experience returns only years experience if required.
- `target_country` is not part of user-facing missing fields.

### RecommendationQueryService

- Incomplete profile returns blocked state with exact missing fields.
- Usable profile with active jobs returns recommendation cards.
- No active jobs returns no-active-jobs state.
- No compatible jobs returns no-match state.
- Failed/stale states are displayed honestly.

### CVParsingService

- Parsed phone/location/links fill empty profile fields.
- Current level is inferred only when obvious.
- Target country is not filled/displayed from CV.
- Years experience is not hallucinated.
- Completion recalculates after profile changes.

### AccountProvisioningService / social provisioning

Use fake provider payloads:

- Google payload fills empty full name and avatar URL.
- GitHub payload fills empty full name, GitHub URL, avatar URL.
- Existing full name is not overwritten silently.
- OAuth tokens are not stored in profile.

### Auth templates/email rendering

- Render/set-password page returns 200 for appropriate user state.
- Social connections page returns 200 and contains Google/GitHub states.
- Email templates render `TuniTech Abroad` and not `example.test`.

## Integration/browser checks

Start server:

```bash
python manage.py runserver 127.0.0.1:8000 --settings=config.settings.local
```

Open:

```text
/accounts/login/
/accounts/signup/
/accounts/password/reset/
/accounts/password/set/
/accounts/email/
/accounts/confirm-email/
/accounts/3rdparty/
/dashboard/account/
/dashboard/account/connections/
/dashboard/profile/
/dashboard/cv/
/dashboard/recommendations/
```

Also test mobile width.

## Required shell proof

```bash
python manage.py shell --settings=config.settings.local -c "
from django.contrib.auth import get_user_model
from apps.profiles.models import CandidateProfile
from apps.recommendations.services.query import RecommendationQueryService
u=get_user_model().objects.get(email__iexact='baha.edine.taouai@gmail.com')
p=CandidateProfile.objects.get(user=u)
print('phone=', p.phone)
print('location=', p.location)
print('current_level=', p.current_level)
print('years_experience=', p.years_experience)
print('target_country=', getattr(p, 'target_country', None))
print('score=', p.profile_completion_score)
result=RecommendationQueryService.get_dashboard_recommendations(u)
print('blocked_reason=', getattr(result, 'blocked_reason', None))
print('missing_fields=', getattr(result, 'missing_fields', None))
print('count=', len(getattr(result, 'recommendations', []) or []))
"
```

The output must match what the UI says.
