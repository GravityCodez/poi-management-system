from __future__ import annotations
from typing import Dict, List, Tuple
import math

MAP_SIZE = 1000  # 1000 x 1000 grid fixed
EPS = 1e-9

def is_close(a: float, b: float, eps: float = EPS) -> bool:
    return abs(a - b) <= eps

def _check_coord(x: int, y: int) -> Tuple[int, int]:
    # keep coords integers and inside [0, MAP_SIZE)
    if not (isinstance(x, int) and isinstance(y, int)):
        raise TypeError("Coordinates must be integers")
    if not (0 <= x < MAP_SIZE and 0 <= y < MAP_SIZE):
        raise ValueError(f"Coordinates must be in [0, {MAP_SIZE})")
    return x, y

class POIType:
    """Defines a type (e.g., 'forest') and its attribute names."""
    def __init__(self, name: str, attributes: List[str] | None = None):
        self.name = name
        self.attributes = list(attributes or [])

    def __str__(self) -> str:
        return f"POIType(name={self.name}, attrs={self.attributes})"

class POI:
    """A POI has an id, name, TYPE, and a *center* location (x,y)."""
    def __init__(self, poi_id: int, name: str, poi_type: POIType, x: int, y: int,
                 values: Dict[str, object] | None = None):
        self._id = poi_id            # immutable by convention
        self._name = name            # immutable by convention
        self._x, self._y = _check_coord(x, y)  # store *center* only
        self.poi_type = poi_type
        self.values = dict(values or {})  # attribute -> value

    # read-only accessors (simple encapsulation per slides)
    @property
    def id(self) -> int: return self._id
    @property
    def name(self) -> str: return self._name
    @property
    def coord(self) -> Tuple[int, int]: return (self._x, self._y)

    def distance_to(self, other: "POI") -> float:
        dx = self._x - other._x
        dy = self._y - other._y
        return math.hypot(dx, dy) # distance formula by a samrt math library

    def __str__(self) -> str:  # pretty printing like your dunder example
        return f"POI(id={self.id}, name={self.name}, type={self.poi_type.name}, center={self.coord})"

class Visitor:
    def __init__(self, visitor_id: int, name: str, nationality: str):
        self.id = visitor_id
        self.name = name
        self.nationality = nationality

    def __str__(self) -> str:
        return f"Visitor(id={self.id}, name={self.name}, nationality={self.nationality})"
    

# --- POIRegistry: so-fish-ticated(sorry for poor humor) manager for types & POIs ---


class POIRegistry:
    def __init__(self):
        self._types: Dict[str, POIType] = {}   # key: lowercase type name -> POIType
        self._pois: Dict[int, POI] = {}        # key: poi_id -> POI
        self._used_poi_ids: set[int] = set()   # enforces “ID non-reuse” (brief)

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
