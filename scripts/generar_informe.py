#!/usr/bin/env python3
"""
Genera el informe HTML del mes a partir de datos.yaml + capturas.

Uso:
  python scripts/generar_informe.py data/2025-12

Salidas en data/<mes>/:
  - informe.html             ← abrir en navegador
  - informe_borrador.md      ← versión texto plano

Para exportar a PDF:
  Abrí informe.html en Chrome → Cmd+P → "Guardar como PDF"
  · Activá "Gráficos de fondo"
  · Márgenes: "Ninguno"
"""
from __future__ import annotations

import base64
import json
import mimetypes
import sys
from pathlib import Path
from datetime import datetime

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "templates"
ASSETS = ROOT / "plantilla" / "assets"
HIST_FILE = ROOT / "data" / "historial.json"


# =============================================================================
# Helpers
# =============================================================================
def variacion_pct(actual, anterior):
    if actual is None or anterior is None:
        return None
    if anterior == 0:
        return None if actual == 0 else float("inf")
    return round((actual - anterior) / anterior * 100, 1)


def fmt_num(n):
    if n is None:
        return "—"
    if isinstance(n, float):
        return f"{n:.1f}".replace(".", ",")
    return f"{n:,}".replace(",", ".")


def delta_str(v):
    if v is None:
        return ""
    if v == float("inf"):
        return "▲ nuevo"
    flecha = "▲" if v >= 0 else "▼"
    return f"{flecha} {abs(v):.1f}%"


def delta_class(v):
    if v is None:
        return "flat"
    if v == 0:
        return "flat"
    if v == float("inf") or v > 0:
        return "up"
    return "down"


def duracion_str(segundos):
    if segundos is None:
        return "—"
    m, s = divmod(int(segundos), 60)
    return f"{m}:{s:02d} min"


# =============================================================================
# Capturas (data URI)
# =============================================================================
def file_to_data_uri(path: Path) -> str:
    if not path.exists():
        return ""
    mime, _ = mimetypes.guess_type(path.name)
    mime = mime or "application/octet-stream"
    data = base64.b64encode(path.read_bytes()).decode()
    return f"data:{mime};base64,{data}"


CAPTURAS_MAP = {
    "contenidos_destacados_anterior": "02_contenidos_destacados_anterior",
    "contenidos_destacados_actual":   "02_contenidos_destacados_actual",
    "publicacion_top":                "03_publicacion_top",
    "seguidores_anterior":            "04_seguidores_anterior",
    "seguidores_actual":              "04_seguidores_actual",
    "visitantes_anterior":            "04b_visitantes_anterior",
    "visitantes_actual":              "04b_visitantes_actual",
    "youtube_anterior":               "07_youtube_anterior",
    "youtube_actual":                 "07_youtube_actual",
    "luciana_perfil_anterior":        "08_luciana_perfil_anterior",
    "luciana_perfil_actual":          "08_luciana_perfil_actual",
    "luciana_interaccion":            "09_luciana_interaccion",
    "luciana_top":                    "09_luciana_top",
    "web_searchconsole_anterior":     "06_web_searchconsole_anterior",
    "web_searchconsole_actual":       "06_web_searchconsole_actual",
}


def cargar_capturas(mes_dir: Path) -> dict[str, str]:
    cap_dir = mes_dir / "capturas"
    out = {}
    for key, prefix in CAPTURAS_MAP.items():
        for ext in ("png", "PNG", "jpg", "JPG", "jpeg", "JPEG", "webp"):
            p = cap_dir / f"{prefix}.{ext}"
            if p.exists():
                out[key] = file_to_data_uri(p)
                break
        else:
            out[key] = ""
    return out


# =============================================================================
# Totales y deltas
# =============================================================================
def total_interacciones(c: dict) -> int:
    return (c.get("reacciones", 0) + c.get("comentarios", 0)
            + c.get("compartidos", 0) + c.get("guardados", 0)
            + c.get("envios", 0))


