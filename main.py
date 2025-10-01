from models import POIType, POI, Visitor,  is_close
from registry import POIRegistry

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
        "9":  ("Within radius (PQ4)", within_radius_menu),
        "10": ("Exactly on boundary",  boundary_menu),
        "11": ("Top-k POIs by distinct visitors (VQ5)", top_pois_menu),
        "12": ("Top-k visitors by distinct POIs (VQ4)", top_visitors_menu),
        "13": ("Counts: distinct visitors per POI (VQ2)", counts_per_poi_menu),
        "14": ("Counts: distinct POIs per visitor (VQ3)", counts_per_visitor_menu),
        "15": ("Coverage fairness (VQ7)", coverage_fairness_menu),
        "16": ("Delete POI (required)", delete_poi_menu),
        "17": ("[Ext] Rename attribute (with migration)", rename_attr_menu),
        "18": ("[Ext] Rename POI type", rename_type_menu),
        "19": ("Delete POI type (only if unused)", delete_type_menu),
        "0": ("Quit", None),
    }
    while True:
        print("\n=== MENU ===")
        for key in sorted(MENU.keys()):
            print(f"{key}) {MENU[key][0]}")
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

#old testing area:
# # test of our models
    # forest = POIType("forest", ["area", "protected"])
    # poi1 = POI(1, "Mangrove Forest", forest, 100, 200, {"area": 350, "protected": True})
    # samAltman = Visitor(10, "Sam Altman", "USA")

    # print(forest)
    # print(poi1)       # should show center=(100, 200) - passed without problems
    # print(samAltman)
    # print("Same object for type?", poi1.poi_type is forest)
    
    # reg = POIRegistry()
    # reg.add_type("forest", ["area", "protected"])
    # reg.add_poi(2, "Cedar Grove", "forest", 120, 220, {"area": 200, "protected": False})
    # print("Types in registry:", reg.list_types())
    # for p in reg.list_pois():
    #     print("POI in registry:", p)

    # # showing the invariant: deleting a type in use should fail gracefully!
    # try:
    #     reg.delete_type("forest")
    # except ValueError as e:
    #     print("Delete error:", e)

    # # distance demo
    # reg = POIRegistry()
    # reg.add_type("forest", ["area", "protected"])
    # p1 = reg.add_poi(100, "A", "forest", 0, 0, {})
    # p2 = reg.add_poi(101, "B", "forest", 3, 4, {})
    # d = p1.distance_to(p2)
    # print("Distance A→B:", d)                 # expect 5.0 (3-4-5 pythagorian triangle)
    # print("Close to 5.0?", is_close(d, 5.0))  # expect True

    #  # --- nearest_k demo (PQ5) ---
    # reg2 = POIRegistry()
    # reg2.add_type("forest", ["area", "protected"])
    # reg2.add_poi(200, "A", "forest", 0, 0, {})
    # reg2.add_poi(201, "B", "forest", 3, 4, {})
    # reg2.add_poi(202, "C", "forest", 10, 0, {})
    # top = reg2.nearest_k(0, 0, 2)
    # for poi, dist in top:
    #     print("Nearest:", poi.name, round(dist, 2))
    
    # # --- radius queries demo (PQ4 + boundary) ---
    # reg3 = POIRegistry()
    # reg3.add_type("forest", ["area", "protected"])
    # reg3.add_poi(300, "O", "forest", 0, 0, {})
    # reg3.add_poi(301, "P", "forest", 3, 4, {})     # distance 5 from (0,0)
    # reg3.add_poi(302, "Q", "forest", 10, 0, {})    # distance 10 from (0,0)

    # within = reg3.within_radius(0, 0, 5.0)
    # for poi, d in within:
    #     print("Within:", poi.name, round(d, 3))

    # boundary = reg3.exactly_on_boundary(0, 0, 5.0)
    # for poi, d in boundary:
    #     print("On boundary:", poi.name, round(d, 3))
    
    # # --- visit demo ---
    # reg4 = POIRegistry()
    # reg4.add_type("museum", ["tickets"])
    # pA = reg4.add_poi(400, "Natl Museum", "museum", 50, 50, {"tickets": 10})
    # vA = reg4.add_visitor(1, "Bob", "BG")
    # # --- visit demo ---
    # reg4 = POIRegistry()
    # reg4.add_type("museum", ["tickets"])
    # pA = reg4.add_poi(400, "Natl Museum", "museum", 50, 50, {"tickets": 10})
    # vA = reg4.add_visitor(1, "Bob", "BG")

    # v1 = reg4.record_visit(1, 400, "30/09/2025", rating=4.5)
    # try:
    #     v2 = reg4.record_visit(1, 400, "01-10-2025")
    # except ValueError as e:
    #     print("Visit error:", e) # invalid date format, should error
    # print("Visits for Natl Museum:", reg4.get_poi_visit_count(400))
    # print("First visit date:", v1.date)  # should print 30/09/2025
    # v1 = reg4.record_visit(1, 400, "30/09/2025", rating=4.5)
    # try:
    #     v2 = reg4.record_visit(1, 400, "01-10-2025")
    # except ValueError as e:
    #     print("Visit error:", e) # invalid date format, should error
    # print("Visits for Natl Museum:", reg4.get_poi_visit_count(400))
    # print("First visit date:", v1.date)  # should print 30/09/2025

    # # --- VQ5: top-k POIs by DISTINCT visitors ---
    # reg5 = POIRegistry()
    # reg5.add_type("park", ["benches"])
    # p1 = reg5.add_poi(501, "Oak Park", "park", 10, 10, {"benches": 5})
    # p2 = reg5.add_poi(502, "Pine Park", "park", 20, 20, {"benches": 3})
    # p3 = reg5.add_poi(503, "Maple Park", "park", 30, 30, {"benches": 2})
    # # --- VQ5: top-k POIs by DISTINCT visitors ---
    # reg5 = POIRegistry()
    # reg5.add_type("park", ["benches"])
    # p1 = reg5.add_poi(501, "Oak Park", "park", 10, 10, {"benches": 5})
    # p2 = reg5.add_poi(502, "Pine Park", "park", 20, 20, {"benches": 3})
    # p3 = reg5.add_poi(503, "Maple Park", "park", 30, 30, {"benches": 2})

    # v1 = reg5.add_visitor(11, "Ana", "BG")
    # v2 = reg5.add_visitor(12, "Ben", "RO")
    # v3 = reg5.add_visitor(13, "Cia", "GR")
    # v1 = reg5.add_visitor(11, "Ana", "BG")
    # v2 = reg5.add_visitor(12, "Ben", "RO")
    # v3 = reg5.add_visitor(13, "Cia", "GR")

    # # record visits (duplicates for same visitor+POI should NOT inflate distinct count)
    # reg5.record_visit(11, 501, "01/10/2025")
    # reg5.record_visit(12, 501, "01/10/2025")
    # reg5.record_visit(12, 501, "02/10/2025")   # same visitor revisits -> still counts once
    # reg5.record_visit(13, 502, "01/10/2025")
    # # record visits (duplicates for same visitor+POI should NOT inflate distinct count)
    # reg5.record_visit(11, 501, "01/10/2025")
    # reg5.record_visit(12, 501, "01/10/2025")
    # reg5.record_visit(12, 501, "02/10/2025")   # same visitor revisits -> still counts once
    # reg5.record_visit(13, 502, "01/10/2025")

    # top = reg5.top_k_pois_by_distinct_visitors(2)
    # for poi, cnt in top:
    #     print("Top POI:", poi.name, cnt)
    # top = reg5.top_k_pois_by_distinct_visitors(2)
    # for poi, cnt in top:
    #     print("Top POI:", poi.name, cnt)

    # # --- VQ4: top-k VISITORS by DISTINCT POIs visited ---
    # reg6 = POIRegistry()
    # reg6.add_type("site", ["tag"])
    # # --- VQ4: top-k VISITORS by DISTINCT POIs visited ---
    # reg6 = POIRegistry()
    # reg6.add_type("site", ["tag"])

    # p1 = reg6.add_poi(601, "S1", "site", 0, 0, {"tag": "a"})
    # p2 = reg6.add_poi(602, "S2", "site", 1, 1, {"tag": "b"})
    # p3 = reg6.add_poi(603, "S3", "site", 2, 2, {"tag": "c"})
    # p1 = reg6.add_poi(601, "S1", "site", 0, 0, {"tag": "a"})
    # p2 = reg6.add_poi(602, "S2", "site", 1, 1, {"tag": "b"})
    # p3 = reg6.add_poi(603, "S3", "site", 2, 2, {"tag": "c"})

    # v1 = reg6.add_visitor(21, "Ava", "BG")
    # v2 = reg6.add_visitor(22, "Bo", "RO")
    # v3 = reg6.add_visitor(23, "Cam", "GR")
    # v1 = reg6.add_visitor(21, "Ava", "BG")
    # v2 = reg6.add_visitor(22, "Bo", "RO")
    # v3 = reg6.add_visitor(23, "Cam", "GR")

    # # Ava visits S1 twice (should count once), and S2 once -> 2 distinct POIs
    # reg6.record_visit(21, 601, "01/10/2025")
    # reg6.record_visit(21, 601, "02/10/2025")
    # reg6.record_visit(21, 602, "02/10/2025")
    # # Bo visits S3 -> 1 distinct
    # reg6.record_visit(22, 603, "01/10/2025")
    # # Cam visits none
    # # Ava visits S1 twice (should count once), and S2 once -> 2 distinct POIs
    # reg6.record_visit(21, 601, "01/10/2025")
    # reg6.record_visit(21, 601, "02/10/2025")
    # reg6.record_visit(21, 602, "02/10/2025")
    # # Bo visits S3 -> 1 distinct
    # reg6.record_visit(22, 603, "01/10/2025")
    # # Cam visits none

    # top_vis = reg6.top_k_visitors_by_distinct_pois(2)
    # for v, cnt in top_vis:
    #     print("Top visitor:", v.name, cnt)

    # # --- Attribute management + PQ1 demo ---
    # reg = POIRegistry()
    # reg.add_type("museum", ["tickets"])
    # p1 = reg.add_poi(900, "City Museum", "museum", 10, 10, {"tickets": 12})
    # p2 = reg.add_poi(901, "Art Hall", "museum", 20, 20, {"tickets": 8})

    # # add a new attribute -> existing POIs get None by default
    # reg.add_attribute_to_type("museum", "open")
    # # set one value to see contrast
    # p2.values["open"] = "10:00-18:00"

    # # delete an attribute -> removed from existing POIs
    # reg.delete_attribute_from_type("museum", "tickets")

    # rows = reg.list_pois_of_type_with_values("museum")
    # for poi, vals in rows:
    #     print("PQ1:", poi.name, vals)

    # # --- PQ2 test (O(n^2)) ---

    # reg_cp_test = POIRegistry()
    # reg_cp_test.add_type("t2", [])
    # reg_cp_test.add_poi(101, "A2", "t2", 0, 0, {})
    # reg_cp_test.add_poi(102, "B2", "t2", 3, 4, {})
    # reg_cp_test.add_poi(103, "C2", "t2", 10, 0, {})
    # reg_cp_test.add_poi(104, "D2", "t2", 11, 0, {})  # 1 unit from C2

    # (pp1, pp2), dd = reg_cp_test.closest_pair_pois()
    # print("Closest pair:", pp1.name, pp2.name, round(dd, 3))

    # # --- PQ3 test: counts per type ---

    # reg_counts = POIRegistry()
    # reg_counts.add_type("museum", ["tickets"])
    # reg_counts.add_type("park", ["benches"])
    # reg_counts.add_type("gallery", [])  # will stay zero

    # reg_counts.add_poi(710, "M1", "museum", 1, 1, {"tickets": 10})
    # reg_counts.add_poi(711, "M2", "museum", 2, 2, {"tickets": 8})
    # reg_counts.add_poi(712, "P1", "park", 3, 3, {"benches": 5})

    # for name, cnt in reg_counts.counts_per_type():
    #     print("Count:", name, cnt)