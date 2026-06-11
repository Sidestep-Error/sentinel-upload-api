const threatFeedStatusEl = document.getElementById("threat-feed-status");
const threatFeedListEl = document.getElementById("threat-feed-list");
const threatMapEl = document.getElementById("threat-map");
let threatMap = null;
let threatMapLayer = null;

const dropzone = document.getElementById("dropzone");
const input = document.getElementById("file-input");
const uploadBtn = document.getElementById("upload-btn");
const statusEl = document.getElementById("status");
const scanFileEl = document.getElementById("scan-file");
const scanStatusEl = document.getElementById("scan-status");
const scanDecisionEl = document.getElementById("scan-decision");
const scanRiskEl = document.getElementById("scan-risk");
const scanEngineEl = document.getElementById("scan-engine");
const scanDetailEl = document.getElementById("scan-detail");
const scanDedupEl = document.getElementById("scan-dedup");
const scanMlEl = document.getElementById("scan-ml");
const scanTiEl = document.getElementById("scan-ti");
const devDocsEl = document.getElementById("dev-docs");
const metricUploads24hEl = document.getElementById("metric-uploads-24h");
const metricRejected24hEl = document.getElementById("metric-rejected-24h");
const metricRejectRate7dEl = document.getElementById("metric-reject-rate-7d");
const metricRisk7dEl = document.getElementById("metric-risk-7d");
const modeIndicatorEl = document.getElementById("mode-indicator");
const modeTooltipEl = document.getElementById("mode-tooltip");
const easterEggEl = document.getElementById("easter-egg");
const easterEggCloseEl = document.getElementById("easter-egg-close");
const easterEggRainEl = document.getElementById("easter-egg-rain");

const isDevHost =
  window.location.hostname === "localhost" ||
  window.location.hostname === "127.0.0.1" ||
  window.location.hostname === "[::1]";
if (isDevHost && devDocsEl) {
  devDocsEl.classList.add("is-visible");
}
function setStatus(message, type) {
  statusEl.textContent = message;
  statusEl.classList.remove("error", "warn");
  if (type) statusEl.classList.add(type);
}

function setScanResult(data) {
  scanFileEl.textContent = data.filename || "-";
  scanStatusEl.textContent = data.scan_status || "unknown";
  scanDecisionEl.textContent = data.decision || "-";
  scanRiskEl.textContent =
    typeof data.risk_score === "number" ? `${data.risk_score}/100` : "-";
  scanEngineEl.textContent = data.scan_engine || "-";
  scanDetailEl.textContent = data.scan_detail || "-";
  scanDedupEl.textContent = data.deduplicated ? "Yes" : "No";

  scanStatusEl.classList.remove("status-clean", "status-malicious", "status-error");
  scanDecisionEl.classList.remove("status-clean", "status-malicious", "status-review");

  if (data.scan_status === "clean") {
    scanStatusEl.classList.add("status-clean");
  } else if (data.scan_status === "malicious") {
    scanStatusEl.classList.add("status-malicious");
  } else {
    scanStatusEl.classList.add("status-error");
  }

  if (data.decision === "accepted") {
    scanDecisionEl.classList.add("status-clean");
  } else if (data.decision === "rejected") {
    scanDecisionEl.classList.add("status-malicious");
  } else if (data.decision === "review") {
    scanDecisionEl.classList.add("status-review");
  }

  updateMlRows(data.sha256);
}

async function updateMlRows(sha256) {
  // ML/threat-intel enrichment from sentinel-ml (via ml_predictions).
  // Complementary and fail-silent: a missing prediction (e.g. integration
  // disabled, or sentinel-ml down) just leaves the rows blank.
  // ML score and threat intel are shown on separate rows so it is clear
  // which of them (or both) blocked the file.
  scanMlEl.textContent = "-";
  scanMlEl.classList.remove("status-clean", "status-malicious");
  scanTiEl.textContent = "-";
  scanTiEl.classList.remove("status-clean", "status-malicious");
  if (!sha256) return;
  try {
    const response = await fetch(`/uploads/${sha256}/ml`);
    if (!response.ok) return; // 404 = no prediction stored
    const doc = await response.json();
    const known =
      (doc.summary && doc.summary.known_malicious_hash) ||
      (doc.upload_result && doc.upload_result.known_malicious);
    const pred = doc.upload_result && doc.upload_result.prediction;

    if (known) {
      scanTiEl.textContent = "MATCH - known malicious hash";
      scanTiEl.classList.add("status-malicious");
    } else {
      scanTiEl.textContent = "No match";
      scanTiEl.classList.add("status-clean");
    }

    if (pred && typeof pred.confidence === "number") {
      scanMlEl.textContent = `${pred.label} (${pred.confidence.toFixed(2)})`;
      // upload-classifier emits accepted/rejected; threat models clean/malicious.
      if (pred.label === "clean" || pred.label === "accepted") {
        scanMlEl.classList.add("status-clean");
      } else if (pred.label === "malicious" || pred.label === "rejected") {
        scanMlEl.classList.add("status-malicious");
      }
    } else {
      scanMlEl.textContent = "No ML data";
    }
  } catch (error) {
    // ML is complementary — never let it disturb the UI.
  }
}

