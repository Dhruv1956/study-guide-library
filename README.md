# Study Guide Library

A small installable PWA that hosts all of Dhruv's HTML study guides in one searchable library. No framework, no build step — vanilla HTML/CSS/JS, a hand-rolled service worker for offline caching, and GitHub Pages for hosting.

## Structure

- `index.html`, `assets/library.css`, `assets/library.js` — the library shell (search + list, grouped by course)
- `guides.json` — index of every guide (title, course, path, date added)
- `guides/<course>/<name>.html` — each guide, self-contained, untouched except for a small "‹ Library" back-link added at the top of `<body>`
- `manifest.json`, `icons/` — PWA manifest and Home Screen icons
- `sw.js` — service worker: precaches the app shell, and caches guide pages plus their CDN dependencies (fonts, MathJax) the first time each is opened, so they work offline afterward

## Updating an existing guide (ACC, EEFM, AI, MVA, FML)

These five guides live outside the repo at their original paths (e.g.
`~/Desktop/ACC/HTML Explanations/ACC_Complete_Guide.html`) and are the
source of truth — edit/append content there as usual. Once saved:

```bash
./sync.sh
```

This pulls the latest version of each source file, re-applies the
"‹ Library" back-link + iOS safe-area snippet, bumps `guides.json`'s
`dateAdded` and the service worker's cache version for whatever actually
changed, then commits and pushes. If nothing changed, it does nothing.
The source→repo mapping lives in `scripts/sync_guides.py`.

## Adding a new guide

1. Save the guide as `guides/<course>/<name>.html`
2. Add one entry to `guides.json`
3. Commit and push — GitHub Pages redeploys automatically (~30s)

To fold a new guide into the `./sync.sh` workflow, add an entry for it
to the `GUIDES` list in `scripts/sync_guides.py`.

## Local preview

Any static file server works, e.g.:

```bash
python3 -m http.server 8080
```

Then open `http://localhost:8080`.

## Notes

- Guide pages currently load fonts and MathJax from CDNs (cdnjs, jsdelivr, Google Fonts). Rather than vendoring those into the repo (which would mean editing every guide's `<script>`/`<link>` tags), the service worker caches those requests at runtime the first time a guide is opened online — so once viewed, a guide (equations included) works offline without touching the guide's own markup.
