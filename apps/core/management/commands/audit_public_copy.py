from django.core.management.base import BaseCommand

from apps.core.services.public_copy_audit import PublicCopyAuditService


class Command(BaseCommand):
    help = "Audit public templates for forbidden France-only phrases."

    def handle(self, *args, **options):
        result = PublicCopyAuditService.find_forbidden_terms()

        if not result["ok"]:
            self.stdout.write(self.style.ERROR("Found forbidden phrases in public templates:"))
            for violation in result["violations"]:
                self.stdout.write(
                    self.style.ERROR(
                        f"- Forbidden phrase '{violation['phrase']}' found in "
                        f"{violation['path']}:{violation['line']}"
                    )
                )
            exit(1)

        self.stdout.write(self.style.SUCCESS("No forbidden phrases found in public templates. Copy is country-neutral."))
