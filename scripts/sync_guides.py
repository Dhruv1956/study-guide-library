#!/usr/bin/env python3
"""
Pulls the latest version of each source guide, re-applies the injected
"‹ Library" back-link + iOS safe-area snippet, and writes it into the repo.
Always regenerates from the pristine source, so it's safe to run repeatedly.

Run via ./sync.sh from the repo root (does copy + commit + push in one go).
"""
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# One entry per guide that has a live source file outside the repo.
# accent_bg matches each guide's own color scheme (used by earlier manual edits).
# extra_css is guide-specific rules for its own sticky/fixed elements (sidebar,
# mobile menu button, etc). Empty string if the guide has none.
GUIDES = [
    {
        "source": "~/Desktop/ACC/HTML Explanations/ACC_Complete_Guide.html",
        "dest": "guides/acc/acc-complete-guide.html",
        "accent_bg": "rgba(21,26,32,0.85)",
        "extra_css": "    .sidebar { padding-top: calc(22px + var(--sgl-safe-top)); }\n",
    },
    {
        "source": "~/Desktop/EEFM/HTML explanations/EEFM_explanation.html",
        "dest": "guides/eefm/eefm-explanation.html",
        "accent_bg": "rgba(31,95,79,0.9)",
        "extra_css": (
            "    #sidebar { padding-top: calc(26px + var(--sgl-safe-top)); }\n"
            "    #menuBtn { top: calc(12px + var(--sgl-safe-top)); }\n"
        ),
    },
    {
        "source": "~/Desktop/AI/HTML explanations/Intro to AI - Beginner Guide (Agents, Search, Local Search).html",
        "dest": "guides/ai/intro-to-ai-guide.html",
        "accent_bg": "rgba(21,26,32,0.85)",
        "extra_css": "    .sidebar { padding-top: calc(22px + var(--sgl-safe-top)); }\n",
    },
    {
        "source": "~/Desktop/MVA/HTML explanations/Multivariate Analysis - Beginner Guide (MND, Hotelling, Correlation, Wishart).html",
        "dest": "guides/mva/mva-beginner-guide.html",
        "accent_bg": "rgba(21,26,32,0.85)",
        "extra_css": "    .sidebar { padding-top: calc(22px + var(--sgl-safe-top)); }\n",
    },
    {
        "source": "~/Desktop/FML/HTML Explanations/ML_Numerical_IA_Prep.html",
        "dest": "guides/fml/ml-numerical-ia-prep.html",
        "accent_bg": "rgba(21,26,32,0.85)",
        "extra_css": "",
    },
]

VIEWPORT_RE = re.compile(
    r'<meta\s+name=["\']viewport["\']\s+content=["\']([^"\']*)["\']\s*/?>',
    re.IGNORECASE,
)
CHARSET_RE = re.compile(r'<meta\s+charset=["\'][^"\']*["\']\s*/?>', re.IGNORECASE)
BODY_RE = re.compile(r'<body(\s[^>]*)?>', re.IGNORECASE)


def build_snippet(accent_bg: str, extra_css: str) -> str:
    css_block = (
        "<style>\n"
        "  :root { --sgl-safe-top: 0px; }\n"
        "  @media (display-mode: standalone) {\n"
        "    :root { --sgl-safe-top: env(safe-area-inset-top); }\n"
        "    body { padding-top: var(--sgl-safe-top); }\n"
        f"{extra_css}"
        "  }\n"
        "</style>\n"
    )
    link = (
        '<a href="../../index.html" style="position:fixed;'
        "top:calc(10px + var(--sgl-safe-top));left:10px;z-index:9999;"
        "font-family:system-ui,sans-serif;font-size:13px;padding:5px 11px;"
        f"border-radius:20px;background:{accent_bg};color:#fff;"
        'text-decoration:none;box-shadow:0 2px 8px rgba(0,0,0,0.2);">'
        "‹ Library</a>"
    )
    return css_block + link


def inject(html: str, accent_bg: str, extra_css: str) -> str:
    m = VIEWPORT_RE.search(html)
    if m:
        content = m.group(1)
        if "viewport-fit" not in content:
            new_tag = m.group(0).replace(content, content + ", viewport-fit=cover")
            html = html[: m.start()] + new_tag + html[m.end() :]
    else:
        cm = CHARSET_RE.search(html)
        if not cm:
            raise ValueError("No <meta charset> found to anchor a new viewport tag")
        viewport_tag = (
            '\n<meta name="viewport" content="width=device-width, '
            'initial-scale=1.0, viewport-fit=cover">'
        )
        html = html[: cm.end()] + viewport_tag + html[cm.end() :]

    bm = BODY_RE.search(html)
    if not bm:
        raise ValueError("No <body> tag found")
    snippet = build_snippet(accent_bg, extra_css)
    html = html[: bm.end()] + "\n" + snippet + html[bm.end() :]
    return html


def main():
    changed = []
    missing = []

    for g in GUIDES:
        src = Path(g["source"]).expanduser()
        dest = REPO / g["dest"]
        if not src.exists():
            missing.append(str(src))
            continue

        html = src.read_text(encoding="utf-8")
        html = inject(html, g["accent_bg"], g["extra_css"])

        before = dest.read_text(encoding="utf-8") if dest.exists() else None
        if before == html:
            continue

        dest.write_text(html, encoding="utf-8")
        changed.append(g["dest"])

    if missing:
        print("Warning — source file(s) not found, skipped:", file=sys.stderr)
        for m in missing:
            print(f"  {m}", file=sys.stderr)

    if not changed:
        print("Nothing changed — all guides already up to date.")
        return 0

    print("Updated:")
    for c in changed:
        print(f"  {c}")

    # Bump guides.json dateAdded for whichever guides changed.
    guides_json_path = REPO / "guides.json"
    entries = json.loads(guides_json_path.read_text(encoding="utf-8"))
    today = date.today().isoformat()
    for entry in entries:
        if entry["path"] in changed:
            entry["dateAdded"] = today
    guides_json_path.write_text(
        json.dumps(entries, indent=2) + "\n", encoding="utf-8"
    )

    # Bump the service worker cache version so installed copies refresh.
    sw_path = REPO / "sw.js"
    sw_text = sw_path.read_text(encoding="utf-8")
    vm = re.search(r"const CACHE_VERSION = 'v(\d+)';", sw_text)
    if vm:
        next_version = int(vm.group(1)) + 1
        sw_text = sw_text.replace(
            f"const CACHE_VERSION = 'v{vm.group(1)}';",
            f"const CACHE_VERSION = 'v{next_version}';",
        )
        sw_path.write_text(sw_text, encoding="utf-8")
        print(f"Bumped service worker cache to v{next_version}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
