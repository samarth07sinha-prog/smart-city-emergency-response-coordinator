# Varanasi map data

The bundled Varanasi street network and display geometry are derived from
© [OpenStreetMap contributors](https://www.openstreetmap.org/copyright).
These derived databases are available under the
[Open Data Commons Open Database License 1.0](https://opendatacommons.org/licenses/odbl/1-0/).
Both archives contain gzip-compressed JSON. Vehicle positions and incidents are fictional.

The extract covers 82.989–83.025° E and 25.292–25.328° N. The river geometry
includes the clipped outer boundary of OpenStreetMap relation 6594443.
The 3D footprint file in `static/varanasi-buildings.json` is a bounded extract
of [Overture Maps](https://overturemaps.org/attribution/) buildings, release
2026-11-18.0. The source records identify Google Open Buildings, Microsoft ML
Buildings and OpenStreetMap, each licensed ODbL-1.0 in this extract. The
footprint file is distributed under that same license. The masthead street
graphic is derived from the OSM street and water layers.

Where a building height is missing, the renderer uses three metres per
mapped floor, or nine metres if floor counts are also unavailable. Heights
are illustrative for most of the buildings.

To refresh the visual extract, save the OSM API map XML for the bounding box
and the full XML of Ganga relation 6594443. Use the Overture CLI to download
the building features for the same bounding box as GeoJSON. With the map
requirements installed, run
`python -m ui.build_scene MAP.osm RIVER.osm BUILDINGS.geojson` from the
project folder. The dashboard uses the prepared files directly at runtime.
