# CV Parser Corpus Policy

Create local private corpus only:

```text
private_test_corpus/cvs/
private_test_corpus/expected/
private_test_corpus/reports/
```

Add to `.gitignore`:

```gitignore
private_test_corpus/
```

Do not commit real CVs. Do not upload friend CVs to agents or logs. Expected JSON must contain field-level expected outputs only, not full CV text.

Core rule:

```text
Wrong empty is acceptable.
Wrong confident value is not acceptable.
```

## Consent and sourcing

Real CVs from friends/users may be used only with explicit consent for local parser testing. Do not upload those CVs to ChatGPT, Gemini, Codex cloud prompts, GitHub, issue trackers, screenshots, logs, or reports.

Preferred corpus sources:

```text
synthetic CVs for edge cases
user-owned CVs
friend CVs with explicit consent
anonymized copies for repeated local testing
```

Expected JSON files should contain only field-level expected outputs, not full CV text.
