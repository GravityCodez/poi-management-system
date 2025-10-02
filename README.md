# POI Management System -  Report + [Demo Video](https://mbzuaiac-my.sharepoint.com/:v:/g/personal/temiko_machavariani_mbzuai_ac_ae/ER9bXQO67xxAtZQgSituFQkBn1DH14cNimevqa3Mca5N3A)

## 1. Design & Data Model 

### 1.1 Core Entities

The system implements four primary domain models with clear separation of concerns:

**POIType**
- Defines categorical schemas for Points of Interest
- Properties: `name` (string), `attributes` (list of attribute names)
- Stored in registry with case-insensitive keys for robustness
- Deletion constrained: only allowed when no POIs reference the type

**POI (Point of Interest)**
- Represents specific locations on a 1000×1000 integer grid
- Properties:
  - `id` (integer, immutable, never reused even after deletion)
  - `name` (string, immutable)
  - `coord` (tuple of integers representing center point)
  - `poi_type` (reference to POIType)
  - `values` (dictionary mapping attribute names to values)
- Center-based positioning for large-area POIs (forests, beaches, etc.)
- Encapsulation via `@property` decorators for id, name, and coord

**Visitor**
- Represents individuals who visit POIs
- Properties: `id` (integer), `name` (string), `nationality` (string)
- No deletion support (historical data preservation)

**Visit**
- Records visit events linking visitors to POIs
- Properties:
  - `visitor` (Visitor reference)
  - `poi` (POI reference)
  - `date` (string in dd/mm/yyyy format, validated)
  - `rating` (optional integer 1-10)
- Date validation ensures format consistency using `datetime.strptime`
- Historical record: persists even after POI deletion

### 1.2 POIRegistry Architecture

The `POIRegistry` class serves as the central orchestrator, managing:
- Type definitions (`_types`: dict[str, POIType])
- Active POIs (`_pois`: dict[int, POI])
- Reserved IDs (`_used_poi_ids`: set[int]) - enforces no-reuse invariant
- Visitors (`_visitors`: dict[int, Visitor])
- Visit history (`_visits`: list[Visit])

This design choice centralizes business logic while maintaining clean entity classes focused on data representation.

### 1.3 Key Invariants

**ID Non-Reuse**: Once a POI ID is assigned, it remains permanently reserved in `_used_poi_ids` even after deletion. This prevents ambiguity in historical data and maintains referential integrity.

**Type Deletion Constraint**: A POI type can only be deleted if no active POIs reference it. The system validates this constraint by iterating through all POIs before allowing deletion.

**Center Coordinates**: All POIs, regardless of physical size, are represented by a single center coordinate. This simplifies distance calculations and maintains consistency across spatial queries.

**Immutability**: POI identifiers, names, and locations cannot be modified after creation, ensuring data consistency and preventing cascading updates.

## 2. Edge Policies & Technical Decisions

### 2.1 Boundary Correctness (ε-based Comparison)

The system implements epsilon-aware floating-point comparison to handle boundary cases:

```python
EPS = 1e-9

def is_close(a: float, b: float, eps: float = EPS) -> bool:
    return abs(a - b) <= eps
```

**Application**: 
- `within_radius`: includes POIs where `d < r or is_close(d, r)`
- `exactly_on_boundary`: includes POIs where `is_close(d, r)`

This approach prevents:
- False exclusion: POIs exactly at radius r are included in boundary queries
- Duplication: Consistent comparison logic prevents double-counting
- Floating-point errors: Accounts for precision limitations in distance calculations

**Epsilon value rationale**: 1e-9 provides sufficient precision for integer coordinates on a 1000×1000 grid while remaining computationally efficient.

### 2.2 Counting Conventions

**Distinct by Default**: All aggregate queries count unique entities:
- "visitors per POI" counts distinct visitors (using set operations)
- "POIs per visitor" counts distinct POIs
- Repeat visits by the same visitor to the same POI count once

