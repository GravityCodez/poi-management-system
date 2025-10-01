from models import POIType, POI, Visitor, POIRegistry, is_close

def main():

    # test of our models
    forest = POIType("forest", ["area", "protected"])
    poi1 = POI(1, "Mangrove Forest", forest, 100, 200, {"area": 350, "protected": True})
    samAltman = Visitor(10, "Sam Altman", "USA")

    print(forest)
    print(poi1)       # should show center=(100, 200) - passed without problems
    print(samAltman)
    print("Same object for type?", poi1.poi_type is forest)
    
    reg = POIRegistry()
    reg.add_type("forest", ["area", "protected"])
    reg.add_poi(2, "Cedar Grove", "forest", 120, 220, {"area": 200, "protected": False})
    print("Types in registry:", reg.list_types())
    for p in reg.list_pois():
        print("POI in registry:", p)

    # showing the invariant: deleting a type in use should fail gracefully!
    try:
        reg.delete_type("forest")
    except ValueError as e:
        print("Delete error:", e)

    # distance demo
    reg = POIRegistry()
    reg.add_type("forest", ["area", "protected"])
    p1 = reg.add_poi(100, "A", "forest", 0, 0, {})
    p2 = reg.add_poi(101, "B", "forest", 3, 4, {})
    d = p1.distance_to(p2)
    print("Distance A→B:", d)                 # expect 5.0 (3-4-5 pythagorian triangle)
    print("Close to 5.0?", is_close(d, 5.0))  # expect True

     # --- nearest_k demo (PQ5) ---
    reg2 = POIRegistry()
    reg2.add_type("forest", ["area", "protected"])
    reg2.add_poi(200, "A", "forest", 0, 0, {})
    reg2.add_poi(201, "B", "forest", 3, 4, {})
    reg2.add_poi(202, "C", "forest", 10, 0, {})
    top = reg2.nearest_k(0, 0, 2)
    for poi, dist in top:
        print("Nearest:", poi.name, round(dist, 2))
    
    # --- radius queries demo (PQ4 + boundary) ---
    reg3 = POIRegistry()
    reg3.add_type("forest", ["area", "protected"])
    reg3.add_poi(300, "O", "forest", 0, 0, {})
    reg3.add_poi(301, "P", "forest", 3, 4, {})     # distance 5 from (0,0)
    reg3.add_poi(302, "Q", "forest", 10, 0, {})    # distance 10 from (0,0)

    within = reg3.within_radius(0, 0, 5.0)
    for poi, d in within:
        print("Within:", poi.name, round(d, 3))

    boundary = reg3.exactly_on_boundary(0, 0, 5.0)
    for poi, d in boundary:
        print("On boundary:", poi.name, round(d, 3))


if __name__ == "__main__":
    main()
