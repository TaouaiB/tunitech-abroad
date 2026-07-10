# Gate D — Admin Anomaly Review Review Prompt

You are reviewing Gate D Admin Anomaly Review changes in the TuniAtlas Django repository.

## Agent choice

Recommended review agent: **Codex GPT-5.5 medium**. Use GPT-5.5 high only if budget allows.

## Strict review goal

Find blockers before commit. Do not implement Gate E. Do not deploy.

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
- Gate D is admin anomaly review only.
- No rematerialization was executed.
- No production deployment changes were made.
- No broad UI/i18n cleanup.
- No extraction model rewrite.
- No CV parser rewrite beyond read-only display of parser warnings/summaries.
- No React/Next/FastAPI/Mongo/SQLAlchemy/SPA.
- No unexpected migrations.

### Architecture

PASS only if:
- views remain thin.
- anomaly logic lives in services/query helpers/admin config.
- admin pages use efficient querysets.
- no external API calls.
- no LLM calls from views/admin.
- no canonical skills are auto-created.
- matching remains deterministic.
- no destructive admin actions.
- CV files remain private.
- CVUpload.objects soft-delete behavior is not weakened.
- CVUpload.all_objects is only used in admin/privacy/deletion/internal code when justified.

### Required behavior checks

Verify tests or code prove:
- zero-skill jobs are visible in anomaly review.
- generic-only jobs are visible.
- low-confidence job skill rows are visible.
- unmatched candidates are reviewable with deterministic ordering/counts.
- failed/partial skill extraction states are visible.
- hidden/excluded job reasons are visible if fields exist.
- admin pages load for superuser.
- non-superusers cannot access admin-only views.
- private CV file URLs are not exposed.
- no internal integer IDs are used in public links.

### Security/privacy

Fail if:
- `.env` is included or printed.
- real secrets are added.
- CV file URLs are exposed publicly.
- public routes expose internal integer IDs.
- private CV storage is weakened.
- soft-deleted CVs become visible in normal user flows.
- destructive bulk admin actions are added.

## Required commands

```bash
python manage.py check --settings=config.settings.local
python manage.py test apps.jobs apps.skills apps.cvs --settings=config.settings.local
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

OUT="/tmp/tuniatlas_gate_d_review_submission"
ZIP="/tmp/tuniatlas_gate_d_review_submission_$(date +%Y%m%d_%H%M%S).zip"

rm -rf "$OUT"
mkdir -p "$OUT/repo_files" "$OUT/meta"

git status --short --branch > "$OUT/meta/git_status.txt"
git log --oneline --decorate -12 > "$OUT/meta/git_log.txt"
git diff --stat > "$OUT/meta/git_diff_stat.txt"
git diff --check > "$OUT/meta/git_diff_check.txt" || true
git diff -- . ':!.env' ':!*.sqlite3' > "$OUT/meta/git_diff.patch"
git ls-files --modified --others --exclude-standard > "$OUT/meta/changed_files.txt"

{
  echo "Gate D Admin Anomaly Review submission"
  echo "Generated: $(date -Iseconds)"
  echo
  echo "Required local checks before zip:"
  echo "- python manage.py check --settings=config.settings.local"
  echo "- python manage.py test apps.jobs apps.skills apps.cvs --settings=config.settings.local"
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

Upload the generated `/tmp/tuniatlas_gate_d_review_submission_*.zip` to ChatGPT.
