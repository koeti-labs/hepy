## Hepy

Índice de precios de alta frecuencia para Paraguay, construido con scraping diario
de 9 supermercados online (Superseis, Stock, Casa Rica, Salemma, Biggie, Areté,
Grütter, Los Jardines, Real), ponderado con la metodología del IPC del Banco
Central del Paraguay (BCP, base diciembre 2017, EPF 2015-2016), y validado
empíricamente contra la serie oficial.

- Código: Apache-2.0 (`LICENSE-CODE`)
- Dataset: CC BY 4.0 (`LICENSE-DATA`) — citar como "Hepy — Koeti Labs (<año>), <URL del dataset>"
- Dataset descargable: [Releases → dataset](../../releases/tag/dataset) (`prices.db`, `prices.csv`, `prices.json`, `index.json`)
- Dashboard: sitio estático (`dashboard/`), desplegado en Cloudflare Pages — servir localmente con `python -m http.server` desde `dashboard/`

### Dashboard

Static dashboard (`dashboard/`) deployable to Cloudflare Pages: no build step, no server. The page fetches `index.json` directly from a GitHub Release client-side and renders charts using Chart.js (CDN).

**Cloudflare Pages config:**
- Build command: (none)
- Output directory: `dashboard`

### Desarrollo

    pip install -r requirements.txt
    pytest
    python run_daily.py       # corre el scraper una vez, localmente
    cd dashboard && python -m http.server

### Estado del proyecto

Fase 1 (scraper + índice ponderado + validación contra el IPC-BCP + detección de
outliers) implementada. Fase 2 (nowcasting con ML) tiene el andamiaje de features
listo (`forecasting/`) pero los modelos no se entrenan todavía — requiere 6-12
meses de historia acumulada en el dataset.

Ver `legal/revision_tos.md` para el detalle de la revisión legal por sitio.
