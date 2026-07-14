from django.core.management.base import BaseCommand, CommandError

from apps.profiles.services.backfill import ProfileSkillBackfillService


class Command(BaseCommand):
    help = (
        "Legacy dry-run inspector for ProfileSkill skill links. "
        "Writes are refused; use repair_profile_skill_links to apply deterministic links."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="This flag is no longer accepted. Use repair_profile_skill_links instead.",
        )
        parser.add_argument(
            "--refresh-results",
            action="store_true",
            help="This flag is no longer accepted with --apply.",
        )

    def handle(self, *args, **options):
        apply = options.get("apply")
        refresh_results = options.get("refresh_results")

        if apply:
            raise CommandError(
                "backfill_profile_skills --apply is no longer allowed. "
                "Use the repair_profile_skill_links management command to apply deterministic links."
            )

        if refresh_results:
            raise CommandError(
                "--refresh-results is no longer supported by this command. "
                "Use repair_profile_skill_links --refresh-results instead."
            )

        self.stdout.write(
            self.style.NOTICE("Starting ProfileSkill backfill (DRY RUN only).")
        )

        report = ProfileSkillBackfillService.backfill_profile_skills(
            apply=False,
            refresh_results=False,
        )

        self.stdout.write(
            self.style.WARNING("Dry run only: no writes were performed.")
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Finished backfill. "
                f"Users scanned: {report['users_scanned']}, "
                f"Users changed: {report['users_changed']}, "
                f"Rows scanned: {report['rows_scanned']}, "
                f"Rows linked: {report['rows_linked']}, "
                f"Rows already linked: {report['rows_already_linked']}, "
                f"Rows ambiguous: {report['rows_ambiguous']}, "
                f"Rows unmatched: {report['rows_unmatched']}, "
                f"Rows ignored/invalid: {report['rows_ignored_or_invalid']}, "
                f"Conflicts: {report['conflicts']}, "
                f"Users refreshed: {report['users_refreshed']}, "
                f"Recommendations created: {report['recommendations_created']}, "
                f"Recommendations updated: {report['recommendations_updated']}, "
                f"Matches recomputed: {report['matches_recomputed']}, "
                f"Errors: {report['errors']}."
            )
        )
