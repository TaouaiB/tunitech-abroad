# Release and Rollback

## Deploy

```bash
cd /home/tunitech/tunitech-abroad
git pull origin main
source .venv/bin/activate
pip install -r requirements/production.txt
python manage.py migrate
npm run css:build
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn celery celerybeat
```

## Rollback

```bash
# Identify previous commit hash
git checkout <PREVIOUS_COMMIT>
source .venv/bin/activate
pip install -r requirements/production.txt
# Check if reverse migrations are needed, otherwise:
sudo systemctl restart gunicorn celery celerybeat
```
