from django.core.management.base import BaseCommand
from apps.cvs.services.parser_audit import CVParserAuditService

class Command(BaseCommand):
    help = "Audit CV parser against a private test corpus."

    def add_arguments(self, parser):
        parser.add_argument('--cv-dir', type=str, required=True, help="Directory containing PDF CVs")
        parser.add_argument('--expected-dir', type=str, required=True, help="Directory containing expected JSON")
        parser.add_argument('--output', type=str, required=True, help="CSV output path or report directory")
        parser.add_argument('--threshold-name-acceptable', type=float, default=None)
        parser.add_argument('--threshold-skill-precision', type=float, default=None)
        parser.add_argument('--threshold-skill-recall', type=float, default=None)

    def handle(self, *args, **options):
        thresholds = {}
        if options["threshold_name_acceptable"] is not None:
            thresholds["name_acceptable_accuracy"] = options["threshold_name_acceptable"]
        if options["threshold_skill_precision"] is not None:
            thresholds["skill_precision"] = options["threshold_skill_precision"]
        if options["threshold_skill_recall"] is not None:
            thresholds["skill_recall"] = options["threshold_skill_recall"]

        result = CVParserAuditService.run(
            options["cv_dir"],
            options["expected_dir"],
            options["output"],
            thresholds=thresholds or None,
        )
        
        message = f"CV parser audit {'passed' if result['ok'] else 'failed'}: {result['counts']}"
        if result["ok"]:
            self.stdout.write(self.style.SUCCESS(message))
        else:
            self.stderr.write(self.style.ERROR(message))
            for error in result.get("errors", []):
                self.stderr.write(f"- {error}")
            raise SystemExit(1)
