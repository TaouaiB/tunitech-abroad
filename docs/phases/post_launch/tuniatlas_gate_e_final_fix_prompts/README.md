# TuniAtlas Gate E Final Correction Pack

## Agent

Use **Codex in Warp, GPT-5.5 medium**.

Gate E is still not safe to commit. The local apply ran, but the report makes several claims that are not calculated from actual data, and the submission omitted the required test logs.

## Workflow

1. Run `01_gate_e_final_corrections.md`.
2. Do not commit, push, or deploy.
3. Run `02_gate_e_final_review.md`.
4. Upload the newly generated review zip to ChatGPT.

## Important local-data note

Gate E already changed the local database.

The earliest reported pre-Gate-E backup is:

```text
/tmp/tuniatlas_gate_e_backup_20260710_171545.dump
```

The correction prompt requires verification and a fresh safety backup before restoring it. If that file is absent or empty, stop rather than guessing.
