#By GravityCodez
#https://github.com/GravityCodez/poi-management-system

from models import POIType, POI, Visitor,  is_close #redundand import
from registry import POIRegistry
from config import load_config_json, ConfigError

def prompt_int(msg: str) -> int:
    while True:
        s = input(msg).strip()
        try:
            return int(s)
        except ValueError:
            print("Please enter an integer.")

def prompt_str(msg: str) -> str:
    while True:
        s = input(msg).strip()
        if s:
            return s
        print("Please enter a non-empty value.")

def add_type_menu(reg: POIRegistry):
    name = prompt_str("Type name: ")
    attrs_raw = input("Attributes (comma-separated, optional): ").strip()
    attrs = [a.strip() for a in attrs_raw.split(",") if a.strip()] if attrs_raw else []
    try:
        reg.add_type(name, attrs)
        print(f"Added type '{name.lower()}' with attrs {attrs}")
    except Exception as e:
        print("Error:", e)

def add_poi_menu(reg: POIRegistry):
    poi_id = prompt_int("POI id (int): ")
    name = prompt_str("POI name: ")
    type_name = prompt_str("Type name (existing): ")
    x = prompt_int("x (0..999): ")
    y = prompt_int("y (0..999): ")
    values = {}
    try:
        p = reg.add_poi(poi_id, name, type_name, x, y, values)
        print("Added:", p)
    except Exception as e:
        print("Error:", e)

def record_visit_menu(reg: POIRegistry):
    vid = prompt_int("Visitor id (int): ")
    pid = prompt_int("POI id (existing): ")
    date = prompt_str("Date (dd/mm/yyyy): ")
    rating_raw = input("Rating (1..10, blank to skip): ").strip()
    if rating_raw:
        try:
            rating = int(rating_raw)
        except ValueError:
            print("Please enter an integer 1..10 for rating or leave blank."); return
    else:
        rating = None

    try:
        reg.record_visit(vid, pid, date, rating)
        print("Visit recorded.")
    except KeyError as e:
        msg = str(e).lower()
        if "visitor" in msg:
            # Ask details ONLY if the visitor is new
            name = prompt_str("New visitor name: ")
            nat  = prompt_str("New visitor nationality (2 letters ok): ")
            try:
                reg.add_visitor(vid, name, nat)
                reg.record_visit(vid, pid, date, rating)
                print("Visitor created and visit recorded.")
            except Exception as e2:
                print("Error:", e2)
        else:
            # e.g., unknown POI id
            print("Error:", e)
    except ValueError as ve:
        # e.g., bad date format (must be dd/mm/yyyy)
        print("Error:", ve)


def counts_menu(reg: POIRegistry):
    for name, cnt in reg.counts_per_type():
        print("Count:", name, cnt)

def nearest_k_menu(reg: POIRegistry):
    x = prompt_int("x (0..999): ")
    y = prompt_int("y (0..999): ")
    k = prompt_int("k (>0): ")
    results = reg.nearest_k(x, y, k)
    for poi, dist in results:
        print(f"Nearest: {poi.name} ({poi.id}) dist={round(dist, 3)}")

def list_pois_type_menu(reg: POIRegistry):
    tname = prompt_str("Type name: ")
    rows = reg.list_pois_of_type_with_values(tname)
    if not rows:
        print("No POIs for that type (or unknown type).")
        return
    for poi, vals in rows:
        print(f"{poi.id}\t{poi.name}\tcenter={poi.coord}\t{vals}")

#visitor history menu
def list_visitor_history_menu(reg: POIRegistry):
    vid = prompt_int("Visitor id: ")
    try:
        rows = reg.list_visited_pois_for_visitor(vid)
    except KeyError as e:
        print("Error:", e); return
    if not rows:
        print("No visits for this visitor yet.")
        return
    for pid, pname, date in rows:
        print(f"{date}\t{pid}\t{pname}")

