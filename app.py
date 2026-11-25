"""Run with python -m streamlit run app.py."""

import streamlit as st
from streamlit_folium import st_folium

from core import build_graph, find_route, load_sample_data, load_varanasi_data, plan_dispatch
from core.graph import straight_line_km
from ui.maps import city_deck, city_scene, street_map
from ui.theme import comparison_table, heading, queue_item, summary


st.set_page_config(page_title="Dispatch Atlas", layout="wide")
state = st.session_state
masthead = st.container()
network_col, strategy_col, controls_col = st.columns([1, 1.5, 1], vertical_alignment="bottom")
city = network_col.selectbox("Road network", ["Varanasi", "Sample city"], key="city_picker")
controls = controls_col.popover("Fleet & display", icon=":material/tune:", width="stretch")
reset = controls.button("Reset scenario")
if reset or state.get("active_city") != city:
    generation = state.get("generation", 0) + 1
    for key in list(state):
        if key != "city_picker":
            del state[key]
    state.generation = generation
    state.active_city = city
    state.data = load_varanasi_data() if city == "Varanasi" else load_sample_data()
    state.calls = state.data.get("showcase_incidents", [
        {"id": "MED-1", "type": "medical", "location_id": "L12"},
        {"id": "MED-2", "type": "medical", "location_id": "L16"},
    ]).copy()
    state.next_id = 3
    state.closures = set()
    state.graph = None

data = state.data
if state.graph is None:
    roads = [dict(r, blocked=r["blocked"] or r["id"] in state.closures) for r in data["roads"]]
    state.graph = build_graph(data["locations"], roads, directed=data.get("directed", False))
graph = state.graph
names = {n: a["name"] for n, a in graph.nodes(data=True)}

controls.markdown("**Available fleet**")
vehicles = [
    dict(v, available=controls.checkbox(v["id"], value=v["available"], key=f"{city}-{v['id']}"))
    for v in data["vehicles"]
]
with masthead:
    heading(city)
plans = plan_dispatch(graph, vehicles, state.calls)
mode = strategy_col.segmented_control("Dispatch strategy", ["Optimized", "Nearest-first"], default="Optimized",
                            required=True, key="strategy")
plan = plans["optimized" if mode == "Optimized" else "greedy"]
summary(plans, plan, state.calls, vehicles, active_mode=mode)

left, right = st.columns([2.45, 1], gap="medium")
with left, st.container(key="scene_panel"):
    modes = ["3D city", "Street map"] if city == "Varanasi" else ["Street map"]
    title, tools, focus = st.columns([0.85, 1.5, 1.15], vertical_alignment="bottom")
    title.subheader("City map")
    view = tools.segmented_control("Map view", modes, default=modes[0], required=True)
    nearest = None
    if view == "3D city":
        camera = focus.selectbox("Camera", ["Overview", "Ghats", *[c["id"] for c in state.calls]])
        buildings = controls.toggle("Show 3D buildings", value=True)
        deck = city_deck(graph, data, vehicles, state.calls, plan, state.closures, camera, buildings)
        st.pydeck_chart(deck, key=f"city3d-{state.generation}-{camera}", height=485,
                        alt="Varanasi street network with buildings, assigned routes, units and incidents")
        st.caption("Drag to pan · Shift-drag to rotate · Scroll to zoom. Use Street map to place a call by clicking.")
    else:
        focus.caption("Click the street map to position a new incident.")
        m = street_map(graph, data, vehicles, state.calls, plan, state.closures)
        event = st_folium(m, height=485, use_container_width=True, key=f"map-{city}-{state.generation}",
                          returned_objects=["last_clicked"])
        click = (event or {}).get("last_clicked")
        if click:
            nearest = min(graph, key=lambda n: straight_line_km(
                {"lat": click["lat"], "lon": click["lng"]}, graph.nodes[n]))
    st.html("""<div class="atlas-legend"><span><i style="background:#219a80"></i>Available unit</span>
        <span><i style="background:#ff7e56"></i>Incident</span>
        <span><i style="background:#9298a0"></i>Busy unit</span>
        <span><i style="background:#e95563"></i>Closure</span></div>""")
    if city == "Varanasi":
        st.caption("[© OpenStreetMap contributors](https://www.openstreetmap.org/copyright) · "
                   "Footprints: [Overture Maps](https://overturemaps.org/attribution/), Google, Microsoft and OSM. "
                   "Missing heights are estimated.")

with right, st.container(key="queue_panel"):
    st.subheader("Incident queue")
    assigned = {a["incident_id"]: a for a in plan["assignments"]}
    for call in state.calls:
        queue_item(call, assigned.get(call["id"]))
    if not state.calls:
        st.caption("No active calls. Add an incident below.")
    kind = st.selectbox("New call type", ["medical", "fire", "police"])
    if view == "3D city":
        places = {p["label"]: p["position"] for p in city_scene()["places"]}
        place = st.selectbox("Place near landmark", sorted(places), index=None,
                             placeholder="Choose a landmark")
        if place:
            lon, lat, _ = places[place]
            nearest = min(graph, key=lambda n: straight_line_km(
                {"lat": lat, "lon": lon}, graph.nodes[n]))
    if nearest:
        st.caption(f"Selected junction · {names[nearest]}")
    if city == "Sample city":
        nearest = st.selectbox("Call location", list(graph), index=list(graph).index(nearest)
                               if nearest else 0, format_func=names.get)
    if st.button("Add incident", disabled=nearest is None, type="primary", width="stretch"):
        state.calls.append({"id": f"CALL-{state.next_id}", "type": kind, "location_id": nearest})
        state.next_id += 1
        st.rerun()
    if state.calls:
        remove = st.selectbox("Resolve call", [c["id"] for c in state.calls])
        if st.button("Remove incident"):
            state.calls = [c for c in state.calls if c["id"] != remove]
            st.rerun()

with st.expander("Road closures and rerouting"):
    route_edges = {graph[a][b]["id"] for assignment in plan["assignments"]
                   for a, b in zip(assignment["route"], assignment["route"][1:])}
    relevant = route_edges | state.closures
    options = sorted(relevant)
    segments = {r["id"]: r for r in data["roads"] if r["id"] in relevant}
    def segment_label(edge):
        road = segments[edge]
        return f"{road.get('name', edge)} · {road['source']} → {road['target']}"
    selected = st.multiselect("Closed segments", options, default=sorted(state.closures),
                              format_func=segment_label)
    if st.button("Apply closures") and set(selected) != state.closures:
        state.closures = set(selected)
        state.graph = None
        st.rerun()

with st.expander("Compare search algorithms"):
    if plan["assignments"]:
        by_id = {a["incident_id"]: a for a in plan["assignments"]}
        route = by_id[st.selectbox("Assigned call", list(by_id))]["route"]
        rows = []
        for algorithm in ("BFS", "DFS", "UCS", "A*"):
            result = find_route(graph, route[0], route[-1], algorithm)
            rows.append({"Algorithm": algorithm, "Distance (km)": round(result["distance_km"], 3),
                         "Nodes expanded": result["nodes_expanded"],
                         "Runtime (ms)": round(result["runtime_ms"], 2)})
        comparison_table(rows)
        st.caption("BFS minimizes hops. DFS follows its traversal order. UCS and A* minimize distance.")
    else:
        st.info("Assign a reachable unit to compare routes.")
