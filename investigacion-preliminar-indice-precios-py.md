# Investigación preliminar — Índice de precios en tiempo real (Paraguay)

**Koeti Labs · reconocimiento previo a PRD · v0.1**

> Proyecto 206 del lote (ODS 2.1, 8.1, 12.8): "Índice de precios en tiempo real desde supermercados online". Este documento valida el terreno antes de escribir el PRD — mismo criterio que se usó para LSPy: chequear el vacío real, no asumirlo.

---

## 0. Conclusión adelantada

El espacio **no está vacío**, pero tampoco está ocupado por lo que importaría publicar como paper. Hay tres antecedentes en Paraguay (uno del BCP, uno académico regional, uno comercial) que cubren partes del problema — ninguno hace el índice ponderado, validado contra el IPC oficial, publicado como dataset+código abiertos. Ese es el hueco real. Detalle abajo.

---

## 1. Precedente internacional

El paper fundacional del campo es Cavallo & Rigobon, *"The Billion Prices Project: Using Online Prices for Measurement and Research"* (Journal of Economic Perspectives, 2016), que nació en 2007-2008 como proyecto académico (Harvard/MIT) para medir inflación en Argentina scrapeando supermercados online, ante la manipulación del IPC oficial del INDEC entre 2007-2015. El proyecto escaló a 50 países y terminó comercializándose como **PriceStats** (hoy parte de State Street). El BPP académico ya no está activo; queda como referencia histórica.

Lo más útil como *precedente metodológico replicable* es **InflaciónVerdadera** (Argentina 2007, luego Venezuela 2017): publican metodología, datos y código abiertos. Su procedimiento es directamente adaptable:
1. Índice por categoría = promedio geométrico de los cambios de precio observados cada día (incluidos los que no cambiaron).
2. Índice agregado = promedio aritmético ponderado usando las ponderaciones oficiales por categoría del instituto de estadística nacional (encuesta de presupuesto familiar).

Esto es, en esencia, el patrón que Koeti debería replicar para Paraguay usando las ponderaciones del IPC del BCP.

---

## 2. Estado del arte en Paraguay — el chequeo de novedad

Esto es lo que cambia el enfoque del proyecto. Encontré **cuatro antecedentes directos**, ninguno mencionado en el lote original:

### 2.1 Banco Central del Paraguay — ya hace web scraping (2024)

El BCP publicó un recuadro técnico en su Informe de Política Monetaria: *"Análisis del Diferencial de Precios con Argentina utilizando Web Scraping"*. Puntos clave:

- Scrapearon **10 supermercados paraguayos** y 8 argentinos diariamente entre abril-junio 2024, ~1.101 precios/supermercado, cubriendo ~17% de la canasta del IPC.
- Código en **Python**, adaptado sitio por sitio.
- Explícitamente hicieron **revisión de términos y condiciones de cada sitio antes de scrapear** — esto es una señal de legitimidad institucional fuerte para el enfoque en general.
- El objetivo fue puntual: comparar diferencial de precios PY-Argentina post-devaluación de Milei. **No es un índice corriendo, no es público, no se repitió después de junio 2024, no está pensado como IPC alternativo doméstico.**

Conclusión: el regulador ya validó que scrapear supermercados paraguayos es técnica y legalmente viable — pero lo usó una vez, para otra pregunta, y no lo dejó corriendo ni lo abrió.

### 2.2 IPC-CDE (Ciudad del Este) — académico, pero manual y regional

Convenio entre la Facultad de Ciencias Económicas de la Universidad Nacional del Este (FCE-UNE) y CEPECON (UNILA, Brasil). Publican un IPC mensual desde 2018 usando la misma canasta y ponderaciones del BCP, pero:

- **Recolección manual, presencial**, el tercer miércoles de cada mes, en 6 supermercados.
- Cubre solo Ciudad del Este (167 productos).
- Sin scraping, sin alta frecuencia, sin cobertura nacional.

Es el precedente académico más cercano en espíritu (validación contra el IPC oficial, boletín público), pero metodológicamente es otra cosa — encuesta tradicional a escala reducida, no datos de alta frecuencia.

### 2.3 `scraper-supermercados` (GitHub) — prueba de concepto abandonada

