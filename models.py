from __future__ import annotations
from typing import Dict, List, Tuple
import math
from datetime import datetime

MAP_SIZE = 1000  # 1000 x 1000 grid fixed
EPS = 1e-9
DATE_FMT = "%d/%m/%Y"

def is_close(a: float, b: float, eps: float = EPS) -> bool:
    return abs(a - b) <= eps

def _check_coord(x: int, y: int) -> Tuple[int, int]:
    # keep coords integers and inside [0, MAP_SIZE)
    if not (isinstance(x, int) and isinstance(y, int)):
        raise TypeError("Coordinates must be integers")
    if not (0 <= x < MAP_SIZE and 0 <= y < MAP_SIZE):
        raise ValueError(f"Coordinates must be in [0, {MAP_SIZE})")
    return x, y

def _validate_date_ddmmyyyy(s: str) -> str:
    try:
        dt = datetime.strptime(s, DATE_FMT)  # parses dd/mm/yyyy
        # return in a zero-padded form
        return f"{dt.day:02d}/{dt.month:02d}/{dt.year:04d}"
    except ValueError:
        raise ValueError("Date must be 'dd/mm/yyyy', e.g., '16/08/2007'")
    
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
        self._x, self._y = _check_coord(x, y)  # store --->center<---- only
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

class Visit:
    def __init__(self, visitor: "Visitor", poi: "POI", date: str, rating: float | None = None):
        self.visitor = visitor
        self.poi = poi
        self.date =  _validate_date_ddmmyyyy(date) #Handle date format and validation
        self.rating = rating      # optional numeric rating

    def __str__(self) -> str:
        r = f", rating={self.rating}" if self.rating is not None else ""
        return f"Visit(visitor={self.visitor.id}, poi={self.poi.id}, date={self.date}{r})"


# --- POIRegistry: so-fish-ticated(sorry for poor humor) manager for types & POIs ---