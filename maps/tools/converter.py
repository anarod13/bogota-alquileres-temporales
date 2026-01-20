import json
import sys

def convert_arcgis_to_geojson(input_file, output_file=None):
    """Convert ArcGIS GeoJSON to standard GeoJSON"""
    
    with open(input_file, 'r', encoding='utf-8') as f:
        arcgis_data = json.load(f)
    
    print(f"🔍 Input file keys: {list(arcgis_data.keys())}")
    
    # Check if it's already standard
    if arcgis_data.get('type') == 'FeatureCollection':
        print("✅ Already standard GeoJSON")
        return arcgis_data
    
    # Convert
    standard_features = []
    
    for feature in arcgis_data.get('features', []):
        standard_feature = {
            "type": "Feature",
            "properties": feature.get('attributes', {}),
            "geometry": feature.get('geometry', {})
        }
        standard_features.append(standard_feature)
    
    standard_geojson = {
        "type": "FeatureCollection",
        "features": standard_features
    }
    
    print(f"✅ Converted {len(standard_features)} features")
    
    # Save if output file specified
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(standard_geojson, f, indent=2)
        print(f"💾 Saved to {output_file}")
    
    return standard_geojson

if __name__ == "__main__":
    if len(sys.argv) > 1:
        convert_arcgis_to_geojson(sys.argv[1], 
                                 sys.argv[2] if len(sys.argv) > 2 else "converted.geojson")
    else:
        print("Usage: python convert_arcgis.py <input.geojson> [output.geojson]")