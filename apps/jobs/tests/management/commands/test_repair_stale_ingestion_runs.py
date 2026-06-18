from io import StringIO
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from apps.jobs.models import JobIngestionConfig, JobIngestionRun

class RepairStaleIngestionRunsTest(TestCase):
    def test_repair_stale_runs(self):
        config = JobIngestionConfig.objects.create(name="test", enabled=True)
        # Create one stale running
        stale = JobIngestionRun.objects.create(
            config=config,
            status="running",
            trigger="celery",
        )
        # Hack started_at
        JobIngestionRun.objects.filter(id=stale.id).update(
            started_at=timezone.now() - timedelta(minutes=400)
        )
        
        fresh = JobIngestionRun.objects.create(
            config=config,
            status="running",
            trigger="celery",
        )
        
        out = StringIO()
        call_command("repair_stale_ingestion_runs", stdout=out)
        
        stale.refresh_from_db()
        fresh.refresh_from_db()
        
        self.assertEqual(stale.status, "failed")
        self.assertEqual(stale.error_summary, "Marked failed by stale-run repair")
        self.assertEqual(fresh.status, "running")

    def test_dry_run(self):
        config = JobIngestionConfig.objects.create(name="test", enabled=True)
        stale = JobIngestionRun.objects.create(
            config=config,
            status="running",
            trigger="celery",
        )
        JobIngestionRun.objects.filter(id=stale.id).update(
            started_at=timezone.now() - timedelta(minutes=400)
        )
        
        out = StringIO()
        call_command("repair_stale_ingestion_runs", "--dry-run", stdout=out)
        
        stale.refresh_from_db()
        self.assertEqual(stale.status, "running")
        self.assertIn("[DRY-RUN]", out.getvalue())
