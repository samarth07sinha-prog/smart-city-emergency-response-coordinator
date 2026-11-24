# Laptop 2 — Antigravity handoff

Clone the [shared GitHub repository](https://github.com/samarth07sinha-prog/smart-city-emergency-response-coordinator)
and create the `codex/streamlit-ui` branch as described in
[TEAM_HANDOFF.md](TEAM_HANDOFF.md). Open the cloned folder in Antigravity,
paste the prompt below, and submit the finished work as a pull request into
`main`.

---

Build the Streamlit interface for our college project, Smart City Emergency
Response Coordinator. The core already exists. Inspect README.md and read
CONTRACT.md fully before editing. Import the existing functions from core;
do not recreate the algorithms or vehicle selection.

Your files: app.py, ui/, and requirements-ui.txt. Do not edit core/, data/,
tests/, CONTRACT.md, or requirements.txt. Report any suspected core bug with a
reproducible example to Laptop 1.

Use Python, Streamlit, Folium, and streamlit-folium. Add requirements-ui.txt
with `-r requirements.txt` plus the UI dependencies. Give exact setup/run
commands. The core is ready, so use real function results immediately.

Implement:

1. A compact dashboard with incident type and location selectors.
2. A vehicle table and controls for changing vehicle availability.
3. Road blocking controls displaying road id and endpoint names.
4. A "Find response vehicle" button using select_vehicle. Label this a
   simulation preview; selection does not reserve or move a vehicle.
5. A Folium map with named locations, available/unavailable vehicle markers,
   incident marker, blocked roads, and the selected UCS route. Draw route
   segments along the sample graph edges; no external routing API is needed.
6. Selected vehicle, total distance in km, and readable route location names.
7. A comparison table for BFS, DFS, UCS, and A*, all from the selected vehicle's
   location to the same incident. Include distance, nodes_expanded, runtime_ms,
   and route. Explain BFS/DFS limitations from CONTRACT.md. Comparisons must
   never change dispatch selection.
8. Friendly messages for no_suitable_vehicle and no_reachable_vehicle; handle
   ValueError without displaying a crash to the user.
9. Session-state persistence of edits across reruns and a Reset demo button.
   Rebuild the graph after road changes. Clear or recompute old results when
   incident, availability, or blocking changes, so routes never become stale.

Use load_sample_data() as the source of truth. L20 is deliberately isolated.
Medical incident L14 demonstrates why an unavailable nearby ambulance must
be ignored. Do not invent ETA, live traffic, AI-generated dispatch text, or
benchmark results. Add a short note that the city is fictional. Folium map
tiles may need internet; core calculations must work without network access.

Verify these interactions: normal dispatch; nearest ambulance unavailable;
road blocked and route recalculated; isolated L20; all suitable vehicles busy;
same source/destination; switching incident type; and reset. Run the existing
core tests after integration. Do not claim a check passed unless you ran it.

Finish with a handoff to Laptop 1 listing changed files, dependency versions,
run commands, checks actually performed, and unresolved issues. Keep your
changes within your assigned files.

## Showcase mode — Two calls come in

Give the dashboard a map-first layout. Keep incident controls in a compact
panel, use distinct vehicle and incident markers, and provide a readable
legend. Use high-contrast colors and line styles for routes and closures.

Add a multi-incident mode with an editable incident queue and a preset
`MED-1: medical at L12`, then `MED-2: medical at L16`. Use `plan_dispatch`
from core. Show nearest-first and optimized assignments side by side, with
served count, total distance, and any unserved incidents. Let the viewer
switch which plan is drawn on the map. Show a distance saving only when
both plans serve the same number of incidents, and make the covered incidents
explicit. With the preset, the optimized plan keeps AMB-02 at L16 for the
second call, so AMB-01 can handle the first.

Add a **Search replay** control only if the core provides actual search
steps. For this version, show the four real routes as selectable overlays
on the same map. Let the viewer block a road and recompute both dispatch
plans. Verify that the preset serves two incidents in both plans, and that
optimized totals 2.5404 km versus 5.7962 km before any edits.
