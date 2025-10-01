from __future__ import annotations
import math
from typing import Dict, List, Set
from datetime import datetime

from models import (
    POIType, POI, Visitor, Visit, DATE_FMT,
    _check_coord, is_close
)

EPS = 1e-9


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
        # rating must be an integer 1..10 if provided, after breaking a lot of tests...
        if rating is not None:
            # accept ints, or floats that are whole numbers (e.g., 7.0)
            if isinstance(rating, float) and rating.is_integer():
                rating = int(rating)
            if not isinstance(rating, int):
                raise ValueError("Rating must be an integer 1..10")
            if not (1 <= rating <= 10):
                raise ValueError("Rating must be an integer 1..10")
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
   
    # ---------- Attributes on a POI type ----------
    def add_attribute_to_type(self, type_name: str, attr_name: str) -> None:
        key = type_name.strip().lower()
        attr = attr_name.strip()
        t = self._types.get(key)
        if not t:
            raise KeyError(f"Unknown POI type '{type_name}'")
        if not attr:
            raise ValueError("Attribute name cannot be empty")
        if attr in t.attributes:
            raise ValueError(f"Attribute '{attr}' already exists on type '{type_name}'")
        t.attributes.append(attr)
        # migrate existing POIs of this type: default None
        for p in self._pois.values():
            if p.poi_type is t and attr not in p.values:
                p.values[attr] = None

    def delete_attribute_from_type(self, type_name: str, attr_name: str) -> bool:
        key = type_name.strip().lower()
        attr = attr_name.strip()
        t = self._types.get(key)
        if not t:
            return False
        if attr not in t.attributes:
            return False
        t.attributes.remove(attr)
        # migrate existing POIs of this type: drop the key
        for p in self._pois.values():
            if p.poi_type is t and attr in p.values:
                del p.values[attr]
        return True

    # ---------- PQ1 ----------
    def list_pois_of_type_with_values(self, type_name: str):
        """Return [(POI, {attr: value or None,...})] for the given type, in id->name order."""
        key = type_name.strip().lower()
        t = self._types.get(key)
        if not t:
            return []
        rows = []
        for p in self._pois.values():
            if p.poi_type is t:
                full = {a: p.values.get(a, None) for a in t.attributes}
                rows.append((p, full))
        # deterministic order (id, then name) per brief’s rule
        rows.sort(key=lambda r: (r[0].id, r[0].name))
        return rows

    # ---------- PQ2: closest pair of POIs (O(n^2), deterministic ties) ----------
    def closest_pair_pois(self):
        """Return ((p1, p2), distance). If <2 POIs, return None.
        Deterministic tie-break: if distances tie (within EPS), pick the pair
        with smaller (min_id, max_id), then by names A→Z.
        """
        """We considered the O(n log n) divide-and-conquer approach but 
        chose the O(n²) version for clarity and because input sizes in this assignment are small.
        We still keep deterministic tie-breakers and epsilon-aware comparisons.
        """
        pois = list(self._pois.values())
        n = len(pois)
        if n < 2:
            return None

        best_d = float("inf")
        best_pair = None

        for i in range(n):
            pi = pois[i]
            xi, yi = pi.coord
            for j in range(i + 1, n):
                pj = pois[j]
                xj, yj = pj.coord
                d = math.hypot(xi - xj, yi - yj)

                if best_pair is None or d + EPS < best_d:
                    best_d, best_pair = d, (pi, pj)
                elif is_close(d, best_d):
                    # tie-break by ids, then names (both normalized to ascending)
                    c_ids = (min(pi.id, pj.id), max(pi.id, pj.id),
                             min(pi.name, pj.name), max(pi.name, pj.name))
                    b1, b2 = best_pair
                    b_ids = (min(b1.id, b2.id), max(b1.id, b2.id),
                             min(b1.name, b2.name), max(b1.name, b2.name))
                    if c_ids < b_ids:
                        best_d, best_pair = d, (pi, pj)

        p1, p2 = best_pair
        if p1.id > p2.id:
            p1, p2 = p2, p1
        return (p1, p2), best_d
    
    # ---------- PQ3: counts per type (include zero-count types) ----------
    def counts_per_type(self):
        """Return [(type_name, count)], sorted by count desc, then name asc."""
        # start with zero for every known type
        counts: Dict[str, int] = {tname: 0 for tname in self._types.keys()}
        for p in self._pois.values():
            counts[p.poi_type.name] = counts.get(p.poi_type.name, 0) + 1
        rows = [(-cnt, name, cnt) for name, cnt in counts.items()]
        rows.sort(key=lambda t: (t[0], t[1]))  # -count then name
        return [(name, cnt) for (_neg, name, cnt) in rows] 
    
    #Visitors Query
    def list_visited_pois_for_visitor(self, visitor_id: int):
        """Return [(poi_id, poi_name, date)] for ALL recorded visits of that visitor,
        sorted by date (oldest→newest), then poi id, then name.
        """
        if visitor_id not in self._visitors:
            raise KeyError(f"Unknown visitor id {visitor_id}")
        rows = []
        for vis in self._visits:
            if vis.visitor.id == visitor_id:
                dt = datetime.strptime(vis.date, DATE_FMT)
                rows.append((dt, vis.poi.id, vis.poi.name, vis.date))
        rows.sort(key=lambda t: (t[0], t[1], t[2]))
        # strip parsed dt for output
        return [(pid, pname, date) for (_dt, pid, pname, date) in rows]
    
    def list_visitors_for_poi(self, poi_id: int, distinct: bool = False):
        """Return rows for a POI.
        If distinct=False: [(date, visitor_id, name, nationality)] sorted by date→id→name.
        If distinct=True:  [(earliest_date, visitor_id, name, nationality)] (one per visitor), id→name.
        """
        if poi_id not in self._pois:
            raise KeyError(f"Unknown poi id {poi_id}")

        if not distinct:
            rows = []
            for vis in self._visits:
                if vis.poi.id == poi_id:
                    rows.append((vis.date, vis.visitor.id, vis.visitor.name, vis.visitor.nationality))
            rows.sort(key=lambda t: (t[0], t[1], t[2]))
            return rows

        # distinct visitors: keep earliest date per visitor
        earliest = {}
        for vis in self._visits:
            if vis.poi.id == poi_id:
                vid = vis.visitor.id
                if (vid not in earliest) or (vis.date < earliest[vid][0]):  # dd/mm/yyyy safe because we kept same format
                    earliest[vid] = (vis.date, vis.visitor.name, vis.visitor.nationality)
        rows = []
        for vid, (date, name, nat) in earliest.items():
            rows.append((date, vid, name, nat))
        rows.sort(key=lambda t: (t[1], t[2]))  # id→name
        return rows
    
    # ---------- VQ2: number of DISTINCT visitors per POI (include zero-visit POIs) ----------
    def counts_distinct_visitors_per_poi(self):
        """Return [(POI, count)], sorted by count desc, then id, then name."""
        # build poi_id -> set(visitor_ids)
        distinct: Dict[int, set[int]] = {}
        for vis in self._visits:
            distinct.setdefault(vis.poi.id, set()).add(vis.visitor.id)
        rows = []
        for pid, p in self._pois.items():
            cnt = len(distinct.get(pid, set()))
            rows.append((-cnt, p.id, p.name, p, cnt))
        rows.sort(key=lambda t: (t[0], t[1], t[2]))
        return [(p, cnt) for (_nc, _id, _nm, p, cnt) in rows]

    # ---------- VQ3: number of DISTINCT POIs per visitor (include visitors with zero) ----------
    def counts_distinct_pois_per_visitor(self):
        """Return [(Visitor, count)], sorted by count desc, then id, then name."""
        # build visitor_id -> set(poi_ids)
        distinct: Dict[int, set[int]] = {vid: set() for vid in self._visitors.keys()}
        for vis in self._visits:
            distinct.setdefault(vis.visitor.id, set()).add(vis.poi.id)
        rows = []
        for vid, v in self._visitors.items():
            cnt = len(distinct.get(vid, set()))
            rows.append((-cnt, v.id, v.name, v, cnt))
        rows.sort(key=lambda t: (t[0], t[1], t[2]))
        return [(v, cnt) for (_nc, _id, _nm, v, cnt) in rows]

    # ---------- VQ7: coverage fairness ----------
    def visitors_meeting_coverage(self, m: int, t: int):
        """Visitors who visited ≥ m DISTINCT POIs across ≥ t DISTINCT TYPES.
        Return [(Visitor, poi_count, type_count)], sorted by poi_count desc,
        then type_count desc, then id, then name.
        """
        if m < 0 or t < 0:
            raise ValueError("m and t must be non-negative integers")
        poi_sets: Dict[int, set[int]] = {}
        type_sets: Dict[int, set[str]] = {}
        for vis in self._visits:
            vid = vis.visitor.id
            poi_sets.setdefault(vid, set()).add(vis.poi.id)
            type_sets.setdefault(vid, set()).add(vis.poi.poi_type.name)
        rows = []
        for vid, v in self._visitors.items():
            pois = len(poi_sets.get(vid, set()))
            types = len(type_sets.get(vid, set()))
            if pois >= m and types >= t:
                rows.append((-pois, -types, v.id, v.name, v, pois, types))
        rows.sort(key=lambda r: (r[0], r[1], r[2], r[3]))
        return [(v, pois, types) for (_np, _nt, _id, _nm, v, pois, types) in rows]


