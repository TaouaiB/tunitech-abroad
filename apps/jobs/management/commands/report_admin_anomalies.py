from django.core.management.base import BaseCommand

from apps.jobs.services.anomaly_review import JobAnomalyReviewService


class Command(BaseCommand):
    help = "Print read-only admin anomaly counts and samples."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=5, help="Sample rows per anomaly bucket.")

    def handle(self, *args, **options):
        limit = max(options["limit"], 0)
        counts = JobAnomalyReviewService.summary_counts()

        self.stdout.write("Admin anomaly review")
        for key, value in counts.items():
            self.stdout.write(f"- {key}: {value}")

        self._print_jobs("Active zero-skill jobs", JobAnomalyReviewService.active_zero_skill_jobs()[:limit])
        self._print_jobs("Active generic-only jobs", JobAnomalyReviewService.active_generic_only_jobs()[:limit])
        self._print_job_skills(
            "Low-confidence job skills",
            JobAnomalyReviewService.low_confidence_job_skills()[:limit],
        )
        self._print_unmatched_candidates(
            "Unmatched skill candidates",
            JobAnomalyReviewService.unmatched_candidates()[:limit],
        )
        self._print_jobs(
            "Failed/partial skill extraction jobs",
            JobAnomalyReviewService.jobs_with_failed_or_partial_skill_extraction()[:limit],
        )
        self._print_jobs("Hidden/excluded jobs", JobAnomalyReviewService.hidden_or_excluded_jobs()[:limit])
        self._print_cv_warnings(
            "Recent CV parses with warnings",
            JobAnomalyReviewService.recent_cv_parses_with_warnings()[:limit],
        )

    def _print_jobs(self, title, jobs):
        self.stdout.write("")
        self.stdout.write(title)
        for job in jobs:
            self.stdout.write(
                f"- {job.public_id} | {job.title} | source={job.source.slug} | "
                f"source_job_id={job.source_job_id} | status={job.status} | "
                f"skill_status={job.skill_extraction_status} | quality={job.skill_signal_quality} | "
                f"reason={job.quality_issue or '-'}"
            )

    def _print_job_skills(self, title, rows):
        self.stdout.write("")
        self.stdout.write(title)
        for row in rows:
            self.stdout.write(
                f"- {row.job.public_id} | {row.skill.canonical_name} | "
                f"confidence={row.confidence} | source={row.source} | requirement={row.requirement_type}"
            )

    def _print_unmatched_candidates(self, title, candidates):
        self.stdout.write("")
        self.stdout.write(title)
        for candidate in candidates:
            self.stdout.write(
                f"- {candidate.normalized_text} | raw={candidate.raw_skill_text} | "
                f"source={candidate.source_type} | status={candidate.status} | "
                f"occurrences={candidate.occurrence_count}"
            )

    def _print_cv_warnings(self, title, parsed_rows):
        self.stdout.write("")
        self.stdout.write(title)
        for parsed in parsed_rows:
            warnings = parsed.warnings_json if isinstance(parsed.warnings_json, list) else []
            self.stdout.write(
                f"- {parsed.cv_upload.public_id} | parse_status={parsed.cv_upload.parse_status} | "
                f"warnings={len(warnings)}"
            )
