# Gate E — Final Review

Use **Codex GPT-5.5 medium**.

Do not commit, push, or deploy.

## Inspect

```bash
cd ~/Projects/tunitech-abroad
source .venv/bin/activate

git status --short --branch
git log --oneline --decorate -8
git diff --stat
git diff --check
git diff -- . ':!.env' ':!*.sqlite3'
```

## Mandatory verdict checks

PASS only if:

- apply remains explicit and local-only
- a verified backup exists before each apply
- the clean local baseline was restored safely before the final rerun
- targeted dry-run/apply/idempotency evidence exists
- full dry-run and approved full apply evidence exists
- recommendation/match consistency compares actual current rows and scores
- database-family checks prove distinct canonical mappings
- Chef tests prove actual context-sensitive materialization
- CV-noise checks examine only CV-origin rows
- quality explanations are calculated, not hard-coded
- broad detected signals are proven not to alter deterministic scoring
- exact hard technical scoring still works
- no unrelated same-user job is refreshed
- no raw CV text, private file path, secret, `.env`, database dump, or backup is included
- no production access or deployment occurred
- no France Travail/OpenRouter calls occurred
- no migrations were created without explicit justification
- all required tests pass

## Run and capture tests

```bash
cd ~/Projects/tunitech-abroad
source .venv/bin/activate

LOGDIR="/tmp/tuniatlas_gate_e_final_logs"
rm -rf "$LOGDIR"
mkdir -p "$LOGDIR"

set -o pipefail

python manage.py check --settings=config.settings.local \
  2>&1 | tee "$LOGDIR/django_check.txt"

python manage.py test \
  apps.jobs.tests.test_gate_e_rematerialization \
  --settings=config.settings.local \
  2>&1 | tee "$LOGDIR/gate_e_tests.txt"

python manage.py test \
  apps.jobs apps.skills apps.cvs apps.matching apps.recommendations \
  --settings=config.settings.local \
  2>&1 | tee "$LOGDIR/domain_tests.txt"

python manage.py test \
  apps.accounts apps.core apps.cvs apps.jobs apps.matching apps.recommendations \
  --settings=config.settings.local \
  2>&1 | tee "$LOGDIR/full_safety_tests.txt"
```

Stop on any failed command. Do not hide failures with `|| true`.

## Verdict format

```text
PASS or FAIL

1. Summary
2. Scope
3. Local-only and backup safety
4. Baseline restore evidence
5. Targeted apply/idempotency
6. Full dry-run/apply
7. Calculated regression checks
8. Broad-signal scoring proof
9. Recommendation/match consistency
10. Privacy/secrets
11. Test results
12. Blockers
13. Non-blocking issues
14. Safe to commit: yes/no
15. Safe to push/deploy: no
```

## Create the final review zip

```bash
cd ~/Projects/tunitech-abroad

OUT="/tmp/tuniatlas_gate_e_final_review_submission"
ZIP="/tmp/tuniatlas_gate_e_final_review_submission_$(date +%Y%m%d_%H%M%S).zip"
LOGDIR="/tmp/tuniatlas_gate_e_final_logs"

rm -rf "$OUT"
mkdir -p "$OUT/repo_files" "$OUT/meta"

git status --short --branch > "$OUT/meta/git_status.txt"
git log --oneline --decorate -12 > "$OUT/meta/git_log.txt"
git diff --stat > "$OUT/meta/git_diff_stat.txt"
git diff --check > "$OUT/meta/git_diff_check.txt"
git diff -- . ':!.env' ':!*.sqlite3' > "$OUT/meta/git_diff.patch"
git ls-files --modified --others --exclude-standard > "$OUT/meta/changed_files.txt"

cp "$LOGDIR/django_check.txt" "$OUT/meta/"
cp "$LOGDIR/gate_e_tests.txt" "$OUT/meta/"
cp "$LOGDIR/domain_tests.txt" "$OUT/meta/"
cp "$LOGDIR/full_safety_tests.txt" "$OUT/meta/"

{
  echo "Gate E final review submission"
  echo "Generated: $(date -Iseconds)"
  echo
  echo "Excluded:"
  echo "- .env and secrets"
  echo "- database backups/dumps"
  echo "- private CV files and raw CV text"
  echo "- sqlite databases"
  echo
  echo "No production access, push, or deployment performed."
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

Upload the generated `tuniatlas_gate_e_final_review_submission_*.zip` to ChatGPT.
