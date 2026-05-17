# CMP — Métricas mensuales RRSS

Agente que automatiza el armado del informe mensual de RRSS de la
**Cámara de Medios de Pago**, con publicación online y comentarios del
cliente.

## Cómo funciona

1. Cada mes pegás las capturas de LinkedIn / YouTube / Search Console / WhatsApp en `data/YYYY-MM/capturas/`.
2. El agente las lee, completa `datos.yaml` y genera el informe HTML.
3. Lo publicás en un hosting estático (Netlify o GitHub Pages) y le mandás el link al cliente.
4. El cliente revisa, escribe comentarios al lado de cada slide, y los exporta en un email para mandarte.

## Estructura

```
.
├── plantilla/
│   ├── METRICAS DICIEMBRE.psd     (template original, referencia visual)
│   └── assets/logo_cmp.png        (extraído del PSD)
├── templates/
│   ├── informe.html.j2            (plantilla del informe mensual)
│   └── indice.html.j2             (página índice de meses)
├── data/
│   ├── historial.json             (histórico mensual)
│   └── YYYY-MM/
│       ├── capturas/              (screenshots del mes)
│       ├── datos.yaml             (fuente de verdad)
│       ├── informe.html           (preview local)
│       └── informe_borrador.md    (versión texto plano)
├── public/                        ← carpeta lista para subir a hosting
│   ├── index.html                 ← lista de meses
│   ├── 2025-12/index.html
│   └── 2026-01/index.html
├── scripts/
│   ├── generar_informe.py         (genera HTML/MD del mes)
│   ├── publicar.py                (arma carpeta public/)
│   ├── inspect_psd.py             (util: lista capas del PSD)
│   ├── extract_logo.py            (util: extrae logo)
│   └── render_pdf.py              (util)
├── AGENTS.md                      (instrucciones para el asistente IA)
└── README.md
```

## Setup inicial

```bash
python3 -m venv .venv
.venv/bin/pip install PyMuPDF PyYAML Jinja2 psd-tools Pillow
```

## Flujo mensual

```bash
# 1. Pegar capturas en data/2026-02/capturas/

# 2. Pedirle al agente que procese el mes
#    (lee capturas y completa data/2026-02/datos.yaml)

# 3. Generar el informe HTML
.venv/bin/python scripts/generar_informe.py data/2026-02

# 4. Armar la carpeta public/ con todos los meses
.venv/bin/python scripts/publicar.py

# 5. Subir public/ al hosting (ver más abajo)
```

## Cómo publicarlo online (gratis)

### Opción A — Netlify (más fácil, sin cuenta)

1. Entrá a <https://app.netlify.com/drop>
2. Arrastrá la carpeta `public/` a la pantalla.
3. Te asigna una URL tipo `https://nombre-aleatorio.netlify.app`.
4. Mandale el link al cliente.

Para cambiar el nombre, hacete una cuenta gratis en Netlify y editás el subdominio (`https://cmp-metricas.netlify.app` por ejemplo).

### Opción B — GitHub Pages (versionado, más profesional)

1. Crear repo en GitHub: `gh repo create cmp-metricas --private`
2. `git init && git add . && git commit -m "Inicial"`
3. `git push -u origin main`
4. En GitHub → Settings → Pages → Source: `main` branch, carpeta `/public`
5. Te queda en `https://tu-usuario.github.io/cmp-metricas/`

URLs por mes: `…/cmp-metricas/2026-01/`, `…/cmp-metricas/2026-02/`.

### Opción C — Dominio propio

Cualquier hosting estático acepta dominio propio. En Netlify es gratis: subís el dominio en "Domain settings" y te dan los DNS records para configurar.

## Cómo lo usa el cliente

1. Abre el link → ve el informe.
2. Debajo de cada slide hay un **recuadro amarillo** donde escribe sus observaciones.
3. Lo que escribe se guarda automáticamente en su navegador (no se pierde si refresca).
4. Cuando termina, hace click en **"Exportar comentarios"** (arriba a la derecha) → se le abre un email con todos los comentarios listos para mandarte.

## Capturas esperadas en `capturas/`

| Archivo | Fuente |
|---|---|
| `02_contenidos_destacados_anterior.png/jpg` | LinkedIn → Análisis → Contenido (mes anterior) |
| `02_contenidos_destacados_actual.png/jpg`   | LinkedIn → Análisis → Contenido (mes actual) |
| `03_publicacion_top.png/jpg`                | LinkedIn → Análisis de la mejor publicación |
| `04_seguidores_anterior.png/jpg`            | LinkedIn → Análisis → Seguidores (anterior) |
| `04_seguidores_actual.png/jpg`              | LinkedIn → Análisis → Seguidores (actual) |
| `04b_visitantes_anterior.png/jpg`           | LinkedIn → Análisis → Visitantes (anterior) |
| `04b_visitantes_actual.png/jpg`             | LinkedIn → Análisis → Visitantes (actual) |
| `06_web_searchconsole_anterior.png/jpg`     | Google Search Console (mes anterior) |
| `06_web_searchconsole_actual.png/jpg`       | Google Search Console (mes actual) |
| `06_web_contenido.png/jpg`                 | Search Console → «Tu contenido» (ranking URLs / clics) |
| `07_youtube_anterior.png/jpg`               | YouTube Studio (mes anterior) |
| `07_youtube_actual.png/jpg`                 | YouTube Studio (mes actual) |
| `08_luciana_perfil_anterior.png/jpg`        | LinkedIn perfil Luciana (anterior) |
| `08_luciana_perfil_actual.png/jpg`          | LinkedIn perfil Luciana (actual) |
| `09_luciana_interaccion.png/jpg`            | LinkedIn perfil Luciana > Interacción |
| `09_luciana_top.png/jpg`                    | LinkedIn perfil Luciana > Top posts |

Si una captura falta, en el HTML aparece un placeholder gris.
