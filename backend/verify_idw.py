import httpx
import numpy as np

def calculate_idw_aqi(ward_lat, ward_lon, stations, power=2):
    if not stations: return 200
    
    weights = []
    values = []
    min_dist = float('inf')
    nearest_station = None
    
    for station in stations:
        lat = station.get("lat", 0)
        lon = station.get("lon", 0)
        aqi = station.get("aqi", 0)
        if aqi <= 0: continue
        
        dist = np.sqrt((ward_lat - lat)**2 + (ward_lon - lon)**2)
        if dist < min_dist:
            min_dist = dist
            nearest_station = station
            
        if dist < 0.001: return int(aqi)
        
        weights.append(1 / (dist ** power))
        values.append(aqi)
    
    if not weights: return 200
    
    interpolated = np.sum(np.array(weights) * np.array(values)) / np.sum(weights)
    
    print(f"Ward ({ward_lat:.4f}, {ward_lon:.4f})")
    print(f"  Nearest Station: {nearest_station['station_name']} (Dist: {min_dist:.4f}, AQI: {nearest_station['aqi']})")
    print(f"  Interpolated AQI: {interpolated:.2f}")
    return int(interpolated)

try:
    data = httpx.get('http://localhost:8000/api/stations').json()
    stations = data['stations']
    print(f"Stations: {len(stations)}")
    
    # Test 1: Near Anand Vihar
    calculate_idw_aqi(28.6500, 77.3150, stations)
    
    # Test 2: Near Punjabi Bagh
    calculate_idw_aqi(28.6600, 77.1200, stations)

except Exception as e:
    print(e)
