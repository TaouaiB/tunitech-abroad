from django.core.management.base import BaseCommand
from apps.skills.services.seed import SkillSeedService

class Command(BaseCommand):
    help = "Seeds initial canonical skills and aliases."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting skill taxonomy seed..."))
        result = SkillSeedService.seed_initial_taxonomy()
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully seeded taxonomy. "
                f"Skills created: {result['skills_created']}, "
                f"Aliases created: {result['aliases_created']}."
            )
        )