**Implementation**: Built using dictionaries mapping to sets:
```python
distinct: Dict[int, Set[int]] = {}
for visit in self._visits:
    distinct.setdefault(poi_id, set()).add(visitor_id)
```

### 2.3 Deterministic Tie-Breaking

All sorting operations use multi-key tuples to ensure reproducible output:

**Distance queries**: `(distance, poi_id, poi_name)`
**Rankings**: `(-count, entity_id, entity_name)` (negative count for descending order)
**Closest pair**: `(min_id, max_id, min_name, max_name)`

This guarantees stable test results and predictable user experience across executions.

### 2.4 Coordinate Bounds

The system enforces integer coordinates in the range [0, 1000):
- Validation occurs in `_check_coord()` with clear error messages
- Type checking ensures coordinates are integers, not floats
- Prevents invalid spatial calculations and maintains grid consistency

### 2.5 Date Format Policy

Dates must follow dd/mm/yyyy format:
- Validated using `datetime.strptime(date, "%d/%m/%Y")`
- Normalized to zero-padded format (e.g., "01/10/2025")
- Enables string-based comparison for chronological sorting
- Error messages include example format for user guidance

## 3. Query Implementation & Complexity

### 3.1 POI Queries

**PQ1 - List POIs by Type**: O(n) where n = total POIs
- Filters POIs matching type, builds complete attribute dictionary with None defaults
- Sorted by (id, name) for determinism

**PQ2 - Closest Pair**: O(n²)
- Brute-force approach checking all pairs
- Epsilon-aware distance comparison
- Deterministic tie-breaking with multi-key tuples
- *Design decision*: Chose simplicity over O(n log n) divide-and-conquer for maintainability

**PQ3 - Counts per Type**: O(n + t) where t = number of types
- Initializes all types with count 0 (includes unused types)
- Single pass through POIs to increment counts
- Sorted by (-count, name)

**PQ4 - Within Radius**: O(n)
- Linear scan computing distances from reference point
- Includes boundary using epsilon comparison
- Returns sorted results

**PQ5 - Nearest K**: O(n log n)
- Computes all distances, stores with (distance, id, name, poi) tuples
- Sorts entire list for determinism
- Returns first k elements

**PQ6 - Boundary Correctness**: O(n)
- Filters POIs where `is_close(distance, radius)`
- Demonstrates epsilon-based equality handling

### 3.2 Visitor Queries

**VQ1 - Visitor History**: O(v log v) where v = visits for that visitor
- Filters visits by visitor_id
- Parses dates for chronological sorting
- Returns all visits (not distinct POIs)

**VQ2 - Visitors for POI**: O(v) or O(v log v)
- Non-distinct mode: returns all visits chronologically
- Distinct mode: tracks earliest visit per visitor using dictionary

**VQ3 - Distinct POIs per Visitor**: O(v + u) where u = visitors
- Builds visitor → set(poi_ids) mapping
- Initializes all visitors with empty sets (includes zero-visit visitors)

**VQ4 - Top K Visitors**: O(v + u log u)
- Aggregates distinct POI counts per visitor
- Sorts by (-count, id, name), returns first k

**VQ5 - Top K POIs**: O(v + p log p) where p = POIs with visits
- Aggregates distinct visitor counts per POI
- Sorted ranking with k-limit

**VQ7 - Coverage Fairness**: O(v + u log u)
- Builds two mappings: visitor → set(poi_ids) and visitor → set(type_names)
- Filters visitors meeting both thresholds (≥m POIs, ≥t types)
- Multi-key sort: (-pois, -types, id, name)

## 4. Configuration System

### 4.1 JSON Structure

The optional configuration loader (`config.py`) accepts JSON with four top-level keys:

```json
{
  "types": [
    {"name": "museum", "attributes": ["tickets", "open"]}
  ],
  "pois": [
    {
      "id": 1,
      "name": "City Museum",
      "type": "museum",
      "x": 10,
      "y": 10,
      "values": {"tickets": 12, "open": "10:00-18:00"}
    }
  ],
  "visitors": [
    {"id": 1, "name": "Sam", "nationality": "GE"}
  ],
  "visits": [
    {
      "visitor_id": 1,
      "poi_id": 1,
      "date": "01/10/2025",
      "rating": 7
    }
  ]
}
```

