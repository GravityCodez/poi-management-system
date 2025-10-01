1) OVERVIEW
This project implements a small, menu-driven POI (Point of Interest) management system in Python,
aligned with the course OOP material. Core entities:
- POIType → a category (e.g., museum, park) with a schema of attribute names.
- POI → a concrete place with unique id, name, CENTER coordinate (x, y), a POIType, and attribute values.
- Visitor → a person who can visit POIs.
- Visit → (visitor, poi, date dd/mm/yyyy, optional rating 1..10).

The CLI supports adding types/POIs, recording visits, spatial queries, rankings, counts, deletions,
and schema updates. A JSON loader (config.py) is available but optional per run.

Global choices:
- Dates validated as dd/mm/yyyy.
- Distances computed on POI centers.
- Distinct-count semantics by default.
- Deterministic tie-breaks everywhere for stable output.
- Epsilon-aware comparisons to include boundary cases accurately.

2) HOW TO RUN
- (Optional) python -m venv .venv  → activate
- (Optional) pip install matplotlib  (only for generating docs; app itself uses stdlib)
- python main.py
Optional loader: choose "Load config from JSON (optional)" and provide a file (e.g., big_demo.json).
The loader mutates the running registry; loading the same data twice will trigger integrity errors
(e.g., id reuse), by design.

3) DATA MODEL & INVARIANTS
Classes
- POIType(name, attributes: list[str])
- POI(id, name, poi_type, x, y, values: dict) → x,y are integers in [0,1000); represent CENTER.
- Visitor(id, name, nationality)
- Visit(visitor, poi, date, rating|None) → date validated with %d/%m/%Y; rating int 1..10 if set.
- POIRegistry → orchestration + query/management operations.

Invariants & policies
- No POI id reuse: once used, an id remains reserved even after deletion.
- Delete type only if unused: cannot remove a type referenced by existing POIs.
- POI deletion preserves Visit history (historical reports remain consistent).
- Attributes per type: add/remove/rename migrates existing POIs; rename policy keeps new key if both exist.
- Tie-breaks (deterministic):
  • distances: (distance, poi.id, poi.name)
  • counts/rankings: (-count, id, name)
  • closest-pair ties: (min_id, max_id, nameA, nameB)
- Boundary epsilon: is_close(a, b) avoids excluding/on-duplication at exactly r.

4) FEATURES (CLI)
Types & attributes
- Add/Delete type (delete only when unused)
- Add/Delete/Rename attribute (with migration)
- Rename type (POIs keep same object reference)

POIs
- Add POI (center coords only; attribute value dict)
- Delete POI (history preserved)
- PQ1: list POIs of a type with full attribute dict (missing → None)
- PQ3: counts per type (include zero-count types; sorted by count↓ then name)

Visitors & visits
- Add visitor (auto-prompt if first seen during record)
- Record visit (date dd/mm/yyyy; rating int 1..10)
- VQ1: visitor history (all visits, date→id→name order)
- VQ2: visitors for a POI — full log OR distinct (earliest date per visitor)
- VQ2 counts: distinct visitors per POI (includes zero)
- VQ3: distinct POIs per visitor (includes zero)
- VQ5: top-k POIs by distinct visitors
- VQ4: top-k visitors by distinct POIs
- VQ7: coverage fairness — visitors with ≥ m DISTINCT POIs across ≥ t DISTINCT types

Spatial (centers)
- PQ5: nearest-k to a point (Euclidean)
- PQ4: within radius ≤ r (ε includes boundary)
- Boundary-only: exactly on radius r

5) TIME-COMPLEXITY DECISION (PQ2) & READABILITY
Options: O(n log n) divide-and-conquer (strip method) vs O(n²) brute-force.
Decision: O(n²) for clarity and correctness at the course scale.
Rationale:
- n is modest; O(n²) is responsive and easy to audit.
- Cleaner integration with deterministic tie-breaks and ε boundary logic.
- Saved time invested in tests, validation, CLI UX, and documentation.
We document the faster O(n log n) approach in the report to show awareness.

