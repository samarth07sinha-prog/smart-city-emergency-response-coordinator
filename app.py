"""Run with python -m streamlit run app.py."""

from pathlib import Path

import streamlit as st
from streamlit_folium import st_folium

from core import build_graph, find_route, load_sample_data, load_varanasi_data, plan_dispatch
from core.graph import straight_line_km
from ui.maps import NEAREST_FIRST, OPTIMIZED, ROUTE_COLORS, load_landmarks, street_map
from ui.replay import DispatchReplay
from ui.theme import WORKSPACES, heading, hero, metrics, panel_title, queue_item, summary


st.set_page_config(
    page_title="Dispatch Atlas",
    page_icon=str(Path(__file__).with_name("static") / "landing" / "favicon.png"),
    layout="wide",
)
if st.query_params.get("view") != "simulator":
    st.html(
        '<a href="./app/static/landing/index.html">Open Dispatch Atlas</a>'
        '<script>window.location.replace("./app/static/landing/index.html");</script>',
        unsafe_allow_javascript=True,
    )
    st.stop()

state = st.session_state
steps_by_slug = {"compare": "Compare", "replay": "Replay", "closures": "Road Closures"}
slug_by_step = {step: slug for slug, step in steps_by_slug.items()}


def select_step(step):
    state.workspace = step
    st.query_params["step"] = slug_by_step[step]


with st.container(key="topbar"):
    brand, settings = st.columns([3, 1], vertical_alignment="center")
    with brand:
        heading()
    with settings.popover("Settings", icon=":material/tune:") as controls:
        city = st.selectbox("City", ["Varanasi", "Sample city"], key="city_picker")
        reset = st.button("Reset scenario", icon=":material/restart_alt:", width="stretch",
                          help="Restore the initial calls, vehicle availability and roads.")
if reset or state.get("active_city") != city:
    generation = state.get("generation", 0) + 1
    for key in list(state):
        if key != "city_picker":
            del state[key]
    if reset:
        st.query_params.pop("step", None)
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
landmarks = load_landmarks() if city == "Varanasi" else {}

controls.markdown("**Available fleet**")
vehicles = [
    dict(v, available=controls.checkbox(v["id"], value=v["available"], key=f"{city}-{v['id']}"))
    for v in data["vehicles"]
]
plans = plan_dispatch(graph, vehicles, state.calls)
intro = st.container(key="intro")
with st.container(key="workflow"):
    steps, strategy = st.columns([2, 1], vertical_alignment="bottom")
    workspace = steps.segmented_control(
        "Workspace", list(WORKSPACES),
        default=None if "workspace" in state else steps_by_slug.get(st.query_params.get("step"), "Compare"),
        format_func=lambda step: WORKSPACES[step][0],
        required=True, key="workspace", label_visibility="collapsed",
        on_change=lambda: select_step(state.workspace),
    )
    mode = strategy.segmented_control(
        "Dispatch plan", ["Optimized", "Nearest-first"], default="Optimized",
        required=True, key="strategy",
    )
plan_key = "optimized" if mode == "Optimized" else "greedy"
plan = plans[plan_key]


def apply_closures(edges):
    state.closures = set(edges)
    state.graph = None
    state.pop("closure_picker", None)
    state.notice = "Routes recalculated with the selected closures." if edges else "Road closures removed."


with intro:
    title, action = st.columns([3, 1], vertical_alignment="bottom")
    with title:
        hero(workspace, city, len(state.calls), len(vehicles))
    with action:
        if workspace == "Compare":
            st.button("Replay dispatch", icon=":material/play_arrow:", type="primary", width="stretch",
                      on_click=select_step, args=("Replay",))
        elif workspace == "Replay":
            st.button("Try a road closure", icon=":material/alt_route:", type="primary", width="stretch",
                      on_click=select_step, args=("Road Closures",))
        elif state.closures:
            st.button("Remove all closures", on_click=apply_closures, args=([],), width="stretch")
        else:
            routes = [a["route"] for a in plan["assignments"] if len(a["route"]) > 1]
            if routes:
                route = max(routes, key=len)
                middle = (len(route) - 1) // 2
                example = graph[route[middle]][route[middle + 1]]["id"]
                st.button("Try an example closure", icon=":material/block:", type="primary",
                          on_click=apply_closures, args=([example],), width="stretch")
reference = None
if workspace == "Road Closures" and state.closures:
    if "baseline_graph" not in state:
        state.baseline_graph = build_graph(data["locations"], data["roads"],
                                           directed=data.get("directed", False))
    baseline = plan_dispatch(state.baseline_graph, vehicles, state.calls)[plan_key]
    reference = ("Before closures", baseline)
if workspace == "Compare":
    summary(plans, state.calls, mode)
elif workspace == "Road Closures" and reference:
    summary({"optimized": baseline, "greedy": plan}, state.calls, mode, closure=True)