def calcular_deltas(d: dict) -> dict:
    deltas: dict = {}

    c = d["contenidos"]
    deltas["rea"]   = variacion_pct(c["actual"]["reacciones"],   c["anterior"]["reacciones"])
    deltas["com"]   = variacion_pct(c["actual"]["comentarios"],  c["anterior"]["comentarios"])
    deltas["share"] = variacion_pct(c["actual"]["compartidos"],  c["anterior"]["compartidos"])
    deltas["interacciones_total"] = variacion_pct(
        total_interacciones(c["actual"]), total_interacciones(c["anterior"])
    )

    s = d["seguidores"]
    deltas["seguidores_total"]  = variacion_pct(s["actual"]["total"],  s["anterior"]["total"])
    deltas["seguidores_nuevos"] = variacion_pct(s["actual"]["nuevos"], s["anterior"]["nuevos"])

    if d.get("visitantes_pagina"):
        v = d["visitantes_pagina"]
        deltas["visit_views"]  = variacion_pct(v["actual"]["visualizaciones"],   v["anterior"]["visualizaciones"])
        deltas["visit_unique"] = variacion_pct(v["actual"]["visitantes_unicos"], v["anterior"]["visitantes_unicos"])

    if d.get("youtube") and d["youtube"].get("anterior") and d["youtube"].get("actual"):
        y = d["youtube"]
        deltas["yt_vistas"] = variacion_pct(y["actual"]["vistas"], y["anterior"]["vistas"])

    if d.get("luciana"):
        L = d["luciana"]
        if L["seguidores"].get("anterior"):
            deltas["luc_total"]  = variacion_pct(L["seguidores"]["actual"]["total"],  L["seguidores"]["anterior"]["total"])
            deltas["luc_nuevos"] = variacion_pct(L["seguidores"]["actual"]["nuevos"], L["seguidores"]["anterior"]["nuevos"])
        if L["interaccion"].get("anterior"):
            deltas["luc_interacciones"] = variacion_pct(
                L["interaccion"]["actual"]["sociales_total"],
                L["interaccion"]["anterior"]["sociales_total"]
            )

    return deltas


def calcular_totales(d: dict) -> dict:
    return {
        "contenidos": {
            "actual":   total_interacciones(d["contenidos"]["actual"]),
            "anterior": total_interacciones(d["contenidos"]["anterior"]),
        }
    }


