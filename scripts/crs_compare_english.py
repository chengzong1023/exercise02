#!/usr/bin/env python3
"""
Weather Station Coordinate System Comparison Analysis
Comparing different coordinate systems and plotting on real Taiwan map
"""

import os
import requests
import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from geopy.distance import geodesic
import cartopy.crs as ccrs
import cartopy.feature as cfeature

class CWACoordinateComparison:
    def __init__(self):
        self.api_key = "CWA-0F19593F-BC83-4B93-8224-B626FD1A8B5C"
        self.base_url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore"
        self.dataset_id = "O-A0003-001"
    
    def fetch_weather_data(self):
        """Get weather station data from CWA API"""
        url = f"{self.base_url}/{self.dataset_id}"
        params = {
            'Authorization': self.api_key,
            'format': 'JSON'
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            return None
    
    def parse_coordinate_data(self, data):
        """Parse coordinate data, extract both coordinate sets"""
        if not data or 'records' not in data:
            return None
        
        stations = []
        records = data['records']['Station']
        
        for record in records:
            try:
                coordinates = record['GeoInfo']['Coordinates']
                
                # Extract coordinate data
                coord_data = {
                    'station_id': record['StationId'],
                    'station_name': record['StationName'],
                    'location': record['GeoInfo']['CountyName'] + record['GeoInfo']['TownName']
                }
                
                # First coordinate set - likely TWD97 (Taiwan Datum 1997)
                if len(coordinates) > 0:
                    coord_data['lat1'] = float(coordinates[0]['StationLatitude'])
                    coord_data['lon1'] = float(coordinates[0]['StationLongitude'])
                    coord_data['crs1'] = coordinates[0].get('CoordinateSystem', 'TWD97')
                
                # Second coordinate set - likely WGS84 (GPS standard)
                if len(coordinates) > 1:
                    coord_data['lat2'] = float(coordinates[1]['StationLatitude'])
                    coord_data['lon2'] = float(coordinates[1]['StationLongitude'])
                    coord_data['crs2'] = coordinates[1].get('CoordinateSystem', 'WGS84')
                
                # Calculate distance (if both coordinate sets exist)
                if len(coordinates) > 1:
                    coord1 = (coord_data['lat1'], coord_data['lon1'])
                    coord2 = (coord_data['lat2'], coord_data['lon2'])
                    distance = geodesic(coord1, coord2).meters
                    coord_data['distance_meters'] = distance
                
                stations.append(coord_data)
                
            except (KeyError, ValueError, TypeError) as e:
                print(f"Error parsing station data {record.get('StationId', 'Unknown')}: {e}")
                continue
        
        return stations
    
    def plot_coordinate_comparison(self, stations_data):
        """Plot coordinate comparison on real Taiwan map"""
        if not stations_data:
            print("No data to plot")
            return
        
        # Filter stations with two coordinate sets
        valid_stations = [s for s in stations_data if 'lat2' in s and 'lon2' in s]
        
        if not valid_stations:
            print("No stations with two coordinate sets found")
            return
        
        # Create map using Cartopy
        fig = plt.figure(figsize=(16, 12))
        ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
        
        # Set Taiwan map extent
        ax.set_extent([119.5, 122.5, 21.5, 25.5], crs=ccrs.PlateCarree())
        
        # Add geographic features
        ax.add_feature(cfeature.LAND.with_scale('10m'), facecolor='lightgray', edgecolor='black', alpha=0.3)
        ax.add_feature(cfeature.OCEAN.with_scale('10m'), facecolor='lightblue', alpha=0.3)
        ax.add_feature(cfeature.COASTLINE.with_scale('10m'), linewidth=1.5)
        ax.add_feature(cfeature.BORDERS.with_scale('10m'), linewidth=1, linestyle='--')
        ax.add_feature(cfeature.LAKES.with_scale('10m'), facecolor='lightblue', alpha=0.5)
        ax.add_feature(cfeature.RIVERS.with_scale('10m'), linewidth=0.5)
        
        # Add grid lines
        ax.gridlines(draw_labels=True, linewidth=0.5, alpha=0.5, linestyle='--')
        
        # Plot first coordinate set (blue circles) - TWD97
        lats1 = [s['lat1'] for s in valid_stations]
        lons1 = [s['lon1'] for s in valid_stations]
        ax.scatter(lons1, lats1, c='blue', alpha=0.8, s=100, label='TWD97 Coordinates (Blue Circles)', 
                  marker='o', edgecolors='darkblue', linewidth=1.5, transform=ccrs.PlateCarree())
        
        # Plot second coordinate set (red triangles) - WGS84
        lats2 = [s['lat2'] for s in valid_stations]
        lons2 = [s['lon2'] for s in valid_stations]
        ax.scatter(lons2, lats2, c='red', alpha=0.8, s=100, label='WGS84 Coordinates (Red Triangles)', 
                  marker='^', edgecolors='darkred', linewidth=1.5, transform=ccrs.PlateCarree())
        
        # Draw connection lines (same station coordinates)
        for station in valid_stations:
            ax.plot([station['lon1'], station['lon2']], 
                   [station['lat1'], station['lat2']], 
                   'gray', alpha=0.6, linewidth=1, linestyle='--', transform=ccrs.PlateCarree())
        
        # Set labels
        ax.set_xlabel('Longitude', fontsize=14)
        ax.set_ylabel('Latitude', fontsize=14)
        ax.set_title('Weather Station Coordinate System Comparison\nTWD97 vs WGS84 (Both treated as EPSG:4326)', 
                    fontsize=16, fontweight='bold', pad=20)
        
        # Create legend
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='blue', 
                      markersize=10, label='TWD97 (Blue Circles)\nTaiwan Datum 1997', markeredgecolor='darkblue'),
            plt.Line2D([0], [0], marker='^', color='w', markerfacecolor='red', 
                      markersize=10, label='WGS84 (Red Triangles)\nGPS Standard System', markeredgecolor='darkred'),
            plt.Line2D([0], [0], color='gray', linewidth=1, linestyle='--', 
                      alpha=0.6, label='Connection Lines\n(Same Station)')
        ]
        ax.legend(handles=legend_elements, loc='upper right', fontsize=11, framealpha=0.9)
        
        # Add explanation text
        explanation_text = """Coordinate System Information:
• Blue Circles: TWD97 (Taiwan Datum 1997)
  - Official Taiwan mapping standard
  - Used by government agencies
  - Compatible with WGS84 within cm-level

• Red Triangles: WGS84 (World Geodetic System 1984)
  - GPS standard coordinate system
  - Global positioning reference
  - Used by most GPS devices

• Note: Both plotted as if they were WGS84 EPSG:4326
• Background: Real Taiwan geographic map"""
        
        plt.text(0.02, 0.98, explanation_text, transform=ax.transAxes, 
                fontsize=10, verticalalignment='top', 
                bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9))
        
        # Save image
        plt.savefig('outputs/coordinate_comparison_with_crs.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        print(f"Plotted {len(valid_stations)} stations coordinate comparison")
        print("Coordinate System Information:")
        print("• Blue Circles = TWD97 (Taiwan Datum 1997)")
        print("• Red Triangles = WGS84 (GPS Standard)")
        print("• Dashed Lines = Same station coordinate connection")
        print("• Background = Real Taiwan geographic map")
        print("• Note: Both treated as WGS84 EPSG:4326 for visualization")
    
    def analyze_distance_statistics(self, stations_data):
        """Analyze distance statistics"""
        if not stations_data:
            return None
        
        # Filter stations with distance data
        valid_stations = [s for s in stations_data if 'distance_meters' in s]
        
        if not valid_stations:
            print("No distance data to analyze")
            return None
        
        distances = [s['distance_meters'] for s in valid_stations]
        
        stats = {
            'total_stations': len(valid_stations),
            'mean_distance': np.mean(distances),
            'median_distance': np.median(distances),
            'min_distance': np.min(distances),
            'max_distance': np.max(distances),
            'std_distance': np.std(distances)
        }
        
        # Plot distance distribution
        plt.figure(figsize=(12, 8))
        
        # Subplot 1: Distance histogram
        plt.subplot(2, 2, 1)
        plt.hist(distances, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
        plt.xlabel('Distance (meters)')
        plt.ylabel('Number of Stations')
        plt.title('Coordinate Distance Distribution')
        plt.grid(True, alpha=0.3)
        
        # Subplot 2: Box plot
        plt.subplot(2, 2, 2)
        plt.boxplot(distances, vert=True)
        plt.ylabel('Distance (meters)')
        plt.title('Distance Distribution Box Plot')
        plt.grid(True, alpha=0.3)
        
        # Subplot 3: Statistics summary table
        plt.subplot(2, 2, 3)
        plt.axis('off')
        stats_text = f"""
Distance Statistics Summary:
Total Stations: {stats['total_stations']}
Mean Distance: {stats['mean_distance']:.2f} meters
Median Distance: {stats['median_distance']:.2f} meters
Min Distance: {stats['min_distance']:.2f} meters
Max Distance: {stats['max_distance']:.2f} meters
Std Deviation: {stats['std_distance']:.2f} meters
        """
        plt.text(0.1, 0.5, stats_text, fontsize=12, verticalalignment='center')
        
        # Subplot 4: Distance ranking plot
        plt.subplot(2, 2, 4)
        sorted_distances = sorted(distances)
        plt.plot(range(len(sorted_distances)), sorted_distances, 'o-', markersize=3)
        plt.xlabel('Station Rank')
        plt.ylabel('Distance (meters)')
        plt.title('Station Distance Ranking')
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('outputs/distance_analysis_english.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        return stats
    
    def save_detailed_data(self, stations_data):
        """Save detailed data"""
        if not stations_data:
            return
        
        # Filter stations with two coordinate sets
        valid_stations = [s for s in stations_data if 'lat2' in s and 'lon2' in s]
        
        if not valid_stations:
            print("No detailed data to save")
            return
        
        # Create DataFrame
        df = pd.DataFrame(valid_stations)
        
        # Reorder columns
        columns_order = ['station_id', 'station_name', 'location', 
                        'crs1', 'lat1', 'lon1', 
                        'crs2', 'lat2', 'lon2', 
                        'distance_meters']
        df = df[columns_order]
        
        # Save as CSV
        df.to_csv('outputs/coordinate_comparison_detailed_english.csv', index=False, encoding='utf-8-sig')
        print(f"Detailed data saved to: outputs/coordinate_comparison_detailed_english.csv")
        
        # Show first 10 records
        print("\nFirst 10 station coordinate comparison data:")
        print(df.head(10).to_string(index=False))

def main():
    """Main program"""
    print("Starting weather station coordinate system comparison analysis...")
    
    try:
        # Ensure output directory exists
        os.makedirs('outputs', exist_ok=True)
        
        # Initialize analyzer
        analyzer = CWACoordinateComparison()
        
        # Get data
        print("Getting data from CWA API...")
        raw_data = analyzer.fetch_weather_data()
        
        if raw_data:
            print("Data retrieved successfully, parsing coordinates...")
            
            # Parse coordinate data
            stations_data = analyzer.parse_coordinate_data(raw_data)
            
            if stations_data:
                print(f"Successfully parsed {len(stations_data)} stations")
                
                # Filter stations with two coordinate sets
                valid_stations = [s for s in stations_data if 'lat2' in s and 'lon2' in s]
                print(f"Found {len(valid_stations)} stations with two coordinate sets")
                
                # Plot coordinate comparison
                print("Plotting coordinate comparison map...")
                analyzer.plot_coordinate_comparison(stations_data)
                
                # Analyze distance statistics
                print("Analyzing distance statistics...")
                stats = analyzer.analyze_distance_statistics(stations_data)
                
                if stats:
                    print(f"\n=== Distance Statistics Summary ===")
                    print(f"Total Stations: {stats['total_stations']}")
                    print(f"Mean Distance: {stats['mean_distance']:.2f} meters")
                    print(f"Median Distance: {stats['median_distance']:.2f} meters")
                    print(f"Min Distance: {stats['min_distance']:.2f} meters")
                    print(f"Max Distance: {stats['max_distance']:.2f} meters")
                    print(f"Std Deviation: {stats['std_distance']:.2f} meters")
                
                # Save detailed data
                analyzer.save_detailed_data(stations_data)
                
            else:
                print("Data parsing failed")
        else:
            print("Data retrieval failed")
            
    except Exception as e:
        print(f"Program execution error: {e}")

if __name__ == "__main__":
    main()