function setMetrics(data) {
  if (!data) return;
  const last24h = data.last_24h || {};
  const last7d = data.last_7d || {};
  metricUploads24hEl.textContent = `${last24h.total_uploads ?? 0}`;
  metricRejected24hEl.textContent = `${last24h.rejected ?? 0}`;
  metricRejectRate7dEl.textContent = `${last7d.rejection_rate_percent ?? 0}%`;
  metricRisk7dEl.textContent = `${last7d.avg_risk_score ?? 0}/100`;
}

function detailRow(label, value, valueClass) {
  const row = document.createElement("div");
  row.className = "scan-row";
  const labelEl = document.createElement("span");
  labelEl.textContent = label;
  const valueEl = document.createElement("strong");
  valueEl.textContent = value;
  if (valueClass) valueEl.classList.add(valueClass);
  row.appendChild(labelEl);
  row.appendChild(valueEl);
  return row;
}

function renderThreatFeed(payload) {
  if (!threatFeedListEl) return;
  const latest = payload.latest || [];
  threatFeedListEl.innerHTML = "";

  // Feed fields are third-party data: render through detailRow (textContent),
  // never string-interpolated HTML.
  const summaryRows = [
    ["Source", payload.source || "CISA KEV"],
    ["Total KEV", String(payload.total_known_exploited_cves ?? 0)],
    ["Added 30d", String(payload.added_last_30_days ?? 0)],
  ];
  summaryRows.forEach(([label, value]) => {
    threatFeedListEl.appendChild(detailRow(label, value));
  });

  latest.slice(0, 5).forEach((item) => {
    threatFeedListEl.appendChild(
      detailRow(
        item.cve || "CVE",
        `${item.vendor || ""} ${item.product || ""} (${item.date_added || ""})`,
      ),
    );
  });

  threatFeedStatusEl.textContent = `Updated ${payload.fetched_at || "recently"} via ${payload.source || "CISA KEV"}.`;
  if (payload.warning) {
    threatFeedStatusEl.textContent = payload.warning;
  }
}

function initThreatMap() {
  if (!threatMapEl || typeof L === "undefined") return;
  const worldBounds = L.latLngBounds(
    L.latLng(-85, -180),
    L.latLng(85, 180),
  );
  threatMap = L.map("threat-map", {
    zoomControl: false,
    attributionControl: true,
    minZoom: 1,
    maxZoom: 8,
    maxBounds: worldBounds,
    maxBoundsViscosity: 1.0,
  }).setView([20, 0], 2);
  L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
    maxZoom: 8,
    subdomains: "abcd",
    noWrap: true,
    attribution: "&copy; OpenStreetMap contributors &copy; CARTO",
  }).addTo(threatMap);
  if (typeof L.markerClusterGroup === "function") {
    threatMapLayer = L.markerClusterGroup({
      showCoverageOnHover: false,
      spiderfyOnMaxZoom: true,
      maxClusterRadius: 42,
    });
    threatMap.addLayer(threatMapLayer);
  } else {
    threatMapLayer = L.layerGroup().addTo(threatMap);
  }
}

function threatPopupContent(item) {
  // IOC feeds are attacker-influenced input (URLhaus rows are literally
  // malicious URLs submitted by third parties). Build the popup from text
  // nodes — Leaflet treats popup strings as HTML.
  const container = document.createElement("div");
  const title = document.createElement("strong");
  title.textContent = item.type || "Threat event";
  container.appendChild(title);

  const details = item.details || {};
  const location =
    `${details.city || ""}${details.country ? ` (${details.country})` : ""}`.trim();
  const lines = [
    item.ioc || "",
    location,
    details.malware_family ? `Malware: ${details.malware_family}` : "",
    details.status ? `Status: ${details.status}` : "",
    typeof item.confidence === "number" ? `Confidence: ${item.confidence}%` : "",
    item.source || "",
    item.timestamp || "",
  ].filter(Boolean);
  lines.forEach((line) => {
    container.appendChild(document.createElement("br"));
    container.appendChild(document.createTextNode(line));
  });
  return container;
}