Repo de un desarrollador individual (23 estrellas, 6 forks, sin actividad reciente visible, sin licencia declarada): scraper en Go para Casa Rica, Superseis (`s6`) y Stock. Es solo el scraper — no publica dataset, no calcula índice, no tiene ponderación ni comparación con el IPC. Útil como referencia técnica de que estos sitios son scrapeables con herramientas simples, nada más.

### 2.4 supermerca2.com — el hallazgo que más importa

Existe un producto **en producción, ahora mismo**, que hace exactamente la mitad del trabajo:

> *"Un catálogo de precios de los supermercados de Paraguay — Areté, Biggie, Casa Rica, Grütter, Los Jardines, Real, Stock y Superseis — con la evolución de cada producto."*

Rastrea precios día a día en **8 supermercados** paraguayos y muestra la evolución de cada producto individual. Es, en la práctica, la validación más fuerte de que el scraping a escala nacional es técnicamente viable y sostenible (está corriendo). Pero:

- Es un **comparador de precios al consumidor** (tipo "Trivago de supermercados"), no un índice macroeconómico.
- No hay evidencia de ponderación por categoría, de cálculo de índice agregado tipo IPC, de comparación con el IPC oficial, de dataset descargable, de licencia abierta, ni de metodología publicada.
- No tiene encuadre académico ni de ODS.
- No se sabe quién lo mantiene (sin sección de autoría visible más allá de "Acerca").

**Esto es lo que hay que resolver antes de seguir**: si Koeti construye "un scraper que arma un catálogo de precios", el resultado ya existe y es peor posicionarlo como novedad. Si Koeti construye "un índice ponderado, validado contra el IPC oficial, publicado como dataset abierto + código abierto + paper reproducible, enmarcado en ODS 2.1/8.1/12.8", ese proyecto no existe en ningún lado — ni BCP, ni CDE, ni supermerca2 lo hacen.

---

## 3. El gap real (lo que sostiene el paper)

Cruzando los cuatro antecedentes, lo que nadie hace en Paraguay simultáneamente:

| Elemento | BCP | IPC-CDE | supermerca2 | **Espacio libre** |
|---|---|---|---|---|
| Alta frecuencia (diaria) | Sí, pero acotado a 3 meses | No (mensual) | Sí | — |
| Cobertura nacional | Sí (una vez) | No (solo CDE) | Sí | — |
| Índice agregado ponderado (tipo Jevons + pesos IPC) | No calculado así, es comparación bilateral | Sí, con pesos oficiales | No visible | **Nadie lo sostiene en el tiempo con esta metodología** |
| Validación sistemática contra IPC oficial (correlación, series públicas) | No | Sí, pero manual/regional | No | **Nadie lo hace a escala nacional con datos de alta frecuencia** |
| Dataset abierto descargable | No | No visible | No | **Vacío total** |
| Código abierto | No | No | No | **Vacío total** |
| Metodología publicada y reproducible | Sí (recuadro técnico, no reproducible por terceros) | Sí | No | **Vacío parcial** |
| Encuadre en ODS / ciencia abierta | No | No | No | **Vacío total** |

La contribución publicable no es "raspar supermercados paraguayos" (ya está hecho tres veces, de tres formas distintas). Es: **construir y sostener un índice de precios de alta frecuencia, ponderado con la metodología oficial del BCP, validado empíricamente contra el IPC publicado, y liberado como dataset (CC0/CC-BY) + código (Apache-2.0) + paper con metodología reproducible** — el mismo patrón que InflaciónVerdadera hizo para Argentina/Venezuela, pero que nadie hizo todavía para Paraguay de forma abierta.

Esto también resuelve el ángulo ODS mejor que el enfoque original: 2.1 (seguridad alimentaria — canasta básica en tiempo real), 8.1 (crecimiento económico — nowcasting de inflación como insumo de política económica accesible a cualquiera, no solo al BCP) y 12.8 (acceso a información para decisiones de consumo — igual que plantea el proyecto IPC-CDE explícitamente: que las familias puedan ver qué subió y ajustar su canasta).

---

## 4. Viabilidad técnica de datos

Supermercados paraguayos confirmados con tienda online (catálogo + precio visible sin login, ya scrapeados por al menos un actor existente):

