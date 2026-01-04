import os
import asyncio
import httpx
import sys

# Add backend directory to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from config import DELHI_STATIONS, AQICN_TOKEN, AQICN_API_URL

async def validate_stations():
    if not AQICN_TOKEN:
        print("Error: AQICN_TOKEN not found.")
        return

    print(f"Validating {len(DELHI_STATIONS)} stations from config...")
    
    async with httpx.AsyncClient() as client:
        with open('debug_output.txt', 'w', encoding='utf-8') as f:
            for station_id in DELHI_STATIONS:
                try:
                    url = f"{AQICN_API_URL}/feed/{station_id}/?token={AQICN_TOKEN}"
                    response = await client.get(url)
                    data = response.json()
                    
                    if data.get("status") == "ok":
                        name = data.get('data', {}).get('city', {}).get('name')
                        f.write(f"✅ {station_id}: Found ({name})\n")
                        print(f"✅ {station_id}: Found")
                    else:
                        f.write(f"❌ {station_id}: Failed (Status: {data.get('status')}, Message: {data.get('data')})\n")
                        print(f"❌ {station_id}: Failed")
                except Exception as e:
                    f.write(f"⚠️ {station_id}: Error ({e})\n")
                    print(f"⚠️ {station_id}: Error")
                
                # Small delay to avoid rate limiting
                # await asyncio.sleep(0.1)
    print("Validation complete. Check debug_output.txt")

if __name__ == "__main__":
    asyncio.run(validate_stations())
