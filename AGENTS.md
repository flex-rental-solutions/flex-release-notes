# Release-notes changes

Read [docs/release-notes-workflow.md](docs/release-notes-workflow.md) before preparing or editing release notes, announcements, highlights, or pinned messages. It owns this repository's workflow, content rules, exact-copy proposal, and PR process. Read README.md for the file map and training-video conventions.

Before any remote push, run the repository checker against the fetched base, including the shared JSON schema and both exact CI checks:

```bash
python3 scripts/check_release_notes.py --base origin/main
jq -e '. | length > 0' flex-enterprise.json > /dev/null
jq -e '. | length > 0' flex-assets.json > /dev/null
```

All must succeed on the final content. Re-run after edits, merges, or rebases. Missing jq or validation dependencies blocks publishing; CI is not a substitute for local checks.

Use the same date for a minor release (`x.y.0`) in Enterprise and Assets, and confirm that shared date with the user for each minor release. Propose the date already established for that version when available; the usual cadence is every three weeks on Thursday, with exceptions. Follow the workflow for missing or conflicting dates.

Create the PR and check GitHub Actions through completion. Merge only after CI is green on the latest PR commit and the user has explicitly approved merging that PR. Do not push directly to main or enable auto-merge: main is served live to customers.