#good handler that turned out ot be VERY useful
def prompt_yesno(msg: str) -> bool:
    while True:
        s = input(msg + " [y/n]: ").strip().lower()
        if s in ("y", "yes"): return True
        if s in ("n", "no"): return False
        print("Please type y or n.")

def visitors_for_poi_menu(reg: POIRegistry):
    pid = prompt_int("POI id: ")
    distinct = prompt_yesno("Distinct visitors only?")
    try:
        rows = reg.list_visitors_for_poi(pid, distinct=distinct)
    except KeyError as e:
        print("Error:", e); return
    if not rows:
        print("No visits for that POI yet."); return
    for date, vid, name, nat in rows:
        print(f"{date}\t{vid}\t{name}\t{nat}")

def top_pois_menu(reg: POIRegistry):
    k = prompt_int("k (>0): ")
    rows = reg.top_k_pois_by_distinct_visitors(k)
    if not rows:
        print("No results (need recorded visits)."); return
    for poi, cnt in rows:
        print(f"{poi.id}\t{poi.name}\t{cnt} distinct visitors")

def top_visitors_menu(reg: POIRegistry):
    k = prompt_int("k (>0): ")
    rows = reg.top_k_visitors_by_distinct_pois(k)
    if not rows:
        print("No results (need recorded visits)."); return
    for v, cnt in rows:
        print(f"{v.id}\t{v.name}\t{cnt} distinct POIs")

def counts_per_poi_menu(reg: POIRegistry):
    rows = reg.counts_distinct_visitors_per_poi()
    if not rows:
        print("No POIs yet."); return
    for p, cnt in rows:
        print(f"{p.id}\t{p.name}\t{cnt} distinct visitors")

def counts_per_visitor_menu(reg: POIRegistry):
    rows = reg.counts_distinct_pois_per_visitor()
    if not rows:
        print("No visitors yet."); return
    for v, cnt in rows:
        print(f"{v.id}\t{v.name}\t{cnt} distinct POIs")

def coverage_fairness_menu(reg: POIRegistry):
    m = prompt_int("Minimum DISTINCT POIs (m): ")
    t = prompt_int("Minimum DISTINCT TYPES (t): ")
    try:
        rows = reg.visitors_meeting_coverage(m, t)
    except ValueError as e:
        print("Error:", e); return
    if not rows:
        print("No visitors meet the thresholds."); return
    for v, pois, types in rows:
        print(f"{v.id}\t{v.name}\tpois={pois}\ttypes={types}")
def counts_per_poi_menu(reg: POIRegistry):
    rows = reg.counts_distinct_visitors_per_poi()
    if not rows:
        print("No POIs yet."); return
    for p, cnt in rows:
        print(f"{p.id}\t{p.name}\t{cnt} distinct visitors")

def counts_per_visitor_menu(reg: POIRegistry):
    rows = reg.counts_distinct_pois_per_visitor()
    if not rows:
        print("No visitors yet."); return
    for v, cnt in rows:
        print(f"{v.id}\t{v.name}\t{cnt} distinct POIs")

def coverage_fairness_menu(reg: POIRegistry):
    m = prompt_int("Minimum DISTINCT POIs (m): ")
    t = prompt_int("Minimum DISTINCT TYPES (t): ")
    try:
        rows = reg.visitors_meeting_coverage(m, t)
    except ValueError as e:
        print("Error:", e); return
    if not rows:
        print("No visitors meet the thresholds."); return
    for v, pois, types in rows:
        print(f"{v.id}\t{v.name}\tpois={pois}\ttypes={types}")

#Spatial queries from PQ4
def within_radius_menu(reg: POIRegistry):
    x = prompt_int("x (0..999): ")
    y = prompt_int("y (0..999): ")
    r_str = prompt_str("radius (float): ")
    try:
        r = float(r_str)
    except ValueError:
        print("Please enter a number for radius."); return
    results = reg.within_radius(x, y, r)
    if not results:
        print("No POIs within radius.")
        return
    for poi, dist in results:
        print(f"Within: {poi.name} ({poi.id}) dist={round(dist, 3)}")

