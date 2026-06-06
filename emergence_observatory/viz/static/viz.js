/* Emergence Observatory — LLM-native society dashboard */

(function () {
  const canvas = document.getElementById("grid");
  const ctx = canvas.getContext("2d");
  const W = 800, H = 600;
  let worldW = 80, worldH = 60;

  const AGENT_COLORS = [
    "#58a6ff", "#3fb950", "#d29922", "#f85149", "#bc8cff",
    "#7ee787", "#ffa657", "#79c0ff", "#ff7b72", "#a5d6ff",
  ];

  fetch("/config").then(r => r.json()).then(cfg => { worldW = cfg.world_width; worldH = cfg.world_height; });

  function drawGrid(snapshot) {
    ctx.clearRect(0, 0, W, H);
    const sw = W / worldW, sh = H / worldH;

    ctx.strokeStyle = "#1c2128"; ctx.lineWidth = 0.5;
    for (let x = 0; x <= worldW; x += 5) { ctx.beginPath(); ctx.moveTo(x * sw, 0); ctx.lineTo(x * sw, H); ctx.stroke(); }
    for (let y = 0; y <= worldH; y += 5) { ctx.beginPath(); ctx.moveTo(0, y * sh); ctx.lineTo(W, y * sh); ctx.stroke(); }

    if (snapshot.conversations) {
      const recent = snapshot.conversations.slice(-5);
      recent.forEach(c => {
        const from = snapshot.agents.find(a => a.agent_id === c.from);
        const to = snapshot.agents.find(a => a.agent_id === c.to);
        if (from && to) {
          ctx.strokeStyle = "rgba(88,166,255,0.25)"; ctx.lineWidth = 1;
          ctx.beginPath(); ctx.moveTo(from.x * sw + sw / 2, from.y * sh + sh / 2);
          ctx.lineTo(to.x * sw + sw / 2, to.y * sh + sh / 2); ctx.stroke();
        }
      });
    }

    if (snapshot.agents) {
      snapshot.agents.forEach(a => {
        const color = a.energy < 15 ? "#f85149" : AGENT_COLORS[a.agent_id % AGENT_COLORS.length];
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(a.x * sw + sw / 2, a.y * sh + sh / 2, Math.max(2.5, sw * 0.65), 0, 2 * Math.PI);
        ctx.fill();
        if (a.group_id) { ctx.strokeStyle = "#d29922"; ctx.lineWidth = 1; ctx.stroke(); }
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
    document.getElementById("numCommunities").textContent = m.num_communities || 0;
    document.getElementById("numAlliances").textContent = m.num_alliances || 0;
    document.getElementById("numGroups").textContent = m.num_groups || 0;
    document.getElementById("passedNorms").textContent = m.passed_norms || 0;
    document.getElementById("openProposals").textContent = m.open_proposals || 0;
    document.getElementById("wordSurvival").textContent = m.longest_word_survival || 0;
    document.getElementById("totalResearch").textContent = m.total_research || 0;
    document.getElementById("totalVotes").textContent = m.total_votes || 0;
  }

  function updateConversations(snapshot) {
    const el = document.getElementById("conversations");
    if (!snapshot.conversations || snapshot.conversations.length === 0) { return; }
    el.textContent = "";
    snapshot.conversations.slice(-12).forEach(c => {
      const div = document.createElement("div"); div.className = "msg";
      div.innerHTML = `<span class="from">A${c.from}</span>→<span class="to">A${c.to}</span>: <span class="content">${esc(c.content)}</span>`;
      el.appendChild(div);
    });
    el.scrollTop = el.scrollHeight;
  }

  function updateProposals(snapshot) {
    const el = document.getElementById("proposals");
    if (!snapshot.proposals || snapshot.proposals.length === 0) { return; }
    el.textContent = "";
    snapshot.proposals.forEach(p => {
      const div = document.createElement("div"); div.className = "prop";
      div.innerHTML = `<span class="title">#${p.id} ${esc(p.title)}</span> <span class="votes">[${p.ptype}] for:${p.for} against:${p.against}</span>`;
      el.appendChild(div);
    });
  }

  function updateWords(snapshot) {
    const el = document.getElementById("word-ticker");
    const words = new Set();
    if (snapshot.agents) snapshot.agents.forEach(a => { if (a.invented_words) Object.keys(a.invented_words).forEach(w => words.add(w)); });
    if (words.size === 0) { return; }
    el.textContent = "";
    words.forEach(w => { const s = document.createElement("span"); s.className = "word"; s.textContent = w; el.appendChild(s); });
  }

  function updateKnowledge(snapshot) {
    const el = document.getElementById("knowledge-topics");
    if (snapshot.knowledge_topics && snapshot.knowledge_topics.length > 0) {
      el.textContent = snapshot.knowledge_topics.join(", ");
    }
  }

  function esc(s) { const d = document.createElement("div"); d.textContent = s; return d.innerHTML; }

  function connect() {
    const evtSource = new EventSource("/stream");
    evtSource.onmessage = e => {
      try {
        const s = JSON.parse(e.data);
        drawGrid(s); updateMetrics(s); updateConversations(s);
        updateProposals(s); updateWords(s); updateKnowledge(s);
      } catch (err) { console.warn("SSE err", err); }
    };
    evtSource.onerror = () => { document.getElementById("status").textContent = "Disconnected..."; evtSource.close(); setTimeout(connect, 2000); };
    evtSource.onopen = () => { document.getElementById("status").textContent = "Connected — live"; };
  }
  connect();
})();