6) CODE QUALITY & STRUCTURE
- Multi-file:
  • models.py: core classes, helpers (date validator, is_close, coord checks)
  • registry.py: business logic + queries
  • config.py: optional JSON loader with precise error paths
  • main.py: minimal CLI, numeric menu order
- Typing & readability:
  • type hints; from __future__ import annotations for forward refs
  • @property for safe read-only attributes (e.g., POI.id, POI.coord)
  • determinstic sort keys captured consistently
- Validation & errors:
  • coords in [0,1000) ints; clear messages
  • date dd/mm/yyyy with a helpful example on error
  • rating int 1..10; non-integers or out-of-range rejected
  • loader reports path like $.visits[3].date for quick fixes
- UX polish:
  • menu sorted numerically (1..N; 0 last)
  • "Record visit" asks name/nationality only for new visitor ids
  • unambiguous messages: "Deleted.", "No such …", or specific ValueError

7) JSON CONFIG (OPTIONAL)
Shape (keys optional; empty arrays allowed). Load order: types → pois → visitors → visits.

Example
{{
  "types":    [{{"name":"museum","attributes":["tickets","open"]}}],
  "pois":     [{{"id":1,"name":"City Museum","type":"museum","x":10,"y":10,
                 "values":{{"tickets":12,"open":"10:00-18:00"}}}}],
  "visitors": [{{"id":1,"name":"Sam","nationality":"GE"}}],
  "visits":   [{{"visitor_id":1,"poi_id":1,"date":"01/10/2025","rating":7}}]
}}
Validation highlights:
- Clear ConfigError with JSONPath-like location for bad/missing fields.
- Rating, if present, must be int 1..10 (also validated in registry).
- Bad dates like 2025-10-10 produce a direct format hint.
Loader mutates the current registry, so new data is instantly visible in queries.

8) TESTING PLAN (HIGHLIGHTS)
- Date validator: accepts dd/mm/yyyy; rejects yyyy-mm-dd, etc.
- ε boundary: exactly-at-r appears in within-r and boundary-only as appropriate.
- Determinism: stable ordering in tie cases (PQ5, counts, rankings).
- Attribute migration: add/delete/rename keeps POI value maps coherent.
- Counts include zeros (types/POIs/visitors with no activity).
- Loader errors pinpoint paths (e.g., $.pois[2].x).
- POI deletion: disappears from current stats; history preserved in VQ1.
- No id reuse: re-adding old id fails with a clear message.

9) DEVELOPMENT PROCESS & GIT INSIGHTS
Commit history shows an incremental approach: feature → test → small bug fix → polish.
Examples: rating int fix, menu sort, POI deletion bugfix, visitor QoL prompt, CLI test suite.
This kept scope aligned with the brief and made behavior reproducible for the demo.

10) LESSONS LEARNED
- @property for encapsulation; type hints improve IntelliSense & reviews.
- from __future__ import annotations simplifies cross-references.
- venv is essential for reproducible environments and clean repos.
- Chose clarity (O(n²) PQ2) over cleverness; documented the faster alternative.
- Deterministic outputs + ε-aware comparisons prevent flaky demos/tests.
- Two-file core split (models/registry) kept responsibilities clean; config loader optional.

11) COMPLEXITY SUMMARY (SELECTED)
- Add type/POI/visitor: O(1) average
- Record visit: O(1)
- PQ5 nearest-k: O(n log n) + O(k)
- PQ4 within radius: O(n)
- VQ2/VQ3 counts: O(n + v) using sets
- VQ4/VQ5 top-k: O(n log n) sorting aggregated rows
- PQ2 closest pair: O(n²) by design for readability

12) FUTURE WORK
- CSV export of results, basic unit tests (unittest/pytest), optional spatial index if n grows,
  and CLI shortcuts for power users.
