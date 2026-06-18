import sys
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from apps.cvs.models import CVUpload
import redis

class Command(BaseCommand):
    help = "Checks if Redis is reachable and if there are any stuck CVs."

    def handle(self, *args, **options):
        # 1. Check Redis connectivity
        redis_url = getattr(settings, 'CELERY_BROKER_URL', 'redis://localhost:6379/0')
        self.stdout.write(f"Checking Redis connection at {redis_url}...")
        try:
            client = redis.from_url(redis_url)
            client.ping()
            self.stdout.write(self.style.SUCCESS("✓ Redis is reachable."))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"✗ Redis connection failed: {e}"))
            self.stderr.write(self.style.ERROR("Please ensure Redis is running."))
            sys.exit(1)

        # 2. Check for stuck CVs
        threshold = timezone.now() - timedelta(minutes=15)
        stuck_cvs = CVUpload.objects.filter(
            parse_status__in=['pending', 'processing'],
            uploaded_at__lt=threshold
        )
        
        stuck_count = stuck_cvs.count()
        if stuck_count > 0:
            self.stderr.write(self.style.WARNING(f"! Found {stuck_count} stuck CVs (queued for > 15 minutes)."))
            self.stderr.write(self.style.WARNING("This usually means the Celery worker is not running or crashed."))
            self.stderr.write(self.style.WARNING("Start worker with: celery -A config worker --loglevel=info"))
        else:
            self.stdout.write(self.style.SUCCESS("✓ No stuck CVs found."))

        self.stdout.write(self.style.SUCCESS("Worker health check completed."))