function renderThreatMap(events) {
  if (!threatMap || !threatMapLayer) return;
  threatMapLayer.clearLayers();
  const points = [];
  const coordBuckets = new Map();
  (events || []).forEach((item) => {
    const lat = Number(item.lat);
    const lon = Number(item.lon);
    if (!Number.isFinite(lat) || !Number.isFinite(lon)) return;

    const severity = (item.severity || "").toLowerCase();
    const size = severity === "high" ? 8 : severity === "medium" ? 7 : 6;
    const bucketKey = `${lat.toFixed(4)},${lon.toFixed(4)}`;
    const bucketIndex = coordBuckets.get(bucketKey) || 0;
    coordBuckets.set(bucketKey, bucketIndex + 1);

    // If several events share identical coordinates, fan them out slightly
    // so all markers become visible instead of stacking as one.
    const angle = bucketIndex * (Math.PI / 4);
    const radius = Math.floor(bucketIndex / 8) * 0.18 + (bucketIndex > 0 ? 0.12 : 0);
    const markerLat = lat + radius * Math.sin(angle);
    const markerLon = lon + radius * Math.cos(angle);

    const icon = L.divIcon({
      className: "threat-dot",
      iconSize: [size, size],
      iconAnchor: [Math.floor(size / 2), Math.floor(size / 2)],
    });
    const marker = L.marker([markerLat, markerLon], { icon, title: item.ioc || item.type || "Threat event" }).addTo(threatMapLayer);
    marker.bindPopup(threatPopupContent(item));
    points.push([markerLat, markerLon]);
  });
  if (points.length > 1) {
    threatMap.fitBounds(points, { padding: [20, 20], maxZoom: 6 });
  }
}

dropzone.addEventListener("dragover", (event) => {
  event.preventDefault();
  dropzone.classList.add("dragover");
});

dropzone.addEventListener("dragleave", () => {
  dropzone.classList.remove("dragover");
});

dropzone.addEventListener("drop", (event) => {
  event.preventDefault();
  dropzone.classList.remove("dragover");
  if (event.dataTransfer.files.length) {
    input.files = event.dataTransfer.files;
    setStatus(`Selected ${input.files[0].name}`);
  }
});

// Avoid double file-picker dialogs on browsers that already trigger via <label for>.
dropzone.addEventListener("click", (event) => {
  const target = event.target;
  const isLabelOrInput =
    target instanceof HTMLElement &&
    (target.tagName === "LABEL" || target.tagName === "INPUT");
  if (isLabelOrInput) return;
  input.click();
});


// Easter egg
let modeClickCount = 0;
let fabulousEnabled = false;
let rainCanvas = null;
let rainCtx = null;
let rainAnimationFrame = null;
let rainStreams = [];
let rainColumns = 0;
const rainFontSize = 16;
const rainColumnWidth = 18;
const rainGlyphs = "01010101<>[]{}()/\\=+-_#;:*$";

function randomRainGlyph() {
  return rainGlyphs[Math.floor(Math.random() * rainGlyphs.length)];
}

function setFabulousMode(enabled) {
  fabulousEnabled = enabled;
  document.body.classList.toggle("fabulous-mode", enabled);
  if (modeIndicatorEl) {
    modeIndicatorEl.textContent = enabled ? "Mode: Fabulous" : "Mode: Secure";
  }
  if (easterEggEl) {
    easterEggEl.classList.toggle("is-visible", enabled);
    easterEggEl.setAttribute("aria-hidden", enabled ? "false" : "true");
  }
  if (!enabled) {
    stopEasterEggRain();
  } else {
    initEasterEggRain();
  }
}

