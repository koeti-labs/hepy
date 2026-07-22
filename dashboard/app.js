const DATASET_RELEASE_BASE = "https://github.com/gsmkev/hepy/releases/download/dataset";
const RAW_MAIN_BASE = "https://raw.githubusercontent.com/gsmkev/hepy/main";
// GitHub Release assets don't send CORS headers (only <a href> downloads
// work there, not fetch()). index.json is small enough to also commit to
// the repo (via the CI workflow, dashboard/data/index.json) and read from
// here instead, which does send CORS headers.
const INDEX_JSON_URL = `${RAW_MAIN_BASE}/dashboard/data/index.json`;
const IPC_OFICIAL_URL = `${RAW_MAIN_BASE}/ipc_oficial.json`;

const PALETTE = {
  ink: "#f1ede4",
  muted: "#9fb3a6",
  panelLine: "#33473c",
  hepy: "#6fcf97",
  terracotta: "#e4572e",
  accent: "#f2c14e",
};

const SERIES_COLORS = ["#f2c14e", "#6fcf97", "#e4572e", "#7ec8e3", "#c792ea", "#f28c6a", "#8bd3c7", "#e07a5f"];

async function loadIndexData() {
  const res = await fetch(INDEX_JSON_URL);
  if (!res.ok) throw new Error(`index.json fetch failed: ${res.status}`);
  return res.json();
}

