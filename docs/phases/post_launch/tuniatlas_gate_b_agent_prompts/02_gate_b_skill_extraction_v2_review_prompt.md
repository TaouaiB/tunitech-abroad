# Gate B — Skill Extraction v2 Review Prompt

You are reviewing Gate B Skill Extraction v2 changes in the TuniAtlas Django repository.

## Agent choice

Recommended review agent: **Codex GPT-5.5 medium**. Use GPT-5.5 high only if budget allows.

## Strict review goal

Find blockers before commit. Do not implement Gate C/D/E. Do not deploy.

## Start commands

```bash
cd ~/Projects/tunitech-abroad
git status --short --branch
git log --oneline --decorate -8
git diff --stat
git diff --check
git diff -- . ':!.env' ':!*.sqlite3'
```

## Review checklist

### Scope

PASS only if:
- Gate B is skill extraction v2 only.
- No CV parser v2 was implemented.
- No admin anomaly UI was implemented.
- No rematerialization was executed.
- No production deploy changes were made.
- No broad UI/i18n cleanup.
- No React/Next/FastAPI/Mongo/SQLAlchemy/SPA.
- No unexpected migrations.

### Architecture

PASS only if:
- views remain thin.
- extraction logic lives in services/policies.
- no external API calls from models/views.
- no LLM calls from views.
- matching remains deterministic.
- unknown skills are not auto-created as canonical skills.
- SQL, SQL Server, PostgreSQL, MySQL, SQLite remain distinct.
- broad/process/soft skills do not drive required missing-skill scoring.

### Required behavior checks

Verify tests or code prove:

- `chef de projet` does not create Chef.
- DevOps Chef still works.
- SQL Server does not create SQL duplicate.
- PostgreSQL/MySQL/SQLite stay distinct.
- plain API does not become a required hard skill.
- REST API/OpenAPI/GraphQL are handled specifically if supported.
- Agile/Scrum/Communication/Teamwork/Leadership do not become technical missing skills.
- Technical Documentation/Technical Watch/Corrective Maintenance do not become required technical skills.
- zero-skill/generic-only jobs get weak/insufficient quality, not misleading strong/partial success.

### Security/privacy

Fail if:
- `.env` is included or printed.
- real secrets are added.
- CV file privacy is weakened.
- public routes expose internal integer IDs.
- CVUpload.objects soft-delete rule is changed incorrectly.

## Required commands

```bash
python manage.py check --settings=config.settings.local
python manage.py test apps.skills apps.jobs apps.matching apps.recommendations --settings=config.settings.local
python manage.py test apps.accounts apps.core apps.cvs apps.jobs apps.matching apps.recommendations --settings=config.settings.local
```

## Review result format

Return:

```text
PASS or FAIL

1. Summary
2. Scope compliance
3. Architecture compliance
4. Behavior review
5. Security/privacy review
6. Test results
7. Blockers
8. Non-blocking issues
9. Exact files requiring changes if FAIL
10. Safe to commit: yes/no
```

## Required zip command for user upload

After review and fixes, create a zip for ChatGPT final review:

```bash
cd ~/Projects/tunitech-abroad

OUT="/tmp/tuniatlas_gate_b_review_submission"
ZIP="/tmp/tuniatlas_gate_b_review_submission_$(date +%Y%m%d_%H%M%S).zip"

rm -rf "$OUT"
mkdir -p "$OUT/repo_files" "$OUT/meta"

git status --short --branch > "$OUT/meta/git_status.txt"
git log --oneline --decorate -12 > "$OUT/meta/git_log.txt"
git diff --stat > "$OUT/meta/git_diff_stat.txt"
git diff --check > "$OUT/meta/git_diff_check.txt" || true
git diff -- . ':!.env' ':!*.sqlite3' > "$OUT/meta/git_diff.patch"
git ls-files --modified --others --exclude-standard > "$OUT/meta/changed_files.txt"

{
  echo "Gate B Skill Extraction v2 review submission"
  echo "Generated: $(date -Iseconds)"
  echo
  echo "Required local checks before zip:"
  echo "- python manage.py check --settings=config.settings.local"
  echo "- python manage.py test apps.skills apps.jobs apps.matching apps.recommendations --settings=config.settings.local"
  echo "- python manage.py test apps.accounts apps.core apps.cvs apps.jobs apps.matching apps.recommendations --settings=config.settings.local"
  echo
  echo "Secret rule:"
  echo "- .env intentionally excluded from zip."
} > "$OUT/meta/review_notes.txt"

while IFS= read -r f; do
  [ -z "$f" ] && continue
  [ "$f" = ".env" ] && continue
  [ -f "$f" ] || continue
  mkdir -p "$OUT/repo_files/$(dirname "$f")"
  cp "$f" "$OUT/repo_files/$f"
done < "$OUT/meta/changed_files.txt"

cd "$OUT"
zip -r "$ZIP" . >/dev/null

echo "=== ZIP_CREATED ==="
ls -lh "$ZIP"
```

Upload the generated `/tmp/tuniatlas_gate_b_review_submission_*.zip` to ChatGPT.
