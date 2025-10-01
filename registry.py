from __future__ import annotations
import math
from typing import Dict, List, Set

from models import (
    POIType, POI, Visitor, Visit,
    _check_coord, is_close
)


class POIRegistry:
    def __init__(self):
        self._types: Dict[str, POIType] = {}   # key: lowercase type name -> POIType
        self._pois: Dict[int, POI] = {}        # key: poi_id -> POI
        self._used_poi_ids: set[int] = set()   # enforces “ID non-reuse” (brief)
        self._visitors: Dict[int, Visitor] = {}
        self._visits: list[Visit] = []

    # --- Types ---
    def add_type(self, name: str, attributes: List[str] | None = None) -> POIType:
        key = name.strip().lower()
        if not key:
            raise ValueError("Type name cannot be empty(Come on, you can do better than this!)")
        if key in self._types:
            raise ValueError(f"POI type '{name}' already exists!!!")
        t = POIType(name=key, attributes=list(attributes or []))
        self._types[key] = t
        return t

    def delete_type(self, name: str) -> bool:
        key = name.strip().lower()
        t = self._types.get(key)
        if not t:
            return False
        # brief constraint: can only delete if unused
        if any(p.poi_type is t for p in self._pois.values()):
            raise ValueError(f"Cannot delete type '{name}': this type is used by existing POIs")
        del self._types[key]
        return True

    def list_types(self) -> List[str]:
        return sorted(self._types.keys())
    
    def nearest_k(self, x: int, y: int, k: int):
        # PQ5: k POIs closest to c0 = (x, y) by Euclidean distance
        x, y = _check_coord(x, y)           # grid is 1000x1000, integer coords
        if k <= 0:
            return []
        items = []
        for p in self._pois.values():
            px, py = p.coord                # use POI center
            d = math.hypot(px - x, py - y)  # same distance formula
            items.append((d, p.id, p.name, p))
        items.sort(key=lambda t: (t[0], t[1], t[2]))  # expectable tie-break: distance, id, name
        return [(p, d) for (d, _id, _name, p) in items[:k]]
    
    def within_radius(self, x: int, y: int, r: float):
        # PQ4: POIs with distance <= r from (x, y), using epsilon-aware comparison
        x, y = _check_coord(x, y)
        if r < 0:
            return []
        items = []
        for p in self._pois.values():
            px, py = p.coord
            d = math.hypot(px - x, py - y)
            if d < r or is_close(d, r):          # include boundary
                items.append((d, p.id, p.name, p))
        items.sort(key=lambda t: (t[0], t[1], t[2]))  # deterministic ordering
        return [(p, d) for (d, _id, _name, p) in items]

    def exactly_on_boundary(self, x: int, y: int, r: float):
        # Boundary-only: distance == r, judged with epsilon
        x, y = _check_coord(x, y)
        if r < 0:
            return []
        hits = []
        for p in self._pois.values():
            px, py = p.coord
            d = math.hypot(px - x, py - y)
            if is_close(d, r):
                hits.append((d, p.id, p.name, p))
        hits.sort(key=lambda t: (t[0], t[1], t[2]))
        return [(p, d) for (d, _id, _name, p) in hits]
    # --- POIs ---
    def add_poi(self, poi_id: int, name: str, type_name: str,
                x: int, y: int, values: Dict[str, object] | None = None) -> POI:
        if poi_id in self._used_poi_ids:
            raise ValueError(f"POI id {poi_id} was used before and cannot be reused once again")
        key = type_name.strip().lower()
        if key not in self._types:
            raise KeyError(f"Unknown POI type '{type_name}'")
        t = self._types[key]
        p = POI(poi_id, name, t, x, y, values)
        self._pois[p.id] = p
        self._used_poi_ids.add(p.id)
        return p

    def list_pois(self) -> List[POI]:
        return list(self._pois.values())
    
    # --- Visitors & Visits ---
    # --- Visitors ---
    def add_visitor(self, visitor_id: int, name: str, nationality: str) -> Visitor:
        if visitor_id in self._visitors:
            raise ValueError(f"Visitor id {visitor_id} already exists")
        v = Visitor(visitor_id, name, nationality)
        self._visitors[visitor_id] = v
        return v

    # --- Visits ---
    def record_visit(self, visitor_id: int, poi_id: int, date: str, rating: float | None = None) -> Visit:
        v = self._visitors.get(visitor_id)
        if v is None:
            raise KeyError(f"Unknown visitor id {visitor_id}")
        p = self._pois.get(poi_id)
        if p is None:
            raise KeyError(f"Unknown poi id {poi_id}")
        visit = Visit(v, p, date, rating)
        self._visits.append(visit)
        return visit

    def top_k_pois_by_distinct_visitors(self, k: int):
        """Return [(POI, distinct_visitor_count)] for the top-k POIs.
        Tie-breaks: higher count first, then lower id, then name A→Z, errored multiple times...
        """
        if k <= 0:
            return []
        # Build poi_id -> set(visitor_ids) for DISTINCT!!! counting by convention
        distinct: Dict[int, set[int]] = {}
        for vis in self._visits:
            pid = vis.poi.id
            vid = vis.visitor.id
            distinct.setdefault(pid, set()).add(vid)

        rows = []
        for pid, vids in distinct.items():
            p = self._pois.get(pid)
            if p is None:
                continue
            cnt = len(vids)
            # sort by (-cnt, id, name) so largest first, deterministic ties
            rows.append((-cnt, p.id, p.name, p, cnt))

        rows.sort(key=lambda t: (t[0], t[1], t[2]))
        return [(p, cnt) for (_nc, _id, _nm, p, cnt) in rows[:k]]

    def top_k_visitors_by_distinct_pois(self, k: int):
        #same rules as above, but for visitors
        if k <= 0:
            return []
        distinct: Dict[int, set[int]] = {}
        for vis in self._visits:
            vid = vis.visitor.id
            pid = vis.poi.id
            distinct.setdefault(vid, set()).add(pid)

        rows = []
        for vid, pids in distinct.items():
            v = self._visitors.get(vid)
            if v is None:
                continue
            cnt = len(pids)
            rows.append((-cnt, v.id, v.name, v, cnt))  # sort key pieces + payload

        rows.sort(key=lambda t: (t[0], t[1], t[2]))
        return [(v, cnt) for (_nc, _id, _nm, v, cnt) in rows[:k]]


    def get_poi_visit_count(self, poi_id: int) -> int:
        return sum(1 for vis in self._visits if vis.poi.id == poi_id)

