# CLAUDE.md — flex-release-notes

This repo is a content-only JSON repository. There is no build step, no dependencies, and no code to run. **Push to `main` and changes are live immediately** — the Flex app fetches these files directly from GitHub at runtime.

## Files

| File | Purpose |
|------|---------|
| `flex-enterprise.json` | What's New popup — Enterprise plan customers |
| `flex-assets.json` | What's New popup — Assets plan customers |
| `flex-training-videos.json` | Training Videos popup |
| `README.md` | Human-readable docs for non-technical editors |

Both `flex-enterprise.json` and `flex-assets.json` share the same schema. When adding a release, add it to **both files** unless there is a specific reason not to (e.g., a feature only available on one plan).

---

## Release Notes Schema (`flex-enterprise.json` / `flex-assets.json`)

Each file is a top-level JSON array. **Newest entries go at the top.** Order matters — the app displays entries in file order.

### How the app classifies entries

The app reads `version` to decide how to render the entry:

- **Release** (`x.y.0` — patch segment is 0): shown as a full release card with a blue left border. Appears in the Releases tab and All tab.
- **Update/patch** (`x.y.z` — patch segment > 0, AND major >= 1): shown as a compact update row. Appears in the All tab only (grouped under their minor version header).
- **Highlight** (`"highlight": true`): shown as a release-style card regardless of version. Appears in the Highlights tab and All tab, but NOT the Releases tab. (Requires app support — see notes below.)

### All fields

```json
{
  "version": "1.16.0",
  "date": "2026-07-09",
  "notes": [
    "First bullet point.",
    "Second bullet point."
  ],
  "announcement": "Optional HTML shown in bold above the bullet points.",
  "title": "Optional custom card heading — replaces 'Release x.y' if provided.",
  "highlight": true,
  "pinned": [
    {
      "flag": "FEATURE-FLAG-KEY",
      "message": "HTML shown in a blue banner at the top of the popup."
    }
  ]
}
```

| Field | Required | Notes |
|-------|----------|-------|
| `version` | ✅ | Semver string. Determines release vs. update classification (see above). For highlight entries, use a descriptive slug like `"highlight-infocomm-2026"` — it won't be displayed. |
| `date` | ✅ | `YYYY-MM-DD`. Shown on the card. |
| `notes` | ✅ | Array of strings. Each string = one bullet. Can be empty array `[]`. |
| `announcement` | ❌ | HTML string. Rendered above bullets in a slightly bolder style. Good for a short intro sentence or headline. Supports `<a>`, `<br>`, `<strong>`, `<span style="...">`. |
| `title` | ❌ | Overrides the auto-generated "Release x.y" heading entirely. Use for highlights or when a release needs a custom label (e.g., "Important Announcement"). |
| `highlight` | ❌ | `true` to mark as a standalone highlight/announcement not tied to a release. Renders as a release card. |
| `pinned` | ❌ | Array of feature-flag-gated banner messages shown at the very top of the popup. Each item needs `flag` (LaunchDarkly/feature flag key, boolean) and `message` (HTML string). |

### Deep-linking into the Flex app

Inside `announcement` or `message` fields, use this pattern to link to a page inside Flex. The popup closes and navigates automatically:

```html
<a class="flex-app-redirect" href="#contact-import/import">Get started</a>
```

Regular `<a target="_blank">` links open in a new browser tab as normal.

### Common tasks

**Add a new major release** (add to top of both JSON files):
```json
{
  "version": "1.17.0",
  "date": "2026-08-01",
  "notes": [
    "Added X feature.",
    "Improved Y workflow."
  ],
  "announcement": "Short headline or intro sentence here."
}
```

**Add a patch/update** (add to top of both JSON files):
```json
{
  "version": "1.17.1",
  "date": "2026-08-05",
  "notes": [
    "Fix for an issue that caused X when doing Y."
  ]
}
```

**Add a highlight/announcement** (add to top of both JSON files):
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

---

## Training Videos Schema (`flex-training-videos.json`)

Top-level JSON array. The **first object** is inline documentation (keys start with `_`) — it is ignored by the app. Do not remove it.

### All fields

| Field | Required | Notes |
|-------|----------|-------|
| `id` | ✅ | Unique kebab-case slug. Never reuse or rename — used as a stable identifier. |
| `title` | ✅ | Display title on the card. |
| `description` | ✅ | Short description. Supports `\n` for line breaks. |
| `youtubeId` | ✅ | YouTube video ID (the part after `?v=`). Any value starting with `PLACEHOLDER` renders a "Coming Soon" overlay. Replace with the real ID when the video is ready. |
| `category` | ✅ | String or array of strings. Videos appear under every matching category filter. Valid categories: `Warehouse`, `Sales`, `Accounting`, `Admin`. |
| `date` | ✅ | `YYYY-MM-DD`. |
| `tags` | ❌ | Array of hidden search keywords. Not displayed but searchable. |
| `isNew` | ❌ | `true` shows a "New" badge on the thumbnail. Remove or set to `false` once no longer new. |

### Adding a video

```json
{
  "id": "your-unique-slug",
  "title": "Your Video Title",
  "description": "A short sentence or two about what this video covers.",
  "youtubeId": "pWsZNV-XOfk",
  "category": ["Warehouse", "Sales"],
  "tags": ["scanning", "checkout", "returns"],
  "date": "2026-08-01",
  "isNew": true
}
```

Add new videos before the closing `]`. The app displays videos in file order.

---

## Rules and conventions

- **JSON must be valid.** Invalid JSON silently breaks the popup. Always validate after editing (e.g., paste into jsonlint.com or use a JSON-aware editor).
- **Newest entries at the top** for both release notes files.
- **No trailing commas.** Standard JSON does not allow them.
- **Both plan files** (`flex-enterprise.json` and `flex-assets.json`) should generally stay in sync for release entries. Assets-specific notes can be omitted from enterprise and vice versa.
- **Patch note tone:** Start with "Fix for an issue that caused..." or "Various fixes and improvements." Keep it user-facing, not technical.
- **Bullet length:** Keep each note to one clear sentence. No markdown — plain text only inside `notes` arrays.
- **HTML in `announcement`:** Keep it concise. Avoid complex styling. Escape double quotes as `\"` inside JSON strings.
