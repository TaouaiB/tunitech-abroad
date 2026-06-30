from django.core.management.base import BaseCommand
from apps.profiles.services.backfill import ProfileSkillBackfillService

class Command(BaseCommand):
    help = "Backfills canonical skill FK on ProfileSkill records."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting ProfileSkill backfill..."))
        result = ProfileSkillBackfillService.backfill_profile_skills()

        self.stdout.write(
            self.style.SUCCESS(
                f"Finished backfill. "
                f"Total processed: {result['total_processed']}, "
                f"Mapped to canonical: {result['mapped_to_canonical']}, "
                f"Sent to UnmatchedSkillCandidate: {result['unmatched_candidates']}."
            )
        )
