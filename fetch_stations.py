import os
import asyncio
import httpx
import json
from dotenv import load_dotenv

load_dotenv('backend/.env')

AQICN_TOKEN = os.getenv("AQICN_TOKEN")
AQICN_API_URL = "https://api.waqi.info"

async def fetch_delhi_stations():
    if not AQICN_TOKEN:
        print("Error: AQICN_TOKEN not found in environment variables.")
        return

    print(f"Searching for stations in Delhi using token: {AQICN_TOKEN[:5]}...")
    
    async with httpx.AsyncClient() as client:
        try:
            # Search for "Delhi"
            url = f"{AQICN_API_URL}/search/?keyword=Delhi&token={AQICN_TOKEN}"
            response = await client.get(url)
            data = response.json()
            
            if data.get("status") != "ok":
                print(f"Error: API returned status {data.get('status')}")
                return

            stations = data.get("data", [])
            print(f"Found {len(stations)} stations matching 'Delhi'.")
            
            # Filter for stations that are actually in Delhi (optional, but good to check)
            # The search might return stations with "Delhi" in the name but elsewhere, 
            # though usually it's accurate for a city search.
            
            delhi_stations = []
            for station in stations:
                # print(f"- {station.get('uid')}: {station.get('station', {}).get('name')} (URL: {station.get('station', {}).get('url')})")
                delhi_stations.append(station.get('station', {}).get('url'))

            print(f"Found {len(delhi_stations)} stations.")
            
            with open('found_stations.json', 'w') as f:
                json.dump(delhi_stations, f, indent=2)
            print("Saved list to found_stations.json")
            
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(fetch_delhi_stations())
