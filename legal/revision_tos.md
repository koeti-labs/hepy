# Revisión de ToS / robots.txt — Hepy

| Sitio | robots.txt | Términos de Servicio | Rate limit aplicado | Decisión |
|---|---|---|---|---|
| Superseis (superseis.com.py) | Bloqueado por CloudFront incluso para /robots.txt (403) | Pendiente de revisión manual (no se pudo cargar la página) | N/A hasta poder acceder | **Reintentar desde red no-datacenter antes de implementar el scraper.** Si sigue bloqueado, documentar como no-viable para v1 y excluir de la canasta agregada (afecta solo cobertura, no invalida el resto). |
| Stock (stock.com.py) | HTTP 200, disallow estándar de nopCommerce (checkout/cuenta/pagos), sin disallow sobre /search | Revisar ToS del sitio manualmente antes de la Task 7 | 1 request cada 2-3s, User-Agent identificado con contacto | Permitido |
| Casa Rica (casarica.com.py) | Sin archivo robots.txt (404) | Revisar ToS manualmente antes de la Task 8 | 1 request cada 2-3s | Permitido, sujeto a revisión de ToS |
| Salemma (salemmaonline.com.py) | HTTP 200, disallow de carrito/checkout/cuenta/login; permite `?page=` | Revisar ToS manualmente antes de la Task 9 | 1 request cada 2-3s | Permitido |
| Biggie (biggie.com.py) | Redirect, no confirmado aún | Revisar ToS manualmente antes de la Task 10; sitio es un SPA Next.js, verificar si expone una API JSON interna antes de scrapear HTML | 1 request cada 2-3s | Permitido con reserva técnica (puede requerir usar su API en vez de HTML) |
| Areté (arete.com.py) | Sin archivo robots.txt (404) | Revisar ToS manualmente antes de la Task 11 | 1 request cada 2-3s | Permitido, sujeto a revisión de ToS |
| Grütter (grutteronline.casagrutter.com.py) | Inalcanzable desde el sandbox de planificación (fallo de conexión, no 403/404) | Reintentar conexión y revisar ToS antes de la Task 12 | 1 request cada 2-3s | Pendiente de confirmar accesibilidad |
| Los Jardines (losjardinesonline.com.py) | Sin archivo robots.txt (404) | Revisar ToS manualmente antes de la Task 13 | 1 request cada 2-3s | Permitido, sujeto a revisión de ToS |
| Real (realonline.com.py) | HTTP 200, declara `Content-Signal: search=yes,ai-train=no,use=reference` | Revisar ToS manualmente antes de la Task 14 | 1 request cada 2-3s | **Permitido explícitamente para "reference"** — citar este directive en el paper/README como evidencia de buena fe |

Regla general aplicada a los 9 scrapers: identificarse con un User-Agent propio
(`Hepy/0.1 (+https://github.com/<org>/hepy; contacto: <email>)`), 1 request cada
2-3 segundos por sitio, nunca en paralelo entre sitios distintos en la misma
ventana de tiempo, y respetar cualquier `Disallow` de robots.txt aunque el
scraping general esté permitido.
