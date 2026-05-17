# Agente — Métricas mensuales CMP

Instrucciones para el asistente IA cuando el usuario pida procesar un nuevo mes.

## Objetivo
A partir de las capturas que el usuario aporta, generar `informe.html` para
ese mes — listo para previsualizar en el navegador y exportar a PDF.

## Flujo

1. **Identificar el mes**
   - Año-mes en formato `YYYY-MM`. El mes anterior se calcula restando 1.

2. **Verificar / crear estructura**
   ```
   data/YYYY-MM/
     capturas/        ← screenshots aportadas por el usuario
     datos.yaml       ← se completa leyendo las capturas
   ```

3. **Capturas esperadas** (en `capturas/`):
   - `02_contenidos_destacados_anterior.png`
   - `02_contenidos_destacados_actual.png`
   - `02_contenidos_grafico_anterior.png`
   - `02_contenidos_grafico_actual.png`
   - `03_publicacion_top.png`
   - `04_seguidores_anterior.png`
   - `04_seguidores_actual.png`
   - `06_web_resumen.png`
   - `06_web_searchconsole.png`
   - `06_web_consultas.png`
   - `06_web_contenido.png`

4. **Leer capturas y completar `datos.yaml`**
   - Usar `data/2025-12/datos.yaml` como referencia de schema.
   - Para los valores `anterior`: si el mes anterior ya está en
     `data/historial.json`, tomarlos de ahí; si no, leerlos de la captura
     correspondiente.
   - No inventar números. Si una captura está borrosa o falta, pedir
     aclaración.
   - Si la lista de grupos de WhatsApp no cambió, copiarla del mes anterior.

5. **Generar el informe**
   ```bash
   .venv/bin/python scripts/generar_informe.py data/YYYY-MM
   open data/YYYY-MM/informe.html
   ```

6. **Confirmar con el usuario**
   - Mostrar las variaciones más relevantes (impresiones, seguidores, web).
   - Pedir que revise los borradores de **Conclusiones** y **Oportunidades**.
   - Opcional: en `datos.yaml` la clave `ejecutivo` con `puntos` (tres strings)
     y `acciones` (dos strings) se usa en borradores / histórico; el HTML del
     informe ya no incluye una slide separada de resumen ejecutivo.
   - Para Conclusiones / Oportunidades: modificar las listas en `datos.yaml` y
     volver a correr el script.

## Reglas
- El script SÓLO regenera Conclusiones / Oportunidades cuando esas claves
  están vacías en `datos.yaml`. Si el usuario las editó, respetarlas.
- Igual criterio para **`ejecutivo`**: si `puntos` (tres ítems) y dos `acciones`
  vienen completos en `datos.yaml`, no se sobrescriben. Si solo hay `sintesis`
  + acciones, se derivan `puntos` sin pisar las acciones editadas.
- El histórico (`data/historial.json`) se sobrescribe entrada por mes; nunca
  borrar otros meses.
- Las capturas se embeben en el HTML como `data:` URI, así el HTML es
  autocontenido y se puede compartir/abrir en cualquier navegador.
- Para exportar PDF: el usuario lo hace desde el navegador (Cmd+P → Guardar
  como PDF, márgenes ninguno, gráficos de fondo activos).
