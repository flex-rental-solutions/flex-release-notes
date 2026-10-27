# flex-release-notes

Content repository for the **What's New** popup and **Training Videos** popup inside Flex.

> **Changes go live immediately after pushing to `main` — no code deploy needed.**

---

## Files

| File | Used by |
|------|---------|
| `flex-enterprise.json` | What's New → Enterprise plan customers |
| `flex-assets.json` | What's New → Assets plan customers |
| `flex-training-videos.json` | Training Videos popup |

---

## What's New (`flex-enterprise.json` / `flex-assets.json`)

Each entry in the array is one item in the timeline. Entries are displayed in the order they appear in the file (newest first).

### Standard release entry

```json
{
  "version": "1.16.0",
  "date": "2026-07-09",
  "notes": [
    "Added limited Excel data type formatting for select fields.",
    "Another bullet point here."
  ]
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `version` | ✅ | Semver string. Determines whether the entry is a **Release** (x.y.0) or an **Update** (x.y.z where z > 0). |
| `date` | ✅ | ISO date string `YYYY-MM-DD`. Displayed on the card. |
| `notes` | ✅ | Array of strings or `{text, editedDate}` objects, one per bullet. Objects require the UI-first rollout below. |
| `announcement` | ❌ | Optional HTML string rendered in bold above the bullet points. Good for a short headline or intro sentence. Supports `<a>` tags — use `class="flex-app-redirect"` with a hash URL to link to a page inside Flex. |

### Edited bullets and UI-first rollout

The schema accepts legacy strings, edited-note objects, or a mixture in `notes`:

```json
"notes": [
  "Existing bullet.",
  { "text": "Bullet added after publishing.", "editedDate": "2026-10-22" }
]
```

An object must contain exactly `text` (a nonblank string, with the same HTML support as string bullets) and `editedDate` (a real calendar date in `YYYY-MM-DD` format, including zero padding; timestamps are rejected). The date is when that bullet was edited, not the release date. Compatible clients show a muted `(edited)` marker with a date tooltip and search the object's `text`. Legacy strings, including existing empty strings, retain their validation behavior.

**UI first:** [flex5-desktop PR #4905](https://github.com/flex-rental-solutions/flex5-desktop/pull/4905) must be deployed to compatible desktop clients before publishing any object bullets. Older clients show `[object Object]` and their search fails. Schema acceptance and a merged UI PR are not deployment evidence. Keep existing bullets as strings; do not convert them as part of this compatibility work.

Local and CI validation accept both formats automatically. No rollout variable or command-line opt-in is required. Passing validation checks the content format; it does not establish desktop deployment readiness. See the [repository workflow](docs/release-notes-workflow.md) for the UI-first publishing prerequisite.

### Tabs in the popup

| Tab | Shows |
|-----|-------|
| **Highlights** *(default)* | Releases + Highlight entries (see below) |
| **Releases** | Major releases (x.y.0) only |
| **All** | Everything — releases, updates, and highlights |

---

### Custom title (optional)

By default, release cards show **"Release x.y"** as the heading. You can override this with a `title` field:

```json
{
  "version": "1.17.0",
  "date": "2026-08-01",
  "title": "Important Announcement",
  "notes": [
    "Custom reports will only be available on Flex5 as of September 1st."
  ]
}
```

The `title` replaces the "Release x.y" text entirely — no prefix is added. Existing entries without `title` are unaffected.

---

### Highlight entries (announcements, events, spotlights)

Use `"highlight": true` for entries that aren't tied to a specific release — events, announcements, deprecation notices, etc. These appear in the **Highlights** and **All** tabs, but **not** in Releases.

```json
{
  "version": "highlight-infocomm-2026",
  "date": "2026-07-21",
  "highlight": true,
  "title": "Join us at InfoComm!",
  "notes": [
    "Sign up for our training workshop at booth #1234.",
    "We'll be demoing the new contact import and report engine."
  ]
}
```

> **`version` on highlight entries** — the value isn't shown anywhere (since `title` overrides it), but it must be unique and must not match semver patch format (x.y.z with z > 0) or it will be treated as an Update. A descriptive slug like `"highlight-infocomm-2026"` works well.

---

### Pinned messages (feature-flag gated banners)

Pinned entries render as a blue info banner at the very top of the popup, above the timeline. They are controlled by a feature flag and only shown when the flag is enabled.

```json
{
  "version": "1.16.0",
  "pinned": [
    {
      "flag": "MY-FEATURE-FLAG-KEY",
      "message": "HTML message shown inside the banner."
    }
  ],
  "notes": []
}
```

---

## Training Videos (`flex-training-videos.json`)

> The first object in this file is inline documentation — it is ignored by the app. Refer to it for a quick reference while editing the file.

### Adding a video

1. Copy a YouTube video URL and grab the video ID — the part after `?v=`, e.g. `pWsZNV-XOfk`
2. Copy an existing entry and paste it before the closing `]`
3. Fill in all fields (see table below)
4. Commit and push — changes go live immediately

### Fields

| Field | Required | Description |
|-------|----------|-------------|
| `id` | ✅ | Unique slug, kebab-case. Never reuse or rename an existing ID. |
| `title` | ✅ | Display title shown on the card. |
| `description` | ✅ | Short description shown below the title. |
| `youtubeId` | ✅ | YouTube video ID. Any value starting with `PLACEHOLDER` renders a "Coming Soon" overlay — replace with the real ID when ready. |
| `category` | ✅ | String or array of strings. Videos appear under every matching category filter. |
| `date` | ✅ | ISO date `YYYY-MM-DD`. |
| `tags` | ❌ | Array of hidden search keywords — not displayed, but users can find the video by searching for them. |
| `isNew` | ❌ | Set to `true` to show a "New" badge on the thumbnail. Remove or set to `false` once it's no longer new. |

---

## Tips

- **Order matters** — entries are displayed in the order they appear in the file. Put newest entries at the top.
- **HTML in `announcement`** — keep it short. Supports basic tags (`<a>`, `<br>`, `<strong>`, `<span style="...">`).
- **Linking into the app** — use `<a class="flex-app-redirect" href="#your-route">link text</a>` to deep-link to a page inside Flex. The popup will close and navigate automatically.
- **No deploy needed** — both files are fetched directly from GitHub at runtime. Push to `main` and it's live.

---

## Agent-assisted release notes and validation

Agents follow [AGENTS.md](AGENTS.md) and the [release-notes workflow](docs/release-notes-workflow.md). The shared agent-config skill routes here; this repository owns the detailed content rules and validation.

From the repository root, install the validation dependency and run the same schema and jq checks as CI before any remote push:

```bash
python3 -m pip install -r requirements-validation.txt
python3 scripts/check_release_notes.py --base origin/main
```

The checker validates both complete plan files against [release-notes.schema.json](release-notes.schema.json), previews changed entries in full, and runs `jq -e '. | length > 0'` on both plan files. Python 3 and jq are required. Historical non-semver labels and highlights without titles remain valid; new or changed entries must follow the current authoring rules. Existing duplicate JSON keys in unchanged historical entries are warnings; new or edited duplicate keys fail validation. This preserves existing content while preventing new ambiguity. Run checker behavior tests with `python3 -m unittest discover -s tests -v`.