# =============================================================================
# Borradores asistidos
# =============================================================================
def sugerir_conclusiones(d: dict, deltas: dict, totales: dict) -> list[str]:
    sugs: list[str] = []
    var_int = deltas.get("interacciones_total")
    int_act = totales["contenidos"]["actual"]
    int_ant = totales["contenidos"]["anterior"]

    if var_int is not None and var_int > 30:
        sugs.append(
            f"Durante {d['mes_label'].lower()} se registró un <b>crecimiento "
            f"significativo en interacciones (+{var_int:.0f}%)</b>, pasando de "
            f"{int_ant} a <b>{int_act}</b>, lo que refleja mayor engagement de "
            f"la comunidad con el contenido publicado."
        )
    elif var_int is not None and var_int < -20:
        sugs.append(
            f"Durante {d['mes_label'].lower()} se observó una <b>caída en "
            f"interacciones ({var_int:.0f}%)</b>, pasando de {int_ant} a "
            f"{int_act}. Sugiere revisar la frecuencia y el tipo de contenido."
        )

    s = d["seguidores"]
    var_n = deltas.get("seguidores_nuevos")
    if var_n is not None and var_n > 0:
        sugs.append(
            f"La adquisición de nuevos seguidores creció {delta_str(var_n)}, "
            f"sumando <b>{s['actual']['nuevos']}</b> nuevos seguidores en el mes "
            f"({s['actual']['total']} en total)."
        )
    elif var_n is not None and var_n < 0:
        sugs.append(
            f"Si bien el alcance se mantiene, los nuevos seguidores cayeron "
            f"{delta_str(var_n)} respecto al mes anterior."
        )

    if d.get("visitantes_pagina"):
        var_v = deltas.get("visit_unique")
        if var_v is not None:
            sugs.append(
                f"La página de LinkedIn registró <b>"
                f"{d['visitantes_pagina']['actual']['visitantes_unicos']} "
                f"visitantes únicos</b> ({delta_str(var_v)} vs "
                f"{d['mes_anterior_label'].lower()})."
            )

    if d.get("youtube"):
        y = d["youtube"]["actual"]
        sugs.append(
            f"El canal de YouTube acumuló <b>{y['vistas']} vistas</b> y cuenta "
            f"con {y['suscriptores_total']} suscriptores. Se observa un canal "
            f"todavía en etapa inicial con margen de crecimiento."
        )

    if d.get("luciana"):
        L = d["luciana"]
        sugs.append(
            f"El perfil ejecutivo de <b>{L['perfil']['nombre']}</b> registró "
            f"{L['interaccion']['actual']['sociales_total']} interacciones "
            f"sociales y suma {L['seguidores']['actual']['total']} seguidores."
        )

    sc = d["web"]["search_console"]
    if sc.get("clics_var_pct", 0) > 0:
        sugs.append(
            f"En el sitio web los clics desde Google crecieron "
            f"<b>+{sc['clics_var_pct']}%</b> ({sc['clics']} clics totales), "
            f"mostrando una correcta articulación entre redes sociales y web."
        )

    return sugs


def sugerir_oportunidades(d: dict, deltas: dict) -> list[str]:
    sugs = [
        "Sostener la <b>frecuencia de publicaciones</b>, especialmente en "
        "semanas de menor actividad, para mantener el ritmo de adquisición "
        "de seguidores.",

        "Replicar contenidos del tipo <b>eventos, reuniones y acciones "
        "institucionales</b>, que demuestran consistentemente alto nivel "
        "de engagement.",

        "Incorporar <b>llamados a la acción claros</b> (visitar la web, "
        "sumarse a grupos, suscribirse al canal de YouTube) para canalizar "
        "el interés generado en redes.",

        "Explorar <b>formatos complementarios</b> (videos cortos, placas "
        "informativas, carruseles) y aumentar la producción de contenido "
        "para el canal de YouTube.",
    ]

    if d.get("luciana"):
        sugs.append(
            "Coordinar la <b>agenda de publicaciones del perfil ejecutivo de "
            f"{d['luciana']['perfil']['nombre']}</b> con la de la Cámara "
            "para amplificar mensajes clave."
        )

    return sugs


# =============================================================================
# Histórico
# =============================================================================
def actualizar_historial(d: dict, totales: dict) -> None:
    HIST_FILE.parent.mkdir(parents=True, exist_ok=True)
    hist = json.loads(HIST_FILE.read_text(encoding="utf-8")) if HIST_FILE.exists() else {}
    entry = {
        "label": d["mes_label"],
        "interacciones_total": totales["contenidos"]["actual"],
        "seguidores": d["seguidores"]["actual"],
        "web_clics": d["web"]["resumen_semanal"]["clics_totales"],
        "whatsapp_grupos": len(d["whatsapp"]["grupos"]),
        "whatsapp_miembros": sum(g["miembros"] for g in d["whatsapp"]["grupos"]),
    }
    if d.get("visitantes_pagina"):
        entry["visitantes_unicos"] = d["visitantes_pagina"]["actual"]["visitantes_unicos"]
    if d.get("youtube"):
        entry["youtube_vistas"] = d["youtube"]["actual"]["vistas"]
        entry["youtube_suscriptores"] = d["youtube"]["actual"]["suscriptores_total"]
    if d.get("luciana"):
        entry["luciana_seguidores"] = d["luciana"]["seguidores"]["actual"]["total"]
        entry["luciana_interacciones"] = d["luciana"]["interaccion"]["actual"]["sociales_total"]
    hist[d["mes"]] = entry
    HIST_FILE.write_text(json.dumps(hist, indent=2, ensure_ascii=False), encoding="utf-8")