### 4.2 Validation & Error Reporting

The loader implements comprehensive validation with JSONPath-style error messages:

**Type validation**: Checks for non-empty strings, proper array types
**Reference integrity**: Validates type names exist before adding POIs
**Constraint enforcement**: Rating must be int 1-10, coordinates in valid range
**Error location**: Reports precise paths like `$.visits[3].date` for rapid debugging

**Example error message**:
```
$.pois[2].x/.y: must be integers in [0, 1000)
```

### 4.3 Loading Behavior

- **Mutates active registry**: Adds to current state rather than replacing
- **Loading twice**: Triggers errors due to ID reuse constraints (by design)
- **Order dependency**: Types must load before POIs, visitors before visits

## 5. Usage Guide

A demo of the whole code can be viewed [here](https://mbzuaiac-my.sharepoint.com/:v:/g/personal/temiko_machavariani_mbzuai_ac_ae/ER9bXQO67xxAtZQgSituFQkBn1DH14cNimevqa3Mca5N3A)

### 5.1 Starting the Application

```bash
python main.py
```

The application presents a numbered menu with 20+ operations.

### 5.2 Sample Session Flow

**Initial Setup**:
```
Choose: 20
Path to JSON file: big_demo.json
Config loaded.
```

**Add a POI Type**:
```
Choose: 1
Type name: restaurant
Attributes (comma-separated, optional): cuisine, capacity, price_range
Added type 'restaurant' with attrs ['cuisine', 'capacity', 'price_range']
```

**Add a POI**:
```
Choose: 2
POI id (int): 500
POI name: The Golden Fork
Type name (existing): restaurant
x (0..999): 250
y (0..999): 375
Added: POI(id=500, name=The Golden Fork, type=restaurant, center=(250, 375))
```

**Record a Visit** (new visitor auto-prompt):
```
Choose: 3
Visitor id (int): 100
POI id (existing): 500
Date (dd/mm/yyyy): 15/09/2025
Rating (1..10, blank to skip): 9
New visitor name: Alice
New visitor nationality (2 letters ok): UK
Visitor created and visit recorded.
```

**Spatial Query - Nearest K**:
```
Choose: 5
x (0..999): 250
y (0..999): 375
k (>0): 3
Nearest: The Golden Fork (500) dist=0.0
Nearest: City Museum (1) dist=412.189
Nearest: Central Park (2) dist=523.452
```

**Ranking Query - Top POIs**:
```
Choose: 11
k (>0): 5
101	City Museum	23 distinct visitors
102	Central Park	18 distinct visitors
103	Art Gallery	15 distinct visitors
...
```

**Coverage Fairness**:
```
Choose: 15
Minimum DISTINCT POIs (m): 5
Minimum DISTINCT TYPES (t): 3
100	Alice	pois=7	types=4
105	Bob	pois=6	types=3
```

### 5.3 Menu Organization

The menu is numerically sorted (1-20) with option 0 for quit. Operations are grouped conceptually:
- Types & POIs: 1-2, 16-19
- Visits: 3
- Queries: 4-15, 20

## 6. Reflection (300-500 words)

The development of this POI management system involved numerous design trade-offs that shaped the final architecture. One of the most significant decisions was choosing O(n²) brute-force for the closest-pair problem (PQ2) despite knowing the O(n log n) divide-and-conquer solution. Initial experimentation with the faster algorithm showed minimal performance differences at the assignment's scale (hundreds of POIs), while the brute-force approach offered substantially clearer code that was easier to debug and integrate with epsilon-based comparisons and deterministic tie-breaking. This reinforced an important lesson: algorithmic efficiency exists on a spectrum with maintainability, and the "optimal" choice depends heavily on context.

The decision to use Python's `@property` decorator for encapsulation proved invaluable. By making `POI.id`, `POI.name`, and `POI.coord` read-only properties, the codebase gained protection against accidental mutations that could violate the immutability invariant, while maintaining clean syntax for access (`poi.id` rather than `poi.get_id()`). This struck an effective balance between object-oriented principles and Python's pragmatic style.

Comprehensive type hints throughout the codebase significantly improved development velocity. Modern IDEs provided accurate autocomplete suggestions, caught type mismatches before runtime, and made refactoring substantially safer. The `from __future__ import annotations` import eliminated circular dependency issues with forward references, demonstrating that staying current with Python features pays dividends in code quality.

The development process itself evolved considerably. Early commits were large, monolithic feature additions that made debugging difficult. As the project progressed, the workflow shifted toward smaller, focused commits paired with targeted testing prints (preserved in `prints.py`). This incremental approach made it trivial to identify which change introduced a bug and facilitated rapid experimentation with different approaches to epsilon handling and tie-breaking strategies. The commit graph visualization clearly shows this maturation from sporadic, large changes to consistent, measured progress.

Epsilon-based boundary handling emerged as more complex than initially anticipated. The first implementation wrongly excluded boundary POIs from `within_radius` queries, requiring careful reasoning about whether to use `<= r` or `< r or is_close(r)`. Ultimately, the decision to include boundaries in range queries but also provide a separate `exactly_on_boundary` method gave users maximum flexibility while maintaining mathematical precision.

The JSON configuration loader added substantial complexity but proved essential for demo scenarios and testing. Implementing JSONPath-style error messages (`$.visits[3].rating: must be an integer 1..10`) transformed cryptic validation failures into actionable feedback. This attention to error message quality throughout the system (coordinate bounds, date formats, type constraints) improved the user experience considerably.

Finally, the constraint that POI IDs are never reused forced careful thinking about the relationship between active entities and historical records. This design prevents ambiguity when analyzing visit history but requires maintaining a separate `_used_poi_ids` set alongside the active `_pois` dictionary—a memory trade-off for data integrity that felt justified given the system's scale and purpose.

## 7. Testing Coverage

The system includes comprehensive manual testing scenarios covering:

**Edge Cases**:
- Epsilon boundary comparison (POIs exactly at radius r)
- Tie-breaking determinism (identical distances, counts)
- Empty result sets (zero-count types, visitors with no visits)

**Invariant Validation**:
- ID reuse prevention (attempting to add POI with used ID)
- Type deletion constraints (deleting type with active POIs)
- Date format validation (rejecting yyyy-mm-dd format)
- Rating bounds checking (rejecting values outside 1-10)

**Data Integrity**:
- Attribute migration during add/delete/rename operations
- Visit history preservation after POI deletion
- Distinct counting correctness with repeated visits

**Configuration Loading**:
- JSONPath error reporting for malformed input
- Reference validation (unknown type names, POI IDs)
- Proper handling of optional fields (rating, attributes)

Test scenarios are documented in `prints.py`, showing the evolutionary testing approach from basic entity creation to complex query validation.

## 8. Extensions Implemented

### 8.1 Attribute Renaming

The `rename_attribute_on_type` method supports renaming attribute names within a POI type:
- Updates the type's schema
- Migrates all existing POI values from old key to new key
- Policy: If new attribute name already exists, old attribute is dropped

### 8.2 Type Renaming

The `rename_poi_type` method renames a POI type:
- Updates the type's name in the registry
- POIs maintain reference to same POIType object (no cascading updates needed)
- Validates new name doesn't conflict with existing types

Both extensions include comprehensive error handling and maintain data consistency through migration steps.

## 9. Conclusion

This POI Management System demonstrates practical application of object-oriented design principles, spatial algorithms, and user-centric interface design. The codebase prioritizes correctness through comprehensive validation, maintainability through clear separation of concerns, and usability through informative error messages. The development process illustrated the value of incremental progress, thorough testing, and pragmatic trade-offs between algorithmic sophistication and implementation clarity.