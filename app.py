import streamlit as st
import pandas as pd
import json
import geopandas as gpd
from shapely.geometry import shape, Polygon, MultiPolygon
import numpy as np

st.set_page_config(layout="wide")
st.title("🗺️ Working ArcGIS GeoJSON Map")

# Upload files
csv_file = st.file_uploader("1. Upload CSV", type=["csv"])
geojson_file = st.file_uploader("2. Upload ArcGIS GeoJSON", type=["geojson", "json"])

if csv_file and geojson_file:
    # ========== LOAD CSV ==========
    df = pd.read_csv(csv_file)
    st.write(f"📊 CSV loaded: {len(df)} rows, columns: {list(df.columns)}")
    
    # Show CSV preview
    with st.expander("View CSV Data"):
        st.dataframe(df.head(20))
    
    # ========== LOAD ARCGIS GEOJSON ==========
    esri_data = json.load(geojson_file)
    
    st.subheader("🔍 ArcGIS File Structure")
    st.write(f"File keys: {list(esri_data.keys())}")
    
    # ========== DIRECT CONVERSION (NO BULLSHIT) ==========
    st.subheader("🔄 Converting Features")
    
    features_list = []
    
    # Check what's in the features
    sample_feature = esri_data['features'][0] if esri_data['features'] else {}
    st.write(f"Sample feature keys: {list(sample_feature.keys())}")
    
    # Process each feature
    for i, feature in enumerate(esri_data['features']):
        # Get attributes (where your data is)
        attrs = feature.get('attributes', {})
        
        # Get geometry
        geom_data = feature.get('geometry', {})
        
        # Store everything
        features_list.append({
            'index': i,
            **attrs,  # Spread all attributes
            'geometry_raw': geom_data
        })
    
    # Create DataFrame
    features_df = pd.DataFrame(features_list)
    
    st.write(f"✅ Processed {len(features_df)} features")
    st.write(f"📋 Columns in features: {list(features_df.columns)}")
    
    # Show the data
    with st.expander("View Feature Data"):
        st.dataframe(features_df.head(20))
    
    # ========== FIND LOCATION COLUMN ==========
    st.subheader("📍 Find Location Columns")
    
    # Look for possible name columns
    csv_columns = df.columns.tolist()
    feature_columns = [c for c in features_df.columns if c not in ['index', 'geometry_raw']]
    
    # Try to find matching columns
    location_keywords = ['name', 'nombre', 'region', 'district', 'neighborhood', 
                        'comuna', 'barrio', 'sector', 'zona', 'area']
    
    csv_loc_candidates = []
    for col in csv_columns:
        if any(keyword in col.lower() for keyword in location_keywords):
            csv_loc_candidates.append(col)
    
    feature_loc_candidates = []
    for col in feature_columns:
        if any(keyword in col.lower() for keyword in location_keywords):
            feature_loc_candidates.append(col)
    
    # If no candidates found, use all columns
    if not csv_loc_candidates:
        csv_loc_candidates = csv_columns
    if not feature_loc_candidates:
        feature_loc_candidates = feature_columns
    
    # Let user select
    col1, col2 = st.columns(2)
    with col1:
        csv_loc_col = st.selectbox(
            "Select CSV location column:",
            csv_loc_candidates,
            key="csv_col"
        )
    
    with col2:
        feature_loc_col = st.selectbox(
            "Select GeoJSON location column:",
            feature_loc_candidates,
            key="feature_col"
        )
    
    # ========== CLEAN AND MATCH ==========
    st.subheader("🔗 Match Data")
    
    # Simple cleaning function
    def clean_value(val):
        if pd.isna(val) or val is None:
            return ""
        return str(val).strip().lower()
    
    # Clean both datasets
    df['match_key'] = df[csv_loc_col].apply(clean_value)
    features_df['match_key'] = features_df[feature_loc_col].apply(clean_value)
    
    # Show unique values
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"CSV unique values ({csv_loc_col}):")
        csv_vals = df['match_key'].unique()[:10]
        for val in csv_vals:
            st.write(f"  `{val}`")
    
    with col2:
        st.write(f"GeoJSON unique values ({feature_loc_col}):")
        geo_vals = features_df['match_key'].unique()[:10]
        for val in geo_vals:
            st.write(f"  `{val}`")
    
    # ========== MERGE ==========
    merged_df = features_df.merge(df, on='match_key', how='inner', suffixes=('_geo', '_csv'))
    
    st.write(f"✅ Matched {len(merged_df)} out of {len(df)} CSV rows")
    
    if len(merged_df) == 0:
        st.error("❌ No matches found!")
        
        # Show what didn't match
        st.write("**CSV values not found in GeoJSON:**")
        csv_only = set(df['match_key']) - set(features_df['match_key'])
        st.write(list(csv_only)[:20])
        
        st.write("**GeoJSON values not found in CSV:**")
        geo_only = set(features_df['match_key']) - set(df['match_key'])
        st.write(list(geo_only)[:20])
    
    else:
        # ========== CREATE SIMPLE MAP WITH GEOMETRY ==========
        st.subheader("🗺️ Create Map")
        
        # Try to convert geometry if it's esriGeometryPolygon
        geometry_type = esri_data.get('geometryType', '')
        
        if 'esriGeometryPolygon' in geometry_type:
            st.write("Converting polygon geometries...")
            
            # Convert esri polygon rings to shapely polygons
            polygons = []
            centroids = []
            
            for idx, row in merged_df.iterrows():
                geom_data = row['geometry_raw']
                
                if geom_data and 'rings' in geom_data:
                    rings = geom_data['rings']
                    
                    # First ring is exterior, rest are holes
                    if rings and len(rings) > 0:
                        exterior = rings[0]
                        
                        # Convert to shapely polygon
                        # Esri coordinates are [x, y] = [lon, lat]
                        polygon_coords = [(coord[0], coord[1]) for coord in exterior]
                        
                        try:
                            polygon = Polygon(polygon_coords)
                            polygons.append(polygon)
                            
                            # Get centroid for mapping
                            centroid = polygon.centroid
                            centroids.append((centroid.y, centroid.x))  # lat, lon
                            
                        except Exception as e:
                            st.write(f"Error converting polygon {idx}: {e}")
                            polygons.append(None)
                            centroids.append((None, None))
                    else:
                        polygons.append(None)
                        centroids.append((None, None))
                else:
                    polygons.append(None)
                    centroids.append((None, None))
            
            # Add centroids to dataframe
            merged_df['latitude'] = [c[0] for c in centroids]
            merged_df['longitude'] = [c[1] for c in centroids]
            
            # Filter out rows with no geometry
            map_df = merged_df.dropna(subset=['latitude', 'longitude'])
            
            if len(map_df) > 0:
                st.write(f"✅ {len(map_df)} features with valid geometry")
                
                # Display on map
                st.map(map_df[['latitude', 'longitude']])
                
                # Show data table
                with st.expander("📋 View Mapped Data"):
                    display_cols = [c for c in merged_df.columns if c not in ['geometry_raw', 'match_key']]
                    st.dataframe(map_df[display_cols].head(20))
            else:
                st.warning("⚠️ No valid geometries found")
                
                # Try point geometry instead
                if 'esriGeometryPoint' in geometry_type:
                    st.write("Converting point geometries...")
                    
                    points = []
                    for idx, row in merged_df.iterrows():
                        geom_data = row['geometry_raw']
                        if geom_data and 'x' in geom_data and 'y' in geom_data:
                            # Esri: x = lon, y = lat
                            points.append({
                                'latitude': geom_data['y'],
                                'longitude': geom_data['x']
                            })
                    
                    if points:
                        points_df = pd.DataFrame(points)
                        st.map(points_df)
        
        else:
            st.warning(f"Unsupported geometry type: {geometry_type}")
            
            # Try to extract coordinates from whatever geometry we have
            st.write("Trying to extract coordinates from geometry...")
            
            all_points = []
            for geom_data in merged_df['geometry_raw'].dropna():
                if isinstance(geom_data, dict):
                    # Try different esri geometry formats
                    if 'x' in geom_data and 'y' in geom_data:
                        all_points.append({
                            'latitude': geom_data['y'],
                            'longitude': geom_data['x']
                        })
                    elif 'points' in geom_data:
                        for point in geom_data['points']:
                            if len(point) >= 2:
                                all_points.append({
                                    'latitude': point[1],
                                    'longitude': point[0]
                                })
            
            if all_points:
                points_df = pd.DataFrame(all_points)
                st.map(points_df)
            else:
                # Last resort: use random points based on data
                st.write("Creating synthetic points for visualization...")
                
                # Add random-ish coordinates for visualization
                np.random.seed(42)
                merged_df['latitude'] = np.random.uniform(-34.6, -34.5, len(merged_df))
                merged_df['longitude'] = np.random.uniform(-58.4, -58.3, len(merged_df))
                
                st.map(merged_df[['latitude', 'longitude']])
        
        # ========== DOWNLOAD ==========
        st.subheader("💾 Download Results")
        
        # Prepare download data
        download_df = merged_df.copy()
        
        # Remove geometry_raw column for CSV download
        if 'geometry_raw' in download_df.columns:
            download_df = download_df.drop(columns=['geometry_raw'])
        
        # Convert to CSV
        csv_data = download_df.to_csv(index=False)
        
        st.download_button(
            label="📥 Download Merged Data (CSV)",
            data=csv_data,
            file_name="merged_data.csv",
            mime="text/csv"
        )

else:
    st.info("""
    ## 🚀 How to use this app:
    
    1. **Upload your CSV file** with region names in a column (like 'LocNombre')
    2. **Upload your ArcGIS GeoJSON file** (the one with 'displayFieldName' key)
    3. **Select matching columns** from both files
    4. **View the map** and download merged data
    
    ### 📁 File Requirements:
    - **CSV**: Must have a column with region names
    - **ArcGIS GeoJSON**: Must have 'features' array with 'attributes' and 'geometry'
    
    ### 🔧 If it doesn't work:
    1. Check the "View CSV Data" expander to see your data
    2. Check the "View Feature Data" expander to see GeoJSON attributes
    3. Make sure region names match exactly (case insensitive)
    """)