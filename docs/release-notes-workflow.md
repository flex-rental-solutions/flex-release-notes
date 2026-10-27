# Flex release notes

Use this workflow for requested content changes in the `flex-release-notes` repository, even when invoked from another Flex workspace. Locate that repository before running Git or validation commands. `main` is served directly to Flex customers: finish with a PR targeting `main`; do not push directly to `main`, merge, or enable auto-merge.

## Start from current main

1. Locate the repository (normally `~/projects/flex/flex-release-notes`). Read its current instructions, `README.md`, relevant JSON entries, CI workflow, and any PR template, including templates under `.github/PULL_REQUEST_TEMPLATE/`. Use the remote URL to confirm the repository identity.
2. Inspect status, current branch, and existing PRs for this request. Preserve unrelated edits and untracked files. On a new request, fetch `origin main` successfully, record `git rev-parse origin/main`, and create a fresh, descriptive branch directly from that ref, e.g. `git switch -c release-notes/1.23.0 origin/main`. A stale local `main`, current feature branch, or cached ref after a failed fetch is insufficient. Use a separate worktree from `origin/main` if switching would carry unrelated changes. Do not reset, clean, or stash another person's work.
3. On a resumed request, reuse its branch/PR rather than duplicating it. Fetch and incorporate newer `origin/main` before editing; preserve existing request commits. If remote access fails, report that latest-main verification is blocked; local drafts may continue but do not claim they are current.

## Resolve the requested content

Preserve supplied wording, punctuation, capitalization, Unicode, links, order, and bullet boundaries. Do not silently fix typos, shorten copy, or apply the documented tone conventions to verbatim user text. If asked to write copy, draft it and show it in full. Use the user's version and release date; do not infer either from the newest entry, today's date, or an existing test placeholder. Ask only for required facts that remain unclear, such as date, plan scope, or a pin's flag key.

- `flex-enterprise.json`: Enterprise What's New content.
- `flex-assets.json`: Assets What's New content. Normally add releases to both files, applying explicit plan restrictions. Explain each difference; do not assume Enterprise features apply to Assets. Keep identical shared wording identical.
- `flex-release-notes.json`: unrelated legacy/sample data, despite its name. Do not use it for What's New.
- `flex-training-videos.json`: change only for an explicit video request; follow its inline documentation and preserve the first documentation object and stable video IDs.

Search each target file for the requested version/slug before adding it. If it exists, update that entry for the requested change rather than creating another. Do not replace unrelated fields, existing announcements, or pins. If existing content conflicts with the request and replacement intent is unclear, clarify. New entries go at the top; preserve older entries and their order. Avoid reformatting entire files.

## Choose fields by intended placement

These are independent choices: a release can contain ordinary notes, an announcement, and pinned messages together. The word “announcement” alone does not identify its intended placement; infer from context or clarify when ambiguous.

| Intent | Representation and behavior |
| --- | --- |
| Release | `version: "x.y.0"`, `date: "YYYY-MM-DD"`, `notes: [strings]`. Full card in Highlights, Releases, and All. |
| Patch/update | `x.y.z` with major >= 1 and patch > 0; same required fields. Update in All, grouped by minor version. Do not renumber a patch to make it a release. Legacy `0.x.y` entries use different classification. |
| Intro/headline on a release card | Optional `announcement` HTML string above bullets. This does not make an entry a highlight or a pin. The patch renderer does not show this field; clarify if a patch request requires a visible headline. |
| Standalone event, notice, spotlight | `highlight: true`, unique non-semver `version` slug such as `highlight-training-2026`, `title`, `date`, and `notes`. Highlights and All, excluded from Releases. |
| Custom heading | Optional `title` replaces the default “Release x.y” heading entirely. It does not change classification. |
| Banner at top of popup | `pinned` with `{ "flag": "actual-flag-key", "message": "HTML copy" }`, or an array of those objects for multiple pins. Both shapes are supported; preserve an existing shape when practical. Each pin requires an actual boolean feature flag key; never invent it or change flag targeting. |

Keep `version`, `date`, and `notes` on new entries, including banner-only entries (`notes: []`). Pins are collected from all eligible entries, so copying an old pin to each new release can duplicate the banner. Preserve historical pins unless removal or movement was requested. Pins on a future version may be hidden by the client's version filter even when their flag is enabled; do not promise immediate visibility just because the date has arrived. For recent patches, the client may show only a changelog link instead of individual bullets.

The docs show pins as arrays, while existing content also uses objects; both are supported by `ReleaseNotesPopup.js` in `flex5-desktop/packages/local/flex-core/src/workbench/`. That renderer also inserts notes and titles as HTML, despite the older plain-text guidance. If behavior is disputed, inspect the available client implementation and state any uncertainty about deployed-client support instead of changing the content schema speculatively.

