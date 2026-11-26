"""Browser-side playback of the currently selected simulated dispatch plan."""
from branca.element import MacroElement, Template

from .maps import ROUTE_COLORS, coords


class DispatchReplay(MacroElement):
    """Attach a local replay controller to a Leaflet map."""
    _template = Template("""
{% macro html(this, kwargs) %}
<style>
.atlas-replay {
  position: absolute; top: 10px; left: 52px; right: 12px; z-index: 800;
  display: grid; gap: 8px; padding: 10px;
  background: #18191bf5; color: #eff0f1; border: 1px solid #526861;
  border-radius: 9px; font: 500 13px system-ui; box-shadow: 0 8px 26px #0008;
}
.atlas-replay div { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.atlas-replay button {
  min-height: 44px; border: 1px solid #5c6268; border-radius: 6px;
  padding: 0 14px; background: #282b2e; color: #eff0f1; cursor: pointer;
}
.atlas-replay button:focus-visible, .atlas-replay input:focus-visible { outline: 2px solid #ff976a; outline-offset: 2px; }
.atlas-replay button[data-play] { min-width: 68px; background: #ff4a1f; border-color: #ff4a1f; color: #18191b; font-weight: 700; }
.atlas-replay button[data-play]:hover:not(:disabled) { background: #ff744c; }
.atlas-replay button:disabled { opacity: .55; cursor: default; }
.atlas-replay input { width: 100%; margin: 0; accent-color: #ff744c; }
.atlas-replay output { margin-inline-start: auto; font: 500 12px ui-monospace, monospace; }
.atlas-replay small { color: #c3c9c8; font-size: 11px; }
@media (max-width: 360px) {
  .atlas-replay { right: 8px; }
  .atlas-replay output { flex-basis: 100%; margin-inline-start: 0; }
}
.atlas-unit{border:2px solid #fff;border-radius:50%;box-shadow:0 0 12px currentColor;background:currentColor}
</style>
<div class="atlas-replay" id="{{this.get_name()}}" role="group" aria-label="Dispatch playback">
  <div><button type="button" data-play>Play</button><button type="button" data-restart>Restart</button>
  <output aria-live="off" data-status></output></div>
  <input type="range" min="0" max="1000" value="0" aria-label="Replay timeline">
  <small>Simulated playback · Equal vehicle speeds</small>
</div>
{% endmacro %}
{% macro script(this, kwargs) %}
(() => {
  const map = {{this._parent.get_name()}};
  const plans = {{this.routes | tojson}};
  const panel = document.getElementById("{{this.get_name()}}");
  const play = panel.querySelector("[data-play]");
  const restart = panel.querySelector("[data-restart]");
  const timeline = panel.querySelector("input");
  const status = panel.querySelector("[data-status]");
  let progress = 0, frame = null, origin = 0;
  const duration = 16000;
  const maxDistance = Math.max(0, ...plans.map(route => route.distances.at(-1)));
  L.DomEvent.disableClickPropagation(panel);
  L.DomEvent.disableScrollPropagation(panel);
  const units = plans.map(route => L.marker(route.points[0], {
    icon: L.divIcon({className: "", iconSize: [14,14], iconAnchor: [7,7],
      html: '<div class="atlas-unit" style="height:14px;width:14px;color:'+route.color+'"></div>'})
  }).addTo(map).bindTooltip(route.label));
  function render(value) {
    progress = value;
    const travel = maxDistance * value;
    let arrived = 0;
    plans.forEach((route, i) => {
      if (travel >= route.distances.at(-1)) {
        arrived++;
        units[i].setLatLng(route.points.at(-1));
        return;
      }
      const end = route.distances.findIndex(distance => distance > travel);
      const t = (travel - route.distances[end-1]) / (route.distances[end] - route.distances[end-1]);
      units[i].setLatLng(route.points[end-1].map((point, j) => point + t * (route.points[end][j] - point)));
    });
    timeline.value = Math.round(value * 1000);
    timeline.setAttribute("aria-valuetext", Math.round(value * 100) + " percent");
    status.textContent = plans.length ? arrived + " / " + plans.length + " units arrived" : "No units assigned";
  }
  function pause() {
    if (frame !== null) cancelAnimationFrame(frame);
    frame = null;
    play.textContent = "Play";
  }
  function tick(now) {
    render(Math.min(1, (now - origin) / duration));
    if (progress < 1) frame = requestAnimationFrame(tick);
    else pause();
  }
  play.disabled = maxDistance === 0;
  play.onclick = () => {
    if (frame !== null) return pause();
    if (progress >= 1) render(0);
    origin = performance.now() - progress * duration;
    play.textContent = "Pause";
    frame = requestAnimationFrame(tick);
  };
  restart.onclick = () => { pause(); render(0); };
  timeline.oninput = () => { pause(); render(Number(timeline.value) / 1000); };
  render(0);
})();
{% endmacro %}
""")

    def __init__(self, graph, assignments):
        super().__init__()
        self._name = "DispatchReplay"
        self.routes = []
        for index, assignment in enumerate(assignments):
            route = assignment["route"]
            distances = [0.0]
            for a, b in zip(route, route[1:]):
                distances.append(distances[-1] + graph[a][b]["distance_km"])
            self.routes.append({
                "points": [coords(graph, node)[::-1] for node in route],
                "distances": distances,
                "color": "#%02x%02x%02x" % ROUTE_COLORS[index % len(ROUTE_COLORS)],
                "label": f'{assignment["vehicle_id"]} → {assignment["incident_id"]}',
            })
