import sys
import os

# Add backend directory to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    from config import DELHI_STATIONS
    print(f"Successfully imported DELHI_STATIONS.")
    print(f"Total stations: {len(DELHI_STATIONS)}")
    print("Sample newly added stations:", DELHI_STATIONS[-15:-5])
except Exception as e:
    print(f"Error importing config: {e}")
