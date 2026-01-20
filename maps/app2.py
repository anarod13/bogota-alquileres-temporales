import streamlit as st
import pandas as pd
import json
import geopandas as gpd
from shapely.geometry import shape, Polygon, MultiPolygon
import numpy as np
import folium
from streamlit_folium import st_folium, folium_static
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from branca.colormap import LinearColormap

st.set_page_config(layout="wide")
st.title("🗺️ Presencia de Airbnb por localidades en Bogotá")

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
    
    # ========== DIRECT CONVERSION ==========
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
    
    # Let user select (with LocNombre as default if exists)
    col1, col2 = st.columns(2)
    with col1:
        # Try to find LocNombre in CSV columns
        csv_loc_default = 'LocNombre' if 'LocNombre' in csv_columns else csv_columns[0]
        csv_loc_col = st.selectbox(
            "Select CSV location column:",
            csv_columns,
            index=csv_columns.index(csv_loc_default) if csv_loc_default in csv_columns else 0,
            key="csv_col"
        )
    
    with col2:
        # Try to find LocNombre in feature columns
        feature_loc_default = 'LocNombre' if 'LocNombre' in feature_columns else feature_columns[0]
        feature_loc_col = st.selectbox(
            "Select GeoJSON location column:",
            feature_columns,
            index=feature_columns.index(feature_loc_default) if feature_loc_default in feature_columns else 0,
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
        # ========== LISTING COUNT GRADUATED COLORS ==========
        st.subheader("🎨 Graduated Coloring by Listing Count")
        
        # Check if listing_count column exists
        listing_count_columns = [col for col in merged_df.columns if 'listing' in col.lower() and 'count' in col.lower()]
        
        if listing_count_columns:
            listing_col = listing_count_columns[0]
            st.write(f"Found listing count column: **{listing_col}**")
            
            # Ensure listing count is numeric
            merged_df[listing_col] = pd.to_numeric(merged_df[listing_col], errors='coerce')
            
            # Remove NaN values for coloring
            valid_data = merged_df[listing_col].dropna()
            
            if len(valid_data) == 0:
                st.warning("⚠️ No valid numeric listing count values found!")
            else:
                # Show distribution
                with st.expander("📊 Listing Count Distribution"):
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Min", int(valid_data.min()))
                    with col2:
                        st.metric("Max", int(valid_data.max()))
                    with col3:
                        st.metric("Mean", f"{valid_data.mean():.1f}")
                    with col4:
                        st.metric("Median", int(valid_data.median()))
                    
                    # Histogram
                    fig, ax = plt.subplots(figsize=(10, 4))
                    ax.hist(valid_data, bins=20, edgecolor='black', alpha=0.7, color='skyblue')
                    ax.set_xlabel('Listing Count')
                    ax.set_ylabel('Frequency')
                    ax.set_title('Distribution of Listing Counts')
                    ax.grid(True, alpha=0.3)
                    st.pyplot(fig)
                
                # ========== COLOR SCALE SELECTION ==========
                st.write("### Color Scale Configuration")
                
                # Define color schemes (darker = higher values)
                color_schemes = {
                    'Reds (Light to Dark)': ['#ffe6e6', '#ffb3b3', '#ff8080', '#ff4d4d', '#ff1a1a', '#e60000', '#b30000'],
                    'Blues (Light to Dark)': ['#e6f2ff', '#b3d9ff', '#80bfff', '#4da6ff', '#1a8cff', '#0073e6', '#0059b3'],
                    'Greens (Light to Dark)': ['#e6ffe6', '#b3ffb3', '#80ff80', '#4dff4d', '#1aff1a', '#00e600', '#00b300'],
                    'Purples (Light to Dark)': ['#f2e6ff', '#d9b3ff', '#bf80ff', '#a64dff', '#8c1aff', '#7300e6', '#5900b3'],
                    'Oranges (Light to Dark)': ['#fff0e6', '#ffd1b3', '#ffb380', '#ff944d', '#ff751a', '#e65c00', '#b34700'],
                    'Greys (Light to Dark)': ['#f2f2f2', '#d9d9d9', '#bfbfbf', '#a6a6a6', '#8c8c8c', '#737373', '#595959'],
                }
                
                # Let user select color scheme
                selected_scheme = st.selectbox(
                    "Select color scheme (darker colors = higher listing counts):",
                    list(color_schemes.keys()),
                    index=0
                )
                
                # Get the selected color palette
                color_palette = color_schemes[selected_scheme]
                
                # Number of color classes
                num_classes = st.slider(
                    "Number of color classes:",
                    min_value=3,
                    max_value=7,
                    value=5,
                    help="How many distinct color shades to use"
                )
                
                # Create color map for the selected number of classes
                if num_classes <= len(color_palette):
                    color_scale = color_palette[:num_classes]
                else:
                    # Interpolate if more classes needed
                    cmap = mcolors.LinearSegmentedColormap.from_list("custom", color_palette, N=num_classes)
                    color_scale = [mcolors.to_hex(cmap(i)) for i in np.linspace(0, 1, num_classes)]
                
                # Classification method
                classification_method = st.radio(
                    "Classification method:",
                    ["Equal Interval", "Quantiles (Equal Count)", "Natural Breaks (Jenks)"],
                    horizontal=True
                )
                
                # Classify data
                if classification_method == "Equal Interval":
                    # Equal interval classification
                    min_val = valid_data.min()
                    max_val = valid_data.max() +1
                    breaks = np.linspace(min_val, max_val, num_classes + 1)
                    
                elif classification_method == "Quantiles (Equal Count)":
                    # Quantile classification
                    quantiles = np.linspace(0, 1, num_classes + 1)
                    breaks = valid_data.quantile(quantiles).tolist()
                    
                else:  # Natural Breaks approximation
                    # Simple approximation of natural breaks
                    sorted_data = np.sort(valid_data)
                    # Create initial breaks
                    breaks = [sorted_data[0]]
                    for i in range(1, num_classes):
                        idx = int(len(sorted_data) * i / num_classes)
                        breaks.append(sorted_data[idx])
                    breaks.append(sorted_data[-1])
                
                # Ensure breaks are unique and sorted
                breaks = sorted(list(set(breaks)))
                
                # Assign colors based on classification
                def get_color_for_value(value, breaks, color_scale):
                    if pd.isna(value):
                        return '#cccccc'  # Gray for missing values
                    
                    for i in range(len(breaks) - 1):
                        if breaks[i] <= value <= breaks[i + 1]:
                            return color_scale[i]
                    # If value is outside range, use last color
                    return color_scale[-1]
                
                # Apply color assignment
                merged_df['color'] = merged_df[listing_col].apply(
                    lambda x: get_color_for_value(x, breaks, color_scale)
                )
                
                # Create a legend
                st.write("### Color Legend")
                legend_data = []
                for i in range(len(color_scale)):
                    lower_bound = breaks[i]
                    upper_bound = breaks[i + 1] if i < len(breaks) - 1 else "∞"
                    legend_data.append({
                        'Color': color_scale[i],
                        'Range': f"{lower_bound:.0f} - {upper_bound:.0f}",
                        'Count': ((merged_df[listing_col] >= lower_bound) & 
                                 (merged_df[listing_col] < upper_bound)).sum()
                    })
                
                # Display legend as colored boxes
                legend_cols = st.columns(num_classes)
                for idx, legend_item in enumerate(legend_data):
                    with legend_cols[idx]:
                        st.markdown(
                            f"""
                            <div style="background-color:{legend_item['Color']}; padding:10px; 
                                      border-radius:5px; text-align:center; border:1px solid #ccc; 
                                      margin-bottom:5px; color:{'white' if idx > num_classes//2 else 'black'};">
                                <strong>{legend_item['Range']}</strong>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        st.caption(f"Count: {legend_item['Count']}")
                
                # Display classification summary
                with st.expander("📋 Classification Summary"):
                    summary_df = pd.DataFrame(legend_data)
                    st.dataframe(summary_df)
                    
        else:
            st.warning("⚠️ No 'listing_count' column found in the data.")
            st.write("Available columns:")
            for col in merged_df.columns:
                st.write(f"- {col}")
            listing_col = None
        
        # ========== CREATE FOLIUM MAP WITH GRADUATED COLORS ==========
        st.subheader("🗺️ Interactive Map with Graduated Colors")
        
        geometry_type = esri_data.get('geometryType', '')
        
        if 'esriGeometryPolygon' in geometry_type:
            st.write("Creating map with graduated colors...")
            
            # Create a base map
            # Find center of all polygons
            all_lats = []
            all_lons = []
            polygons_list = []
            print(merged_df.columns)

            for idx, row in merged_df.iterrows():
                geom_data = row['geometry_raw']
                
                if geom_data and 'rings' in geom_data:
                    rings = geom_data['rings']
                    
                    if rings and len(rings) > 0:
                        exterior = rings[0]
                        polygon_coords = [(coord[1], coord[0]) for coord in exterior]  # lat, lon
                        
                        try:
                            # Create polygon for Folium
                            polygons_list.append({
                                'polygon': polygon_coords,
                                'color': row.get('color', '#3388ff') if listing_col else '#3388ff',
                                'name': row.get('LocNombre_geo', f"Feature {idx}"),
                                'listing_count': row[listing_col] if listing_col else "N/A",
                                'category': row.get('listing_category', 'N/A')
                            })
                            
                            # Add to center calculation
                            for coord in polygon_coords:
                                all_lats.append(coord[0])
                                all_lons.append(coord[1])
                                
                        except Exception as e:
                            st.write(f"Error processing polygon {idx}: {e}")
            
            if polygons_list:
                # Calculate map center
                if all_lats and all_lons:
                    center_lat = sum(all_lats) / len(all_lats)
                    center_lon = sum(all_lons) / len(all_lons)
                else:
                    center_lat, center_lon = 0, 0
                
                # Create Folium map
                m = folium.Map(location=[center_lat, center_lon], zoom_start=10)
                # Add polygons to map with graduated colors
                for poly_data in polygons_list:

                    # Create popup content
                    popup_content = f"""
                    <div style="font-family: Arial; min-width: 200px;">
                        <h4 style="margin-bottom: 5px;">{poly_data['name']}</h4>
                        <hr style="margin: 5px 0;">
                        <b>Airbnb Registered:</b> {poly_data['listing_count']}<br>
                    </div>
                    """
                    
                    # Add polygon to map
                    folium.Polygon(
                        locations=poly_data['polygon'],
                        color='#000000',  # Border color
                        weight=1,  # Border width
                        fill=True,
                        fill_color=poly_data['color'],
                        fill_opacity=0.7,
                        popup=folium.Popup(popup_content, max_width=300)
                    ).add_to(m)
                
                # Add color legend to map if we have listing counts
                if listing_col and 'color_scale' in locals():
                    # Create a color legend
                    colormap = LinearColormap(
                        colors=color_scale,
                        vmin=valid_data.min(),
                        vmax=valid_data.max(),
                        caption=f'Listing Count ({listing_col})'
                    )
                    colormap.add_to(m)
                
                # Display the map
                folium_static(m, width=1200, height=600)
                
                # Show data summary
                st.write(f"### 📊 Mapped {len(polygons_list)} polygons")
                
                # Display polygon data
                with st.expander("📋 View Polygon Data"):
                    display_cols = [c for c in merged_df.columns if c not in ['geometry_raw', 'match_key']]
                    if listing_col:
                        # Sort by listing count (highest first)
                        sorted_df = merged_df.sort_values(listing_col, ascending=False)
                        st.dataframe(sorted_df[display_cols].head(20))
                    else:
                        st.dataframe(merged_df[display_cols].head(20))
                
            else:
                st.warning("⚠️ No valid polygons found in the data.")
                
        else:
            st.warning(f"⚠️ Unsupported geometry type: {geometry_type}")
            st.info("This app works best with polygon data (esriGeometryPolygon).")
        
        # ========== DOWNLOAD ==========
        st.subheader("💾 Download Results")
        
        # Prepare download data
        download_df = merged_df.copy()
        
        # Remove geometry_raw column for CSV download
        if 'geometry_raw' in download_df.columns:
            download_df = download_df.drop(columns=['geometry_raw'])
        
        # Convert to CSV
        csv_data = download_df.to_csv(index=False)
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📥 Download Merged Data (CSV)",
                data=csv_data,
                file_name="merged_data.csv",
                mime="text/csv"
            )
        
        # Also download the styled map as HTML if we created one
        if 'm' in locals():
            with col2:
                map_html = m._repr_html_()
                st.download_button(
                    label="🗺️ Download Map (HTML)",
                    data=map_html,
                    file_name="graduated_colors_map.html",
                    mime="text/html"
                )

else:
    st.info("""
    ## 🚀 How to use this app:
    
    1. **Upload your CSV file** with region names and listing_count column
    2. **Upload your ArcGIS GeoJSON file** (polygon data preferred)
    3. **Select matching columns** (LocNombre or similar)
    4. **Configure graduated colors** for listing_count
    5. **View the interactive map** with darker colors for higher counts
    
    ### 🎨 Color Features:
    - **Graduated colors**: Higher listing counts = darker colors
    - **Multiple color schemes**: Blues, Greens, Reds, etc.
    - **Classification methods**: Equal interval, quantiles, natural breaks
    - **Customizable classes**: 3-7 color classes
    
    ### 📊 Requirements:
    - CSV must have a numeric `listing_count` column (or similar)
    - GeoJSON should contain polygon geometry (esriGeometryPolygon)
    - Location columns should match between files
    """)