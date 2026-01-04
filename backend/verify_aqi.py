import httpx

print("=== AQI DATA VERIFICATION ===\n")

# Get official AQICN values
test_stations = ['delhi', 'delhi/anand-vihar', 'noida', 'gurgaon']
print("OFFICIAL AQICN VALUES:")
for station in test_stations:
    try:
        r = httpx.get(f'https://api.waqi.info/feed/{station}/?token=094940392a04f517f5534565c3910867fe47a785', timeout=10)
        data = r.json()
        if data.get('status') == 'ok':
            info = data['data']
            name = info.get('city', {}).get('name', station)
            aqi = info.get('aqi', 'N/A')
            print(f"  {name}: AQI {aqi}")
    except Exception as e:
        print(f"  {station}: Error")

print("\nOUR DASHBOARD DATA:")
our_data = httpx.get('http://localhost:8000/api/stations').json()
print(f"  Source: {our_data['source']}")
print(f"  Stations: {our_data['count']}")
for s in our_data['stations'][:5]:
    print(f"  {s['station_name']}: AQI {s['aqi']}")

print("\n=== VERIFICATION COMPLETE ===")
