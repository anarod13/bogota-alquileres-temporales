import json
import sys

def inspect_geojson(filepath):
    """Brutal inspection of GeoJSON file"""
    
    print(f"=== INSPECTING: {filepath} ===\n")
    
    # 1. Load the file
    with open(filepath, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"❌ INVALID JSON: {e}")
            return
    
    # 2. Check basic structure
    print("1. TOP-LEVEL KEYS:", list(data.keys()))
    print("   Type:", data.get('type', 'MISSING'))
    
    # 3. Check if it's a FeatureCollection
    if data.get('type') != 'FeatureCollection':
        print("❌ WARNING: Not a FeatureCollection")
    
    features = data.get('features', [])
    print(f"\n2. NUMBER OF FEATURES: {len(features)}")
    
    if not features:
        print("❌ ERROR: No features found!")
        return
    
    # 4. Inspect first feature thoroughly
    print("\n3. INSPECTING FIRST FEATURE:")
    first_feature = features[0]
    
    print(f"   Feature type: {first_feature.get('type')}")
    print(f"   Geometry type: {first_feature.get('geometry', {}).get('type')}")
    
    # Properties
    props = first_feature.get('properties', {})
    print(f"\n4. PROPERTIES KEYS: {list(props.keys())}")
    
    # 5. Show property values for first 5 features
    print("\n5. PROPERTY VALUES (first 5 features):")
    print("-" * 50)
    
    all_keys = set()
    for i, feature in enumerate(features[:5]):
        props = feature.get('properties', {})
        all_keys.update(props.keys())
        print(f"\nFeature {i}:")
        for key, value in props.items():
            print(f"  {key}: {repr(value)} (type: {type(value).__name__})")
    
    print("\n6. ALL UNIQUE PROPERTY KEYS IN ENTIRE FILE:")
    for key in sorted(all_keys):
        # Get sample values for this key
        values = []
        for feature in features[:3]:
            val = feature.get('properties', {}).get(key)
            if val is not None:
                values.append(repr(val))
        
        if values:
            print(f"  '{key}': {', '.join(values[:3])}")
    
    # 7. Check for null/weird values
    print("\n7. CHECKING FOR PROBLEMATIC VALUES:")
    
    problematic_keys = {}
    for i, feature in enumerate(features):
        props = feature.get('properties', {})
        for key, value in props.items():
            if value is None:
                problematic_keys.setdefault(key, []).append(i)
            elif isinstance(value, (list, dict)):
                problematic_keys.setdefault(key, []).append(i)
    
    for key, rows in problematic_keys.items():
        print(f"  '{key}' has {len(rows)} problematic values (None/list/dict)")
        if len(rows) < 10:
            print(f"    Rows: {rows}")
    
    # 8. Check for LocNombre or similar columns
    print("\n8. SEARCHING FOR LOCATION NAME COLUMNS:")
    
    location_keys = []
    for key in all_keys:
        key_lower = key.lower()
        if any(term in key_lower for term in ['name', 'nombre', 'region', 'district', 'boro', 'neigh', 'loc']):
            location_keys.append(key)
    
    if location_keys:
        print(f"  Found potential location columns: {location_keys}")
        
        # Show unique values for location columns
        for key in location_keys[:3]:  # First 3 only
            unique_vals = set()
            for feature in features:
                val = feature.get('properties', {}).get(key)
                if val is not None:
                    unique_vals.add(str(val).strip())
            
            print(f"\n  Unique values for '{key}' (first 10):")
            for val in list(unique_vals)[:10]:
                print(f"    '{repr(val)}'")
    else:
        print("  No obvious location columns found!")
    
    # 9. Save a summary to file
    print("\n9. SAVING SUMMARY TO 'geojson_report.txt'...")
    
    with open('geojson_report.txt', 'w', encoding='utf-8') as f:
        f.write(f"=== GEOJSON REPORT: {filepath} ===\n\n")
        f.write(f"Total features: {len(features)}\n")
        f.write(f"Property keys: {sorted(all_keys)}\n\n")
        
        f.write("SAMPLE DATA (first 3 features):\n")
        f.write("-" * 50 + "\n")
        
        for i, feature in enumerate(features[:3]):
            f.write(f"\nFeature {i}:\n")
            props = feature.get('properties', {})
            for key, value in props.items():
                f.write(f"  {key}: {repr(value)}\n")
    
    print("\n✅ Report saved to 'geojson_report.txt'")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        inspect_geojson(sys.argv[1])
    else:
        print("Usage: python check_geojson.py <your-file.geojson>")