function initEasterEggRain() {
  if (!easterEggRainEl || rainAnimationFrame) return;
  if (!rainCanvas) {
    rainCanvas = document.createElement("canvas");
    rainCanvas.className = "easter-egg-rain-canvas";
    easterEggRainEl.innerHTML = "";
    easterEggRainEl.appendChild(rainCanvas);
    rainCtx = rainCanvas.getContext("2d");
  }
  resizeEasterEggRain();

  const draw = () => {
    if (!rainCtx || !rainCanvas) return;
    rainCtx.fillStyle = "rgba(0, 0, 0, 1)";
    rainCtx.fillRect(0, 0, rainCanvas.width, rainCanvas.height);
    rainCtx.font = `${rainFontSize}px "JetBrains Mono", monospace`;
    rainCtx.textAlign = "left";
    rainCtx.textBaseline = "top";
    rainCtx.shadowBlur = 10;
    rainCtx.shadowColor = "rgba(255, 170, 227, 0.72)";

    for (let i = 0; i < rainColumns; i += 1) {
      const stream = rainStreams[i];
      const x = i * rainColumnWidth + stream.jitter;
      for (let c = 0; c < stream.length; c += 1) {
        const y = stream.y - c * (rainFontSize * 0.9);
        if (y < -rainFontSize || y > rainCanvas.height + rainFontSize) continue;
        const alpha = 1 - (c / stream.length);
        rainCtx.fillStyle = c === 0
          ? `rgba(255, 244, 251, ${0.95 * alpha})`
          : `rgba(255, 164, 227, ${0.82 * alpha})`;
        rainCtx.fillText(randomRainGlyph(), x, y);
      }

      stream.y += stream.speed;
      if (stream.y - stream.length * rainFontSize > rainCanvas.height + 40) {
        stream.y = -Math.random() * rainCanvas.height * 0.8;
        stream.speed = 0.24 + Math.random() * 0.22;
        stream.length = 16 + Math.floor(Math.random() * 24);
        stream.jitter = Math.floor(Math.random() * 4) - 2;
      }
    }
    rainAnimationFrame = window.requestAnimationFrame(draw);
  };

  draw();
}

function resizeEasterEggRain() {
  if (!rainCanvas || !easterEggRainEl) return;
  const bounds = easterEggRainEl.getBoundingClientRect();
  rainCanvas.width = Math.max(1, Math.floor(bounds.width));
  rainCanvas.height = Math.max(1, Math.floor(bounds.height));
  rainColumns = Math.ceil(rainCanvas.width / rainColumnWidth);
  rainStreams = Array.from({ length: rainColumns }, () => ({
    y: -Math.random() * rainCanvas.height,
    speed: 0.24 + Math.random() * 0.22,
    length: 16 + Math.floor(Math.random() * 24),
    jitter: Math.floor(Math.random() * 4) - 2,
  }));
}

function stopEasterEggRain() {
  if (rainAnimationFrame) {
    window.cancelAnimationFrame(rainAnimationFrame);
    rainAnimationFrame = null;
  }
}

if (modeIndicatorEl && modeTooltipEl) {
  const showTooltip = () => modeTooltipEl.classList.add("is-visible");
  const hideTooltip = () => modeTooltipEl.classList.remove("is-visible");

  modeIndicatorEl.addEventListener("mouseenter", showTooltip);
  modeIndicatorEl.addEventListener("mouseleave", hideTooltip);

  modeIndicatorEl.addEventListener("mousemove", (event) => {
    modeTooltipEl.style.left = `${event.clientX + 14}px`;
    modeTooltipEl.style.top = `${event.clientY + 14}px`;
  });

  modeIndicatorEl.addEventListener("click", () => {
    modeClickCount += 1;
    if (modeClickCount === 3) {
      setFabulousMode(true);
      modeClickCount = 0;
    }
  });
}

if (easterEggCloseEl) {
  easterEggCloseEl.addEventListener("click", () => {
    setFabulousMode(false);
    modeClickCount = 0;
  });
}

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && fabulousEnabled) {
    setFabulousMode(false);
    modeClickCount = 0;
  }
});

window.addEventListener("resize", () => {
  if (fabulousEnabled) {
    resizeEasterEggRain();
  }
});
// Allow selecting the same file again after a previous upload.
input.addEventListener("click", () => {
  input.value = "";
});
input.addEventListener("change", () => {
  if (input.files.length) {
    setStatus(`Selected ${input.files[0].name}`);
  }
});

