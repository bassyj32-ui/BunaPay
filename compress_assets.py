"""Compress pics/*.png to web copies < 400KB. Metadata-only; never views images."""
from pathlib import Path

from PIL import Image

TARGET = 400 * 1024
MAX_DIM = 1024
MIN_DIM = 512

for name in ("bunapay_logo.png", "bunapay_hero.png"):
    p = Path("pics") / name
    before = p.stat().st_size
    img = Image.open(p)
    print(f"{name} mode={img.mode} size={img.size} before={before}B")

    dim = MAX_DIM
    result = None
    while dim >= MIN_DIM:
        img2 = img.copy()
        w, h = img2.size
        scale = min(1.0, dim / max(w, h))
        if scale < 1.0:
            img2 = img2.resize(
                (max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS
            )
        if img2.mode not in ("RGB", "RGBA", "L"):
            img2 = img2.convert("RGBA" if "A" in img2.getbands() else "RGB")
        img2.save(p, optimize=True)
        after = p.stat().st_size
        result = img2.size
        if after <= TARGET:
            break
        dim = int(dim * 0.85)

    if after > TARGET:
        # last resort: 8-bit palette PNG
        img3 = img.copy().convert("P", palette=Image.ADAPTIVE, colors=256)
        w, h = img3.size
        scale = min(1.0, MIN_DIM / max(w, h))
        if scale < 1.0:
            img3 = img3.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        img3.save(p, optimize=True)
        after = p.stat().st_size
        result = img3.size

    print(f"  -> after={after}B ({(after/before*100):.0f}%) final_size={result} "
          f"{'OK' if after <= TARGET else 'STILL OVER'}")
print("COMPRESS_DONE")
