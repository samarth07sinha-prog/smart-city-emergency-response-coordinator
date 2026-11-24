"""Build a local driving-network snapshot for the Varanasi simulation."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from xml.etree import ElementTree

import networkx as nx

from .graph import build_graph, straight_line_km
from .planning import plan_dispatch

CENTER = (25.310, 83.009)
BBOX = (82.989, 25.292, 83.025, 25.328)
DRIVABLE = {
    "motorway", "trunk", "primary", "secondary", "tertiary",
    "motorway_link", "trunk_link", "primary_link", "secondary_link",
    "tertiary_link", "unclassified", "residential", "living_street", "service",
}
ATTRIBUTION = "© OpenStreetMap contributors"
ATTRIBUTION_URL = "https://www.openstreetmap.org/copyright"


def make_scenario(streets: nx.MultiDiGraph) -> dict:
    locations = [
        {"id": str(node), "name": f"Junction {node}",
         "lat": float(attrs["y"]), "lon": float(attrs["x"])}
        for node, attrs in sorted(streets.nodes(data=True))
    ]
    roads = [
        {"id": f"{source}:{target}:{key}", "source": str(source),
         "target": str(target), "distance_km": float(attrs["length"]) / 1000,
         "blocked": False, "name": attrs.get("name") or "Unnamed road"}
        for source, target, key, attrs in sorted(streets.edges(keys=True, data=True))
        if source != target and attrs["length"] > 0
    ]
    graph = build_graph(locations, roads, directed=True)
    component = max(nx.strongly_connected_components(graph), key=len, default=set())
    if len(component) < 6:
        raise ValueError("Varanasi extract does not contain enough connected junctions")
    selectable = sorted(component)

    def snap(lat, lon):
        point = {"lat": lat, "lon": lon}
        return min(selectable, key=lambda node: straight_line_km(point, graph.nodes[node]))

    vehicles = [
        {"id": vehicle_id, "type": vehicle_type, "available": True,
         "location_id": snap(lat, lon)}
        for vehicle_id, vehicle_type, lat, lon in [
            ("AMB-01", "ambulance", 25.309, 82.992),
            ("AMB-02", "ambulance", 25.310, 83.014),
            ("FIRE-01", "fire_engine", 25.319, 83.004),
            ("POL-01", "police", 25.298, 83.006),
        ]
    ]
    incidents = [
        {"id": "MED-1", "type": "medical", "location_id": snap(25.308, 83.005)},
        {"id": "MED-2", "type": "medical", "location_id": snap(25.317, 83.016)},
    ]
    return {
        "city": "Varanasi", "directed": True, "map_center": list(CENTER),
        "attribution": ATTRIBUTION, "attribution_url": ATTRIBUTION_URL,
        "locations": locations, "roads": roads, "vehicles": vehicles,
        "default_incident": incidents[0], "showcase_incidents": incidents,
    }


def main():
    try:
        import osmnx as ox
    except ImportError as exc:
        raise SystemExit("Install requirements-map.txt to fetch the Varanasi streets.") from exc

    query = urlencode({"bbox": ",".join(map(str, BBOX))})
    request = Request(f"https://api.openstreetmap.org/api/0.6/map?{query}",
                      headers={"User-Agent": "SmartCityResponseCoordinator/1.0"})
    with urlopen(request, timeout=30) as response:
        xml = ElementTree.parse(response)
    root = xml.getroot()
    for item in list(root):
        if item.tag == "relation":
            root.remove(item)
        elif item.tag == "way":
            tags = {tag.attrib["k"]: tag.attrib["v"] for tag in item.findall("tag")}
            if (tags.get("highway") not in DRIVABLE or tags.get("area") == "yes"
                    or any(tags.get(key) in {"no", "private"}
                           for key in ("access", "vehicle", "motor_vehicle", "motorcar"))
                    or tags.get("service") in {"parking_aisle", "driveway", "emergency_access"}):
                root.remove(item)

    # Keep intermediate OSM nodes so routes follow the original street shapes.
    with TemporaryDirectory() as directory:
        path = Path(directory) / "streets.osm"
        xml.write(path, encoding="utf-8", xml_declaration=True)
        streets = ox.graph.graph_from_xml(path, simplify=False, retain_all=True)
    streets = ox.truncate.truncate_graph_bbox(streets, BBOX)
    scenario = make_scenario(streets)
    graph = build_graph(scenario["locations"], scenario["roads"], directed=True)
    comparison = plan_dispatch(graph, scenario["vehicles"], scenario["showcase_incidents"])
    path = Path(__file__).resolve().parent.parent / "data" / "varanasi.local.json"
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(scenario, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)
    print(f"Saved {graph.number_of_nodes()} junctions and {graph.number_of_edges()} directed links.")
    for name, plan in comparison.items():
        print(f"{name}: {plan['served_count']} calls, {plan['total_distance_km']:.2f} km")
    print(f"Road data: {ATTRIBUTION} ({ATTRIBUTION_URL})")


if __name__ == "__main__":
    main()
