"""Rebuild the display geometry from a bounded OSM XML extract and full Ganga relation."""
import argparse
import gzip
import json
import math
import re
from pathlib import Path
from xml.etree import ElementTree as ET

from shapely.geometry import LineString, Polygon, box, shape
from shapely.ops import polygonize, unary_union

from core.varanasi import BBOX

DATA = Path(__file__).resolve().parents[1] / "data"
WINDOW = box(*BBOX)


def osm_elements(path):
    root = ET.parse(path).getroot()
    nodes = {n.get("id"): [float(n.get("lon")), float(n.get("lat"))] for n in root.findall("node")}
    return root, nodes


def tags(element):
    return {item.get("k"): item.get("v") for item in element.findall("tag")}


def rings(shape):
    if not shape.is_valid:
        shape = shape.buffer(0)
    clipped = shape.intersection(WINDOW)
    parts = getattr(clipped, "geoms", [clipped])
    for part in parts:
        if part.geom_type == "Polygon" and part.area > 1e-12:
            yield [[[round(x, 6), round(y, 6)] for x, y in ring.coords]
                   for ring in [part.exterior, *part.interiors]]


def building_height(info):
    for tag, multiplier, label in [("height", 1, "mapped height"),
                                    ("building:levels", 3, "estimated from floors")]:
        value = info.get(tag, "").strip()
        match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*(m|ft)?", value)
        if match:
            height = float(match[1]) * multiplier * (0.3048 if match[2] == "ft" else 1)
            if 0 < height < 500 and math.isfinite(height):
                return round(height, 1), label
    return 9, "illustrative height"


def write_scene(map_path, river_path, building_path, destination):
    root, nodes = osm_elements(map_path)
    result = {"water": [], "green": [], "streets": [], "places": []}
    osm_heights = {}
    for way in root.findall("way"):
        info = tags(way)
        points = [nodes[n.get("ref")] for n in way.findall("nd")]
        if len(points) < 2:
            continue
        road = info.get("highway")
        if road and info.get("area") != "yes":
            line = LineString(points).intersection(WINDOW)
            for part in getattr(line, "geoms", [line]):
                if not part.is_empty and part.geom_type == "LineString":
                    result["streets"].append({"path": list(part.coords),
                        "major": road in {"primary", "secondary", "tertiary", "trunk"}})
        if len(points) < 4 or points[0] != points[-1]:
            continue
        if info.get("building") not in (None, "no"):
            osm_heights["w" + way.get("id")] = building_height(info)
        elif info.get("natural") == "water" or info.get("leisure") in {"park", "garden"}:
            layer = "water" if info.get("natural") == "water" else "green"
            result[layer].extend({"polygon": ring} for ring in rings(Polygon(points)))

    river, coords = osm_elements(river_path)
    rel = river.find("relation[@id='6594443']")
    ways = {w.get("id"): w for w in river.findall("way")}
    lines = [LineString([coords[n.get("ref")] for n in ways[m.get("ref")].findall("nd")])
             for m in rel.findall("member") if m.get("role") == "outer"]
    for poly in polygonize(unary_union(lines)):
        result["water"].extend({"polygon": ring} for ring in rings(poly))
    chosen = {"Lahurabir", "Nai Sarak", "Sidhgiri Bagh", "Kedar Ghat", "Dasaswamedh Ghat",
              "Panchganga Ghat", "Shivala Ghat"}
    for n in root.findall("node"):
        info = tags(n)
        name = info.get("name:en", info.get("name"))
        if name in chosen:
            result["places"].append({"label": name, "position": [*nodes[n.get("id")], 12]})
            chosen.remove(name)
    buildings = []
    for feature in json.loads(building_path.read_text(encoding="utf-8"))["features"]:
        info = feature["properties"]
        if info.get("is_underground"):
            continue
        height = info.get("height")
        floors = info.get("num_floors")
        if height and height > 0:
            elevation, basis = height, "mapped height"
        elif floors and floors > 0:
            elevation, basis = floors * 3, "estimated from floors"
        else:
            elevation, basis = 9, "illustrative height"
            for source in info.get("sources", []):
                osm_id = (source.get("record_id") or "").partition("@")[0]
                if source.get("dataset") == "OpenStreetMap" and osm_id in osm_heights:
                    elevation, basis = osm_heights[osm_id]
                    break
        for polygon in rings(shape(feature["geometry"])):
            buildings.append({"p": polygon, "h": elevation})
    building_file = DATA.parent / "static" / "varanasi-buildings.json"
    building_file.parent.mkdir(exist_ok=True)
    building_file.write_text(json.dumps(buildings, separators=(",", ":")), encoding="utf-8")
    result["building_count"] = len(buildings)
    packed = json.dumps(result, separators=(",", ":")).encode()
    destination.write_bytes(gzip.compress(packed, mtime=0))
    print(f"Packed {len(buildings):,} above-ground footprint polygons")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("map", type=Path)
    parser.add_argument("river", type=Path)
    parser.add_argument("buildings", type=Path)
    args = parser.parse_args()
    write_scene(args.map, args.river, args.buildings, DATA / "varanasi.scene.json.gz")
