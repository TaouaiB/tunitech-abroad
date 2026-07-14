from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.profiles.services.backfill import ProfileSkillBackfillService

User = get_user_model()


class Command(BaseCommand):
    help = (
        "Dry-run or repair null-linked ProfileSkill rows by linking them to canonical skills."
    )

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--user-id", type=int, help="Repair a single user by ID.")
        group.add_argument("--all-users", action="store_true", help="Repair all users with profiles.")
        parser.add_argument("--apply", action="store_true", help="Apply deterministic links.")
        parser.add_argument(
            "--confirm-production",
            action="store_true",
            help="Confirm apply in a non-DEBUG (production) environment.",
        )
        parser.add_argument(
            "--refresh-results",
            action="store_true",
            help="Refresh recommendations and current match rows for changed users (requires --apply).",
        )

    def handle(self, *args, **options):
        user_id = options.get("user_id")
        all_users = options.get("all_users")
        apply = options.get("apply")
        confirm_production = options.get("confirm_production")
        refresh_results = options.get("refresh_results")

        if refresh_results and not apply:
            raise CommandError("--refresh-results requires --apply.")

        if apply and not settings.DEBUG and not confirm_production:
            raise CommandError(
                "Production apply requires --confirm-production."
            )

        user = None
        if user_id:
            try:
                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                raise CommandError(f"User with id={user_id} not found.")

        report = ProfileSkillBackfillService.repair(
            user=user,
            apply=apply,
            refresh_results=refresh_results,
        )

        if not apply:
            self.stdout.write(
                self.style.WARNING("Dry run only: no writes were performed.")
            )

        self.stdout.write(
            f"users_scanned={report.users_scanned} "
            f"users_changed={report.users_changed} "
            f"rows_scanned={report.rows_scanned} "
            f"rows_linked={report.rows_linked} "
            f"rows_already_linked={report.rows_already_linked} "
            f"rows_ambiguous={report.rows_ambiguous} "
            f"rows_unmatched={report.rows_unmatched} "
            f"rows_ignored_or_invalid={report.rows_ignored_or_invalid} "
            f"conflicts={report.conflicts} "
            f"users_refreshed={report.users_refreshed} "
            f"recommendations_created={report.recommendations_created} "
            f"recommendations_updated={report.recommendations_updated} "
            f"matches_recomputed={report.matches_recomputed} "
            f"errors={report.errors}"
        )

        for user_report in report.user_reports:
            for error in user_report.errors:
                self.stderr.write(self.style.ERROR(f"user={user_report.user_id}: {error}"))

        if report.errors:
            raise CommandError(
                f"Repair finished with {report.errors} error(s). "
                f"{report.rows_linked} row(s) linked across {report.users_changed} user(s). "
                f"See output above for details."
            )

        if apply:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Repair complete. {report.rows_linked} row(s) linked across "
                    f"{report.users_changed} user(s)."
                )
            )
