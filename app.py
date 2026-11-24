"""Run with python -m streamlit run app.py."""

from pathlib import Path

import folium
import streamlit as st
from streamlit_folium import st_folium

from core import build_graph, find_route, load_sample_data, load_varanasi_data, plan_dispatch
from core.graph import straight_line_km


st.set_page_config(page_title="Dispatch Atlas", layout="wide")
state = st.session_state
snapshot = Path(__file__).parent / "data" / "varanasi.local.json"
cities = ["Varanasi", "Sample city"] if snapshot.exists() else ["Sample city"]
city = st.sidebar.selectbox("Road network", cities, key="city_picker")
if not snapshot.exists():
    st.sidebar.caption("For Varanasi, install requirements-map.txt and run python -m core.varanasi.")
reset = st.sidebar.button("Reset scenario")
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

def point(node):
    return [graph.nodes[node]["lat"], graph.nodes[node]["lon"]]

st.sidebar.subheader("Available fleet")
vehicles = [
    dict(v, available=st.sidebar.checkbox(v["id"], value=v["available"], key=f"{city}-{v['id']}"))
    for v in data["vehicles"]
]
st.title("Dispatch Atlas")
st.caption(f"{city}  /  Emergency response simulation")
plans = plan_dispatch(graph, vehicles, state.calls)
cols = st.columns(3)
for col, key, label in zip(cols, ("greedy", "optimized"), ("Nearest-first", "Fleet optimum")):
    plan = plans[key]
    col.metric(label, f"{plan['total_distance_km']:.2f} km",
               f"{plan['served_count']} of {len(state.calls)} calls covered", delta_color="off")
cols[2].metric("Available units", f"{sum(v['available'] for v in vehicles)} / {len(vehicles)}")
mode = st.radio("Map assignment", ["Optimized", "Nearest-first"], horizontal=True)
plan = plans["optimized" if mode == "Optimized" else "greedy"]
m = folium.Map(location=data.get("map_center", point(state.calls[0]["location_id"])
               if state.calls else point(next(iter(graph)))), zoom_start=14, control_scale=True)
colors = ["#007e80", "#bf551a", "#604ab2", "#1e63a5"]
if city == "Sample city":
    for r in data["roads"]:
        folium.PolyLine([point(r["source"]), point(r["target"])], color="#86949c",
                        weight=2).add_to(m)
for r in data["roads"]:
    if r["blocked"] or r["id"] in state.closures:
        folium.PolyLine([point(r["source"]), point(r["target"])], color="#af2546",
                        weight=5, dash_array="6 6", tooltip="Closed segment").add_to(m)
for i, assignment in enumerate(plan["assignments"]):
    if len(assignment["route"]) > 1:
        folium.PolyLine([point(n) for n in assignment["route"]], weight=5,
                        color=colors[i % len(colors)],
                        tooltip=f"{assignment['vehicle_id']} → {assignment['incident_id']}").add_to(m)
for v in vehicles:
    folium.CircleMarker(point(v["location_id"]), radius=7, fill=True, fill_opacity=1,
                        color="#164a67" if v["available"] else "#89939b",
                        tooltip=v["id"]).add_to(m)
for call in state.calls:
    folium.Marker(point(call["location_id"]), tooltip=f"{call['id']} · {call['type']}").add_to(m)

left, right = st.columns([2, 1])
with left:
    st.caption("Pins mark calls. Circles mark units. Click the map to place a new call.")
    event = st_folium(m, height=450, use_container_width=True, key=f"map-{city}-{state.generation}",
                      returned_objects=["last_clicked"])
with right:
    st.subheader("Incident queue")
    assigned = {a["incident_id"]: a for a in plan["assignments"]}
    for call in state.calls:
        assignment = assigned.get(call["id"])
        st.markdown(f"**{call['id']}** · {call['type'].title()}")
        st.caption(f"{assignment['vehicle_id']} · {assignment['distance_km']:.2f} km"
                   if assignment else "Unassigned · no available reachable unit in this plan")
    kind = st.selectbox("New call type", ["medical", "fire", "police"])
    click = (event or {}).get("last_clicked")
    if click:
        nearest = min(graph, key=lambda n: straight_line_km(
            {"lat": click["lat"], "lon": click["lng"]}, graph.nodes[n]))
        st.caption(f"Selected junction · {names[nearest]}")
    else:
        nearest = None
    if city == "Sample city":
        nearest = st.selectbox("Call location", list(graph), index=list(graph).index(nearest)
                               if nearest else 0, format_func=names.get)
    if st.button("Add incident", disabled=nearest is None):
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
        st.dataframe(rows, hide_index=True)
        st.caption("BFS minimizes hops. DFS follows its traversal order. UCS and A* minimize distance.")
    else:
        st.info("Assign a reachable unit to compare routes.")
if city == "Varanasi":
    st.caption("Road data © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright).")
