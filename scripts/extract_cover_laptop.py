"""Recorta la foto del laptop+dashboard de la página 1 del PDF original."""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).parent.parent
src = ROOT / ".preview" / "page_01.png"
dst = ROOT / "plantilla" / "assets" / "cover_laptop.png"

img = Image.open(src)
W, H = img.size  # 3200x1800 aprox.
print(f"Imagen original: {W}x{H}")

# La foto del laptop ocupa aprox la mitad derecha de la página
# Recortamos el rectángulo del lado derecho con un poco de margen
left = int(W * 0.42)
top = int(H * 0.05)
right = W
bottom = H

cropped = img.crop((left, top, right, bottom))
cropped.save(dst, optimize=True)
print(f"Recortado: {cropped.size} → {dst}")
