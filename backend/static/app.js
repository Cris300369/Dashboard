const API_BASE = "/analytics";
const SELECTORS = {
  os: document.getElementById("filterOs"),
  fab: document.getElementById("filterFab"),
  cat: document.getElementById("filterCat"),
  pan: document.getElementById("filterPan"),
  cpu: document.getElementById("filterCpu"),
  ram: document.getElementById("filterRam"),
  alm: document.getElementById("filterAlm"),
};
const totalCountEl = document.getElementById("totalCount");
const uniqueModelsEl = document.getElementById("uniqueModels");
const top5Body = document.querySelector("#top5Table tbody");
const combosBody = document.querySelector("#combosTable tbody");
const applyButton = document.getElementById("applyFilters");
const clearButton = document.getElementById("clearFilters");

let allLaptops = [];
let charts = {};

async function fetchLaptops(filters = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value && value !== "Todos") {
      params.set(key, value);
    }
  });
  const response = await fetch(`${API_BASE}/laptops?${params.toString()}`);
  return response.json();
}

function unique(values) {
  return [...new Set(values.filter(Boolean))].sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));
}

function populateSelect(select, values) {
  select.innerHTML = "";
  const defaultOption = document.createElement("option");
  defaultOption.value = "Todos";
  defaultOption.textContent = "Todos";
  select.appendChild(defaultOption);
  values.forEach((value) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    select.appendChild(option);
  });
}

function buildBucket(dataset, key) {
  return dataset.reduce((acc, row) => {
    const value = row[key] || "Sin dato";
    acc[value] = (acc[value] || 0) + 1;
    return acc;
  }, {});
}

function getChartData(dataset, key, groupThreshold = null) {
  const bucket = buildBucket(dataset, key);
  const entries = Object.entries(bucket);

  if (!groupThreshold || entries.length <= 0) {
    return {
      labels: entries.map(([label]) => label),
      values: entries.map(([, value]) => value),
    };
  }

  const grouped = [];
  const others = [];

  entries.forEach(([label, value]) => {
    if (value <= groupThreshold) {
      others.push([label, value]);
    } else {
      grouped.push([label, value]);
    }
  });

  const totalOthers = others.reduce((sum, [, value]) => sum + value, 0);
  if (totalOthers > 0) {
    grouped.push(["Otros", totalOthers]);
  }

  return {
    labels: grouped.map(([label]) => label),
    values: grouped.map(([, value]) => value),
  };
}

function buildChart(canvasId, type, data, options = {}) {
  const ctx = document.getElementById(canvasId).getContext("2d");
  if (charts[canvasId]) {
    charts[canvasId].destroy();
  }

  const legendPosition = type === "doughnut" ? "right" : "bottom";
  const legendOptions = {
    display: true,
    position: legendPosition,
    align: "start",
    labels: {
      color: "#475569",
      boxWidth: 18,
      boxHeight: 18,
      padding: 18,
      font: { size: 14, family: "Inter, ui-sans-serif, system-ui" },
      usePointStyle: true,
      pointStyle: "rectRounded",
      textAlign: "left",
    },
    onClick: function (evt, item, legend) {
      if (evt && evt.native && typeof evt.native.preventDefault === "function") {
        evt.native.preventDefault();
      }
    },
    onHover: function (evt) {
      if (evt && evt.native && evt.native.target) {
        evt.native.target.style.cursor = "default";
      }
    },
  };

  charts[canvasId] = new Chart(ctx, {
    type,
    data: {
      labels: data.labels,
      datasets: [
        {
          label: data.label || "",
          data: data.values,
          backgroundColor: [
            "#2563eb",
            "#10b981",
            "#f97316",
            "#8b5cf6",
            "#ef4444",
            "#14b8a6",
            "#f59e0b",
            "#3b82f6",
            "#ec4899",
          ],
          borderWidth: 0,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: legendOptions,
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: {
            color: "rgba(148, 163, 184, 0.15)",
          },
        },
        x: {
          grid: {
            display: false,
          },
        },
      },
      ...options,
    },
  });
}

function updateDashboard(dataset) {
  totalCountEl.textContent = dataset.length.toLocaleString();
  uniqueModelsEl.textContent = unique(dataset.map((row) => row.NOT_Desc)).length.toLocaleString();

  const fabricante = getChartData(dataset, "FAB_Desc", 70);
  const categoria = getChartData(dataset, "CAT_Desc");
  const sistema = getChartData(dataset, "SIO_Desc");
  const cpu = getChartData(dataset, "CPU_Fabric");
  const gpu = getChartData(dataset, "GPU_Fabric");
  const ram = getChartData(dataset, "RAM_Desc");

  buildChart("chartFabricantes", "doughnut", fabricante, { plugins: { legend: { position: "right" } }, layout: { padding: 12 } });
  buildChart("chartCategorias", "doughnut", categoria, { plugins: { legend: { position: "right" } }, layout: { padding: 12 } });
  buildChart("chartOs", "doughnut", sistema, { plugins: { legend: { position: "right" } }, layout: { padding: 12 } });
  buildChart("chartCpu", "bar", cpu, { scales: { x: { ticks: { maxRotation: 45, minRotation: 0 } } }, layout: { padding: 12 } });
  buildChart("chartGpu", "bar", gpu, { scales: { x: { ticks: { maxRotation: 45, minRotation: 0 } } }, layout: { padding: 12 } });
  buildChart("chartRam", "bar", ram, { scales: { x: { ticks: { maxRotation: 45, minRotation: 0 } } }, layout: { padding: 12 } });

  updateTop5Table(dataset);
  updateCombosTable(dataset);
}

