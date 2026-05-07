"""Inspecciona el PSD master para ver qué capas tiene y exporta el logo."""
from psd_tools import PSDImage
from pathlib import Path

ROOT = Path(__file__).parent.parent
psd = PSDImage.open(ROOT / "plantilla" / "METRICAS DICIEMBRE.psd")

def walk(layer, depth=0):
    pad = "  " * depth
    kind = type(layer).__name__
    extra = ""
    if hasattr(layer, "text") and layer.text:
        snippet = layer.text.replace("\n", " | ")[:80]
        extra = f"  TEXT='{snippet}'"
    print(f"{pad}- [{kind}] '{layer.name}' visible={layer.visible}{extra}")
    if layer.is_group():
        for child in layer:
            walk(child, depth + 1)

print(f"PSD: {psd.size}, capas top-level: {len(list(psd))}")
for layer in psd:
    walk(layer)
