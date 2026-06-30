# Changelog v3 — Post-launch Folder Path Update

This pack supersedes v2 for repositories that separate completed MVP launch phases from post-launch phases.

## Path decision

All v1.1 execution files now live under:

```text
docs/phases/post_launch/
```

Previous MVP/build/deployment phases should stay under:

```text
docs/phases/mvp_launch/
```

## Updated references

All Gemini prompts, Codex review prompts, README, install guidance, and shared policy references now point to:

```text
docs/phases/post_launch/...
```

## Use this pack instead of v2

Do not mix v2 and v3 phase files. If v2 was already copied directly into `docs/phases/`, move or replace those files so the active post-launch phase pack is under `docs/phases/post_launch/`.
