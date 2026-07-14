# Gate E — Re-review After Blocking Fixes

Use **Codex GPT-5.5 medium**.

Do not commit, push, or deploy.

## Review

Run:

```bash
cd ~/Projects/tunitech-abroad
source .venv/bin/activate

git status --short --branch
git log --oneline --decorate -8
git diff --stat
git diff --check
git diff -- . ':!.env' ':!*.sqlite3'
```

Verify all of the following:

- default mode is dry-run
- apply requires explicit `--apply`
- apply requires exact local settings
- apply rejects remote IPs and remote hostnames
- verified non-empty PostgreSQL backup is created before mutation
- targeted apply report exists
- second targeted apply/idempotency report exists
- full dry-run report exists
- full local apply report exists, or full apply was correctly stopped because dry-run exposed a blocking quality regression
- regression statuses are computed, never hard-coded PASS
- added skills are split into hard technical versus broad/non-scoring
- actual top unmatched phrases are reported
- zero-skill and quality transitions are internally consistent
- only actually changed jobs are considered affected
- targeted match refresh does not recompute an unrelated job for the same user
- dry-run cannot reparse CVs
- no external API, LLM, email, or task enqueue from dry-run
- no canonical Skill auto-creation
- no raw CV text, private path, secret, backup, `.env`, or database dump in Git/zip
- no migrations unless explicitly justified
- no production access

## Required tests

```bash
python manage.py check --settings=config.settings.local
python manage.py test apps.jobs.tests.test_gate_e_rematerialization --settings=config.settings.local
python manage.py test apps.jobs apps.skills apps.cvs apps.matching apps.recommendations --settings=config.settings.local
python manage.py test apps.accounts apps.core apps.cvs apps.jobs apps.matching apps.recommendations --settings=config.settings.local
```

## Verdict format

```text
PASS or FAIL

1. Summary
2. Scope
3. Apply guard
4. Backup evidence
5. Targeted apply and idempotency
6. Full dry-run/apply
7. Report correctness
8. Refresh scope
9. Security/privacy
10. Test results
11. Blockers
12. Non-blocking issues
13. Safe to commit: yes/no
14. Safe to push/deploy: no
```

## Create new review zip

```bash
cd ~/Projects/tunitech-abroad

OUT="/tmp/tuniatlas_gate_e_fixed_review_submission"
ZIP="/tmp/tuniatlas_gate_e_fixed_review_submission_$(date +%Y%m%d_%H%M%S).zip"

rm -rf "$OUT"
mkdir -p "$OUT/repo_files" "$OUT/meta"

git status --short --branch > "$OUT/meta/git_status.txt"
git log --oneline --decorate -12 > "$OUT/meta/git_log.txt"
git diff --stat > "$OUT/meta/git_diff_stat.txt"
git diff --check > "$OUT/meta/git_diff_check.txt" || true
git diff -- . ':!.env' ':!*.sqlite3' > "$OUT/meta/git_diff.patch"
git ls-files --modified --others --exclude-standard > "$OUT/meta/changed_files.txt"

{
  echo "Gate E fixed review submission"
  echo "Generated: $(date -Iseconds)"
  echo
  echo "Excluded:"
  echo "- .env"
  echo "- database backups/dumps"
  echo "- private CV files"
  echo "- sqlite databases"
  echo
  echo "No production deployment performed."
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

Upload the generated `tuniatlas_gate_e_fixed_review_submission_*.zip` to ChatGPT.
