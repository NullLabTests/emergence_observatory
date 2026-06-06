from __future__ import annotations
import json
import time
import threading
from queue import Queue, Empty

from flask import Flask, Response, render_template, jsonify

from ..core.simulation import Simulation


def create_app(simulation: Simulation) -> Flask:
    """Build a Flask application that serves the live visualisation.

    Two routes:

      - ``GET /``  — the main dashboard HTML.
      - ``GET /stream`` — SSE endpoint that pushes simulation snapshots.
    """

    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config["simulation"] = simulation
    event_queue: Queue = Queue()

    # ------------------------------------------------------------------
    # Routes
    # ------------------------------------------------------------------

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/config")
    def get_config():
        sim: Simulation = app.config["simulation"]
        return jsonify({
            "grid_width": sim.config.grid_width,
            "grid_height": sim.config.grid_height,
            "num_agents": len(sim.agents),
            "max_agents": sim.config.max_agents,
        })

    @app.route("/stream")
    def stream():
        def generate():
            sim: Simulation = app.config["simulation"]
            while sim.running:
                snapshot = event_queue.get()
                yield f"data: {json.dumps(snapshot, default=str)}\n\n"
            yield "event: close\ndata: \n\n"
        return Response(generate(), mimetype="text/event-stream")

    # ------------------------------------------------------------------
    # Background tick thread
    # ------------------------------------------------------------------

    def _run_loop(sim: Simulation, queue: Queue):
        while sim.running:
            snapshot = sim.step()
            queue.put(snapshot)
            time.sleep(sim.config.viz_update_interval_ms / 1000.0)

    def start() -> None:
        sim: Simulation = app.config["simulation"]
        sim.running = True
        t = threading.Thread(target=_run_loop, args=(sim, event_queue), daemon=True)
        t.start()

    app.start_simulation = start  # type: ignore[attr-defined]

    return app
