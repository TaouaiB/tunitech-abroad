import json

from django.core.management.base import BaseCommand

from apps.skills.services.alias_audit import SkillAliasAuditService

class Command(BaseCommand):
    help = "Audit skill aliases for duplicates, ambiguity, and frequent unmatched candidates."

    def handle(self, *args, **options):
        diagnostics = SkillAliasAuditService.audit()
        self.stdout.write(json.dumps(diagnostics, indent=2, sort_keys=True))
