import os
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings

class Command(BaseCommand):
    help = "Run all seed commands to initialize the demo data (skills, sources, and job fixtures)."

    def handle(self, *args, **options):
        from django.contrib.sites.models import Site
        Site.objects.update_or_create(
            id=1,
            defaults={
                'domain': 'localhost:8000',
                'name': 'TuniTech Abroad'
            }
        )

        self.stdout.write(self.style.NOTICE("Seeding skills..."))
        call_command('seed_skills')
        
        self.stdout.write(self.style.NOTICE("Seeding job sources..."))
        call_command('seed_job_sources')
        
        fixture_path = os.path.join(settings.BASE_DIR, 'apps', 'jobs', 'fixtures', 'france_travail_sample_jobs.json')
        if os.path.exists(fixture_path):
            self.stdout.write(self.style.NOTICE(f"Ingesting job fixtures from {fixture_path}..."))
            call_command('ingest_job_fixtures', fixture_path, '--normalize')
        else:
            self.stdout.write(self.style.WARNING(f"Fixture file not found: {fixture_path}"))
            
        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully!"))
