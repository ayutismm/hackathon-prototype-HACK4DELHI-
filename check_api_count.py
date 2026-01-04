import httpx
import asyncio

async def check_stations():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/api/stations")
            if response.status_code == 200:
                data = response.json()
                stations = data.get("stations", [])
                print(f"Total stations returned: {len(stations)}")
                print("Station Names:")
                for s in stations:
                    print(f"- {s.get('station_name')} (AQI: {s.get('aqi')})")
            else:
                print(f"Error: Status code {response.status_code}")
    except Exception as e:
        print(f"Error connecting to backend: {e}")

if __name__ == "__main__":
    asyncio.run(check_stations())
