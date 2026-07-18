# ML-0 deterministic product baseline

This test/evidence harness freezes the existing service behavior at the source
commit recorded in the private bundle manifest. It calls the production job
skill extraction/materialization, CV PDF/text and deterministic extraction,
taxonomy normalization, match scoring, match-result, and recommendation
services from an isolated Django test database.

All fixtures are committed, deterministic, and synthetic. Public object and
canonical skill identities use fixed UUIDv4 values; database primary keys are
never exported. LLM, job enrichment, France Travail, and other external calls
are disabled and patched to fail. Temporary PDF files are born-digital,
text-extractable, and removed before the exporter exits.

The immutable private output belongs under the sibling ML repository at
`data/private/baselines/ml0/deterministic-v1/`. It is ignored there and is not
part of either Git repository. The bundle records the taxonomy version
`sha256:d6d5aebf5e4b958f163d2f33b8d441a36e6d638ac8c92379f18e6ebd40e2fc05`.

This harness does not change extraction rules, canonicalization, scoring,
recommendation logic, views, templates, tasks, models, migrations, or product
behavior. Known template/i18n assertions involving raw `À vérifier` and
`Points de vigilance` remain outside this backend baseline ticket.
