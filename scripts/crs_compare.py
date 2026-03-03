#!/usr/bin/env python3
"""
氣象站坐標系統比較分析
比較不同坐標系統的差異並繪製地圖
"""

import os
import requests
import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from geopy.distance import geodesic
import seaborn as sns
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.font_manager import FontProperties

# 設定中文字體
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

class CWACoordinateComparison:
    def __init__(self):
        self.api_key = "CWA-0F19593F-BC83-4B93-8224-B626FD1A8B5C"
        self.base_url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore"
        self.dataset_id = "O-A0003-001"
    
    def fetch_weather_data(self):
        """獲取全台自動氣象站觀測資料"""
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
            print(f"API 請求失敗: {e}")
            return None
    
    def parse_coordinate_data(self, data):
        """解析坐標資料，提取兩組坐標"""
        if not data or 'records' not in data:
            return None
        
        stations = []
        records = data['records']['Station']
        
        for record in records:
            try:
                coordinates = record['GeoInfo']['Coordinates']
                
                # 提取兩組坐標
                coord_data = {
                    'station_id': record['StationId'],
                    'station_name': record['StationName'],
                    'location': record['GeoInfo']['CountyName'] + record['GeoInfo']['TownName']
                }
                
                # 第一組坐標
                if len(coordinates) > 0:
                    coord_data['lat1'] = float(coordinates[0]['StationLatitude'])
                    coord_data['lon1'] = float(coordinates[0]['StationLongitude'])
                    coord_data['crs1'] = coordinates[0].get('CoordinateSystem', 'Unknown')
                
                # 第二組坐標
                if len(coordinates) > 1:
                    coord_data['lat2'] = float(coordinates[1]['StationLatitude'])
                    coord_data['lon2'] = float(coordinates[1]['StationLongitude'])
                    coord_data['crs2'] = coordinates[1].get('CoordinateSystem', 'Unknown')
                
                # 計算距離（如果有兩組坐標）
                if len(coordinates) > 1:
                    coord1 = (coord_data['lat1'], coord_data['lon1'])
                    coord2 = (coord_data['lat2'], coord_data['lon2'])
                    distance = geodesic(coord1, coord2).meters
                    coord_data['distance_meters'] = distance
                
                stations.append(coord_data)
                
            except (KeyError, ValueError, TypeError) as e:
                print(f"解析站點資料時發生錯誤 {record.get('StationId', 'Unknown')}: {e}")
                continue
        
        return stations
    
    def plot_coordinate_comparison(self, stations_data):
        """繪製坐標比較圖 - 使用真實台灣地圖"""
        if not stations_data:
            print("沒有資料可繪製")
            return
        
        # 過濾有兩組坐標的測站
        valid_stations = [s for s in stations_data if 'lat2' in s and 'lon2' in s]
        
        if not valid_stations:
            print("沒有找到包含兩組坐標的測站")
            return
        
        # 創建地圖 - 使用Cartopy
        fig = plt.figure(figsize=(16, 12))
        ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
        
        # 設定台灣地圖範圍
        ax.set_extent([119.5, 122.5, 21.5, 25.5], crs=ccrs.PlateCarree())
        
        # 添加地理特徵
        ax.add_feature(cfeature.LAND.with_scale('10m'), facecolor='lightgray', edgecolor='black', alpha=0.3)
        ax.add_feature(cfeature.OCEAN.with_scale('10m'), facecolor='lightblue', alpha=0.3)
        ax.add_feature(cfeature.COASTLINE.with_scale('10m'), linewidth=1.5)
        ax.add_feature(cfeature.BORDERS.with_scale('10m'), linewidth=1, linestyle='--')
        ax.add_feature(cfeature.LAKES.with_scale('10m'), facecolor='lightblue', alpha=0.5)
        ax.add_feature(cfeature.RIVERS.with_scale('10m'), linewidth=0.5)
        
        # 添加網格線
        ax.gridlines(draw_labels=True, linewidth=0.5, alpha=0.5, linestyle='--')
        
        # 繪製第一組坐標（藍色圓形）
        lats1 = [s['lat1'] for s in valid_stations]
        lons1 = [s['lon1'] for s in valid_stations]
        ax.scatter(lons1, lats1, c='blue', alpha=0.8, s=100, label='第一組坐標', 
                  marker='o', edgecolors='darkblue', linewidth=1.5, transform=ccrs.PlateCarree())
        
        # 繪製第二組坐標（紅色三角形）
        lats2 = [s['lat2'] for s in valid_stations]
        lons2 = [s['lon2'] for s in valid_stations]
        ax.scatter(lons2, lats2, c='red', alpha=0.8, s=100, label='第二組坐標', 
                  marker='^', edgecolors='darkred', linewidth=1.5, transform=ccrs.PlateCarree())
        
        # 繪製連接線（表示同一測站的兩組坐標）
        for station in valid_stations:
            ax.plot([station['lon1'], station['lon2']], 
                   [station['lat1'], station['lat2']], 
                   'gray', alpha=0.6, linewidth=1, linestyle='--', transform=ccrs.PlateCarree())
        
        # 設定標籤
        ax.set_xlabel('經度 (Longitude)', fontsize=14)
        ax.set_ylabel('緯度 (Latitude)', fontsize=14)
        ax.set_title('氣象站坐標系統比較分析\n兩組坐標位置對照圖（均假設為WGS84 EPSG:4326）', 
                    fontsize=16, fontweight='bold', pad=20)
        
        # 創建圖例
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='blue', 
                      markersize=10, label='第一組坐標 (藍色圓形)', markeredgecolor='darkblue'),
            plt.Line2D([0], [0], marker='^', color='w', markerfacecolor='red', 
                      markersize=10, label='第二組坐標 (紅色三角形)', markeredgecolor='darkred'),
            plt.Line2D([0], [0], color='gray', linewidth=1, linestyle='--', 
                      alpha=0.6, label='坐標連接線 (同一測站)')
        ]
        ax.legend(handles=legend_elements, loc='upper right', fontsize=12, framealpha=0.9)
        
        # 添加說明文字
        explanation_text = """說明：
• 藍色圓形：第一組坐標位置
• 紅色三角形：第二組坐標位置  
• 虛線：連接同一測站的兩組坐標
• 所有坐標均假設為WGS84 EPSG:4326
• 背景為真實台灣地理地圖"""
        
        plt.text(0.02, 0.98, explanation_text, transform=ax.transAxes, 
                fontsize=11, verticalalignment='top', 
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9))
        
        # 儲存圖片
        plt.savefig('outputs/coordinate_comparison.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        print(f"已繪製 {len(valid_stations)} 個測站的坐標比較圖")
        print("圖例說明：")
        print("• 藍色圓形 = 第一組坐標")
        print("• 紅色三角形 = 第二組坐標")
        print("• 虛線 = 同一測站的兩組坐標連接")
        print("• 背景為真實台灣地理地圖")
    
    def analyze_distance_statistics(self, stations_data):
        """分析距離統計"""
        if not stations_data:
            return None
        
        # 過濾有距離資料的測站
        valid_stations = [s for s in stations_data if 'distance_meters' in s]
        
        if not valid_stations:
            print("沒有距離資料可分析")
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
        
        # 繪製距離分佈圖
        plt.figure(figsize=(12, 8))
        
        # 子圖1: 距離分佈直方圖
        plt.subplot(2, 2, 1)
        plt.hist(distances, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
        plt.xlabel('距離 (公尺)')
        plt.ylabel('測站數量')
        plt.title('坐標距離分佈')
        plt.grid(True, alpha=0.3)
        
        # 子圖2: 箱型圖
        plt.subplot(2, 2, 2)
        plt.boxplot(distances, vert=True)
        plt.ylabel('距離 (公尺)')
        plt.title('距離分佈箱型圖')
        plt.grid(True, alpha=0.3)
        
        # 子圖3: 統計摘要表格
        plt.subplot(2, 2, 3)
        plt.axis('off')
        stats_text = f"""
距離統計摘要：
總測站數: {stats['total_stations']}
平均距離: {stats['mean_distance']:.2f} 公尺
中位數距離: {stats['median_distance']:.2f} 公尺
最小距離: {stats['min_distance']:.2f} 公尺
最大距離: {stats['max_distance']:.2f} 公尺
標準差: {stats['std_distance']:.2f} 公尺
        """
        plt.text(0.1, 0.5, stats_text, fontsize=12, verticalalignment='center')
        
        # 子圖4: 距離排序圖
        plt.subplot(2, 2, 4)
        sorted_distances = sorted(distances)
        plt.plot(range(len(sorted_distances)), sorted_distances, 'o-', markersize=3)
        plt.xlabel('測站排名')
        plt.ylabel('距離 (公尺)')
        plt.title('測站距離排序')
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('outputs/distance_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        return stats
    
    def save_detailed_data(self, stations_data):
        """儲存詳細資料"""
        if not stations_data:
            return
        
        # 過濾有兩組坐標的測站
        valid_stations = [s for s in stations_data if 'lat2' in s and 'lon2' in s]
        
        if not valid_stations:
            print("沒有詳細資料可儲存")
            return
        
        # 創建DataFrame
        df = pd.DataFrame(valid_stations)
        
        # 重新排列欄位順序
        columns_order = ['station_id', 'station_name', 'location', 
                        'crs1', 'lat1', 'lon1', 
                        'crs2', 'lat2', 'lon2', 
                        'distance_meters']
        df = df[columns_order]
        
        # 儲存為CSV
        df.to_csv('outputs/coordinate_comparison_detailed.csv', index=False, encoding='utf-8-sig')
        print(f"詳細資料已儲存至: outputs/coordinate_comparison_detailed.csv")
        
        # 顯示前10筆資料
        print("\n前10筆測站坐標比較資料:")
        print(df.head(10).to_string(index=False))

def main():
    """主程式"""
    print("開始分析氣象站坐標系統差異...")
    
    try:
        # 確保輸出目錄存在
        os.makedirs('outputs', exist_ok=True)
        
        # 初始化分析器
        analyzer = CWACoordinateComparison()
        
        # 獲取資料
        print("正在從 CWA API 獲取資料...")
        raw_data = analyzer.fetch_weather_data()
        
        if raw_data:
            print("成功獲取資料，正在解析坐標...")
            
            # 解析坐標資料
            stations_data = analyzer.parse_coordinate_data(raw_data)
            
            if stations_data:
                print(f"成功解析 {len(stations_data)} 個測站資料")
                
                # 過濾有兩組坐標的測站
                valid_stations = [s for s in stations_data if 'lat2' in s and 'lon2' in s]
                print(f"其中 {len(valid_stations)} 個測站有兩組坐標資料")
                
                # 繪製坐標比較圖
                print("正在繪製坐標比較圖...")
                analyzer.plot_coordinate_comparison(stations_data)
                
                # 分析距離統計
                print("正在分析距離統計...")
                stats = analyzer.analyze_distance_statistics(stations_data)
                
                if stats:
                    print(f"\n=== 距離統計摘要 ===")
                    print(f"總測站數: {stats['total_stations']}")
                    print(f"平均距離: {stats['mean_distance']:.2f} 公尺")
                    print(f"中位數距離: {stats['median_distance']:.2f} 公尺")
                    print(f"最小距離: {stats['min_distance']:.2f} 公尺")
                    print(f"最大距離: {stats['max_distance']:.2f} 公尺")
                    print(f"標準差: {stats['std_distance']:.2f} 公尺")
                
                # 儲存詳細資料
                analyzer.save_detailed_data(stations_data)
                
            else:
                print("解析資料失敗")
        else:
            print("獲取資料失敗")
            
    except Exception as e:
        print(f"程式執行發生錯誤: {e}")

if __name__ == "__main__":
    main()
