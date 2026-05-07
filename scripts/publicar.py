#!/usr/bin/env python3
"""
Genera la carpeta `docs/` lista para publicar con GitHub Pages.

Estructura producida:
  docs/
    index.html              ← lista todos los meses con links
    2025-12/index.html      ← informe diciembre
    2026-01/index.html      ← informe enero
    ...

Cada informe es autocontenido (imágenes en data: URI), así que la carpeta
`docs/` se puede subir tal cual a:
  - GitHub Pages (carpeta /docs)
  - Netlify (drag & drop)
  - Vercel
  - Cualquier hosting estático

Uso:
  python scripts/publicar.py
"""
from __future__ import annotations

import base64
import json
import mimetypes
import shutil
import sys
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "templates"
DATA_DIR = ROOT / "data"
ASSETS = ROOT / "plantilla" / "assets"
PUBLIC = ROOT / "docs"
HIST_FILE = DATA_DIR / "historial.json"


def file_to_data_uri(path: Path) -> str:
    if not path.exists():
        return ""
    mime, _ = mimetypes.guess_type(path.name)
    mime = mime or "application/octet-stream"
    data = base64.b64encode(path.read_bytes()).decode()
    return f"data:{mime};base64,{data}"


def main():
    if PUBLIC.exists():
        shutil.rmtree(PUBLIC)
    PUBLIC.mkdir(parents=True)

    # Cargar todos los meses con datos.yaml e informe.html generado
    meses_dirs = sorted(
        [d for d in DATA_DIR.iterdir()
         if d.is_dir() and (d / "informe.html").exists()],
        reverse=True,   # más reciente primero
    )

    if not meses_dirs:
        sys.exit("No hay informes generados aún. "
                 "Corré scripts/generar_informe.py data/<mes> primero.")

    hist = {}
    if HIST_FILE.exists():
        hist = json.loads(HIST_FILE.read_text(encoding="utf-8"))

    meses_meta = []
    for mdir in meses_dirs:
        mes_id = mdir.name
        target = PUBLIC / mes_id
        target.mkdir()
        shutil.copy(mdir / "informe.html", target / "index.html")
        h = hist.get(mes_id, {})
        meses_meta.append({
            "id": mes_id,
            "label": h.get("label", mes_id),
            "interacciones": h.get("interacciones_total"),
            "seguidores": h.get("seguidores", {}).get("total") if isinstance(h.get("seguidores"), dict) else None,
            "web_clics": h.get("web_clics"),
            "whatsapp_grupos": h.get("whatsapp_grupos"),
        })

    # Render índice
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES)),
        autoescape=select_autoescape(["html"]),
    )
    tmpl = env.get_template("indice.html.j2")
    logo_uri = file_to_data_uri(ASSETS / "logo_cmp.png")
    html = tmpl.render(
        meses=meses_meta,
        logo_uri=logo_uri,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )
    (PUBLIC / "index.html").write_text(html, encoding="utf-8")

    print(f"OK · {len(meses_meta)} mes(es) publicados en {PUBLIC.relative_to(ROOT)}/")
    for m in meses_meta:
        print(f"   · {m['id']}/index.html · {m['label']}")
    print()
    print("Para publicar online (GitHub Pages):")
    print("  git add docs/ && git commit -m 'Actualizar informe' && git push")
    print()
    print("Si el repo todavía no está conectado, ver README.md → 'Setup GitHub'")


if __name__ == "__main__":
    main()
