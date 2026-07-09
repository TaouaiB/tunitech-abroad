# Open Questions Before Human Signoff

These do not block implementation, but must be reviewed before commit/deploy.

1. Which OpenRouter model should be used for local testing?
2. What daily limit is acceptable during local test: 20, 50, 100, or more?
3. Should admin have a page to inspect raw vs validated enrichment in this phase or later?
4. Should `JOB_RECOMMENDATIONS_USE_ENRICHED_DATA` be enabled in local immediately after tests pass, or manually after sample enrichment proof?
5. Should old Phase 14C `classification_json` be kept long-term or marked deprecated later?