def boundary_menu(reg: POIRegistry):
    x = prompt_int("x (0..999): ")
    y = prompt_int("y (0..999): ")
    r_str = prompt_str("radius (float): ")
    try:
        r = float(r_str)
    except ValueError:
        print("Please enter a number for radius."); return
    results = reg.exactly_on_boundary(x, y, r)
    if not results:
        print("No POIs exactly on boundary.")
        return
    for poi, dist in results:
        print(f"On boundary: {poi.name} ({poi.id}) dist={round(dist, 3)}")
#Bug N2: fix for POI deletion 
def delete_poi_menu(reg: POIRegistry):
    pid = prompt_int("POI id to delete: ")
    ok = reg.delete_poi(pid)
    print("Deleted." if ok else "No such POI.")

def delete_type_menu(reg: POIRegistry):
    t = prompt_str("Type name to delete: ")
    try:
        ok = reg.delete_type(t)
        print("Deleted." if ok else "No such type.")
    except ValueError as e:
        print("Error:", e)  # e.g., "type is used by existing POIs"

def rename_attr_menu(reg: POIRegistry):
    t = prompt_str("Type name: ")
    old = prompt_str("Old attribute: ")
    new = prompt_str("New attribute: ")
    try:
        reg.rename_attribute_on_type(t, old, new)
        print("Attribute renamed.")
    except Exception as e:
        print("Error:", e)

def rename_type_menu(reg: POIRegistry):
    old = prompt_str("Old type name: ")
    new = prompt_str("New type name: ")
    try:
        reg.rename_poi_type(old, new)
        print("Type renamed.")
    except Exception as e:
        print("Error:", e)

#JSON Loading config menu
def load_config_menu(reg: POIRegistry):
    path = prompt_str("Path to JSON file: ")
    try:
        load_config_json(path, reg)
        print("Config loaded.")
    except ConfigError as e:
        print("Config error:", e)

def main():
    reg = POIRegistry()
    MENU = {
        "1": ("Add POI type", add_type_menu),
        "2": ("Add POI", add_poi_menu),
        "3": ("Record visit (dd/mm/yyyy)", record_visit_menu),
        "4": ("Counts per type", counts_menu),
        "5": ("Nearest-k", nearest_k_menu),
        "6": ("List POIs of a type", list_pois_type_menu),
        "7": ("Visitor history", list_visitor_history_menu),
        "8": ("Visitors for a POI", visitors_for_poi_menu),
        "9":  ("Within radius", within_radius_menu),
        "10": ("Exactly on boundary",  boundary_menu),
        "11": ("Top-k POIs by distinct visitors", top_pois_menu),
        "12": ("Top-k visitors by distinct POIs", top_visitors_menu),
        "13": ("Counts: distinct visitors per POI", counts_per_poi_menu),
        "14": ("Counts: distinct POIs per visitor", counts_per_visitor_menu),
        "15": ("Coverage fairness", coverage_fairness_menu),
        "16": ("Delete POI", delete_poi_menu),
        "17": ("[Ext] Rename attribute", rename_attr_menu),
        "18": ("[Ext] Rename POI type", rename_type_menu),
        "19": ("Delete POI type (only if unused)", delete_type_menu),
        "20": ("Load config from JSON (optional)", load_config_menu),
        "0": ("Quit", None),
    }
    while True:
        print("\n=== MENU ===")
        # show numeric order and put Quit last
        keys = sorted((k for k in MENU if k != "0"), key=int) + ["0"]
        for k in keys:
            print(f"{k}) {MENU[k][0]}")

        choice = input("Choose: ").strip()
        if choice == "0":
            print("And with that, our demo comes to an end, goodnight!"); break
        action = MENU.get(choice)
        if not action:
            print("Unknown choice.")
            continue
        action[1](reg)

if __name__ == "__main__":
    main()