async function loadUploads() {
  try {
    const response = await fetch("/uploads?limit=25");
    if (!response.ok) {
      if (response.status === 401) {
        throw new Error("Auth required");
      }
      throw new Error("Database unavailable");
    }
    const data = await response.json();
    const list = document.getElementById("uploads-list");
    list.innerHTML = "";
    if (!data.items.length) {
      list.innerHTML = '<div class="list-item">No uploads yet</div>';
      return;
    }
    data.items.forEach((item) => {
      const wrapper = document.createElement("div");
      wrapper.className = "upload-item";

      const row = document.createElement("div");
      row.className = "list-item list-item-toggle";
      row.setAttribute("role", "button");
      row.setAttribute("tabindex", "0");
      row.setAttribute("aria-expanded", "false");
      row.title = "Click to show scan details";
      const nameSpan = document.createElement("span");
      nameSpan.textContent = item.filename;
      const typeSpan = document.createElement("span");
      typeSpan.textContent = item.content_type;
      const statusSpan = document.createElement("span");
      statusSpan.textContent = item.status;
      if (item.status === "rejected") {
        statusSpan.classList.add("status-malicious");
      } else if (item.status === "accepted") {
        statusSpan.classList.add("status-clean");
      } else {
        statusSpan.classList.add("status-review");
      }
      row.appendChild(nameSpan);
      row.appendChild(typeSpan);
      row.appendChild(statusSpan);

      const details = document.createElement("div");
      details.className = "upload-details";
      details.appendChild(detailRow("Result", item.scan_status || "unknown"));
      details.appendChild(detailRow("Decision", item.decision || "-", item.decision === "rejected" ? "status-malicious" : item.decision === "accepted" ? "status-clean" : "status-review"));
      details.appendChild(detailRow("Risk score", typeof item.risk_score === "number" ? `${item.risk_score}/100` : "-"));
      details.appendChild(detailRow("Engine", item.scan_engine || "-"));
      details.appendChild(detailRow("Detail", item.scan_detail || "-"));
      details.appendChild(detailRow("Deduplicated", item.deduplicated ? "Yes" : "No"));
      details.appendChild(detailRow("SHA-256", item.sha256 || "-"));

      // Visibility is owned entirely by the .is-open CSS rule.
      const toggleDetails = () => {
        const isOpen = wrapper.classList.toggle("is-open");
        row.setAttribute("aria-expanded", isOpen ? "true" : "false");
        // Keep the side panel in sync with selected row.
        setScanResult(item);
      };
      row.addEventListener("click", toggleDetails);
      row.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          toggleDetails();
        }
      });

      wrapper.appendChild(row);
      wrapper.appendChild(details);
      list.appendChild(wrapper);
    });
  } catch (error) {
    const list = document.getElementById("uploads-list");
    list.innerHTML = "";
    const errorItem = document.createElement("div");
    errorItem.className = "list-item";
    errorItem.textContent = error.message;
    list.appendChild(errorItem);
  }
}

async function loadMetrics() {
  try {
    const response = await fetch("/metrics/summary");
    if (!response.ok) {
      throw new Error("Metrics unavailable");
    }
    const data = await response.json();
    setMetrics(data);
  } catch (_error) {
    metricUploads24hEl.textContent = "-";
    metricRejected24hEl.textContent = "-";
    metricRejectRate7dEl.textContent = "-";
    metricRisk7dEl.textContent = "-";
  }
}

async function loadThreatFeed() {
  try {
    const response = await fetch("/external/threats/kev-summary");
    if (!response.ok) {
      throw new Error("Threat feed unavailable");
    }
    const data = await response.json();
    renderThreatFeed(data);
  } catch (_error) {
    if (threatFeedStatusEl) {
      threatFeedStatusEl.textContent = "Unable to load threat feed right now.";
    }
  }
}

async function loadThreatMapEvents() {
  try {
    const response = await fetch("/api/v1/threats/?limit=200");
    if (!response.ok) {
      throw new Error("Threat map data unavailable");
    }
    const events = await response.json();
    renderThreatMap(events);
  } catch (_error) {
    if (threatMapLayer) {
      threatMapLayer.clearLayers();
    }
  }
}

uploadBtn.addEventListener("click", async () => {
  if (!input.files.length) {
    setStatus("Choose a file first.", "warn");
    return;
  }

  const formData = new FormData();
  formData.append("file", input.files[0]);

  try {
    setStatus("Uploading...");
    const response = await fetch("/upload", {
      method: "POST",
      body: formData,
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Upload failed");
    }
    setStatus(`Accepted: ${data.filename} (${data.content_type})`);
    setScanResult(data);
    await loadUploads();
    await loadMetrics();
  } catch (error) {
    setStatus(error.message, "error");
  }
});

loadUploads();
loadMetrics();
initThreatMap();
loadThreatFeed();
loadThreatMapEvents();
setInterval(() => {
  loadThreatFeed();
  loadThreatMapEvents();
}, 60000);
