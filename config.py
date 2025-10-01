from __future__ import annotations
import json
from typing import Any, Dict, List
from registry import POIRegistry
from models import DATE_FMT  

class ConfigError(Exception):
    """Raised when the JSON config is invalid with a clear location path."""
    pass

def _expect(cond: bool, path: str, msg: str) -> None:
    if not cond:
        raise ConfigError(f"{path}: {msg}")

def _is_int(x: Any) -> bool:
    return isinstance(x, int) and not isinstance(x, bool)

def _is_str(x: Any) -> bool:
    return isinstance(x, str)

def _is_list(x: Any) -> bool:
    return isinstance(x, list)

def _is_dict(x: Any) -> bool:
    return isinstance(x, dict)

def load_config_json(path: str, reg: POIRegistry) -> None:
    """
    Load initial data into `reg` from a JSON file.
    The file is OPTIONAL per run — call this only if you want to preload data.

    Expected shape (keys optional; empty arrays allowed):
    {
      "types":    [ {"name": "museum", "attributes": ["tickets","open"] }, ... ],
      "pois":     [ {"id": 1, "name": "City", "type": "museum", "x": 10, "y": 10,
                     "values": {"tickets": 12, "open":"10:00-18:00"} }, ... ],
      "visitors": [ {"id": 1, "name": "Sam", "nationality": "GE"}, ... ],
      "visits":   [ {"visitor_id": 1, "poi_id": 1, "date": "01/10/2025", "rating": 7}, ... ]
    }
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError as e:
        raise ConfigError(f"$: file not found: {path}") from e
    except json.JSONDecodeError as e:
        raise ConfigError(f"$: invalid JSON (line {e.lineno}, col {e.colno}): {e.msg}") from e

    _expect(_is_dict(data), "$", "top-level must be an object")

    # ---- types ----
    types = data.get("types", [])
    _expect(_is_list(types), "$.types", "must be an array")
    for i, t in enumerate(types):
        p = f"$.types[{i}]"
        _expect(_is_dict(t), p, "must be an object")
        name = t.get("name")
        attrs = t.get("attributes", [])
        _expect(_is_str(name) and name.strip(), p + ".name", "must be a non-empty string")
        _expect(_is_list(attrs), p + ".attributes", "must be an array")
        for j, a in enumerate(attrs):
            _expect(_is_str(a) and a.strip(), f"{p}.attributes[{j}]", "must be a non-empty string")
        try:
            reg.add_type(name, [a.strip() for a in attrs])
        except Exception as e:
            raise ConfigError(f"{p}: {e}") from e

    # ---- POIs ----
    pois = data.get("pois", [])
    _expect(_is_list(pois), "$.pois", "must be an array")
    for i, po in enumerate(pois):
        p = f"$.pois[{i}]"
        _expect(_is_dict(po), p, "must be an object")
        pid = po.get("id")
        pname = po.get("name")
        ptype = po.get("type")
        x = po.get("x"); y = po.get("y")
        values = po.get("values", {})
        _expect(_is_int(pid), p + ".id", "must be an integer")
        _expect(_is_str(pname) and pname.strip(), p + ".name", "must be a non-empty string")
        _expect(_is_str(ptype) and ptype.strip(), p + ".type", "must be a non-empty string")
        _expect(_is_int(x) and _is_int(y), p + ".x/.y", "must be integers in [0, 1000)")
        _expect(_is_dict(values), p + ".values", "must be an object (attr -> value)")
        try:
            reg.add_poi(pid, pname, ptype, int(x), int(y), values)
        except Exception as e:
            raise ConfigError(f"{p}: {e}") from e

    # ---- visitors ----
    visitors = data.get("visitors", [])
    _expect(_is_list(visitors), "$.visitors", "must be an array")
    for i, vi in enumerate(visitors):
        p = f"$.visitors[{i}]"
        _expect(_is_dict(vi), p, "must be an object")
        vid = vi.get("id")
        vname = vi.get("name")
        nat = vi.get("nationality")
        _expect(_is_int(vid), p + ".id", "must be an integer")
        _expect(_is_str(vname) and vname.strip(), p + ".name", "must be a non-empty string")
        _expect(_is_str(nat) and nat.strip(), p + ".nationality", "must be a non-empty string")
        try:
            reg.add_visitor(vid, vname, nat)
        except Exception as e:
            raise ConfigError(f"{p}: {e}") from e

    # ---- visits ----
    visits = data.get("visits", [])
    _expect(_is_list(visits), "$.visits", "must be an array")
    for i, v in enumerate(visits):
        p = f"$.visits[{i}]"
        _expect(_is_dict(v), p, "must be an object")
        vid = v.get("visitor_id")
        pid = v.get("poi_id")
        date = v.get("date")
        rating = v.get("rating", None)
        _expect(_is_int(vid), p + ".visitor_id", "must be an integer")
        _expect(_is_int(pid), p + ".poi_id", "must be an integer")
        _expect(_is_str(date) and date.strip(), p + ".date", f"must be 'dd/mm/yyyy' (e.g., 01/10/2025)")
        # rating: optional; if present, must be int 1..10 (registry enforces again)
        if rating is not None and not _is_int(rating):
            raise ConfigError(f"{p}.rating: must be an integer 1..10 if provided")
        try:
            reg.record_visit(vid, pid, date, rating)
        except Exception as e:
            raise ConfigError(f"{p}: {e}") from e
