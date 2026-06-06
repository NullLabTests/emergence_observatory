/* Emergence Observatory — Live browser visualisation */

(function () {
  const canvas = document.getElementById("grid");
  const ctx = canvas.getContext("2d");
  const W = 700, H = 700;
  let worldW = 100, worldH = 100;

  // Colour map for strategies
  const STRAT_COLORS = {
    explore: "#58a6ff",
    gather: "#3fb950",
    social: "#d29922",
    rest: "#8b949e",
  };

  // Fetch config first
  fetch("/config")
    .then((r) => r.json())
    .then((cfg) => {
      worldW = cfg.grid_width;
      worldH = cfg.grid_height;
    });

  // ---- Drawing -----------------------------------------------------------
  function drawGrid(snapshot) {
    ctx.clearRect(0, 0, W, H);
    const sw = W / worldW;
    const sh = H / worldH;

    // Draw resources
    if (snapshot.resources) {
      snapshot.resources.forEach((r) => {
        ctx.fillStyle = "#2ea043";
        ctx.globalAlpha = Math.min(1, (r.amount || 1) / 20);
        ctx.fillRect(r.x * sw, r.y * sh, sw, sh);
        ctx.globalAlpha = 1;
      });
    }

    // Draw agents
    if (snapshot.agents) {
      snapshot.agents.forEach((a) => {
        const color = a.energy < 20 ? "#f85149" : STRAT_COLORS[a.strategy] || "#58a6ff";
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(a.x * sw + sw / 2, a.y * sh + sh / 2, Math.max(2, sw * 0.8), 0, 2 * Math.PI);
        ctx.fill();
      });
    }
  }

  // ---- Metrics update ----------------------------------------------------
  function updateMetrics(snapshot) {
    const m = snapshot.metrics || {};
    document.getElementById("tick").textContent = snapshot.tick || 0;
    document.getElementById("numAgents").textContent = snapshot.num_agents || 0;
    document.getElementById("avgEnergy").textContent = m.avg_energy || 0;
    document.getElementById("vocabSize").textContent = m.vocab_size || 0;
    document.getElementById("entropy").textContent = m.entropy || 0;
    document.getElementById("graphDensity").textContent = m.graph_density || 0;

    // Strategy distribution bar
    const bar = document.getElementById("strategy-bar");
    const labels = document.getElementById("strategy-labels");
    const dist = m.strategy_distribution || {};
    const total = Object.values(dist).reduce((s, v) => s + v, 0) || 1;
    bar.innerHTML = "";
    labels.innerHTML = "";
    const order = ["explore", "gather", "social", "rest"];
    order.forEach((k) => {
      const v = dist[k] || 0;
      const pct = (v / total) * 100;
      const div = document.createElement("div");
      div.style.width = pct + "%";
      div.style.background = STRAT_COLORS[k] || "#555";
      div.title = `${k}: ${v}`;
      bar.appendChild(div);
      if (pct > 0) {
        const lbl = document.createElement("span");
        lbl.style.marginRight = "12px";
        lbl.innerHTML = `<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${STRAT_COLORS[k]};margin-right:3px;"></span>${k}: ${v}`;
        labels.appendChild(lbl);
      }
    });
  }

  // ---- Event log ---------------------------------------------------------
  const logEl = document.getElementById("log");
  function addLog(msg) {
    const div = document.createElement("div");
    div.textContent = msg;
    logEl.appendChild(div);
    logEl.scrollTop = logEl.scrollHeight;
    while (logEl.children.length > 50) logEl.removeChild(logEl.firstChild);
  }

  // ---- SSE connection ----------------------------------------------------
  function connect() {
    const evtSource = new EventSource("/stream");
    evtSource.onmessage = (e) => {
      try {
        const snapshot = JSON.parse(e.data);
        drawGrid(snapshot);
        updateMetrics(snapshot);
        addLog(`tick ${snapshot.tick} | agents ${snapshot.num_agents}`);
      } catch (err) {
        console.warn("SSE parse error", err);
      }
    };
    evtSource.onerror = () => {
      document.getElementById("status").textContent = "Disconnected — retrying…";
      evtSource.close();
      setTimeout(connect, 2000);
    };
    evtSource.onopen = () => {
      document.getElementById("status").textContent = "Connected";
    };
  }

  connect();
})();
