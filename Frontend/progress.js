/* ===========================================================
   Quickeys – Progress page logic
   =========================================================== */

/* ---------- user badge & logout ---------- */
const username = localStorage.getItem("quickeys_user") || "Guest";
const nameEl = document.getElementById("userName");
if (nameEl) nameEl.textContent = username;

const logoutBtn = document.getElementById("logoutBtn");
if (logoutBtn) {
  logoutBtn.onclick = () => {
    localStorage.removeItem("quickeys_token");
    localStorage.removeItem("quickeys_user");
    location.href = "login.html";
  };
}

/* ---------- CSV helper ---------- */
function downloadCSV(rows, filename) {
  const csv  = rows.map(r => r.join(",")).join("\n");
  const blob = new Blob([csv], { type: "text/csv" });
  const a    = Object.assign(document.createElement("a"), {
    href: URL.createObjectURL(blob),
    download: filename
  });
  a.click();
  URL.revokeObjectURL(a.href);
}

/* ---------- fetch progress data ---------- */
let fullData = [];           // global cache
(async function loadProgress() {
  try {
    const token = localStorage.getItem("quickeys_token");
    if (!token) {
      location.href = "login.html";
      return;
    }

    const res = await fetch("http://127.0.0.1:5000/history", {
      headers: { Authorization: "Bearer " + token }
    });
    
    if (res.status === 401) {
       localStorage.clear();
       location.href = "login.html";
       return;
    }
    
    if (!res.ok) throw new Error(`History fetch failed (${res.status})`);

    fullData = await res.json();   // [{date,wpm,accuracy,level,mistakes}, …]
    renderEverything("all");       // default view
  } catch (e) {
    console.error(e);
    // Silent fail or show simple message in table
    document.querySelector("#historyTable tbody").innerHTML = "<tr><td colspan='5'>No data available yet.</td></tr>";
  }
})();

/* ---------- filter selector ---------- */
const filterRange = document.getElementById("filterRange");
if (filterRange) {
  filterRange.onchange = e => renderEverything(e.target.value);
}

/* ---------- main render ---------- */
function renderEverything(range = "all") {
  if (!fullData || fullData.length === 0) return;

  /* ---- filter rows ---- */
  const ms      = range === "all" ? 0 : +range * 86_400_000;   // days → ms
  const cutoff  = Date.now() - ms;
  
  // Filter and REVERSE so newest is at the top of the table
  const data = fullData
    .filter(r => ms === 0 || new Date(r.date).getTime() >= cutoff)
    .reverse();

  /* ---- summary stats ---- */
  const bestWPM = data.length ? Math.max(...data.map(d => d.wpm)) : 0;
  const avgAcc  = data.length
    ? data.reduce((s, d) => s + d.accuracy, 0) / data.length
    : 0;
  const total   = data.length;
  const last    = total ? data[0].date : "-"; // data[0] is newest because we reversed it

  /* ---- summary cards ---- */
  const summaryContainer = document.getElementById("summaryCards");
  if (summaryContainer) {
    summaryContainer.innerHTML = `
      <div class="summary-grid">
        <div class="performance-card">
          <div class="metric-icon">🏆</div>
          <div class="metric-content">
            <span class="metric-value">${bestWPM.toFixed(0)}</span>
            <span class="metric-label">Best WPM</span>
          </div>
        </div>

        <div class="performance-card">
          <div class="metric-icon">🎯</div>
          <div class="metric-content">
            <span class="metric-value">${avgAcc.toFixed(0)}%</span>
            <span class="metric-label">Avg Accuracy</span>
          </div>
        </div>

        <div class="performance-card">
          <div class="metric-icon">📈</div>
          <div class="metric-content">
            <span class="metric-value">${total}</span>
            <span class="metric-label">Total Tests</span>
          </div>
        </div>

        <div class="performance-card">
          <div class="metric-icon">🕒</div>
          <div class="metric-content">
            <span class="metric-value" style="font-size:1rem">${last}</span>
            <span class="metric-label">Last Test</span>
          </div>
        </div>
      </div>`;
  }

  /* ---- line chart ---- */
  const chartEl = document.getElementById("wpmChart");
  if (chartEl) {
    const ctx = chartEl.getContext("2d");
    if (window.wpmChart instanceof Chart) window.wpmChart.destroy();
    
    // For the chart, we want Oldest -> Newest (left to right)
    const chartData = [...data].reverse();
    
    window.wpmChart = new Chart(ctx, {
      type: "line",
      data: {
        labels: chartData.map((d, i) => `Test ${i+1}`),
        datasets: [{
          label: "WPM",
          data: chartData.map(d => d.wpm),
          borderColor: "#7c3aed",
          backgroundColor: "rgba(124, 58, 237, 0.1)",
          tension: 0.3,
          fill: true
        }]
      },
      options: {
        plugins: { legend: { display: false }},
        scales:  { y: { beginAtZero: true }},
        responsive: true,
        maintainAspectRatio: false
      }
    });
  }

  /* ---- history table ---- */
  const tbody = document.querySelector("#historyTable tbody");
  if (tbody) {
    tbody.innerHTML = data.map(d => {
      // ✅ FIX: Check for 'mistakes' OR 'errors' to be safe
      const errCount = (d.mistakes !== undefined) ? d.mistakes : (d.errors || 0);
      
      return `
      <tr>
        <td>${d.date}</td>
        <td style="font-weight:bold; color:#7c3aed">${d.wpm.toFixed(0)}</td>
        <td>${d.accuracy.toFixed(0)}%</td>
        <td>${d.level || "Intermediate"}</td>
        <td>${errCount}</td> 
      </tr>`;
    }).join("");
  }

  /* ---- CSV download ---- */
  const csvBtn = document.getElementById("csvBtn");
  if (csvBtn) {
    csvBtn.onclick = () =>
      downloadCSV(
        [
          ["Date", "WPM", "Accuracy", "Level", "Mistakes"],
          ...data.map(d => [
            d.date,
            d.wpm.toFixed(2),
            d.accuracy.toFixed(2),
            d.level,
            d.mistakes || 0
          ])
        ],
        `quickeys_${username}.csv`
      );
  }
}