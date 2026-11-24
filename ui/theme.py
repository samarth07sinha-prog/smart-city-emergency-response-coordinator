"""Dashboard typography, palette, and compact dispatch summaries."""
from html import escape

import streamlit as st

CSS = """
<style>
:root{--ink:#132a39;--muted:#506775;--line:#c9d3d3;--paper:#f7f8f3;--navy:#192e3c;--mint:#58e8be}
.stApp{background:var(--paper);color:var(--ink)}
.stMainBlockContainer{max-width:1510px;padding:2.4rem clamp(1rem,3vw,3.4rem) 3rem}
[data-testid="stHeader"]{background:transparent}
[data-testid="stSidebar"]{background:#e8eeea;border-right:1px solid var(--line)}
[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3{font-size:1.05rem}
.st-key-scene_panel,.st-key-queue_panel{border:1px solid var(--line);border-radius:14px;padding:1rem;background:#fff}
.st-key-scene_panel [data-testid="stDeckGlJsonChart"]{overflow:hidden;border-radius:9px;background:#172533}
.st-key-scene_panel iframe{border-radius:9px}
.stApp h1,.stApp h2,.stApp h3{color:var(--ink);font-family:"Segoe UI",Arial,sans-serif;letter-spacing:-.04em}
.atlas-head{display:flex;align-items:center;gap:12px;border-bottom:1px solid var(--line);padding-bottom:14px;margin-bottom:14px}
.atlas-brand{font:800 17px/1 "Segoe UI",sans-serif;letter-spacing:-.04em}
.atlas-icon{width:32px;height:32px;background:#173340;display:inline-grid;place-content:center;border-radius:9px;color:#85edc6;font:800 25px/1 monospace}
.atlas-mode{margin-left:auto;color:#45605f;font:600 12px/1.5 Consolas,monospace;display:flex;gap:8px;align-items:center}
.atlas-mode:before{content:'';width:8px;height:8px;background:#2c826e;border-radius:50%}
.atlas-title h1{font:700 clamp(36px,4vw,65px)/1.02 "Segoe UI",sans-serif;letter-spacing:-.065em;margin:0;padding:0}
.atlas-title{background:#17303e;color:white;border-radius:14px;padding:20px 26px;overflow:hidden}
.atlas-title.varanasi{background:linear-gradient(95deg,#142f3d 10%,rgba(20,47,61,.93) 39%,rgba(20,47,61,.08) 91%), url("./app/static/varanasi-masthead.png") right center / cover}
.atlas-title h1{color:#f3faf6}.atlas-title h1 em{font-weight:400;color:#9ce6d5;font-style:normal}
.atlas-title p{font-size:14px;color:#c2d9dc;margin:.4rem 0 0}
.atlas-metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:1px;background:var(--line);border:1px solid var(--line);border-radius:12px;overflow:hidden}
.atlas-stat{background:white;padding:14px 18px}.atlas-stat:first-child{background:#193441;color:white}
.atlas-stat span,.atlas-stat small{display:block}.atlas-stat span{font:650 12px/1.4 "Segoe UI",sans-serif}
.atlas-stat strong{display:block;font:650 clamp(23px,2.3vw,34px)/1.2 "Segoe UI",sans-serif;letter-spacing:-.055em;margin:3px 0}
.atlas-stat small{font-size:12px;color:var(--muted)}.atlas-stat:first-child small{color:#b4d5d0}
.call-row{padding:11px 0;border-bottom:1px solid #dce3df;color:var(--ink);line-height:1.35}
.call-row b{font:700 14px/1.4 Consolas,monospace}.call-kind{float:right;font-size:12px;color:#506775}
.call-detail{font-size:13px;margin-top:3px;color:#395564}
.atlas-legend{display:flex;flex-wrap:wrap;gap:8px 16px;font-size:12px;color:var(--muted)}
.atlas-legend i{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:5px}
@media(max-width:750px){.atlas-metrics{grid-template-columns:repeat(2,1fr)}.stMainBlockContainer{padding-top:3rem}.atlas-title h1{font-size:40px}}
</style>"""


def heading(city):
    st.html(CSS)
    st.html(f"""<header class="atlas-head"><span class="atlas-icon" aria-hidden="true">↗</span>
        <span class="atlas-brand">Dispatch Atlas</span><span class="atlas-mode">Simulation</span></header>
        <div class="atlas-title {'varanasi' if city == 'Varanasi' else ''}"><h1>{escape(city)} <em>dispatch</em></h1>
        <p>{"Central Varanasi · Ganges riverfront and old city" if city == "Varanasi" else "Fictional city · Route planning sandbox"}</p></div>""")


def summary(plans, plan, calls, vehicles):
    cards = [
        ("Fleet optimum", f'{plans["optimized"]["total_distance_km"]:.2f} km',
         f'{plans["optimized"]["served_count"]} calls covered'),
        ("Nearest-first", f'{plans["greedy"]["total_distance_km"]:.2f} km',
         f'{plans["greedy"]["served_count"]} calls covered'),
        ("Incidents covered", f'{plan["served_count"]} / {len(calls)}', "Selected plan"),
        ("Available units", f'{sum(v["available"] for v in vehicles)} / {len(vehicles)}', "Simulated fleet"),
    ]
    st.html('<section class="atlas-metrics">' + "".join(
        f'<div class="atlas-stat"><span>{label}</span><strong>{value}</strong><small>{detail}</small></div>'
        for label, value, detail in cards) + '</section>')


def queue_item(call, assignment):
    detail = (f'{assignment["vehicle_id"]} · {assignment["distance_km"]:.2f} km'
              if assignment else "Unassigned · no reachable available unit in this plan")
    st.html(f'<div class="call-row"><b>{escape(call["id"])}</b>'
            f'<span class="call-kind">{escape(call["type"].title())}</span>'
            f'<div class="call-detail">{escape(detail)}</div></div>')
