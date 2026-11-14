"""Import four licensed editorial photographs as first-party optimized site assets.

One-time release tool only; NOT part of daily data collection or scoring.
Sources were manually reviewed on their Unsplash pages for the free Unsplash
License on 2026-11-14. Do not bulk-scrape or substitute Unsplash+ photos.

Licensing is for the photographs, not depicted trademarks, artworks or
recognizable people. These selected frames are non-portrait architectural
subjects and are used as abstract *illustrative* visuals, not ratings evidence.
"""
from __future__ import annotations
from io import BytesIO
from pathlib import Path
from urllib.request import Request, urlopen
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1] / "site/img"
PHOTOS = [
    ("bridge-editorial-cover.webp",
     "https://images.unsplash.com/photo-1777455223644-6c9f8b1e992a?auto=format&fit=crop&w=1700&q=84",
     "Seongjin Park", "https://unsplash.com/photos/beFnFbrzM8k"),
    ("bridge-editorial-rhythm.webp",
     "https://images.unsplash.com/photo-1713999212351-78f54ee46d9e?auto=format&fit=crop&w=1700&q=84",
     "Clark Van Der Beken", "https://unsplash.com/photos/vZ257hxat1w"),
    ("bridge-editorial-reading.webp",
     "https://images.unsplash.com/photo-1646654858478-1353b164555b?auto=format&fit=crop&w=1700&q=84",
     "Chris Linnett", "https://unsplash.com/photos/uHwPdVbpi9s"),
    ("bridge-editorial-structure.webp",
     "https://images.unsplash.com/photo-1647612728126-9034b22035d3?auto=format&fit=crop&w=1700&q=84",
     "Clark Van Der Beken", "https://unsplash.com/photos/tqss4wZILRQ"),
]


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    for filename, url, author, page in PHOTOS:
        request = Request(url, headers={"User-Agent": "BRIDGEBRAND editorial asset curation (contact: bridgebrand.co.kr)", "Accept": "image/jpeg,image/*;q=0.8"})
        with urlopen(request, timeout=50) as response:
            raw = response.read(10_000_001)
        if len(raw) < 10000 or len(raw) > 10_000_000:
            raise RuntimeError(f"Invalid photographic source size {filename}: {len(raw)}")
        im = Image.open(BytesIO(raw))
        im.verify()
        im = Image.open(BytesIO(raw))
        im = ImageOps.exif_transpose(im).convert("RGB")
        if im.width < 900 or im.height < 500:
            raise RuntimeError(f"Insufficient resolution: {filename} {im.size}")
        if im.width > 1700:
            im.thumbnail((1700, 1700), Image.Resampling.LANCZOS)
        out = ROOT / filename
        im.save(out, "WEBP", quality=81, method=5)
        if out.stat().st_size > 1_000_000:
            raise RuntimeError(f"Asset exceeds 1MB: {filename}")
        print(f"{filename}: {im.width}x{im.height} / {out.stat().st_size} bytes | {author} | {page}")


if __name__ == "__main__":
    main()
