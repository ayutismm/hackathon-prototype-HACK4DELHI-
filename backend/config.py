"""
Configuration Module for Delhi Pollution Dashboard
===================================================
Loads environment variables and provides configuration constants.
"""

import os
from pathlib import Path
from typing import List

# Try to load .env file
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    load_dotenv(env_path)
except ImportError:
    pass  # python-dotenv not installed, rely on system env vars

# ============================================================================
# API KEYS
# ============================================================================

# CPCB API Key from data.gov.in
CPCB_API_KEY: str = os.getenv("CPCB_API_KEY", "")

# AQICN Token
AQICN_TOKEN: str = os.getenv("AQICN_TOKEN", "")

# Groq API Key (for AI analysis)
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

# OpenWeatherMap API Key (for weather data)
OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "")

# ============================================================================
# API ENDPOINTS
# ============================================================================

# CPCB via data.gov.in
CPCB_API_URL = "https://api.data.gov.in/resource/3b01bcb8-0b14-4abf-b6f2-c1bfd384ba69"

# AQICN API
AQICN_API_URL = "https://api.waqi.info"

# OpenAQ v3 API
OPENAQ_API_URL = "https://api.openaq.org/v3"

# ============================================================================
DELHI_STATIONS = [
    # Major monitoring stations
    "delhi",
    "delhi/anand-vihar",
    "delhi/r.k.-puram",
    "delhi/dwarka",
    "delhi/shaheed-sukhdev-college-of-business-studies--rohini",
    "delhi/punjabi-bagh",
    "delhi/dite-okhla",
    "delhi/pooth-khurd--bawana",
    "delhi/iti-jahangirpuri",
    "delhi/igi-airport",
    "delhi/shadipur",
    "delhi/siri-fort",
    "delhi/mandir-marg",
    "delhi/ito",
    "delhi/lodhi-road",
    # Additional NCR stations
    "delhi/delhi-institute-of-tool-engineering--wazirpur",
    "delhi/mother-dairy-plant--parparganj",
    "delhi/jawaharlal-nehru-stadium",
    "delhi/dtu",
    "delhi/north-campus",
    "delhi/dr.-karni-singh-shooting-range",
    "delhi/burari-crossing",
    "delhi/major-dhyan-chand-national-stadium",
    "delhi/alipur",
    "delhi/narela",
    "delhi/mundka",
    "delhi/sonia-vihar-water-treatment-plant-djb",
    # Newly found stations
    "delhi/pusa",
    "delhi/pgdav-college--sriniwaspuri",
    "delhi/satyawati-college",
    "delhi/iti-shahdra--jhilmil-industrial-area",
    "india/noida/sector-1",
    "india/new-delhi/us-embassy",
    "delhi/ihbas",
    # NCR nearby cities for broader coverage
    "noida",
    "gurgaon",
    "faridabad",
    "ghaziabad",
]

# ============================================================================
# CACHE SETTINGS
# ============================================================================

# Cache Time-To-Live in minutes
CACHE_TTL_MINUTES: int = int(os.getenv("CACHE_TTL_MINUTES", "5"))

# ============================================================================
# API PRIORITY
# ============================================================================

def get_api_priority() -> List[str]:
    """Get API priority order from environment or default"""
    # CPCB commented out for faster startup - can re-enable later
    priority_str = os.getenv("API_PRIORITY", "aqicn,openaq")  # removed cpcb
    return [p.strip().lower() for p in priority_str.split(",")]

API_PRIORITY: List[str] = get_api_priority()

# ============================================================================
# VALIDATION
# ============================================================================

def validate_config():
    """Check if required API keys are configured"""
    missing = []
    
    if not CPCB_API_KEY or CPCB_API_KEY == "your_data_gov_in_api_key_here":
        missing.append("CPCB_API_KEY")
    
    if not AQICN_TOKEN or AQICN_TOKEN == "your_aqicn_token_here":
        missing.append("AQICN_TOKEN")
    
    return {
        "valid": len(missing) == 0,
        "missing": missing,
        "available_apis": [
            api for api in ["cpcb", "aqicn", "openaq"]
            if api == "openaq" or (api == "cpcb" and CPCB_API_KEY) or (api == "aqicn" and AQICN_TOKEN)
        ]
    }