# =============================================================================
# Markdown borrador
# =============================================================================
def render_md(d: dict, deltas: dict, totales: dict) -> str:
    L = []
    L.append(f"# Informe — {d['mes_label']}")
    L.append("")
    L.append(f"_Generado el {datetime.now():%Y-%m-%d %H:%M}_")
    L.append("")
    L.append(f"## KPI principal del mes")
    L.append(f"- **Interacciones totales (CMP):** {totales['contenidos']['actual']} "
             f"({delta_str(deltas.get('interacciones_total'))})")
    L.append(f"- **Nuevos seguidores (CMP):** {d['seguidores']['actual']['nuevos']} "
             f"({delta_str(deltas.get('seguidores_nuevos'))})")
    if d.get("visitantes_pagina"):
        L.append(f"- **Visitantes únicos:** {d['visitantes_pagina']['actual']['visitantes_unicos']} "
                 f"({delta_str(deltas.get('visit_unique'))})")
    if d.get("youtube"):
        L.append(f"- **Vistas YouTube:** {d['youtube']['actual']['vistas']}")
    if d.get("luciana"):
        L.append(f"- **Interacciones perfil Luciana:** "
                 f"{d['luciana']['interaccion']['actual']['sociales_total']}")
    L.append(f"- **Clics web (Search Console):** {d['web']['search_console']['clics']} "
             f"(+{d['web']['search_console']['clics_var_pct']}%)")
    L.append("")
    L.append("## Conclusiones (borrador)")
    for x in d["conclusiones"]:
        L.append(f"- {x}")
    L.append("")
    L.append("## Oportunidades (borrador)")
    for x in d["oportunidades"]:
        L.append(f"- {x}")
    return "\n".join(L)


# =============================================================================
# Main
# =============================================================================
def main():
    if len(sys.argv) != 2:
        print(__doc__); sys.exit(1)

    mes_dir = Path(sys.argv[1]).resolve()
    yaml_file = mes_dir / "datos.yaml"
    if not yaml_file.exists():
        sys.exit(f"No se encontró {yaml_file}")

    d = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))

    totales = calcular_totales(d)
    deltas = calcular_deltas(d)

    if not d.get("conclusiones"):
        d["conclusiones"] = sugerir_conclusiones(d, deltas, totales)
    if not d.get("oportunidades"):
        d["oportunidades"] = sugerir_oportunidades(d, deltas)

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES)),
        autoescape=select_autoescape(["html"]),
    )
    env.globals.update(
        fmt_num=fmt_num,
        delta_str=delta_str,
        delta_class=delta_class,
        duracion_str=duracion_str,
    )
    tmpl = env.get_template("informe.html.j2")

    logo_uri = file_to_data_uri(ASSETS / "logo_cmp.png")
    capturas = cargar_capturas(mes_dir)

    html = tmpl.render(d=d, deltas=deltas, totales=totales,
                       capturas=capturas, logo_uri=logo_uri)
    out_html = mes_dir / "informe.html"
    out_html.write_text(html, encoding="utf-8")

    out_md = mes_dir / "informe_borrador.md"
    out_md.write_text(render_md(d, deltas, totales), encoding="utf-8")

    actualizar_historial(d, totales)

    print(f"OK · HTML       → {out_html.relative_to(ROOT)}")
    print(f"OK · borrador   → {out_md.relative_to(ROOT)}")
    print(f"OK · histórico  → {HIST_FILE.relative_to(ROOT)}")
    print()
    print("Para previsualizar:")
    print(f"  open {out_html.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
