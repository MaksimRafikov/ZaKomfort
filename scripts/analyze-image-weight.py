#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
DATA = ROOT / "js" / "data.js"

def main() -> None:
    print(f"data.js size: {DATA.stat().st_size / 1024:.1f} KB")
    rows = []
    for case_dir in sorted(ASSETS.iterdir()):
        if not case_dir.is_dir() or case_dir.name == "brand":
            continue
        imgs = [
            p
            for p in case_dir.iterdir()
            if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
        ]
        if not imgs:
            continue
        total = sum(p.stat().st_size for p in imgs)
        after = [p for p in imgs if p.name.startswith("after")]
        avg_after = sum(p.stat().st_size for p in after) / max(1, len(after))
        rows.append((total, len(imgs), case_dir.name, avg_after))

    rows.sort(reverse=True)
    print("\nTop cases by total image weight:")
    for total, n, name, avg_after in rows[:10]:
        print(f"  {name}: {n} imgs, {total / 1024 / 1024:.1f} MB total, avg after {avg_after / 1024:.0f} KB")

    all_imgs = [
        p
        for p in ASSETS.rglob("*")
        if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"} and "brand" not in p.parts
    ]
    png = [p for p in all_imgs if p.suffix.lower() == ".png"]
    jpg = [p for p in all_imgs if p.suffix.lower() in {".jpg", ".jpeg"}]
    print(
        f"\nAll case images: {len(all_imgs)} files, "
        f"{sum(p.stat().st_size for p in all_imgs) / 1024 / 1024:.1f} MB total"
    )
    if png:
        print(f"  PNG: {len(png)} files, avg {sum(p.stat().st_size for p in png) / len(png) / 1024:.0f} KB")
    if jpg:
        print(f"  JPG: {len(jpg)} files, avg {sum(p.stat().st_size for p in jpg) / len(jpg) / 1024:.0f} KB")

    print("\nLargest 12 files:")
    for p in sorted(all_imgs, key=lambda x: x.stat().st_size, reverse=True)[:12]:
        print(f"  {p.relative_to(ROOT)}: {p.stat().st_size / 1024:.0f} KB")

    mp4 = [p for p in ASSETS.rglob("*.mp4") if "brand" not in p.parts]
    if mp4:
        big_mp4 = sorted(mp4, key=lambda p: p.stat().st_size, reverse=True)[:5]
        print("\nLargest videos:")
        for p in big_mp4:
            print(f"  {p.relative_to(ROOT)}: {p.stat().st_size / 1024 / 1024:.1f} MB")


if __name__ == "__main__":
    main()
