# ML-0 deterministic product baseline

`deterministic-v1` is retained for audit but is superseded and
non-authoritative because it populated the isolated database from the initial
seed while recording the identity of the larger approved snapshot.

This test/evidence harness freezes the existing service behavior at the source
commit recorded in the private bundle manifest. It calls the production job
skill extraction/materialization, CV PDF/text and deterministic extraction,
taxonomy normalization, match scoring, match-result, and recommendation
services from an isolated Django test database.

The corrected `deterministic-v2` harness validates and loads the exact approved
private taxonomy snapshot into the isolated test database, then proves exact
skill, alias, active/inactive, UUID, category, and deprecation/replacement
equality before running any case. The initial seed is not an authority source.

All fixtures are committed, deterministic, and synthetic. Public object and
canonical skill identities use fixed UUIDv4 values; database primary keys are
never exported. LLM, job enrichment, France Travail, and other external calls
are disabled and patched to fail. Temporary PDF files are born-digital,
text-extractable, and removed before the exporter exits.

The immutable private output belongs under the sibling ML repository at
`data/private/baselines/ml0/deterministic-v2/`. It is ignored there and is not
part of either Git repository. The bundle records the taxonomy version
`sha256:d6d5aebf5e4b958f163d2f33b8d441a36e6d638ac8c92379f18e6ebd40e2fc05`.

This harness does not change extraction rules, canonicalization, scoring,
recommendation logic, views, templates, tasks, models, migrations, or product
behavior. Known template/i18n assertions involving raw `À vérifier` and
`Points de vigilance` remain outside this backend baseline ticket.

The v2 failure ledger is derived assertion by assertion from obvious-gold
expectations, and the publisher uses Linux atomic no-replace semantics. It
cannot overwrite a concurrently created empty or non-empty target.