- **Superseis**, **Stock**, **Casa Rica**, **Salemma**, **Biggie**, **Areté**, **Grütter**, **Los Jardines**, **Real** — los ocho de supermerca2.com más Salemma, que tiene tienda online propia (`salemmaonline.com.py`) y no aparece en esa lista, posible expansión de cobertura.
- El BCP usó 10 supermercados paraguayos (no nombrados en el recuadro) — probablemente superset de los anteriores.
- Fortis (mayorista) también tiene presencia relevante pero es otro segmento (B2B/cash & carry), no directamente comparable a la canasta IPC del hogar urbano.

Con 8-10 cadenas ya confirmadas como scrapeables, la cobertura de supermercados no es el cuello de botella. El cuello de botella real, según lo que reporta el propio BCP, es **combustibles** (los emblemas no publican precio diario online) — habría que excluir ese rubro o buscar fuente alternativa (ANDE/PETROPAR no scrapeable de la misma forma).

---

## 5. Marco legal

Paraguay promulgó su primera ley integral de protección de datos personales el **27 de noviembre de 2025** (Ley N° 7.593/2025). Cubre datos de **personas físicas identificadas o identificables** — precios de productos, SKUs y catálogos de supermercado no caen bajo esta ley, así que el riesgo regulatorio específico de datos personales es bajo para este proyecto (distinto sería si se scrapeara, por ejemplo, reseñas de usuarios con nombre).

Lo que sí aplica, y es lo que el propio BCP marcó como paso obligatorio en su metodología, es la **revisión de términos y condiciones de cada sitio** antes de scrapear (algunos ToS prohíben scraping explícitamente, independientemente de la ley de datos personales) y buenas prácticas técnicas: respetar `robots.txt`, rate-limiting razonable, no saturar los servidores, no scrapear datos que no sean de producto/precio. Esto habría que hacerlo sitio por sitio antes de construir el pipeline — es tarea de reconocimiento adicional, no bloqueante.

---

## 6. Riesgos y puntos débiles (actualizados)

Del lote original, ajustado con lo encontrado:

- **Cobertura online vs. góndola**: sigue siendo la limitación estructural señalada en el lote — precios online no siempre reflejan el precio físico, y la cobertura de productos es parcial (el propio BCP excluyó rubros enteros como combustibles).
- **Riesgo de redundancia percibida**: si el paper no deja clarísima la diferencia metodológica con supermerca2.com (comparador) y con el recuadro del BCP (análisis puntual), un revisor puede leerlo como "ya existe". Hay que citarlos y diferenciarse explícitamente desde la introducción.
- **Mantenimiento continuo**: a diferencia de un dataset estático, un índice de alta frecuencia exige que el scraper siga funcionando indefinidamente — cambios de estructura HTML, anti-bot, sitios caídos. Es el mismo patrón de "corre solo" que señalaba el lote, pero con más superficie de fallo que un scraper de un solo sitio.
- **Validación**: para que el paper tenga peso, la comparación contra el IPC oficial del BCP necesita series suficientemente largas — esto empuja a que el proyecto tenga que correr varios meses antes de poder publicar resultados robustos (no es algo que se resuelva con una corrida única).

---

## 7. Recomendación

El proyecto tiene mérito, pero **no como estaba planteado en el lote** ("construir un scraper que arma un índice de canasta básica"). El encuadre que sí sostiene un paper de Koeti:

1. Nombre guaraní de una palabra (siguiendo la convención de Ayvu Rapytá) para el índice.
2. Alcance: índice ponderado (Jevons por categoría + pesos oficiales del IPC-BCP), corriendo diariamente sobre 8-10 supermercados con tienda online.
3. Contribución central del paper: la **validación empírica contra el IPC oficial** (correlación, lag, capacidad de nowcasting) — esto es lo que ningún antecedente paraguayo hace hoy.
4. Publicación: dataset bajo CC0/CC-BY, código bajo Apache-2.0, metodología documentada y reproducible por terceros — igual que Ayvu Rapytá.
5. Encuadre explícito en ODS 2.1, 8.1 y 12.8, citando el precedente de IPC-CDE como el antecedente paraguayo más cercano en misión pública (acceso a información para decisiones de consumo), no como competencia.
6. Empezar hoy con el scraper corriendo es correcto — el valor del dataset crece con el tiempo que lleve funcionando, y necesitás una serie larga para la validación contra el IPC.

