import fitz
import sys
from pathlib import Path

src = Path(sys.argv[1])
out_dir = Path(sys.argv[2])
out_dir.mkdir(parents=True, exist_ok=True)

doc = fitz.open(src)
for i, page in enumerate(doc, start=1):
    pix = page.get_pixmap(dpi=120)
    pix.save(out_dir / f"page_{i:02d}.png")
    print(f"page {i}: {pix.width}x{pix.height}")
print(f"Total pages: {len(doc)}")
