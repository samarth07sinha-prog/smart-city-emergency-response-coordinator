"""Presentation helpers shared by the Dispatch Atlas workspaces."""

from html import escape
from pathlib import Path

import streamlit as st


STYLE = Path(__file__).with_name("workspace.css")
WORKSPACES = {
    "Compare": (
        "Compare plans",
        "Compare dispatch plans",
        "See how far vehicles drive and which calls each plan covers.",
    ),
    "Replay": (
        "Replay",
        "Replay dispatch routes",
        "Watch the selected plan unfold. Play the dispatch or drag the timeline to jump ahead.",
    ),
    "Road Closures": (
        "Road closures",
        "Test road closures",
        "Close a street segment and compare the rerouted plan with the original.",
    ),
}


def heading():
    st.html(STYLE)
    st.html(
        '<a class="atlas-skip" href="#atlas-workspace">Skip to workspace</a>'
        '<a class="atlas-brand" href="./app/static/landing/index.html" target="_self">'
        '<span class="atlas-mark" aria-hidden="true"></span>Dispatch Atlas</a>'
        """<script type="module">
        const metadata = {
          description: "Compare, replay and test emergency dispatch plans on Varanasi’s roads.",
          "og:title": "Dispatch Atlas",
          "og:description": "Explore emergency dispatch plans in Varanasi.",
          "og:image": new URL("./app/static/landing/share.jpg", location.href).href,
          "twitter:card": "summary_large_image",
          "theme-color": "#18191b"
        };
        for (const [name, content] of Object.entries(metadata)) {
          const key = name.startsWith("og:") ? "property" : "name";
          if (document.head.querySelector(`meta[${key}="${name}"]`)) continue;
          const meta = document.createElement("meta");
          meta.setAttribute(key, name);
          meta.content = content;
          document.head.append(meta);
        }
        if (!document.documentElement.classList.contains("m-enter")) {
          const enter = document.createElement("script");
          enter.textContent = "document.documentElement.classList.add('m-enter');"
            + "setTimeout(() => document.documentElement.classList.add('m-enter-done'), 700);";
          document.head.append(enter);
        }
        </script>""",
        unsafe_allow_javascript=True,
    )


def hero(workspace, city, calls, vehicles):
    _, title, description = WORKSPACES[workspace]
    call_label = "call" if calls == 1 else "calls"
    vehicle_label = "vehicle" if vehicles == 1 else "vehicles"
    st.html(
        '<section class="atlas-hero hero" data-enter aria-labelledby="atlas-workspace">'
        '<div class="hero__c">'
        f'<p class="atlas-context">{escape(city)} · {calls} {call_label} · {vehicles} {vehicle_label}</p>'
        f'<h1 id="atlas-workspace" tabindex="-1">{escape(title)}</h1>'
        f'<p class="hero__lead">{escape(description)}</p>'
        '</div></section>'
        '<script type="module">'
        'const {init} = await import("./app/static/landing/assets/motion/motion.js");'
        'init();'
        '</script>',
        unsafe_allow_javascript=True,
    )


def panel_title(title, detail=""):
    description = f"<p>{escape(detail)}</p>" if detail else ""
    st.html(f'<div class="atlas-panel-title"><h2>{escape(title)}</h2>{description}</div>')


def metrics(items):
    stats = []
    for label, value, detail, tone in items:
        count = " data-count" if any(character.isdigit() for character in value) else ""
        stats.append(
            f'<div class="atlas-stat" data-tone="{tone}">'
            f'<span>{escape(label)}</span><strong{count}>{escape(value)}</strong>'
            f'<small>{escape(detail)}</small></div>'
        )
    st.html(
        '<div class="atlas-metrics" data-moment="counter-rolls">' + "".join(stats) + '</div>'
        '<script type="module">'
        'const row = document.querySelector(".atlas-metrics[data-moment]");'
        'if (row) {'
        '  window.__momentsManual = true;'
        '  const {mount} = await import("./app/static/landing/assets/moments/moments.js");'
        '  await mount(row);'
        '}'
        '</script>',
        unsafe_allow_javascript=True,
    )


def summary(plans, calls, active_mode, closure=False):
    optimized, greedy = plans["optimized"], plans["greedy"]
    diff = greedy["total_distance_km"] - optimized["total_distance_km"]
    same_calls = set(optimized["unassigned_incident_ids"]) == set(greedy["unassigned_incident_ids"])
    if not same_calls:
        result = ("Coverage changed" if closure else "Different coverage", "Compare the calls assigned")
    elif closure:
        result = (f"{diff:+.2f} km" if abs(diff) >= 0.005 else "0.00 km", "Same calls covered")
    elif diff > 0.005:
        percent = 100 * diff / greedy["total_distance_km"]
        result = (f"{diff:.2f} km", f"{percent:.0f}% less driving · same calls covered")
    else:
        result = ("0.00 km", "No distance difference")
    labels = ("Before closures", "With closures") if closure else ("Optimized", "Nearest-first")
    tones = ("neutral", "teal") if closure else ("teal", "amber")
    rows = []
    for label, plan, tone in zip(labels, (optimized, greedy), tones):
        detail = f"{plan['served_count']} of {len(calls)} calls assigned"
        if not closure and label == active_mode:
            detail += " · Selected"
        rows.append((label, f"{plan['total_distance_km']:.2f} km", detail, tone))
    label = ("Distance change" if closure else "Distance saved") if same_calls else "Coverage"
    rows.append((label, *result, "accent"))
    metrics(rows)


def queue_item(call, assignment, color, location, before=None, compare=False):
    detail = (f'{assignment["vehicle_id"]} · {assignment["distance_km"]:.2f} km'
              if assignment else "Waiting for a compatible, reachable unit")
    status = "Assigned" if assignment else "Unassigned"
    change = ""
    if compare:
        if before and assignment:
            if before["route"] == assignment["route"] and before["vehicle_id"] == assignment["vehicle_id"]:
                change = "Route unchanged"
            else:
                change = f'Previously {before["vehicle_id"]} · {before["distance_km"]:.2f} km'
        elif before:
            change = "Previously assigned · coverage lost"
        elif assignment:
            change = "Previously unassigned"
    st.html(f'<div class="call-row" style="--route:{color}"><b>{escape(call["id"])}'
            f' · {escape(call["type"].title())}</b>'
            f'<span class="call-status{"" if assignment else " waiting"}">{status}</span>'
            f'<strong class="location">{escape(location)}</strong>'
            f'<span class="call-detail">{escape(detail)}</span>'
            + (f'<span class="call-detail">{escape(change)}</span>' if change else "") + '</div>')