else:
    label = "Closed segments" if workspace == "Road Closures" else "Plan distance"
    value = str(len(state.closures)) if workspace == "Road Closures" else f"{plan['total_distance_km']:.2f} km"
    detail = "Open-road baseline" if workspace == "Road Closures" else "Total assigned driving"
    metrics([
        ("Calls assigned", f"{plan['served_count']}/{len(state.calls)}", mode, "teal"),
        (label, value, detail, "amber"),
        ("Units available", str(sum(vehicle["available"] for vehicle in vehicles)), f"Of {len(vehicles)} vehicles", "neutral"),
    ])

with st.container(key="board"):
    left, right = st.columns([2.35, 1], gap="medium")
with left, st.container(key="scene_panel"):
    show_routes = "Both"
    if workspace == "Compare":
        map_title, filters = st.columns([1, 1.4], vertical_alignment="center")
        with map_title:
            panel_title("Street map")
        show_routes = filters.segmented_control(
            "Visible routes", ["Both", "Optimized", "Nearest-first"],
            default="Both", required=True, key="route_visibility", label_visibility="collapsed",
        )
    else:
        panel_title("Dispatch playback" if workspace == "Replay" else "Road network")
    nearest = None
    if workspace == "Replay":
        assignments = plan["assignments"]
        moving = {a["vehicle_id"] for a in assignments}
        m = street_map(graph, data, vehicles, state.calls, plan, state.closures, moving, active_label=mode)
        m.add_child(DispatchReplay(graph, assignments))
        st.iframe(m.get_root().render(), height=510, alt="Street map with dispatch playback controls")
    else:
        if workspace == "Compare":
            other_key = "greedy" if plan_key == "optimized" else "optimized"
            other_label = "Nearest-first" if other_key == "greedy" else "Optimized"
            reference = (other_label, plans[other_key])
        focus_call = next((c for c in state.calls if c["id"] == state.get("focus_call")), None)
        focus_node = focus_call["location_id"] if focus_call else None
        m = street_map(graph, data, vehicles, state.calls, plan, state.closures, reference=reference,
                       active_label="With closures" if workspace == "Road Closures" and reference else mode,
                       show_routes=show_routes, focus_node=focus_node)
        event = st_folium(m, height=510, use_container_width=True,
                          key=f"map-{city}-{state.generation}-{workspace}-{focus_node}",
                          returned_objects=["last_clicked"])
        click = (event or {}).get("last_clicked")
        if click and (city == "Sample city" or state.get("location_method") == "Use a map click"):
            nearest = min(graph, key=lambda n: straight_line_km(
                {"lat": click["lat"], "lon": click["lng"]}, graph.nodes[n]))
        if focus_node:
            st.button("Reset map view", on_click=lambda: state.pop("focus_call", None))
    keys = ({
        "Compare": [("", "Optimized"), ("nearest", "Nearest-first")],
        "Road Closures": [("baseline", "Before closures"), ("", "With closures"), ("closed", "Closed segment")],
    }).get(workspace, [])
    if workspace != "Replay":
        if workspace == "Compare" and show_routes != "Both":
            keys = [item for item in keys if item[1] == show_routes]
        if workspace == "Compare" and state.closures:
            keys.append(("closed", "Closed segment"))
        if workspace == "Road Closures" and not reference:
            keys = [("nearest" if mode == "Nearest-first" else "", mode)]
        legend = "".join(f'<span><i class="{style}" aria-hidden="true"></i>{label}</span>' for style, label in keys)
        st.html(f'<div class="atlas-legend">{legend}</div>')

