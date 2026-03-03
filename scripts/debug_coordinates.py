#!/usr/bin/env python3
"""
調試氣象站坐標資料
"""

from cwa_weather_api import CWAWeatherAPI
import json

def main():
    api = CWAWeatherAPI()
    data = api.fetch_weather_data()
    
    if data and 'records' in data:
        station = data['records']['Station'][0]
        print('第一個測站的坐標資訊:')
        print(json.dumps(station['GeoInfo']['Coordinates'], indent=2, ensure_ascii=False))
        
        print('\n坐標詳細資訊:')
        for i, coord in enumerate(station['GeoInfo']['Coordinates']):
            print(f'坐標 {i}:')
            print(f"  緯度: {coord.get('StationLatitude', 'N/A')}")
            print(f"  經度: {coord.get('StationLongitude', 'N/A')}")
            print(f"  坐標系統: {coord.get('CoordinateSystem', 'N/A')}")
            print()

if __name__ == "__main__":
    main()
