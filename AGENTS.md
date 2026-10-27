# Release-notes changes

Read [docs/release-notes-workflow.md](docs/release-notes-workflow.md) before preparing or editing release notes, announcements, highlights, or pinned messages. It owns this repository's workflow, content rules, exact-copy proposal, and PR process. Read README.md for the file map and training-video conventions.

Before any remote push, run the repository checker against the fetched base, including the shared JSON schema and both exact CI checks:

```bash
python3 scripts/check_release_notes.py --base origin/main
jq -e '. | length > 0' flex-enterprise.json > /dev/null
jq -e '. | length > 0' flex-assets.json > /dev/null
```

All must succeed on the final content. Re-run after edits, merges, or rebases. Missing jq or validation dependencies blocks publishing; CI is not a substitute for local checks. Do not push directly to main or merge a PR without a separate request: main is served live to customers.
