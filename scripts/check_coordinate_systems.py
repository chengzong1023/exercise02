#!/usr/bin/env python3
"""
Check coordinate systems in CWA API data
"""

import requests

def main():
    api_key = "CWA-0F19593F-BC83-4B93-8224-B626FD1A8B5C"
    base_url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore"
    dataset_id = "O-A0003-001"
    
    url = f"{base_url}/{dataset_id}"
    params = {
        'Authorization': api_key,
        'format': 'JSON'
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data and 'records' in data:
            stations = data['records']['Station']
            
            print("Coordinate Systems Analysis:")
            print("=" * 50)
            
            coordinate_systems = set()
            crs_examples = {}
            
            for i, station in enumerate(stations[:10]):  # Check first 10 stations
                print(f"\nStation {i+1}: {station.get('StationName', 'Unknown')}")
                print(f"Station ID: {station.get('StationId', 'Unknown')}")
                
                coordinates = station['GeoInfo']['Coordinates']
                
                for j, coord in enumerate(coordinates):
                    crs = coord.get('CoordinateSystem', 'Unknown')
                    lat = coord.get('StationLatitude', 'N/A')
                    lon = coord.get('StationLongitude', 'N/A')
                    
                    print(f"  Coordinate Set {j+1}:")
                    print(f"    CRS: {crs}")
                    print(f"    Lat: {lat}")
                    print(f"    Lon: {lon}")
                    
                    coordinate_systems.add(crs)
                    
                    if crs not in crs_examples:
                        crs_examples[crs] = {
                            'station': station.get('StationName', 'Unknown'),
                            'lat': lat,
                            'lon': lon,
                            'index': j+1
                        }
            
            print(f"\nAll Coordinate Systems Found:")
            for crs in sorted(coordinate_systems):
                example = crs_examples[crs]
                print(f"  {crs}:")
                print(f"    Example: {example['station']} - Set {example['index']}")
                print(f"    Coordinates: ({example['lat']}, {example['lon']})")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
