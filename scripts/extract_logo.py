"""Extrae el logo de la Cámara desde el PSD master, lo recorta y guarda como PNG."""
from psd_tools import PSDImage
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).parent.parent
psd = PSDImage.open(ROOT / "plantilla" / "METRICAS DICIEMBRE.psd")

assets_dir = ROOT / "plantilla" / "assets"
assets_dir.mkdir(exist_ok=True)


def find_logo(layer):
    if layer.name and "LOGO" in layer.name.upper():
        return layer
    if layer.is_group():
        for child in layer:
            r = find_logo(child)
            if r:
                return r
    return None


for artboard in psd:
    logo = find_logo(artboard)
    if logo:
        img = logo.composite()
        if img is None:
            continue
        bbox = img.getbbox()
        if bbox:
            img = img.crop(bbox)
        out = assets_dir / "logo_cmp.png"
        img.save(out)
        print(f"Logo guardado en {out} ({img.size})")
        break