with right, st.container(key="queue_panel"):
    if workspace == "Replay" and not plan["assignments"]:
        st.warning("No vehicles are assigned. Check the incident list or make a vehicle available.")
    if workspace == "Road Closures":
        panel_title("Closure controls", "Use an example from the current routes or choose a segment.")
        options = state.closures | {graph[a][b]["id"] for assignment in plan["assignments"]
                                    for a, b in zip(assignment["route"], assignment["route"][1:])}
        segments = {r["id"]: r for r in data["roads"] if r["id"] in options}

        if not options:
            st.info("An assigned vehicle needs a route before you can close a segment on it.")

        def segment_label(edge):
            road = segments[edge]
            return f"{road.get('name', edge)} · {road['source']} → {road['target']}"

        with st.expander("Choose road segments manually"):
            selected = st.multiselect("Road segments to close", sorted(options), default=sorted(state.closures),
                                      format_func=segment_label, key="closure_picker")
            st.button("Apply closures", disabled=set(selected) == state.closures, width="stretch",
                      on_click=apply_closures, args=(selected,))
    panel_title("Emergency calls")
    if message := state.pop("notice", None):
        st.toast(message)
    assigned = {a["incident_id"]: a for a in plan["assignments"]}
    before_assignments = {a["incident_id"]: a for a in baseline["assignments"]} if workspace == "Road Closures" and reference else {}
    route_colors = {a["incident_id"]: "#%02x%02x%02x" % ROUTE_COLORS[i % len(ROUTE_COLORS)]
                    for i, a in enumerate(plan["assignments"])}
    for call in state.calls:
        current = assigned.get(call["id"])
        color = OPTIMIZED
        if workspace == "Replay":
            color = route_colors.get(call["id"], "#c49260")
        elif mode == "Nearest-first" and (workspace == "Compare" or not state.closures):
            color = NEAREST_FIRST
        location = call.get("display_location")
        if not location:
            node = call["location_id"]
            location = names[node]
            if landmarks and location.startswith("Junction "):
                distance, landmark = min(
                    (straight_line_km(graph.nodes[node], {"lat": lat, "lon": lon}), name)
                    for name, (lon, lat) in landmarks.items()
                )
                if distance <= 0.5:
                    location = f"Near {landmark}"
        queue_item(call, current, color, location,
                   before_assignments.get(call["id"]), workspace == "Road Closures" and bool(reference))
        if workspace != "Replay":
            st.button("Show on map", icon=":material/location_on:", key=f"focus-{call['id']}",
                      on_click=lambda call_id=call["id"]: state.update(focus_call=call_id))
    st.caption(f"{sum(v['available'] for v in vehicles)} of {len(vehicles)} units available")
    if not state.calls:
        st.caption("No calls yet. Add one below or reset to the demo.")
    with st.expander("Add an emergency call", icon=":material/add_location:"):
        place = None
        kind = st.selectbox("Emergency type", ["medical", "fire", "police"], format_func=str.title)
        if city == "Varanasi":
            choices = ["Choose a landmark"] if workspace == "Replay" else ["Choose a landmark", "Use a map click"]
            method = st.radio("Where is the call?", choices, horizontal=True, key="location_method")
        if city == "Varanasi" and method == "Choose a landmark":
            nearest = None
            place = st.selectbox("Landmark", sorted(landmarks), index=None,
                                 placeholder="Choose a landmark")
            if place:
                lon, lat = landmarks[place]
                nearest = min(graph, key=lambda n: straight_line_km(
                    {"lat": lat, "lon": lon}, graph.nodes[n]))
        elif city == "Varanasi" and nearest is None:
            st.caption("Click a street near the emergency. The call will use the nearest mapped junction.")
        if city == "Sample city":
            nearest = st.selectbox("Call location", list(graph), index=list(graph).index(nearest)
                                   if nearest else 0, format_func=names.get)
        if nearest:
            st.caption(f"Selected location · {place or names[nearest]}")
        if st.button("Add call", disabled=nearest is None, type="primary", width="stretch"):
            call_id = f"CALL-{state.next_id}"
            new_call = {"id": call_id, "type": kind, "location_id": nearest}
            if place:
                new_call["display_location"] = f"Near {place}"
            state.calls.append(new_call)
            state.next_id += 1
            state.notice = f"{call_id} added"
            st.rerun()
    if state.calls:
        with st.expander("Resolve an incident", icon=":material/task_alt:"):
            remove = st.selectbox("Call to resolve", [c["id"] for c in state.calls])
            if st.button("Resolve incident"):
                state.calls = [c for c in state.calls if c["id"] != remove]
                state.notice = f"{remove} resolved"
                st.rerun()

with st.expander("Technical details"):
    st.caption("Optimized plans all assignments together. Nearest-first assigns one call at a time.")
    show_details = st.checkbox("Compare the route search methods")
    if show_details and plan["assignments"]:
        by_id = {a["incident_id"]: a for a in plan["assignments"]}
        route = by_id[st.selectbox("Assigned call", list(by_id))]["route"]
        rows = []
        for algorithm in ("BFS", "DFS", "UCS", "A*"):
            result = find_route(graph, route[0], route[-1], algorithm)
            rows.append({"Algorithm": algorithm, "Distance (km)": round(result["distance_km"], 3),
                         "Nodes expanded": result["nodes_expanded"],
                         "Runtime (ms)": round(result["runtime_ms"], 2)})
        st.dataframe(rows, hide_index=True, width="stretch", column_config={
            "Distance (km)": st.column_config.NumberColumn("Distance (km)", format="%.3f"),
            "Runtime (ms)": st.column_config.NumberColumn("Time (ms)", format="%.2f"),
        })
        st.caption("BFS minimizes hops. DFS follows its traversal order. UCS and A* minimize distance.")
    elif show_details:
        st.info("Assign a reachable unit to compare routes.")

if city == "Varanasi":
    st.html('<footer class="atlas-credits"><a href="https://www.openstreetmap.org/copyright">'
            '© OpenStreetMap contributors</a></footer>')