async function loadIpcOficial() {
  try {
    const res = await fetch(IPC_OFICIAL_URL);
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

function chartDefaults() {
  Chart.defaults.color = PALETTE.muted;
  Chart.defaults.borderColor = PALETTE.panelLine;
  Chart.defaults.font.family = "ui-monospace, SFMono-Regular, Consolas, Menlo, monospace";
  Chart.defaults.font.size = 11;
}

function lineChart(canvas, datasets) {
  return new Chart(canvas, {
    type: "line",
    data: { datasets },
    options: {
      parsing: { xAxisKey: "x", yAxisKey: "y" },
      scales: {
        x: { type: "category" },
        y: { beginAtZero: false },
      },
      plugins: { legend: { display: datasets.length > 1 } },
      elements: { point: { radius: 2 }, line: { tension: 0.15 } },
    },
  });
}

function toPoints(series) {
  return series.map(r => ({ x: r.date, y: r.value }));
}

function renderBoard(aggregate) {
  const numberEl = document.getElementById("board-number");
  const deltaEl = document.getElementById("board-delta");
  const dateEl = document.getElementById("board-date");

  if (aggregate.length === 0) {
    numberEl.textContent = "—";
    document.getElementById("board").querySelector(".board-eyebrow").textContent = "Índice agregado";
    dateEl.textContent = "Todavía no hay datos publicados. La primera corrida diaria todavía no se completó — volvé mañana temprano.";
    return;
  }

  const sorted = [...aggregate].sort((a, b) => a.date.localeCompare(b.date));
  const latest = sorted[sorted.length - 1];
  const prev = sorted.length > 1 ? sorted[sorted.length - 2] : null;

  numberEl.textContent = latest.value.toFixed(1);
  dateEl.textContent = `Al ${latest.date}${prev ? "" : " (primer día registrado — base 100)"}`;

  if (prev) {
    const change = latest.value - prev.value;
    const pct = (change / prev.value) * 100;
    deltaEl.textContent = `${change >= 0 ? "▲" : "▼"} ${Math.abs(pct).toFixed(2)}% vs. ayer`;
    deltaEl.classList.add(change >= 0 ? "up" : "down");
  } else {
    deltaEl.remove();
  }
}

function renderAggregateChart(aggregate) {
  const canvas = document.getElementById("aggregate-chart");
  if (aggregate.length === 0) {
    canvas.replaceWith(Object.assign(document.createElement("p"), {
      className: "board-empty",
      textContent: "Sin datos todavía.",
    }));
    return;
  }
  lineChart(canvas, [{
    label: "Índice agregado",
    data: toPoints(aggregate),
    borderColor: PALETTE.hepy,
    backgroundColor: PALETTE.hepy + "33",
    fill: true,
  }]);
}

function renderPuestos(indexDaily, supermarkets) {
  const container = document.getElementById("puestos");
  if (supermarkets.length === 0) {
    container.innerHTML = '<p class="board-empty">Sin supermercados con datos todavía.</p>';
    return;
  }
  for (const sm of supermarkets) {
    const series = indexDaily.filter(r => r.supermarket === sm).sort((a, b) => a.date.localeCompare(b.date));
    const latest = series[series.length - 1];

    const card = document.createElement("div");
    card.className = "puesto";

    const name = document.createElement("p");
    name.className = "puesto-name";
    name.textContent = sm.replace(/_/g, " ");

    const value = document.createElement("p");
    value.className = "puesto-value";
    value.textContent = latest.value.toFixed(1);

    card.append(name, value);
    container.appendChild(card);
  }
}

function renderCompareChart(indexDaily, supermarkets) {
  const controls = document.getElementById("compare-controls");
  const canvas = document.getElementById("compare-chart");

  if (supermarkets.length === 0) {
    canvas.replaceWith(Object.assign(document.createElement("p"), {
      className: "board-empty",
      textContent: "Sin supermercados con datos todavía.",
    }));
    return;
  }

  const initiallyChecked = new Set(supermarkets.slice(0, 3));
  for (const sm of supermarkets) {
    const label = document.createElement("label");

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.id = `cmp-${sm}`;
    checkbox.checked = initiallyChecked.has(sm);

    label.append(checkbox, document.createTextNode(` ${sm.replace(/_/g, " ")}`));
    controls.appendChild(label);
  }

  const buildDatasets = () =>
    supermarkets
      .filter(sm => document.getElementById(`cmp-${sm}`).checked)
      .map((sm, i) => ({
        label: sm.replace(/_/g, " "),
        data: toPoints(indexDaily.filter(r => r.supermarket === sm).sort((a, b) => a.date.localeCompare(b.date))),
        borderColor: SERIES_COLORS[i % SERIES_COLORS.length],
        backgroundColor: "transparent",
      }));

  const chart = lineChart(canvas, buildDatasets());
  controls.addEventListener("change", () => {
    chart.data.datasets = buildDatasets();
    chart.update();
  });
}

async function renderIpcPanel(aggregate) {
  const statusEl = document.getElementById("ipc-status");
  const sourceEl = document.getElementById("ipc-source");
  const ipcData = await loadIpcOficial();

  if (!ipcData || !ipcData.index_general) {
    statusEl.textContent = "No se pudo cargar la serie oficial del IPC-BCP en este momento.";
    return;
  }

  const ipcSeries = ipcData.index_general;
  const ipcDates = Object.keys(ipcSeries).sort();
  const hepyDates = new Set(aggregate.map(r => r.date));
  const overlap = ipcDates.filter(d => hepyDates.has(d));

  sourceEl.textContent = `Fuente: ${ipcData._source || "BCP"} — serie oficial: ${ipcDates[0]} a ${ipcDates[ipcDates.length - 1]}.`;

  if (overlap.length < 2) {
    const firstHepy = aggregate.length ? [...aggregate].sort((a, b) => a.date.localeCompare(b.date))[0].date : null;
    statusEl.textContent = firstHepy
      ? `Todavía no hay suficiente historia de Hepy para correlacionar con el IPC-BCP (Hepy arrancó el ${firstHepy}; la serie oficial cubre ${ipcDates[0]}–${ipcDates[ipcDates.length - 1]}). Necesitamos varias semanas de datos acumulados.`
      : "Todavía no hay datos de Hepy para comparar.";
    return;
  }

  const xs = overlap.map(d => hepyValueFor(aggregate, d));
  const ys = overlap.map(d => ipcSeries[d]);
  const r = pearson(xs, ys);
  statusEl.textContent = r === null
    ? "No se pudo calcular una correlación con los datos disponibles."
    : `Correlación (sin rezago) sobre ${overlap.length} fechas en común: r = ${r.toFixed(3)}.`;
}

function hepyValueFor(aggregate, date) {
  return aggregate.find(r => r.date === date).value;
}

function pearson(xs, ys) {
  const n = xs.length;
  if (n < 2) return null;
  const meanX = xs.reduce((a, b) => a + b, 0) / n;
  const meanY = ys.reduce((a, b) => a + b, 0) / n;
  const num = xs.reduce((sum, x, i) => sum + (x - meanX) * (ys[i] - meanY), 0);
  const denX = Math.sqrt(xs.reduce((sum, x) => sum + (x - meanX) ** 2, 0));
  const denY = Math.sqrt(ys.reduce((sum, y) => sum + (y - meanY) ** 2, 0));
  if (denX === 0 || denY === 0) return null;
  return num / (denX * denY);
}

function renderDownloads() {
  const downloads = document.getElementById("downloads");
  for (const [fname, label] of [["prices.db", "SQLite"], ["prices.csv", "CSV"], ["prices.json", "JSON (precios)"], ["index.json", "JSON (índice)"]]) {
    const li = document.createElement("li");
    const a = document.createElement("a");
    a.href = `${DATASET_RELEASE_BASE}/${fname}`;
    a.textContent = label;
    li.appendChild(a);
    downloads.appendChild(li);
  }
  document.getElementById("cc-year").textContent = new Date().getFullYear();
}

function initScrollReveal() {
  const sections = document.querySelectorAll(".reveal");
  if (!("IntersectionObserver" in window)) {
    sections.forEach(el => el.classList.add("is-visible"));
    return;
  }
  const observer = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      }
    }
  }, { threshold: 0.15 });
  sections.forEach(el => observer.observe(el));
}

async function main() {
  initScrollReveal();
  chartDefaults();
  const data = await loadIndexData();
  const indexDaily = data.index_daily || [];
  const aggregate = indexDaily.filter(r => r.supermarket === "AGREGADO");
  const supermarkets = [...new Set(indexDaily.map(r => r.supermarket).filter(s => s !== "AGREGADO"))].sort();

  renderBoard(aggregate);
  renderAggregateChart(aggregate);
  renderPuestos(indexDaily, supermarkets);
  renderCompareChart(indexDaily, supermarkets);
  renderIpcPanel(aggregate);
  renderDownloads();
}

main().catch((err) => {
  console.error(err);
  document.getElementById("board-date").textContent =
    "No se pudo cargar el índice todavía. Puede que la primera corrida diaria no se haya completado — volvé más tarde.";
  renderDownloads();
});
