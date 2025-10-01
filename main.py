from models import POIType, POI, Visitor, POIRegistry, is_close
from registry import POIRegistry

def main():

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
    
    # --- visit demo ---
    reg4 = POIRegistry()
    reg4.add_type("museum", ["tickets"])
    pA = reg4.add_poi(400, "Natl Museum", "museum", 50, 50, {"tickets": 10})
    vA = reg4.add_visitor(1, "Bob", "BG")

    v1 = reg4.record_visit(1, 400, "30/09/2025", rating=4.5)
    try:
        v2 = reg4.record_visit(1, 400, "01-10-2025")
    except ValueError as e:
        print("Visit error:", e) # invalid date format, should error
    print("Visits for Natl Museum:", reg4.get_poi_visit_count(400))
    print("First visit date:", v1.date)  # should print 30/09/2025

    # --- VQ5: top-k POIs by DISTINCT visitors ---
    reg5 = POIRegistry()
    reg5.add_type("park", ["benches"])
    p1 = reg5.add_poi(501, "Oak Park", "park", 10, 10, {"benches": 5})
    p2 = reg5.add_poi(502, "Pine Park", "park", 20, 20, {"benches": 3})
    p3 = reg5.add_poi(503, "Maple Park", "park", 30, 30, {"benches": 2})

    v1 = reg5.add_visitor(11, "Ana", "BG")
    v2 = reg5.add_visitor(12, "Ben", "RO")
    v3 = reg5.add_visitor(13, "Cia", "GR")

    # record visits (duplicates for same visitor+POI should NOT inflate distinct count)
    reg5.record_visit(11, 501, "01/10/2025")
    reg5.record_visit(12, 501, "01/10/2025")
    reg5.record_visit(12, 501, "02/10/2025")   # same visitor revisits -> still counts once
    reg5.record_visit(13, 502, "01/10/2025")

    top = reg5.top_k_pois_by_distinct_visitors(2)
    for poi, cnt in top:
        print("Top POI:", poi.name, cnt)

    # --- VQ4: top-k VISITORS by DISTINCT POIs visited ---
    reg6 = POIRegistry()
    reg6.add_type("site", ["tag"])

    p1 = reg6.add_poi(601, "S1", "site", 0, 0, {"tag": "a"})
    p2 = reg6.add_poi(602, "S2", "site", 1, 1, {"tag": "b"})
    p3 = reg6.add_poi(603, "S3", "site", 2, 2, {"tag": "c"})

    v1 = reg6.add_visitor(21, "Ava", "BG")
    v2 = reg6.add_visitor(22, "Bo", "RO")
    v3 = reg6.add_visitor(23, "Cam", "GR")

    # Ava visits S1 twice (should count once), and S2 once -> 2 distinct POIs
    reg6.record_visit(21, 601, "01/10/2025")
    reg6.record_visit(21, 601, "02/10/2025")
    reg6.record_visit(21, 602, "02/10/2025")
    # Bo visits S3 -> 1 distinct
    reg6.record_visit(22, 603, "01/10/2025")
    # Cam visits none

    top_vis = reg6.top_k_visitors_by_distinct_pois(2)
    for v, cnt in top_vis:
        print("Top visitor:", v.name, cnt)

if __name__ == "__main__":
    main()
