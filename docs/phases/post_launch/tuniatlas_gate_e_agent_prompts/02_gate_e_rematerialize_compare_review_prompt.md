# Gate E — Rematerialize and Compare Review Prompt

You are reviewing Gate E local rematerialization and comparison changes in the TuniAtlas Django repository.

## Agent choice

Recommended review agent: **Codex GPT-5.5 medium**. Use GPT-5.5 high only if budget allows.

## Strict review goal

Find blockers before commit or push. Confirm local data mutation was safe, backed up, deterministic, and reported. Do not deploy.

## Start commands

```bash
cd ~/Projects/tunitech-abroad
source .venv/bin/activate

git status --short --branch
git log --oneline --decorate -8
git diff --stat
git diff --check
git diff -- . ':!.env' ':!*.sqlite3'
```

## Review checklist

### Scope

PASS only if:
- Gate E is local rematerialization/comparison only.
- No production deployment.
- No branch push.
- No live France Travail calls.
- No uncontrolled LLM/OpenRouter calls.
- No broad UI/i18n cleanup.
- No new extraction model.
- No React/Next/FastAPI/Mongo/SQLAlchemy/SPA.
- No unexpected migrations.

### Safety

PASS only if:
- apply requires explicit `--apply`.
- default mode is dry-run.
- production settings are blocked.
- a verified non-empty local DB backup was created before mutation.
- backup is not staged or included in zip.
- `.env` and secrets are excluded.
- no production DB was accessed.
- failures stop safely or are isolated according to documented transaction policy.

### Architecture

PASS only if:
- orchestration calls existing services.
- no duplicated scoring/extraction business logic.
- views remain thin.
- no external API calls from models/views/command.
- canonical skills are not auto-created.
- matching stays deterministic.
- search-vector rebuild uses existing architecture.
- CV reparse, if used, goes through existing service and active `CVUpload.objects`.
- CV privacy and soft-delete behavior remain correct.

### Required behavior

Verify:
- targeted dry-run works without mutation.
- targeted apply works.
- second targeted apply is idempotent.
- full local dry-run/apply results are reported.
- zero-skill/generic-only/low-confidence metrics are compared.
- noisy skill removals are visible.
- SQL family remains distinct.
- Chef context behavior is correct.
- metadata phrases are rejected.
- broad/soft/process terms do not drive matching.
- affected matches/recommendations are invalidated/refreshed.
- report contains no raw CV text or secrets.
- CV reparse is explicit opt-in only.

### Tests

Run:

```bash
python manage.py check --settings=config.settings.local
python manage.py test apps.jobs apps.skills apps.cvs apps.matching apps.recommendations --settings=config.settings.local
python manage.py test apps.accounts apps.core apps.cvs apps.jobs apps.matching apps.recommendations --settings=config.settings.local
```

## Review result format

Return:

```text
PASS or FAIL

1. Summary
2. Scope compliance
3. Backup and safety review
4. Architecture compliance
5. Rematerialization behavior
6. Before/after report review
7. Security/privacy review
8. Test results
9. Blockers
10. Non-blocking issues
11. Exact files requiring changes if FAIL
12. Safe to commit: yes/no
13. Safe to push/deploy: no
```

## Required zip command for user upload

After review and fixes, create a zip for ChatGPT final review:

```bash
cd ~/Projects/tunitech-abroad

OUT="/tmp/tuniatlas_gate_e_review_submission"
ZIP="/tmp/tuniatlas_gate_e_review_submission_$(date +%Y%m%d_%H%M%S).zip"

rm -rf "$OUT"
mkdir -p "$OUT/repo_files" "$OUT/meta"

git status --short --branch > "$OUT/meta/git_status.txt"
git log --oneline --decorate -12 > "$OUT/meta/git_log.txt"
git diff --stat > "$OUT/meta/git_diff_stat.txt"
git diff --check > "$OUT/meta/git_diff_check.txt" || true
git diff -- . ':!.env' ':!*.sqlite3' > "$OUT/meta/git_diff.patch"
git ls-files --modified --others --exclude-standard > "$OUT/meta/changed_files.txt"

{
  echo "Gate E rematerialize and compare review submission"
  echo "Generated: $(date -Iseconds)"
  echo
  echo "Required checks:"
  echo "- python manage.py check --settings=config.settings.local"
  echo "- python manage.py test apps.jobs apps.skills apps.cvs apps.matching apps.recommendations --settings=config.settings.local"
  echo "- python manage.py test apps.accounts apps.core apps.cvs apps.jobs apps.matching apps.recommendations --settings=config.settings.local"
  echo
  echo "Safety:"
  echo "- .env intentionally excluded."
  echo "- database backups intentionally excluded."
  echo "- private CV files intentionally excluded."
  echo "- no production deployment performed."
} > "$OUT/meta/review_notes.txt"

while IFS= read -r f; do
  [ -z "$f" ] && continue
  [ "$f" = ".env" ] && continue
  [ -f "$f" ] || continue
  case "$f" in
    *.dump|*.sql|*.sqlite3|private_media/*|media/*)
      continue
      ;;
  esac
  mkdir -p "$OUT/repo_files/$(dirname "$f")"
  cp "$f" "$OUT/repo_files/$f"
done < "$OUT/meta/changed_files.txt"

cd "$OUT"
zip -r "$ZIP" . >/dev/null

echo "=== ZIP_CREATED ==="
ls -lh "$ZIP"
```

Upload the generated `/tmp/tuniatlas_gate_e_review_submission_*.zip` to ChatGPT.
