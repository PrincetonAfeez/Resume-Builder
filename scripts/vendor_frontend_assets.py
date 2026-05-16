"""Download pinned frontend vendor assets into resumes/static/resumes/vendor/."""

from __future__ import annotations

import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
VENDOR_DIR = BASE_DIR / "resumes" / "static" / "resumes" / "vendor"

ASSETS = {
    "htmx.min.js": "https://unpkg.com/htmx.org@2.0.4/dist/htmx.min.js",
    "lucide.min.js": "https://unpkg.com/lucide@0.469.0/dist/umd/lucide.min.js",
}


def download_assets() -> None:
    VENDOR_DIR.mkdir(parents=True, exist_ok=True)
    for filename, url in ASSETS.items():
        destination = VENDOR_DIR / filename
        urllib.request.urlretrieve(url, destination)
        print(f"Wrote {destination}")


def main() -> None:
    download_assets()
    print(
        "Rebuild Tailwind: cd frontend && npm install && "
        "npx tailwindcss -c tailwind.config.js -i input.css "
        "-o ../resumes/static/resumes/vendor/tailwind.css --minify"
    )


if __name__ == "__main__":
    main()
