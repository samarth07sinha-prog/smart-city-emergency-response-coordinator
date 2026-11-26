"""Interactive maps for the same dispatch plan and road-closure state."""
import json
from html import escape
from pathlib import Path

import folium
import streamlit as st

DATA = Path(__file__).resolve().parents[1] / "data"
ROUTE_COLORS = [(108, 224, 204), (255, 164, 87), (156, 212, 121), (126, 189, 255)]
CALL = [255, 126, 86]
UNIT = [127, 242, 196]
OPTIMIZED = "#6ce0cc"
NEAREST_FIRST = "#ffa457"
BASELINE = "#c3cbd0"
CLOSED = "#ff6673"


@st.cache_data(show_spinner=False)
def load_landmarks():
    return json.loads((DATA / "varanasi.landmarks.json").read_text(encoding="utf-8"))


def coords(graph, node):
    attrs = graph.nodes[node]
    return [attrs["lon"], attrs["lat"]]


def overlays(graph, vehicles, calls, plan):
    routes = [{"path": [coords(graph, n) for n in a["route"]],
               "color": list(ROUTE_COLORS[i % len(ROUTE_COLORS)]),
               "label": f"{a['vehicle_id']} → {a['incident_id']}"}
              for i, a in enumerate(plan["assignments"]) if len(a["route"]) > 1]
    markers = [{"position": coords(graph, v["location_id"]), "label": v["id"],
                "color": UNIT if v["available"] else [147, 152, 160], "unit": True}
               for v in vehicles]
    markers.extend({"position": coords(graph, c["location_id"]), "label": c["id"],
                    "color": CALL, "unit": False} for c in calls)
    return routes, markers


def street_map(graph, data, vehicles, calls, plan, closures, moving=(), reference=None,
               *, active_label="Optimized", show_routes="Both", focus_node=None):
    routes, markers = overlays(graph, vehicles, calls, plan)
    center = data.get("map_center", markers[0]["position"][::-1])
    m = folium.Map(location=center, zoom_start=14, tiles="OpenStreetMap", control_scale=True)
    map_style = folium.Element("""
        <style>
        .leaflet-container { background: #18292e; }
        .leaflet-tile-pane { filter: invert(.92) hue-rotate(170deg) saturate(.65) brightness(.68); }
        .leaflet-tooltip {
          border: 1px solid #638079; border-radius: 5px; background: #152329; color: #eff6f4;
          font: 600 12px system-ui; padding: 4px 7px;
        }
        .leaflet-control-zoom a, .leaflet-control-attribution {
          background: #152329 !important; color: #eff6f4 !important;
        }
        .leaflet-control-attribution a { color: #a9e1d5 !important; }
        .leaflet-control-zoom a:focus-visible { outline: 2px solid #ff825c; outline-offset: -3px; }
        </style>
    """)
    m.get_root().html.add_child(map_style)
    for r in data["roads"]:
        closed = r["blocked"] or r["id"] in closures
        if not closed and not data.get("directed"):
            points = [coords(graph, r[k])[::-1] for k in ("source", "target")]
            folium.PolyLine(points, color="#90a2b0", weight=2).add_to(m)
    if reference and show_routes != active_label:
        label, prior_plan = reference
        prior_routes, _ = overlays(graph, vehicles, calls, prior_plan)
        for route in prior_routes:
            path = [xy[::-1] for xy in route["path"]]
            color = {"Optimized": OPTIMIZED, "Nearest-first": NEAREST_FIRST}.get(label, BASELINE)
            folium.PolyLine(path, weight=8, color=color, opacity=0.9,
                            dash_array=None if label == "Optimized" else "12 7",
                            tooltip=f"{label}: {route['label']}").add_to(m)
    if not reference or show_routes in {"Both", active_label}:
        for route in routes:
            path = [xy[::-1] for xy in route["path"]]
            color = OPTIMIZED if active_label != "Nearest-first" else NEAREST_FIRST
            folium.PolyLine(path, weight=5,
                            color="#%02x%02x%02x" % tuple(route["color"]) if moving else color,
                            dash_array="9 6" if active_label == "Nearest-first" else None,
                            tooltip=f"{active_label}: {route['label']}").add_to(m)
    for road in data["roads"]:
        if road["id"] in closures or road["blocked"]:
            points = [coords(graph, road[k])[::-1] for k in ("source", "target")]
            folium.PolyLine(points, color=CLOSED, weight=8, dash_array="4 4",
                            tooltip="Closed segment").add_to(m)
    for item in markers:
        if item["unit"] and item["label"] in moving:
            continue
        xy = item["position"][::-1]
        if item["unit"]:
            folium.CircleMarker(xy, radius=7, color="#193647", fill=True, fill_opacity=1,
                                fill_color="#%02x%02x%02x" % tuple(item["color"]),
                                tooltip=item["label"]).add_to(m)
        else:
            folium.CircleMarker(xy, radius=9, color="#193647", weight=2.5, fill=True,
                                fill_opacity=1, fill_color="#ff7e56",
                                tooltip=folium.Tooltip(escape(item["label"]), permanent=True,
                                                       direction="right")).add_to(m)
    if focus_node:
        m.location = coords(graph, focus_node)[::-1]
        m.options["zoom"] = 16
    elif markers:
        m.fit_bounds([item["position"][::-1] for item in markers],
                     padding_top_left=(36, 150 if moving else 36),
                     padding_bottom_right=(36, 36), max_zoom=16)
    return m
