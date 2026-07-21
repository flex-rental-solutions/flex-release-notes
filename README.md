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
| `notes` | ✅ | Array of strings. Each string is one bullet point on the card. |
| `announcement` | ❌ | Optional HTML string rendered in bold above the bullet points. Good for a short headline or intro sentence. Supports `<a>` tags — use `class="flex-app-redirect"` with a hash URL to link to a page inside Flex. |

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
