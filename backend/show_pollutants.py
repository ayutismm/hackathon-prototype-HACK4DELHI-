import httpx

print("=== POLLUTANT BREAKDOWN FROM AQICN ===\n")

stations = ['delhi', 'delhi/anand-vihar', 'noida']

for station in stations:
    try:
        r = httpx.get(f'https://api.waqi.info/feed/{station}/?token=094940392a04f517f5534565c3910867fe47a785', timeout=10)
        data = r.json()
        if data.get('status') == 'ok':
            info = data['data']
            name = info.get('city', {}).get('name', station)
            aqi = info.get('aqi', 'N/A')
            iaqi = info.get('iaqi', {})
            dominant = info.get('dominentpol', 'Unknown')
            
            print(f"📍 {name}")
            print(f"   AQI: {aqi}")
            print(f"   🔴 Dominant Pollutant: {dominant.upper()}")
            print(f"   Breakdown:")
            
            # Show each pollutant
            pollutants = {
                'pm25': 'PM2.5',
                'pm10': 'PM10', 
                'no2': 'NO₂',
                'so2': 'SO₂',
                'co': 'CO',
                'o3': 'O₃'
            }
            for key, label in pollutants.items():
                if key in iaqi:
                    val = iaqi[key].get('v', 'N/A')
                    marker = " ⬅ DOMINANT" if key == dominant else ""
                    print(f"     {label}: {val}{marker}")
            print()
    except Exception as e:
        print(f"{station}: Error - {e}")

print("The dominant pollutant is what's driving the AQI value!")
