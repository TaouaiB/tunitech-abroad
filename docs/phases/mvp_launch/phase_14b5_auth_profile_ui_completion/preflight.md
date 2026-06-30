# Preflight

Run from project root:

```bash
cd ~/Projects/tunitech-abroad
source .venv/bin/activate

git status --short
git diff --stat

python manage.py check --settings=config.settings.local
python manage.py makemigrations --check --dry-run --settings=config.settings.local
python manage.py migrate --settings=config.settings.local
```

Route audit:

```bash
python manage.py shell --settings=config.settings.local -c "
from django.urls import get_resolver, URLPattern, URLResolver

def walk(patterns, prefix=''):
    for p in patterns:
        if isinstance(p, URLPattern):
            print(prefix + str(p.pattern), 'name=', p.name, 'callback=', getattr(p.callback, '__name__', p.callback))
        elif isinstance(p, URLResolver):
            walk(p.url_patterns, prefix + str(p.pattern))
walk(get_resolver().url_patterns)
"
```

Allauth template audit:

```bash
python - <<'PY'
import allauth, pathlib
root = pathlib.Path(allauth.__file__).parent
for path in sorted(root.rglob('templates/**/*.html')):
    s = str(path)
    if '/account/' in s or '/socialaccount/' in s:
        print(path)
PY
```

Do not continue until the agent has listed all user-facing account/socialaccount pages it will style.
