### 📋 Release Notes Living In A GitHub Repo — Concept Exploration

⚠️ This is a concept to explore, not a recommended approach.


### The Idea
What if release notes lived as simple JSON files in this public GitHub repo, and the app just fetched them directly at runtime via raw URL?
No backend. No CMS. No deployment pipeline for content updates — just edit a JSON file, push to GitHub, and the app picks it up.

### How It Might Work
The Flex Web frontend would fetch the appropriate JSON file using GitHub's raw content URL and render it for the user.

Something like: https://raw.githubusercontent.com/flex-rental-solutions/flex-release-notes/refs/heads/main/flex-release-notes.json

### Why This Is Worth Exploring

Simple — release notes are just JSON text files, so why over-engineer it?

No deployment needed — a team member could technically update release notes with just an edit in the GitHub UI.

Public repo = no auth headaches for the app fetching the files

GitHub raw URLs work in the browser — CORS is not an issue


### Open Questions & Potential Pitfalls

- Rate limits — GitHub doesn't publish exact limits for raw file requests. For low-to-moderate traffic this is probably fine, but we don't know where the ceiling is. Worth investigating before we ship.
- Caching — GitHub CDNs raw files for roughly 5 minutes. If we push an update, users won't see it instantly. Is that acceptable for our use case?
- Reliability — This ties our release notes to GitHub's uptime. Probably fine, but worth acknowledging.
- Who owns updates? — Is this a dev workflow or can non-devs manage it?
- What about geographical deploys? Release Notes would show everywhere by default unless there was a way to accomodate that.
