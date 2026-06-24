from django.core.management.base import BaseCommand
from django.db import transaction
from apps.skills.models import UnmatchedSkillCandidate, Skill, SkillAlias
from apps.skills.services.ignored import IgnoredSkillService
from apps.skills.services.phase_15d_decisions import approved_reconcile_decisions

class Command(BaseCommand):
    help = "Reconcile old pending unmatched candidates with newly added aliases and ignore rules."

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Actually update the database. If not passed, runs in dry-run mode.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without committing changes (default if --apply is missing).',
        )

    def handle(self, *args, **options):
        apply = options['apply']
        dry_run = options['dry_run']
        
        if not apply and not dry_run:
            dry_run = True

        decisions = approved_reconcile_decisions()
        candidates = UnmatchedSkillCandidate.objects.filter(
            status='pending',
            normalized_text__in=list(decisions.keys()),
        )
        total_pending = candidates.count()

        aliases = SkillAlias.objects.filter(skill__is_active=True).select_related('skill')
        alias_map = {alias.normalized_alias: alias.skill for alias in aliases}
        skill_map = {
            skill.canonical_name: skill
            for skill in Skill.objects.filter(
                canonical_name__in=[
                    decision.target_canonical_skill
                    for decision in decisions.values()
                    if decision.target_canonical_skill
                ],
                is_active=True,
            )
        }

        mapped_count = 0
        ignored_count = 0

        with transaction.atomic():
            for candidate in candidates:
                decision = decisions.get(candidate.normalized_text)
                if not decision:
                    continue

                if decision.decision == "ignore" and IgnoredSkillService.is_ignored(candidate.normalized_text):
                    if apply:
                        candidate.status = 'ignored'
                        candidate.save(update_fields=['status'])
                    ignored_count += 1

                elif decision.decision in {"alias_to_existing", "create_new_skill"}:
                    target_skill = alias_map.get(candidate.normalized_text) or skill_map.get(decision.target_canonical_skill)
                    if not target_skill:
                        continue
                    if apply:
                        candidate.status = 'mapped'
                        candidate.mapped_skill = target_skill
                        candidate.save(update_fields=['status', 'mapped_skill'])
                    mapped_count += 1

                elif decision.decision == "already_resolved":
                    target_skill = alias_map.get(candidate.normalized_text) or skill_map.get(decision.target_canonical_skill)
                    if not target_skill:
                        continue
                    if apply:
                        candidate.status = "mapped"
                        candidate.mapped_skill = target_skill
                        candidate.save(update_fields=["status", "mapped_skill"])
                    mapped_count += 1

            if dry_run or not apply:
                transaction.set_rollback(True)
                self.stdout.write(self.style.WARNING("Dry run: Changes rolled back."))
            else:
                self.stdout.write(self.style.SUCCESS("Apply: Changes committed."))

        self.stdout.write(f"Total pending candidates evaluated: {total_pending}")
        self.stdout.write(f"Resolved (mapped): {mapped_count}")
        self.stdout.write(f"Resolved (ignored): {ignored_count}")
        self.stdout.write(f"Remaining pending: {total_pending - mapped_count - ignored_count}")