Si esto te cierra, el siguiente paso natural es armar el PRD con el protocolo de siempre (preguntas aclaratorias primero). Si preferís, puedo arrancar por ahí.

---

## 8. Componente de IA/ML — la pieza que sube el peso del paper

Pregunta que motiva esta sección: ¿dónde entra un modelo (liviano, no frontier) que *prediga* algo, y por qué eso importa más que "solo" publicar el índice.

### 8.1 La pieza central: nowcasting del IPC oficial

Esto es, en rigor, lo que le dio prestigio al Billion Prices Project — no el índice en sí, sino demostrar que anticipa el dato oficial antes de que se publique. Hay precedente reciente y específico para el caso de Koeti:

- **Bolivar (2025)**, *"High-frequency inflation forecasting: A two-step machine learning methodology"* (Latin American Journal of Central Banking) — exactamente el escenario de Paraguay: un país en desarrollo donde el IPC oficial solo se publica mensualmente y con rezago. Metodología: entrena modelos de ML sobre datos mensuales alineados, y los usa para generar pronósticos semanales/diarios. Reporta que XGBoost superó a los benchmarks econométricos tradicionales.
- **Beck et al. (2023/2024, Bundesbank)** — usan datos de scanner semanales de Alemania (180 índices de precios) para nowcastear la inflación mensual oficial con un modelo mixed-frequency (LASSO sparse-group).
- **Federal Reserve Bank of Cleveland** — nowcasting diario de CPI/PCE en EE.UU. con métodos de mixed-frequency (MIDAS, MF-DFM) y ML; documentan que ML es competitivo pero no automáticamente superior a métodos econométricos clásicos — vale la pena decirlo así de honesto en el paper también.

**Propuesta concreta para Koeti:**

- **Variable objetivo**: variación intermensual del IPC oficial (BCP, de acceso público).
- **Features**: variación diaria/semanal del índice scrapeado por categoría, rezagos de esas variaciones, tipo de cambio (BCP publica series diarias), y opcionalmente series públicas gratuitas adicionales (comparables a lo que hace Bolivar con precios mayoristas y tipo de cambio).
- **Modelos, en orden de complejidad creciente** (todos livianos, corren en la laptop o en la instancia ARM sin GPU):
  1. Regresión Ridge/Lasso/ElasticNet — punto de partida interpretable, bajo riesgo de sobreajuste con series cortas.
  2. Random Forest / Gradient Boosting (XGBoost o LightGBM) — es lo que domina en la literatura reciente de nowcasting de inflación en economías en desarrollo.
  3. ARIMA/SARIMAX como benchmark econométrico clásico, obligatorio para poder decir "el modelo de ML mejora sobre X%".
- **Validación**: backtesting walk-forward (expanding window), comparado contra un benchmark naive (última variación observada) y contra el ARIMA. Métricas: MAE, RMSE.
- **Por qué sube el peso del paper**: pasa de "construimos un índice descriptivo" a "construimos un índice Y demostramos que anticipa el IPC oficial con X días de anticipación y un error Y% menor que el benchmark ingenuo" — es un resultado cuantitativo, evaluable objetivamente por un revisor, y con aplicación directa de política económica (ODS 8.1 se fortalece mucho con esto).

**Limitación honesta a anotar desde ya**: con pocos meses de historia scrapeada al momento de escribir el paper, el poder predictivo del modelo va a ser limitado — el N de entrenamiento son meses, no días. Conviene diseñar el pipeline de nowcasting desde el arranque del scraper (para no perder historia), pero tratar los resultados de esta parte como preliminares si el paper se escribe antes de acumular ~12 meses de datos, o directamente plantear el paper en dos entregas (dataset+índice primero, nowcasting cuando haya historia suficiente).

### 8.2 Capa de control de calidad: detección de outliers (no opcional, es higiene de datos — pero es "IA" que suma metodológicamente)

Los institutos de estadística nacionales (ONS del Reino Unido y otros, vía el proyecto ESCoE) tienen una línea de trabajo específica para esto: antes de incorporar datos scrapeados o de scanner a un IPC oficial, filtran outliers con métodos estandarizados — algoritmo de Tukey, método de cuartiles, método de Hidiroglou-Berthelot, "resistant fences". Es exactamente el tipo de control que un revisor de journal va a preguntar si no está: sin esto, el índice puede estar contaminado por errores de scraping, ofertas relámpago, o cambios de SKU mal capturados (el propio Cavallo señala este problema en *"Scraped Data and Sticky Prices"*).

