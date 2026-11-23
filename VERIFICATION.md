# Foundation verification

Verified on 23 November 2026 with Python 3.12.10 and NetworkX 3.7.
The test environment was a separate virtual environment in the Codex workspace;
no global Python packages were changed. Follow README.md to create this
project's own .venv on either laptop.

Command: `python -m unittest discover -s tests -v`

Result: **12 tests passed**. Coverage includes weighted paths versus BFS,
vehicle availability and type, blocked-road detours, disconnected destinations,
no suitable vehicle, start equal to goal, tie resolution, input validation,
safe A* scaling, fresh data loading, and nonmutation of vehicle records.
The sample-city test compares UCS and A* with NetworkX Dijkstra for all 400
ordered location pairs (800 route comparisons, including unreachable pairs).

Command: `python -m core.demo`

Result: medical incident L14 selected AMB-01 via L01 -> L07 -> L13 -> L14,
distance 3.9344 km. The unavailable ambulance AMB-03 at L14 was ignored.

| Algorithm | Observed route distance (km) | Nodes expanded |
| --- | ---: | ---: |
| BFS | 3.9591 | 13 |
| DFS | 8.1230 | 8 |
| UCS | 3.9344 | 14 |
| A* | 3.9344 | 7 |

These values describe this sample, not a universal algorithm ranking. Runtime
is measured on each execution and is not used as a performance claim.

The Streamlit interface and map have not been built or tested. Their task is
defined in ANTIGRAVITY_HANDOFF.md. No external service or Git remote was set up.
