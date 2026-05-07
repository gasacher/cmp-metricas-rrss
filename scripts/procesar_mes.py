#!/usr/bin/env python3
"""
Procesa los datos de un mes (datos.yaml) y produce:
  - informe_borrador.md  : datos listos para copiar al PSD + borrador de
                           Conclusiones y Oportunidades para revisar.
  - data/historial.json  : se actualiza con los datos del mes para que la
                           próxima corrida pueda hacer comparativas.

Uso:
  python scripts/procesar_mes.py data/2025-12
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from datetime import datetime

import yaml


ROOT = Path(__file__).resolve().parent.parent
HIST_FILE = ROOT / "data" / "historial.json"


# =============================================================================
# Helpers
# =============================================================================
def variacion_pct(actual: float | None, anterior: float | None) -> float | None:
    """% de cambio respecto al mes anterior. None si no hay base."""
    if actual is None or anterior is None:
        return None
    if anterior == 0:
        return None if actual == 0 else float("inf")
    return round((actual - anterior) / anterior * 100, 1)


def fmt_var(v: float | None) -> str:
    """Formatea un % de variación con flecha."""
    if v is None:
        return "—"
    if v == float("inf"):
        return "▲ nuevo"
    flecha = "▲" if v >= 0 else "▼"
    return f"{flecha} {abs(v):.1f}%"


def fmt_num(n) -> str:
    if n is None:
        return "—"
    if isinstance(n, float):
        return f"{n:.1f}"
    return f"{n:,}".replace(",", ".")


# =============================================================================
# Generación del borrador
# =============================================================================
def render_md(d: dict) -> str:
    out: list[str] = []
    push = out.append

    push(f"# Informe — {d['mes_label']}")
    push("")
    push(f"_Generado el {datetime.now():%Y-%m-%d %H:%M}_")
    push("")
    push("Este documento contiene **los valores listos para copiar al PSD** y un "
          "**borrador** de Conclusiones y Oportunidades para que revises antes "
          "de exportar el informe final.")
    push("")

    # ------------------------------------------------------------- Slide 2
    push("## Slide 2 — Contenidos: datos destacados")
    push("")
    c = d["contenidos"]
    push(f"| Métrica | {d['mes_anterior_label']} ({c['rango_anterior']}) | "
         f"{d['mes_label']} ({c['rango_actual']}) | Variación |")
    push("|---|---:|---:|---:|")
    for key, label in [
        ("impresiones", "Impresiones"),
        ("reacciones", "Reacciones"),
        ("comentarios", "Comentarios"),
        ("compartidos", "Veces compartido"),
    ]:
        ant = c["anterior"][key]
        act = c["actual"][key]
        push(f"| {label} | {fmt_num(ant)} | {fmt_num(act)} | "
             f"{fmt_var(variacion_pct(act, ant))} |")
    push("")

    # ------------------------------------------------------------- Slide 3
    p = d["publicacion_top"]
    push("## Slide 3 — Publicación con mejor rendimiento")
    push("")
    push(f"**Descripción:** {p['descripcion'].strip()}")
    push("")
    push("**Descubrimiento orgánico**")
    push(f"- Impresiones: **{fmt_num(p['descubrimiento']['impresiones'])}**")
    push(f"- Miembros alcanzados: **{fmt_num(p['descubrimiento']['miembros_alcanzados'])}**")
    push("")
    push("**Actividad orgánica de la página**")
    push(f"- Visualizaciones de la página: **{fmt_num(p['actividad']['visualizaciones_pagina'])}**")
    push(f"- Seguidores obtenidos: **{fmt_num(p['actividad']['seguidores_obtenidos'])}**")
    push("")
    push("**Interacción orgánica**")
    i = p["interaccion"]
    push(f"- Interacciones: **{fmt_num(i['interacciones'])}**")
    push(f"- Tasa de interacción: **{i['tasa_interaccion_pct']}%**")
    push(f"- Clics: **{fmt_num(i['clics'])}**")
    push(f"- Porcentaje de clics: **{i['porcentaje_clics_pct']}%**")
    push(f"- Reacciones: **{fmt_num(i['reacciones'])}**")
    push(f"- Comentarios: **{fmt_num(i['comentarios'])}**")
    push(f"- Veces compartido: **{fmt_num(i['veces_compartido'])}**")
    push("")

    # ------------------------------------------------------------- Slide 4
    s = d["seguidores"]
    push("## Slide 4 — Seguidores")
    push("")
    push(f"| Métrica | {d['mes_anterior_label']} | {d['mes_label']} | Variación |")
    push("|---|---:|---:|---:|")
    push(f"| Total seguidores | {fmt_num(s['anterior']['total'])} | "
         f"{fmt_num(s['actual']['total'])} | "
         f"{fmt_var(variacion_pct(s['actual']['total'], s['anterior']['total']))} |")
    push(f"| Nuevos seguidores | {fmt_num(s['anterior']['nuevos'])} | "
         f"{fmt_num(s['actual']['nuevos'])} | "
         f"{fmt_var(variacion_pct(s['actual']['nuevos'], s['anterior']['nuevos']))} |")
    push("")

    # ------------------------------------------------------------- Slide 5
    w = d["whatsapp"]
    total_miembros = sum(g["miembros"] for g in w["grupos"])
    push("## Slide 5 — WhatsApp")
    push("")
    push(f"**{len(w['grupos'])} GRUPOS ACTIVOS** — {total_miembros} miembros en total")
    push("")
    for g in w["grupos"]:
        push(f"- **{g['nombre']}** — Grupo · {g['miembros']} miembros")
    push("")

    # ------------------------------------------------------------- Slide 6
    web = d["web"]
    push("## Slide 6 — Web")
    push("")
    push("**Resumen del mes**")
    r = web["resumen_semanal"]
    push(f"- Clics totales: **{fmt_num(r['clics_totales'])}**")
    push(f"- Impresiones totales: **{fmt_num(r['impresiones_totales'])}**")
    push(f"- CTR medio: **{r['ctr_pct']}%**")
    push(f"- Posición media: **{r['posicion_media']}**")
    push("")
    sc = web["search_console"]
    push("**Search Console (vs mes anterior)**")
    push(f"- Clics: **{fmt_num(sc['clics'])}** (▲ {sc['clics_var_pct']}%)")
    push(f"- Impresiones: **{fmt_num(sc['impresiones'])}** (▲ {sc['impresiones_var_pct']}%)")
    push("")
    push("**Tu contenido — top**")
    for c2 in web["contenido_top"]:
        flecha = ""
        if c2.get("var_pct") is not None:
            flecha = f" ({'▲' if c2['var_pct'] >= 0 else '▼'} {abs(c2['var_pct'])}%)"
        elif c2.get("nota"):
            flecha = f" ({c2['nota']})"
        push(f"- {c2['titulo']} — clics: **{c2['clics']}**{flecha}")
    push("")

    # ------------------------------------------------------------- Conclusiones
    push("## Slide 7 — Conclusiones (borrador)")
    push("")
    for linea in d["conclusiones"]:
        push(f"- {linea}")
    push("")

    push("## Slide 8 — Oportunidades (borrador)")
    push("")
    for linea in d["oportunidades"]:
        push(f"- {linea}")
    push("")

    return "\n".join(out)


# =============================================================================
# Borradores asistidos de Conclusiones / Oportunidades
# =============================================================================
def sugerir_conclusiones(d: dict) -> list[str]:
    sugs: list[str] = []
    c = d["contenidos"]
    var_imp = variacion_pct(c["actual"]["impresiones"], c["anterior"]["impresiones"])
    var_rea = variacion_pct(c["actual"]["reacciones"], c["anterior"]["reacciones"])

    if var_imp is not None and var_imp > 50:
        sugs.append(
            f"Durante {d['mes_label'].lower()} se registró un crecimiento "
            f"significativo en impresiones (+{var_imp:.0f}%) y reacciones "
            f"({fmt_var(var_rea)}), lo que indica una mejora en la visibilidad "
            f"general de la marca en redes sociales."
        )
    elif var_imp is not None and var_imp < -20:
        sugs.append(
            f"Durante {d['mes_label'].lower()} se observó una caída en "
            f"impresiones ({var_imp:.0f}%), lo que sugiere revisar la frecuencia "
            f"y el tipo de contenido publicado."
        )

    p = d["publicacion_top"]
    if p["interaccion"]["tasa_interaccion_pct"] >= 30:
        sugs.append(
            f"El contenido con mejor rendimiento alcanzó una tasa de interacción "
            f"del {p['interaccion']['tasa_interaccion_pct']}%, demostrando que "
            f"este tipo de publicaciones (acciones institucionales y encuentros "
            f"presenciales) generan mayor interés, interacción y captación de "
            f"nuevos seguidores."
        )

    s = d["seguidores"]
    var_nuevos = variacion_pct(s["actual"]["nuevos"], s["anterior"]["nuevos"])
    if var_nuevos is not None and var_nuevos > 0:
        sugs.append(
            f"La adquisición de nuevos seguidores creció {fmt_var(var_nuevos)} "
            f"respecto a {d['mes_anterior_label'].lower()}, sosteniendo la "
            f"tendencia positiva del período."
        )
    elif var_nuevos is not None and var_nuevos < 0:
        sugs.append(
            f"Si bien el alcance creció, los nuevos seguidores cayeron "
            f"{fmt_var(var_nuevos)} respecto al mes anterior, lo que refuerza la "
            f"necesidad de sostener la frecuencia y diversidad de contenidos."
        )

    sc = d["web"]["search_console"]
    if sc["clics_var_pct"] > 0 and sc["impresiones_var_pct"] > 0:
        sugs.append(
            f"En el sitio web se detecta un incremento en clics "
            f"(+{sc['clics_var_pct']}%) e impresiones (+{sc['impresiones_var_pct']}%), "
            f"lo que evidencia una correcta articulación entre redes sociales y "
            f"tráfico hacia la web."
        )

    return sugs


def sugerir_oportunidades(d: dict) -> list[str]:
    sugs: list[str] = []
    c = d["contenidos"]
    if c["actual"]["comentarios"] <= 5:
        sugs.append(
            "Incorporar llamados a la acción más claros en redes (visitar la web, "
            "sumarse a los grupos, conocer actividades) para capitalizar el "
            "aumento de impresiones y estimular comentarios."
        )

    sugs.append(
        "Replicar y planificar más contenidos del tipo eventos, reuniones, "
        "acciones internas y logros institucionales, que demostraron alto nivel "
        "de engagement."
    )

    sugs.append(
        "Incrementar la frecuencia de publicaciones, especialmente en semanas "
        "con menor actividad, para evitar caídas en el alcance y en la "
        "adquisición de seguidores."
    )

    sugs.append(
        "Explorar formatos complementarios (videos cortos, placas informativas, "
        "carruseles explicativos) para diversificar el contenido y mejorar la "
        "interacción."
    )
    return sugs


# =============================================================================
# Histórico
# =============================================================================
def actualizar_historial(d: dict) -> None:
    HIST_FILE.parent.mkdir(parents=True, exist_ok=True)
    hist = {}
    if HIST_FILE.exists():
        hist = json.loads(HIST_FILE.read_text(encoding="utf-8"))

    hist[d["mes"]] = {
        "label": d["mes_label"],
        "contenidos": d["contenidos"]["actual"],
        "seguidores": d["seguidores"]["actual"],
        "web_clics": d["web"]["resumen_semanal"]["clics_totales"],
        "web_impresiones": d["web"]["resumen_semanal"]["impresiones_totales"],
        "whatsapp_grupos": len(d["whatsapp"]["grupos"]),
        "whatsapp_miembros": sum(g["miembros"] for g in d["whatsapp"]["grupos"]),
    }

    HIST_FILE.write_text(
        json.dumps(hist, indent=2, ensure_ascii=False), encoding="utf-8"
    )


# =============================================================================
# Main
# =============================================================================
def main() -> None:
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    mes_dir = Path(sys.argv[1]).resolve()
    yaml_file = mes_dir / "datos.yaml"
    if not yaml_file.exists():
        sys.exit(f"No se encontró {yaml_file}")

    d = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))

    if not d.get("conclusiones"):
        d["conclusiones"] = sugerir_conclusiones(d)
    if not d.get("oportunidades"):
        d["oportunidades"] = sugerir_oportunidades(d)

    md = render_md(d)
    out_md = mes_dir / "informe_borrador.md"
    out_md.write_text(md, encoding="utf-8")

    actualizar_historial(d)

    print(f"OK · borrador → {out_md.relative_to(ROOT)}")
    print(f"OK · histórico actualizado → {HIST_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
