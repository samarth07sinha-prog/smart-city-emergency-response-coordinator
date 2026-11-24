# Team handoff

All laptops use the [same GitHub repository](https://github.com/samarth07sinha-prog/smart-city-emergency-response-coordinator).
Read README.md for setup and CONTRACT.md before changing how the core and UI
interact. Clone the repository on a laptop that does not already have a copy:

```powershell
git clone https://github.com/samarth07sinha-prog/smart-city-emergency-response-coordinator.git
cd smart-city-emergency-response-coordinator
```

Start from an up-to-date `main` and create the branch listed for your laptop
with `git switch -c <branch>`. Push your branch and open a pull request into
`main`. Teammates with write access can push to the shared repo. Everyone else
can fork the repo and open a pull request from their fork.

## Laptop 1 — Core and integration

Branch: `codex/core-integration`. Own `core/`, `data/`, `tests/`,
`CONTRACT.md`, and `requirements.txt`.

Keep the existing routing and dispatch API stable. Reproduce and fix core
issues reported by the team. Review the UI pull request for contract
compatibility. Run `python -m unittest discover -s tests -v` and
`python -m core.demo` in the configured environment. After merging the UI,
run the integrated demo and record the checks performed and any open issues.

## Laptop 2 — Optional visual review

Run the existing dashboard, check route readability and narrow-screen layout,
and submit any visual adjustments. See [the short handoff](ANTIGRAVITY_HANDOFF.md).

## Laptop 3 — QA and demo scenarios (if available)

Branch: `codex/qa-demo`. Own `docs/QA_AND_DEMO.md`.

Run the core demo now. Test the dashboard in the integrated checkout. Cover normal dispatch, an unavailable ambulance, a blocked-road
reroute, isolated L20, all suitable vehicles busy, and reset. Record the commit
tested, steps, expected and actual results, and any reproducible bugs. Add a
short demo script. Send core issues to Laptop 1 and UI issues to Laptop 2.

## Laptop 4 — Project report (if available)

Branch: `codex/project-report`. Own `docs/PROJECT_REPORT.md` and
`docs/screenshots/`.

Explain the fictional city, dispatch rules, and what BFS, DFS, UCS, and A*
optimize. Use the existing demo or verified QA results for one example. Add
screenshots after the UI is runnable and describe the simulation's limitations.
List setup and demo steps that you have actually verified.

If only two laptops are available, Laptop 1 can take the QA and report tasks
after the interface is ready.