Aplicable con estadística simple y liviana (no hace falta ML pesado): z-score robusto, MAD (median absolute deviation) sobre los cambios de precio en log, o el método de Hidiroglou-Berthelot ya estandarizado en la literatura de precios. Si se quiere ir un poco más allá, Isolation Forest o DBSCAN son las opciones no supervisadas más citadas en detección de anomalías de precios de e-commerce — pero no son necesarias para tener una capa de control creíble.

### 8.3 Clasificación automática de producto → categoría IPC (opcional, coherente con lo que ya saben hacer)

En vez de mapear cada producto scrapeado a su categoría del IPC a mano (que es lo que hace IPC-CDE manualmente), se puede entrenar un clasificador de texto liviano (TF-IDF + regresión logística, o embeddings chicos) sobre una muestra taxonomizada a mano al principio, y usarlo para escalar cobertura sin escalar el trabajo manual. Es el mismo patrón "small but impeccable" que ya usan en Ayvu, aplicado a otro dominio (texto de producto en español, no jopará) — reutiliza expertise, no dataset.

### 8.4 Extensión a futuro, no para la v1: ajuste hedónico con IA

Limitación reconocida en toda la literatura del campo (Cavallo & Rigobon la mencionan explícitamente): el scraping no captura cambios de calidad o tamaño de producto (shrinkflation, por ejemplo). Hay trabajo reciente sobre índices ajustados por calidad usando IA para resolver esto. Vale mencionarlo como línea de trabajo futuro en el paper, sin comprometerse a implementarlo en la primera versión — sube el peso del "future work" sin inflar el scope actual.

### 8.5 Secuencia recomendada

1. Scraper corriendo + índice ponderado + validación de correlación contra el IPC (lo ya recomendado en la sección 7).
2. Capa de outlier detection integrada al pipeline desde el día uno — no es una fase aparte, es parte del pipeline base.
3. Una vez acumulados ~6-12 meses de historia: entrenar y evaluar los modelos de nowcasting, empezando por Ridge/Lasso y comparando contra XGBoost y ARIMA.
4. Opcional / futuro: clasificación automática de productos, ajuste hedónico.

Todo esto corre sin GPU — regresiones, gradient boosting y clasificadores de texto livianos son cómodos en la laptop o en "Santiago" (ARM). Coincide con el principio de eficiencia del Manifiesto: no hace falta un modelo grande para que el resultado importe.

---

## Fuentes consultadas

- Cavallo, A. & Rigobon, R. (2016). *The Billion Prices Project: Using Online Prices for Measurement and Research.* Journal of Economic Perspectives / NBER WP 22111.
- thebillionpricesproject.com — estado actual del proyecto (inactivo, redirige a PriceStats/State Street).
- inflacionverdadera.com — metodología abierta Argentina/Venezuela.
- BCP, *Informe de Política Monetaria*, Recuadro I: "Análisis del Diferencial de Precios con Argentina utilizando Web Scraping" (2024).
- FCE-UNE / CEPECON-UNILA, boletín IPC-CDE (Ciudad del Este), desde 2018.
- github.com/matiasinsaurralde/scraper-supermercados
- supermerca2.com (catálogo, sección "Acerca")
- Ley N° 7.593/2025 "De Protección de Datos Personales" (Paraguay, promulgada 27/11/2025).
- Textos de metas ODS 2.1 y 12.8 (Agenda 2030, Naciones Unidas).
- Bolivar, O. (2025). *High-frequency inflation forecasting: A two-step machine learning methodology.* Latin American Journal of Central Banking.
- Beck, G.W., Carstensen, K., Menz, J.-O., Schnorrenberger, R., Wieland, E. *Nowcasting consumer price inflation using high-frequency scanner data: Evidence from Germany.* Deutsche Bundesbank Discussion Paper.
- Federal Reserve Bank of Cleveland, Working Paper 24-06, *Nowcasting Inflation.*
- ESCoE / Office for National Statistics (UK), *Outlier detection methodologies for alternative data sources.*
- Cavallo, A. (2015). *Scraped Data and Sticky Prices.* NBER Working Paper 21490.
