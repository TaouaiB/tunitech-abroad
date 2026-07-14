import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.accounts.models import User
from apps.matching.models import MatchResult
from apps.matching.services.match_result import MatchResultService
from apps.matching.services.policy_version import MATCH_SCORING_VERSION, RECOMMENDATION_VERSION
from apps.recommendations.models import JobRecommendation
from apps.recommendations.services.recommendation import RecommendationService
from apps.recommendations.services.staleness import RecommendationStalenessService


LOCAL_SETTINGS_MODULE = "config.settings.local"
LOCAL_HOSTS = {"", "localhost", "127.0.0.1", "::1", "tunitech_postgres"}


class Command(BaseCommand):
    help = "Preview or locally refresh one user's persisted pre-Gate-F match policy results."

    def add_arguments(self, parser):
        parser.add_argument("--user-id", type=int, required=True)
        parser.add_argument("--apply", action="store_true", help="Apply the scoped local refresh.")

    def handle(self, *args, **options):
        db_info = self._safe_database_info()
        self._assert_local_apply_allowed(options, db_info)

        user = User.objects.filter(pk=options["user_id"]).first()
        if user is None:
            raise CommandError("User not found.")

        old_matches = MatchResult.objects.filter(user=user).exclude(scoring_version=MATCH_SCORING_VERSION)
        old_recommendations = JobRecommendation.objects.filter(user=user).exclude(
            recommendation_version=RECOMMENDATION_VERSION
        )
        self.stdout.write(
            f"user_id={user.pk} old_matches={old_matches.count()} "
            f"old_recommendations={old_recommendations.count()} apply={options['apply']}"
        )
        if not options["apply"]:
            self.stdout.write("Dry run only; pass --apply to refresh this user.")
            return

        refreshed_matches = 0
        for match in old_matches.select_related("job").order_by("job_id", "-created_at").distinct("job_id"):
            MatchResultService.refresh_if_stale(match)
            refreshed_matches += 1

        RecommendationStalenessService.mark_outdated_policy_recommendations_stale(user)
        recommendation_result = RecommendationService.refresh_for_user(user, "manual_admin")
        self.stdout.write(
            self.style.SUCCESS(
                f"Refreshed {refreshed_matches} match rows and "
                f"stored {recommendation_result.stored_recommendations_count} recommendations."
            )
        )

    @staticmethod
    def _safe_database_info() -> dict[str, str]:
        db = settings.DATABASES["default"]
        return {
            "engine": db.get("ENGINE", ""),
            "host": db.get("HOST") or "",
            "name": db.get("NAME") or "",
            "port": str(db.get("PORT") or ""),
        }

    @staticmethod
    def _assert_local_apply_allowed(options, db_info: dict[str, str]) -> None:
        # Dry-run stays the default; only `--apply` may mutate state and even then
        # only when every local-only invariant holds. This command must never
        # become a production refresh path.
        if not options.get("apply"):
            return

        settings_module = os.environ.get("DJANGO_SETTINGS_MODULE", "")
        if settings_module != LOCAL_SETTINGS_MODULE:
            raise CommandError(
                "Refusing Gate F refresh apply unless "
                f"DJANGO_SETTINGS_MODULE={LOCAL_SETTINGS_MODULE}."
            )
        if not settings.DEBUG:
            raise CommandError("Refusing Gate F refresh apply when DEBUG=False.")
        host = (db_info.get("host") or "").lower()
        if host not in LOCAL_HOSTS:
            raise CommandError(
                "Refusing Gate F refresh apply because the database host is not local "
                f"(got {host or '<empty>'!r})."
            )
        if "postgresql" not in (db_info.get("engine") or ""):
            raise CommandError(
                "Refusing Gate F refresh apply because the configured database "
                "is not PostgreSQL."
            )
