"""Interactive maps for the same dispatch plan and road-closure state."""
import gzip
import json
from html import escape
from pathlib import Path

import folium
import pydeck as pdk
import streamlit as st

DATA = Path(__file__).resolve().parents[1] / "data"
ROUTE_COLORS = [(41, 229, 208), (255, 188, 92), (180, 151, 250), (106, 187, 255)]
CALL = [255, 126, 86]
UNIT = [127, 242, 196]


@st.cache_data(show_spinner=False)
def city_scene():
    with gzip.open(DATA / "varanasi.scene.json.gz", "rt", encoding="utf-8") as src:
        return json.load(src)


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


def street_map(graph, data, vehicles, calls, plan, closures):
    routes, markers = overlays(graph, vehicles, calls, plan)
    center = data.get("map_center", markers[0]["position"][::-1])
    m = folium.Map(location=center, zoom_start=14, tiles="OpenStreetMap", control_scale=True)
    for r in data["roads"]:
        closed = r["blocked"] or r["id"] in closures
        if closed or not data.get("directed"):
            points = [coords(graph, r[k])[::-1] for k in ("source", "target")]
            folium.PolyLine(points, color="#e44d43" if closed else "#90a2b0",
                            weight=5 if closed else 2, dash_array="6 5" if closed else None,
                            tooltip="Closed segment" if closed else None).add_to(m)
    for route in routes:
        path = [xy[::-1] for xy in route["path"]]
        folium.PolyLine(path, weight=8, color="#213246", opacity=0.9).add_to(m)
        folium.PolyLine(path, weight=4, color="#%02x%02x%02x" % tuple(route["color"]),
                        tooltip=route["label"]).add_to(m)
    for item in markers:
        xy = item["position"][::-1]
        if item["unit"]:
            folium.CircleMarker(xy, radius=7, color="#193647", fill=True, fill_opacity=1,
                                fill_color="#%02x%02x%02x" % tuple(item["color"]),
                                tooltip=item["label"]).add_to(m)
        else:
            folium.Marker(xy, icon=folium.Icon(color="red", icon="info-sign"),
                          tooltip=escape(item["label"])).add_to(m)
    if markers:
        m.fit_bounds([item["position"][::-1] for item in markers], padding=(36, 36), max_zoom=16)
    return m


def city_deck(graph, data, vehicles, calls, plan, closures, camera, buildings):
    scene = city_scene()
    routes, markers = overlays(graph, vehicles, calls, plan)
    x, y = zip(*(item["position"] for item in markers))
    lon, lat = (min(x) + max(x)) / 2, (min(y) + max(y)) / 2
    zoom, pitch, bearing = 14.35, 45, -16
    if camera == "Ghats":
        lat, lon, zoom, pitch, bearing = 25.308, 83.0115, 16.5, 55, -32
    elif camera != "Overview":
        item = next(c for c in calls if c["id"] == camera)
        lon, lat = coords(graph, item["location_id"])
        zoom, pitch = 16.5, 50

    def polygon(layer_id, records, color):
        return pdk.Layer("PolygonLayer", id=layer_id, data=records,
                         get_polygon="polygon", get_fill_color=color, stroked=False)

    layers = [
        polygon("water", scene["water"], [28, 79, 98]),
        polygon("parks", scene["green"], [39, 77, 70]),
        pdk.Layer("PathLayer", id="streets", data=scene["streets"], get_path="path",
                  get_color="major ? [130,147,157] : [73,92,107]",
                  get_width="major ? 7 : 3", width_min_pixels=1),
    ]
    if buildings:
        layers.append(pdk.Layer("PolygonLayer", id="buildings",
            data="./app/static/varanasi-buildings.json", get_polygon="p",
            extruded=True, get_elevation="h", get_fill_color=[128, 159, 173],
            material={"ambient": 0.45, "diffuse": 0.75, "shininess": 12},
            stroked=False, pickable=False))
    closed = [{"path": [coords(graph, r[k]) for k in ("source", "target")]}
              for r in data["roads"] if r["blocked"] or r["id"] in closures]
    layers.extend([
        pdk.Layer("PathLayer", id="route-casing", data=routes, get_path="path",
                  get_color=[12, 31, 44], get_width=10, width_min_pixels=7),
        pdk.Layer("PathLayer", id="routes", data=routes, get_path="path",
                  get_color="color", get_width=5, width_min_pixels=3),
        pdk.Layer("PathLayer", id="closures", data=closed, get_path="path",
                  get_color=[255, 87, 99], get_width=7, width_min_pixels=4),
        pdk.Layer("TextLayer", id="places", data=scene["places"], get_position="position",
                  get_text="label", get_size=11, get_color=[209, 221, 226], billboard=True,
                  font_family="'Arial'"),
        pdk.Layer("ScatterplotLayer", id="markers", data=markers, get_position="position",
                  get_fill_color="color", get_line_color=[10, 33, 44], stroked=True,
                  line_width_min_pixels=2, get_radius=9, radius_min_pixels=6),
        pdk.Layer("TextLayer", id="labels", data=markers, get_position="position",
                  get_text="label", get_size=12, get_color=[255, 255, 250],
                  get_pixel_offset=[0, -17], background=True,
                  get_background_color=[15, 32, 46, 225], background_padding=[4, 2, 4, 2],
                  font_family="'Arial'", font_weight="'bold'"),
    ])
    # Keep operational marks legible above the building mesh at high pitch.
    for layer in layers:
        if layer.id in {"places", "markers", "labels", "routes", "route-casing", "closures"}:
            layer.parameters = {"depthCompare": "always", "depthWriteEnabled": False}
    return pdk.Deck(layers=layers, map_provider="maplibre", map_style="./app/static/atlas-style.json",
                    initial_view_state=pdk.ViewState(latitude=lat, longitude=lon, zoom=zoom,
                        pitch=pitch, bearing=bearing, min_zoom=13, max_zoom=19),
                    views=[pdk.View(type="MapView", controller=True, clear=True,
                                    clear_color=[0.09, 0.145, 0.20, 1])], tooltip=False)
