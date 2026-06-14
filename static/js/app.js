// ── Page Router ───────────────────────────────────────────────
let currentPage = "dashboard";

function showPage(page) {
  document.querySelectorAll(".page").forEach(el => el.classList.remove("active"));
  document.querySelectorAll(".nav-item").forEach(el => el.classList.remove("active"));

  const pageEl = document.getElementById("page-" + page);
  const navEl  = document.querySelector(`.nav-item[data-page="${page}"]`);
  if (pageEl) pageEl.classList.add("active");
  if (navEl)  navEl.classList.add("active");

  currentPage = page;

  if (page === "sessions") loadSessions();
  if (page === "config")   loadConfig();
  if (page === "logs")     loadLogs();
}

document.querySelectorAll(".nav-item").forEach(el => {
  el.addEventListener("click", (e) => {
    e.preventDefault();
    showPage(el.dataset.page);
  });
});

// ── Dashboard ─────────────────────────────────────────────────
let totalVisits = 0;

function log(msg, cls = "") {
  const term = document.getElementById("terminal");
  const ts = new Date().toLocaleTimeString("id-ID");
  const line = document.createElement("div");
  line.className = cls;
  line.textContent = `[${ts}] ${msg}`;
  term.appendChild(line);
  term.scrollTop = term.scrollHeight;
}

function updateStats(results, total) {
  const success = results.filter(r => r.status === "success").length;
  const fail    = results.filter(r => r.status !== "success").length;
  document.getElementById("stat-total").textContent   = results.length;
  document.getElementById("stat-success").textContent = success;
  document.getElementById("stat-fail").textContent    = fail;
  document.getElementById("stat-rate").textContent    =
    results.length ? Math.round((success / results.length) * 100) + "%" : "—";

  if (total > 0) {
    const pct = Math.round((results.length / total) * 100);
    document.getElementById("progress-fill").style.width = pct + "%";
    document.getElementById("progress-label").textContent = `${results.length} / ${total}`;
  }
}

function addTableRow(r) {
  const tbody = document.getElementById("log-body");
  const empty = tbody.querySelector(".empty-row");
  if (empty) empty.remove();

  const ts   = new Date(r.timestamp).toLocaleTimeString("id-ID");
  const chip = r.status === "success"
    ? `<span class="chip chip--ok">✓ OK</span>`
    : `<span class="chip chip--err">✗ Gagal</span>`;
  const row = document.createElement("tr");
  row.innerHTML = `
    <td>${r.session_id}</td>
    <td>${ts}</td>
    <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${r.url}">${r.url}</td>
    <td style="max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${r.page_title || "—"}</td>
    <td>${r.duration_sec}s</td>
    <td>${chip}</td>
  `;
  tbody.insertBefore(row, tbody.firstChild);
}

async function startBot() {
  const url    = document.getElementById("inp-url").value.trim();
  const visits = parseInt(document.getElementById("inp-visits").value) || 10;
  if (!url) { alert("Masukkan URL target dulu!"); return; }

  totalVisits = visits;

  document.getElementById("btn-run").disabled = true;
  document.getElementById("status-badge").textContent = "Running";
  document.getElementById("status-badge").className   = "badge badge--running";
  document.getElementById("progress-wrap").classList.remove("hidden");
  document.getElementById("terminal").innerHTML = "";
  document.getElementById("log-body").innerHTML =
    '<tr class="empty-row"><td colspan="6">Menunggu hasil sesi pertama…</td></tr>';

  log(`Memulai bot → ${url} | ${visits} kunjungan`, "t-info");

  try {
    const res  = await fetch("/api/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, visits }),
    });
    const data = await res.json();
    if (data.error) { log("Error: " + data.error, "t-err"); return; }
    log("Bot berjalan…", "t-ok");
  } catch (e) {
    log("Gagal menghubungi server: " + e.message, "t-err");
    document.getElementById("btn-run").disabled = false;
    return;
  }

  const es = new EventSource("/api/stream");
  const allResults = [];

  es.onmessage = (e) => {
    const msg = JSON.parse(e.data);
    if (msg.type === "ping") return;

    if (msg.type === "start") {
      log(`Target: ${msg.url} | ${msg.visits} sesi`, "t-info");
    }

    if (msg.type === "progress") {
      const r = msg.result;
      allResults.push(r);
      addTableRow(r);
      updateStats(allResults, totalVisits);
      const cls = r.status === "success" ? "t-ok" : "t-err";
      log(`Sesi ${r.session_id} — ${r.status === "success" ? "✓" : "✗"} ${r.page_title || r.url} (${r.duration_sec}s)`, cls);
    }

    if (msg.type === "done") {
      es.close();
      document.getElementById("btn-run").disabled = false;
      document.getElementById("status-badge").textContent = "Done";
      document.getElementById("status-badge").className   = "badge badge--done";
      const s = allResults.filter(r => r.status === "success").length;
      log(`✅ Selesai! ${s}/${allResults.length} berhasil.`, "t-ok");
    }
  };

  es.onerror = () => {
    log("Koneksi SSE terputus.", "t-err");
    es.close();
    document.getElementById("btn-run").disabled = false;
  };
}

