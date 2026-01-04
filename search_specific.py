import os
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv('backend/.env')

AQICN_TOKEN = os.getenv("AQICN_TOKEN")
AQICN_API_URL = "https://api.waqi.info"

KEYWORDS = [
    "Airport"
]

async def search_keywords():
    if not AQICN_TOKEN:
        print("Error: AQICN_TOKEN not found.")
        return

    async with httpx.AsyncClient() as client:
        with open('search_results.txt', 'w', encoding='utf-8') as f:
            for keyword in KEYWORDS:
                try:
                    url = f"{AQICN_API_URL}/search/?keyword={keyword}&token={AQICN_TOKEN}"
                    response = await client.get(url)
                    data = response.json()
                    
                    f.write(f"\n--- Results for '{keyword}' ---\n")
                    print(f"Searching for '{keyword}'...")
                    if data.get("status") == "ok":
                        stations = data.get("data", [])
                        for s in stations:
                            line = f"  - {s.get('uid')}: {s.get('station', {}).get('name')} -> {s.get('station', {}).get('url')}\n"
                            f.write(line)
                    else:
                        f.write("  No data found or error.\n")
                except Exception as e:
                    f.write(f"  Error: {e}\n")
    print("Search complete. Check search_results.txt")

if __name__ == "__main__":
    asyncio.run(search_keywords())
