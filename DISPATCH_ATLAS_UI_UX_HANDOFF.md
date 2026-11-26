# Dispatch Atlas UI and UX Handoff

Use this brief to redesign Dispatch Atlas from scratch for a college competition. Dispatch Atlas is an emergency response simulation set in Varanasi. Design a polished desktop web dashboard that makes it easy to compare dispatch plans, replay vehicle movement, and see what changes when a road closes. This handoff covers the interface, interactions, and visual assets.

## Deliverables

- Three high-fidelity desktop screens at **1440 × 900**. Show Compare with the default preset, Replay in progress, and Road Closures after a closure is applied.
- One desktop empty or degraded state, such as a call waiting for an available unit.
- A **390 px mobile layout** showing how Compare adapts. Desktop is the priority.
- Editable design source or export, a design token sheet, and notes for interactions that screenshots cannot show. If implementing in the existing app, connect the screens to its current scenario state and report which browser interactions you verified.

Previous Stitch exports are mobile visual references. Use the cleaner graphite variants for their route styling, cards, and navigation. Compose a new desktop workspace around the map rather than enlarging the phone screen. Start with Compare and extend the approved layout to the other views.

## Desktop Composition

Use a compact top bar with the Dispatch Atlas wordmark, a city chooser, and a visible **Simulation** label. Place **Compare**, **Replay**, and **Road Closures** together in a consistent navigation row. Use a compact results strip or map header for the figures that matter to the current view.

At 1440 × 900, give the map approximately two-thirds of the workspace and reserve roughly 340–380 px for incident details and relevant controls. A judge should see the map, key results, first incident cards, and primary action without scrolling. Keep the primary workflow usable at 1280 × 800. At 1920 × 1080, give extra space to the map. On mobile, stack the map and panels without horizontal scrolling or clipped labels.

| Screen area | Purpose |
| --- | --- |
| Top bar | Identify the project and scenario. Include a discoverable Fleet & settings control. |
| Workspace navigation | Switch between Compare, Replay, and Road Closures while keeping scenario edits. |
| Map | Show route geometry, incident and unit markers, closures, and a compact legend. |
| Side panel | Show the current view’s primary action, incident queue, and the details needed for that action. |
| Secondary controls | Handle reset, fleet availability, and map configuration without crowding the main screen. |

## Visual Direction

Create a restrained atlas feel with graphite and slate surfaces, warm white text, and a bright, legible street map. Use teal for Optimized, amber for Nearest-first or a clearly labeled before route, and red for closures. Distinguish routes with solid and dashed lines as well as color. Preserve the visual relationship between a route, its incident card, and the relevant legend entry.

Use a clear sans serif for labels and body text. Reserve monospace for IDs or numeric readouts. Use roughly 14–16 px for standard desktop text, clear heading sizes, and generous click targets. Define colors, type sizes, spacing, radii, and focus styles as reusable tokens. Let Varanasi’s street and riverfront geometry provide the visual character. Use functional icons, concise labels, and motion that conveys what changed. Keep attribution visible and controls clear of it.

Avoid oversized banners, fake terminal readouts, decorative profile avatars, dense badge clusters, and permanently blinking indicators. Preserve visible focus, keyboard access, readable contrast, and reduced-motion behavior.

## Compare

Open on this view with the existing Varanasi preset. Overlay **Optimized** and **Nearest-first** routes on the same street map, with a legend and controls to isolate either plan. Make shared segments readable with alternate line styles. Let the user switch the active plan for incident details and playback. Make selection visible with text and styling.

Show each plan’s **calls assigned** and **total route distance** together. Show distance saved only when both plans cover the same incidents. If coverage differs, say so and keep both coverage counts visible. Use values passed by the working app for all numbers. For a design-only example, the default preset may show **2.71 km vs 4.84 km**, with **2 of 2 calls assigned** by both and **2.13 km saved**. Treat these values as sample data when presenting the mockup.

Make **Replay dispatch** the most visible next action. Keep **Add incident** easy to find. Make it clear when the street map accepts clicks for incident placement. Keep the scenario intact across views.

## Replay

Keep the map in the same position and animate assigned units along displayed routes. Put **Play/Pause**, **Restart**, and a keyboard-accessible timeline beside or directly below the map. Show selected plan, playback progress, and a summary such as **1 of 2 assigned units arrived**. Keep waiting calls visible.

Design ready, playing, paused, complete, and no-assignment states. If a unit starts at its destination, show it as arrived. Label the playback as simulated. Use playback progress and arrival counts instead of real-world arrival estimates. Offer speed controls only if they work.

## Road Closures

Keep the map and incident queue in familiar positions. Let the user select a segment on a displayed route, with a road name where available and direction when relevant. Provide clear **Apply closures** and **Remove closure** actions or a single apply control with an equally obvious way to clear the selection.

Show the closed segment in red and overlay **Before** and **With closures** routes for the same plan, calls, and fleet. Show distance and coverage for both cases. If a call becomes unassigned, highlight the loss in the results and its incident card. If the chosen closure leaves the route unchanged, say so plainly. Show a useful prompt before any closure is applied and restore the default view when the scenario is reset.

## Incident Queue and Fleet Controls

- Show incident ID, type, location when available, and a plain-text status. An assigned card shows unit ID and route distance. A waiting card explains the current state. Reserve status colors for meaningful differences.
- **Add incident** opens a compact form. Let the user choose Medical, Fire, or Police, then pick a supported landmark or click the street map. Confirm the selected location before submission and give immediate feedback afterward.
- Give **Resolve incident** a clear place in the queue. Keep the map and queue consistent after adding or resolving a call.
- Put vehicle ID, type, and availability in **Fleet & settings**. Make changes reflected in the results. Keep **Reset scenario** discoverable and make its scope clear.
- Preserve scenario edits across Compare, Replay, and Road Closures. Avoid stale annotations or selected items when a call is resolved or the scenario is reset.

## Copy and Recovery States

Keep the simulation label visible. Use real road and landmark names where available. Show data the interface can support: route distance, assigned calls, vehicle availability, closures, and replay progress. Avoid live traffic claims, unsupported arrival times, invented severity, and nonfunctional actions such as “Commit route” or “Deploy unit.”

Design for map loading, unavailable background tiles with a clear recovery message, an empty incident queue, no assignments, differing coverage, and an incident losing its route after a closure. Give each state a clear next action when one is available. The main demo should use the bundled Varanasi map without requiring a paid map account.

## Competition Demo and Acceptance Checks

A judge should be able to complete this sequence without coaching:

1. Read the two plan results and find their routes opposite the incident queue.
2. Open Replay, play and pause, then restart or scrub.
3. Open Road Closures, select a segment, apply it, and read the before-and-after outcome.
4. Remove the closure or reset the scenario for the next judge.

Confirm the three views look like the same product, the right panel fits at desktop widths, long labels wrap sensibly, and the mobile view has no horizontal overflow. Check visible keyboard focus and information that remains understandable without color. For a working implementation, verify plan selection, adding and resolving incidents, changing availability, replay, closures, and reset. For a design export, annotate how each action works and include the required state variations.