// ── Sessions ──────────────────────────────────────────────────
async function loadSessions() {
  try {
    const res  = await fetch("/api/sessions");
    const data = await res.json();

    document.getElementById("sess-stat-total").textContent = data.total;
    document.getElementById("sess-stat-ok").textContent    = data.success;
    document.getElementById("sess-stat-fail").textContent  = data.failed;
    document.getElementById("sess-stat-rate").textContent  =
      data.total ? Math.round((data.success / data.total) * 100) + "%" : "—";

    const tbody = document.getElementById("sessions-body");
    tbody.innerHTML = "";

    if (!data.sessions || data.sessions.length === 0) {
      tbody.innerHTML = '<tr class="empty-row"><td colspan="6">Belum ada riwayat sesi.</td></tr>';
      return;
    }

    // Show newest first
    [...data.sessions].reverse().forEach(r => {
      const ts   = new Date(r.timestamp).toLocaleTimeString("id-ID");
      const chip = r.status === "success"
        ? `<span class="chip chip--ok">✓ OK</span>`
        : `<span class="chip chip--err">✗ Gagal</span>`;
      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${r.session_id}</td>
        <td>${ts}</td>
        <td style="max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${r.url}">${r.url}</td>
        <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${r.page_title || "—"}</td>
        <td>${r.duration_sec}s</td>
        <td>${chip}</td>
      `;
      tbody.appendChild(row);
    });
  } catch (e) {
    console.error("Gagal load sessions:", e);
  }
}

async function clearSessions() {
  if (!confirm("Hapus semua riwayat sesi?")) return;
  await fetch("/api/sessions/clear", { method: "POST" });
  loadSessions();
}

// ── Config ────────────────────────────────────────────────────
async function loadConfig() {
  try {
    const res  = await fetch("/api/config");
    const cfg  = await res.json();

    document.getElementById("cfg-url").value    = cfg.TARGET_URL   || "";
    document.getElementById("cfg-visits").value = cfg.TOTAL_VISITS || 20;
    document.getElementById("cfg-min-gap").value = cfg.MIN_GAP_SEC || 3;
    document.getElementById("cfg-max-gap").value = cfg.MAX_GAP_SEC || 8;

    const headlessEl = document.getElementById("cfg-headless");
    headlessEl.checked = !!cfg.HEADLESS;
    updateHeadlessLabel(headlessEl.checked);

    document.getElementById("cfg-ua").value =
      (cfg.USER_AGENTS || []).join("\n");
  } catch (e) {
    console.error("Gagal load config:", e);
  }
}

function updateHeadlessLabel(checked) {
  document.getElementById("cfg-headless-label").textContent =
    checked ? "Aktif (tanpa jendela browser)" : "Nonaktif (browser tampil)";
}

document.addEventListener("DOMContentLoaded", () => {
  const h = document.getElementById("cfg-headless");
  if (h) h.addEventListener("change", () => updateHeadlessLabel(h.checked));
});

async function saveConfig() {
  const agents = document.getElementById("cfg-ua").value
    .split("\n")
    .map(s => s.trim())
    .filter(Boolean);

  const payload = {
    TARGET_URL:   document.getElementById("cfg-url").value.trim(),
    TOTAL_VISITS: parseInt(document.getElementById("cfg-visits").value),
    MIN_GAP_SEC:  parseFloat(document.getElementById("cfg-min-gap").value),
    MAX_GAP_SEC:  parseFloat(document.getElementById("cfg-max-gap").value),
    HEADLESS:     document.getElementById("cfg-headless").checked,
    USER_AGENTS:  agents,
  };

  try {
    const res  = await fetch("/api/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (data.status === "saved") {
      // Also update dashboard inputs
      document.getElementById("inp-url").value    = payload.TARGET_URL;
      document.getElementById("inp-visits").value = payload.TOTAL_VISITS;

      const badge = document.getElementById("cfg-save-badge");
      badge.style.display = "inline-block";
      badge.className = "badge badge--done";
      badge.textContent = "Tersimpan ✓";
      setTimeout(() => { badge.style.display = "none"; }, 2500);
    }
  } catch (e) {
    console.error("Gagal simpan config:", e);
    alert("Gagal menyimpan config.");
  }
}

// ── Logs ──────────────────────────────────────────────────────
async function loadLogs() {
  const viewer = document.getElementById("log-viewer");
  viewer.textContent = "Memuat log…";
  try {
    const res  = await fetch("/api/logs");
    const data = await res.json();

    document.getElementById("log-line-count").textContent = `${data.total} baris`;

    if (!data.lines || data.lines.length === 0) {
      viewer.innerHTML = '<span style="color:var(--muted)">Log kosong.</span>';
      return;
    }

    viewer.innerHTML = "";
    data.lines.forEach(line => {
      const div = document.createElement("div");
      // Colorize based on keywords
      if      (/ERROR|error/i.test(line))   div.className = "t-err";
      else if (/WARNING/i.test(line))       div.className = "t-warn";
      else if (/INFO.*Done|Session.*✓/i.test(line)) div.className = "t-ok";
      else if (/INFO/i.test(line))          div.className = "t-info";
      div.textContent = line;
      viewer.appendChild(div);
    });
    viewer.scrollTop = viewer.scrollHeight;
  } catch (e) {
    viewer.innerHTML = '<span style="color:var(--red)">Gagal memuat log.</span>';
    console.error(e);
  }
}

async function clearLogs() {
  if (!confirm("Hapus isi file log?")) return;
  await fetch("/api/logs/clear", { method: "POST" });
  loadLogs();
}