## Preserve text through JSON and HTML

Treat these as separate encoding layers:

- Build strings in memory and use a JSON serializer to escape `"`, backslashes, newlines, tabs, and control characters exactly once. Apostrophes, curly quotes, emoji, `/`, and ordinary Unicode do not need manual JSON escaping. Avoid whole-file serialization when it would rewrite historical formatting or duplicate keys.
- HTML is supported in `announcement`, pin `message`, and existing note bullets. Preserve intended tags and their attributes. For literal text rendered in HTML, encode literal `&`, `<`, and `>` as `&amp;`, `&lt;`, and `&gt;` where necessary; encode attribute values appropriately. Do not HTML-escape an entire intentional link or double-encode existing entities. Explain necessary representation changes while preserving the user's visible copy.
- App links use `<a class="flex-app-redirect" href="#contact-import/import">Get started</a>`. External links can follow existing `target="_blank" rel="noopener noreferrer"` conventions. Preserve supplied destinations; do not invent routes.
- Example decoded string: `Choose "Save" in C:\Reports.` Its JSON representation is `"Choose \"Save\" in C:\\Reports."`. Example HTML source: `<a href="https://example.com/?a=1&amp;b=2">Read more</a>`; JSON serialization escapes the attribute quotes, leaving the intentional HTML intact.
- Keep content out of shell interpolation. Use file-edit tools or quoted heredocs and serializers; backticks and `$()` in copy must stay literal. Supply multiline PR bodies through a connector argument or `gh ... --body-file`.

## Validate and show the complete proposal

From the repository root, run `python3 scripts/check_release_notes.py --base origin/main`. Install its dependency with `python3 -m pip install -r requirements-validation.txt` if needed. CI uses the same checker and `release-notes.schema.json`. The checker validates both plan files, checks changed entries and duplicate keys against the base, and emits complete JSON and decoded text. Unchanged historical duplicate keys are warnings; do not rewrite them incidentally. Review copy, audience, dates, flags, links, HTML intent, and the actual diff separately. Run behavior tests with `python3 -m unittest discover -s tests -v`.

Before **any push to a remote**, run the current repository CI validation locally against the exact files being pushed. Read `.github/workflows/validate-json.yml` for changes to these checks. Currently both commands must succeed:

```bash
jq -e '. | length > 0' flex-enterprise.json > /dev/null
jq -e '. | length > 0' flex-assets.json > /dev/null
```

The bundled checker also executes these two `jq` checks at the end. A missing `jq`, nonzero exit, malformed JSON, or empty file blocks pushing and PR creation. Install an available local `jq` through an authorized method or report the blocker; do not substitute Python parsing or defer validation to CI. Repeat the checks after every edit, merge, or rebase before a subsequent push.

Before committing/pushing and creating the PR, send a comprehensive user-facing proposal derived from the actual edited files:

- Version or highlight slug, release date, message types, target plans/files, and each plan-specific difference or exclusion.
- The **full, unaltered text** of every proposed note, title, announcement, and pin, in order, including flag keys and complete links. Use fenced text/HTML blocks so markup is visible; do not paraphrase, truncate, replace copy with ellipses, or refer only to an attachment/diff. When both plans have identical content, show it once and explicitly identify both audiences. Show differing content completely for each plan.
- Exact JSON for the proposed entries so escaping is reviewable, alongside the decoded copy. Explain necessary encoding and any existing content being replaced or removed. Report validation results and unresolved limitations.

This summary is required before PR creation; it is not an additional approval gate when the user already requested the PR. If required facts or conflicting replacement intent remain unresolved, keep the draft local and ask the focused question. If the user asked to approve the proposal first, wait for their response.

## Create and verify the PR

1. Inspect `git diff --check` and the complete scoped diff. Confirm only intended content changed and existing versions were not duplicated. Re-run validation after any subsequent edit or integration of newer main.
2. Fetch `origin main` again before publishing. If it advanced, incorporate it, resolve content conflicts without dropping either change, validate, and refresh the full proposal if proposed content changed.
3. Commit only the requested files, ensure both CI-equivalent `jq` checks have passed on the final content, push the feature branch, and create a PR with base `main` through an already authorized GitHub connector or CLI. Check for an existing PR before retrying after an uncertain create result. Do not start browser authentication without explicit approval.
4. Read and follow the repository's actual PR template, preserving headings and checklists. If none exists, include the version/date, audience, content types, full proposed content, relevant encoding decisions, and verification. Check only verified items; leave pending CI unchecked. Read back the saved PR body and verify base/head and changed files. Fix any missing or altered copy.
5. Return the PR link, affected audiences/version, and validation/CI status. Attach the PR to the chat if that capability is available. Stop at the PR; merging publishes customer-visible content and requires a separate request.
