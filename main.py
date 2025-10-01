from models import POIType, POI, Visitor, POIRegistry

def main():
    # test of models
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

    # show the invariant: deleting a type in use should fail gracefully!
    try:
        reg.delete_type("forest")
    except ValueError as e:
        print("Delete error:", e)

if __name__ == "__main__":
    main()