function updateTop5Table(dataset) {
  const sorted = [...dataset].sort((a, b) => b.Precio_Euro - a.Precio_Euro).slice(0, 5);
  top5Body.innerHTML = "";
  sorted.forEach((row, index) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${index + 1}</td>
      <td>${row.FAB_Desc || "-"}</td>
      <td>${row.CAT_Desc || "-"}</td>
      <td>${row.CPU_Desc || "-"}</td>
      <td>${row.GPU_Model || row.GPU_Fabric || "-"}</td>
      <td>${row.RAM_Desc || "-"}</td>
      <td>€${parseFloat(row.Precio_Euro).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
    `;
    top5Body.appendChild(tr);
  });
}

function updateCombosTable(dataset) {
  const comboCounts = dataset.reduce((acc, row) => {
    const cpu = row.CPU_Fabric || "Sin dato";
    const gpu = row.GPU_Fabric || "Sin dato";
    const key = `${cpu}||${gpu}`;
    acc[key] = (acc[key] || 0) + 1;
    return acc;
  }, {});
  const rows = Object.entries(comboCounts)
    .map(([key, count]) => {
      const [cpu, gpu] = key.split("||");
      return { cpu, gpu, count };
    })
    .sort((a, b) => b.count - a.count)
    .slice(0, 5);

  combosBody.innerHTML = "";
  rows.forEach((item, index) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${index + 1}</td>
      <td>${item.cpu}</td>
      <td>${item.gpu}</td>
      <td>${item.count}</td>
    `;
    combosBody.appendChild(tr);
  });
}

function getFiltersFromForm() {
  return {
    os_desc: SELECTORS.os.value,
    fab_desc: SELECTORS.fab.value,
    cat_desc: SELECTORS.cat.value,
    pan_desc: SELECTORS.pan.value,
    cpu_fab: SELECTORS.cpu.value,
    ram_desc: SELECTORS.ram.value,
    alm_desc: SELECTORS.alm.value,
  };
}

function resetFilters() {
  Object.values(SELECTORS).forEach((select) => {
    select.value = "Todos";
  });
}

async function loadData() {
  const dataset = await fetchLaptops();
  allLaptops = dataset;
  const filters = {
    os_desc: unique(dataset.map((row) => row.SIO_Desc)),
    fab_desc: unique(dataset.map((row) => row.FAB_Desc)),
    cat_desc: unique(dataset.map((row) => row.CAT_Desc)),
    pan_desc: unique(dataset.map((row) => row.PAN_Desc)),
    cpu_fab: unique(dataset.map((row) => row.CPU_Fabric)),
    ram_desc: unique(dataset.map((row) => row.RAM_Desc)),
    alm_desc: unique(dataset.map((row) => row.ALM_Desc)),
  };

  populateSelect(SELECTORS.os, filters.os_desc);
  populateSelect(SELECTORS.fab, filters.fab_desc);
  populateSelect(SELECTORS.cat, filters.cat_desc);
  populateSelect(SELECTORS.pan, filters.pan_desc);
  populateSelect(SELECTORS.cpu, filters.cpu_fab);
  populateSelect(SELECTORS.ram, filters.ram_desc);
  populateSelect(SELECTORS.alm, filters.alm_desc);

  updateDashboard(allLaptops);
}

function applyFilters() {
  const filters = getFiltersFromForm();
  const filtered = allLaptops.filter((row) => {
    return Object.entries(filters).every(([key, value]) => {
      if (!value || value === "Todos") return true;
      const field = {
        os_desc: "SIO_Desc",
        fab_desc: "FAB_Desc",
        cat_desc: "CAT_Desc",
        pan_desc: "PAN_Desc",
        cpu_fab: "CPU_Fabric",
        ram_desc: "RAM_Desc",
        alm_desc: "ALM_Desc",
      }[key];
      return String(row[field] || "").trim() === value;
    });
  });
  updateDashboard(filtered);
}

applyButton.addEventListener("click", () => applyFilters());
clearButton.addEventListener("click", () => {
  resetFilters();
  updateDashboard(allLaptops);
});

loadData().catch((error) => {
  console.error("Error cargando datos:", error);
});
