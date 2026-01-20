# Alquileres Temporales - Bogotá

A project for analyzing and visualizing temporary rental listings (Airbnb) data for Bogotá, Colombia. This repository contains tools for data collection, processing, and interactive mapping.

## 📁 Project Structure

```
alquileres-temporales-dev/
├── airdna/              # AirDNA data scraping tools
├── maps/                # Mapping data and visualizations
├── raw-data/            # Raw geographic data (GeoJSON files)
├── app.py               # Streamlit app (basic version)
├── app2.py              # Streamlit app (advanced with graduated colors)
├── converter.py         # ArcGIS GeoJSON to standard GeoJSON converter
└── requirements.txt     # Python dependencies
```

## 🚀 Quick Start

### Installation

1. Clone this repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the Streamlit Apps

**Basic Map Visualization:**
```bash
streamlit run app.py
```

**Advanced Map with Graduated Colors:**
```bash
streamlit run app2.py
```

## 📚 Documentation

### [AirDNA Data Scraping Guide](./airdna/README.md)

For instructions on scraping AirDNA data, processing HAR files, and generating cleaned CSV files, see the [AirDNA README](./airdna/README.md).

## 🗺️ Features

- **Interactive Maps**: Visualize rental listings data on interactive Folium maps
- **Graduated Colors**: Color-code geographic regions by listing count with customizable color schemes
- **Data Processing**: Convert ArcGIS GeoJSON to standard GeoJSON format
- **Data Collection**: Scrape and process AirDNA data by localidad (neighborhood)

## 📊 Main Components

- **app2.py**: Advanced Streamlit application with graduated color mapping, multiple classification methods, and interactive features
- **app.py**: Basic Streamlit application for GeoJSON visualization
- **converter.py**: Utility to convert ArcGIS GeoJSON format to standard GeoJSON
- **airdna/**: Collection of Jupyter notebooks for scraping and processing AirDNA data

## 🔧 Requirements

See `requirements.txt` for full list of dependencies. Key packages include:
- streamlit
- pandas
- geopandas
- folium
- matplotlib
- numpy

## 📝 Notes

- The project focuses on Bogotá's localidades (neighborhoods)
- Data sources include AirDNA and ArcGIS GeoJSON files
- Output formats include CSV and interactive HTML maps
