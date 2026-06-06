/* Emergence Observatory — LLM-native live dashboard */

(function () {
  const canvas = document.getElementById("grid");
  const ctx = canvas.getContext("2d");
  const W = 800, H = 600;
  let worldW = 80, worldH = 60;

  const STRAT_COLORS = [
    "#58a6ff", "#3fb950", "#d29922", "#f85149", "#bc8cff",
    "#7ee787", "#ffa657", "#79c0ff", "#ff7b72", "#a5d6ff",
  ];

  fetch("/config")
    .then((r) => r.json())
    .then((cfg) => {
      worldW = cfg.world_width;
      worldH = cfg.world_height;
    });

  function drawGrid(snapshot) {
    ctx.clearRect(0, 0, W, H);
    const sw = W / worldW;
    const sh = H / worldH;

    // Draw background grid
    ctx.strokeStyle = "#1c2128";
    ctx.lineWidth = 0.5;
    for (let x = 0; x <= worldW; x += 5) {
      ctx.beginPath(); ctx.moveTo(x * sw, 0); ctx.lineTo(x * sw, H); ctx.stroke();
    }
    for (let y = 0; y <= worldH; y += 5) {
      ctx.beginPath(); ctx.moveTo(0, y * sh); ctx.lineTo(W, y * sh); ctx.stroke();
    }

    // Draw agents
    if (snapshot.agents) {
      snapshot.agents.forEach((a) => {
        const color = a.energy < 20 ? "#f85149" : STRAT_COLORS[a.agent_id % STRAT_COLORS.length];
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(a.x * sw + sw / 2, a.y * sh + sh / 2, Math.max(3, sw * 0.7), 0, 2 * Math.PI);
        ctx.fill();
        if (a.energy > 0) {
          ctx.fillStyle = "rgba(255,255,255,0.15)";
          ctx.beginPath();
          ctx.arc(a.x * sw + sw / 2, a.y * sh + sh / 2, Math.max(5, sw * 1.5), 0, 2 * Math.PI);
          ctx.fill();
        }
      });
    }

    // Draw conversations as lines between agents
    if (snapshot.conversations) {
      const recent = snapshot.conversations.slice(-5);
      recent.forEach((c) => {
        const from = snapshot.agents.find((a) => a.agent_id === c.from);
        const to = snapshot.agents.find((a) => a.agent_id === c.to);
        if (from && to) {
          ctx.strokeStyle = "rgba(88,166,255,0.3)";
          ctx.lineWidth = 1.5;
          ctx.beginPath();
          ctx.moveTo(from.x * sw + sw / 2, from.y * sh + sh / 2);
          ctx.lineTo(to.x * sw + sw / 2, to.y * sh + sh / 2);
          ctx.stroke();
        }
      });
    }
  }

  function updateMetrics(snapshot) {
    const m = snapshot.metrics || {};
    document.getElementById("tick").textContent = snapshot.tick || 0;
    document.getElementById("numAgents").textContent = snapshot.num_agents || 0;
    document.getElementById("avgEnergy").textContent = m.avg_energy || 0;
    document.getElementById("vocabSize").textContent = m.vocab_size || 0;
    document.getElementById("entropy").textContent = m.message_entropy || 0;
    document.getElementById("graphDensity").textContent = (m.graph_density || 0).toFixed(4);
    document.getElementById("numCommunities").textContent = m.num_communities || 0;
    document.getElementById("numAlliances").textContent = m.num_alliances || 0;
    document.getElementById("wordSurvival").textContent = m.longest_word_survival || 0;
    document.getElementById("allianceSurvival").textContent = m.longest_alliance_survival || 0;
  }

  function updateConversations(snapshot) {
    const el = document.getElementById("conversations");
    if (!snapshot.conversations || snapshot.conversations.length === 0) {
      if (el.children.length === 0) el.textContent = "Awaiting first interactions...";
      return;
    }
    el.textContent = "";
    snapshot.conversations.slice(-15).forEach((c) => {
      const div = document.createElement("div");
      div.className = "msg";
      div.innerHTML = `<span class="from">Agent ${c.from}</span> → <span class="from" style="color:#3fb950">Agent ${c.to}</span>: <span class="content">${escHtml(c.content)}</span>`;
      el.appendChild(div);
    });
    el.scrollTop = el.scrollHeight;
  }

  function updateWords(snapshot) {
    const el = document.getElementById("word-ticker");
    const words = new Set();
    if (snapshot.agents) {
      snapshot.agents.forEach((a) => {
        if (a.invented_words) {
          Object.keys(a.invented_words).forEach((w) => words.add(w));
        }
      });
    }
    if (words.size === 0) { el.textContent = "None yet."; return; }
    el.textContent = "";
    words.forEach((w) => {
      const span = document.createElement("span");
      span.className = "word";
      span.textContent = w;
      el.appendChild(span);
    });
  }

  function escHtml(s) {
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }

  function connect() {
    const evtSource = new EventSource("/stream");
    evtSource.onmessage = (e) => {
      try {
        const snapshot = JSON.parse(e.data);
        drawGrid(snapshot);
        updateMetrics(snapshot);
        updateConversations(snapshot);
        updateWords(snapshot);
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
      document.getElementById("status").textContent = "Connected — live";
    };
  }

  connect();
})();
