"""
Delhi Ward-Wise Pollution Action Dashboard - Backend API
=========================================================
A FastAPI backend with REAL-TIME pollution data from multiple APIs:
- CPCB (Central Pollution Control Board via data.gov.in)
- AQICN (World Air Quality Index)
- OpenAQ v3

Uses Inverse Distance Weighting (IDW) interpolation for ward-level estimates.

Author: AI Assistant for Hack4Delhi Hackathon
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
import numpy as np
import random
import asyncio
import json
import os
from datetime import datetime
from contextlib import asynccontextmanager

# Import our modules
from config import validate_config, CACHE_TTL_MINUTES, GROQ_API_KEY, OPENWEATHER_API_KEY
from cache import aqi_cache
from aqi_fetcher import aggregator, get_live_stations, get_api_status
from ai_analyzer import analyze_all_wards, get_ward_ai_analysis, get_cached_weather, ai_cache

# ============================================================================
# PYDANTIC MODELS FOR DATA VALIDATION
# ============================================================================

class Coordinates(BaseModel):
    """Geographic coordinates"""
    lat: float = Field(..., description="Latitude")
    lon: float = Field(..., description="Longitude")

class WardSummary(BaseModel):
    """Summary data for a ward (used in GET /wards)"""
    id: int
    name: str
    ward_no: str
    coordinates: Coordinates
    aqi: int
    color_code: str
    dominant_source: str
    trend: str

class PollutionBreakdown(BaseModel):
    """Breakdown of pollution sources"""
    traffic: float
    industrial: float
    construction_dust: float
    biomass_burning: float
    other: float

class WardDetail(BaseModel):
    """Detailed data for a specific ward"""
    id: int
    name: str
    ward_no: str
    coordinates: Coordinates
    aqi: int
    color_code: str
    dominant_source: str
    trend: str
    pollution_breakdown: PollutionBreakdown
    recommendations: List[str]
    population: int
    area_sqkm: float
    last_updated: str
    pollutants: Optional[Dict[str, Optional[float]]] = None

class SimulateRequest(BaseModel):
    """Request body for simulation endpoint"""
    traffic_reduction_percentage: float = Field(..., ge=0, le=100)

class ReportRequest(BaseModel):
    """Request body for citizen reports"""
    lat: float
    lon: float
    issue_type: str = Field(..., description="Type: Burning, Dust, Smoke, Industrial, Other")
    description: Optional[str] = None

class ReportResponse(BaseModel):
    """Response for report submission"""
    id: int
    message: str
    timestamp: str

# ============================================================================
# REAL DELHI WARD DATA (Extracted from Delhi_Wards.geojson)
# ============================================================================

DELHI_WARDS = [
    {"name": "Delhi Cantt Charge 1", "ward_no": "CANT_1", "lat": 28.6189, "lon": 77.1304},
    {"name": "Delhi Cantt Charge 2", "ward_no": "CANT_2", "lat": 28.6100, "lon": 77.1420},
    {"name": "Delhi Cantt Charge 3", "ward_no": "CANT_3", "lat": 28.5890, "lon": 77.1498},
    {"name": "Delhi Cantt Charge 4", "ward_no": "CANT_4", "lat": 28.5620, "lon": 77.1450},
    {"name": "Delhi Cantt Charge 5", "ward_no": "CANT_5", "lat": 28.5750, "lon": 77.1330},
    {"name": "Delhi Cantt Charge 6", "ward_no": "CANT_6", "lat": 28.5820, "lon": 77.1050},
    {"name": "Delhi Cantt Charge 7", "ward_no": "CANT_7", "lat": 28.6030, "lon": 77.1150},
    {"name": "Delhi Cantt Charge 8", "ward_no": "CANT_8", "lat": 28.5980, "lon": 77.1250},
    {"name": "NDMC Charge 1", "ward_no": "NDMC_1", "lat": 28.6250, "lon": 77.2280},
    {"name": "NDMC Charge 2", "ward_no": "NDMC_2", "lat": 28.6380, "lon": 77.2150},
    {"name": "NDMC Charge 3", "ward_no": "NDMC_3", "lat": 28.6280, "lon": 77.1900},
    {"name": "NDMC Charge 4", "ward_no": "NDMC_4", "lat": 28.6200, "lon": 77.2100},
    {"name": "NDMC Charge 5", "ward_no": "NDMC_5", "lat": 28.6020, "lon": 77.2200},
    {"name": "NDMC Charge 6", "ward_no": "NDMC_6", "lat": 28.5850, "lon": 77.2200},
    {"name": "NDMC Charge 7", "ward_no": "NDMC_7", "lat": 28.5720, "lon": 77.2050},
    {"name": "NDMC Charge 8", "ward_no": "NDMC_8", "lat": 28.5780, "lon": 77.1950},
    {"name": "NDMC Charge 9", "ward_no": "NDMC_9", "lat": 28.5880, "lon": 77.1800},
    {"name": "Chandni Chowk", "ward_no": "80", "lat": 28.6580, "lon": 77.2300},
    {"name": "Minto Road", "ward_no": "81", "lat": 28.6400, "lon": 77.2350},
    {"name": "Kucha Pandit", "ward_no": "82", "lat": 28.6490, "lon": 77.2250},
    {"name": "Bazar Sitaram", "ward_no": "83", "lat": 28.6480, "lon": 77.2320},
    {"name": "Idgah Road", "ward_no": "85", "lat": 28.6550, "lon": 77.2180},
    {"name": "Khyala", "ward_no": "108", "lat": 28.6520, "lon": 77.1050},
    {"name": "Janak Puri North", "ward_no": "109", "lat": 28.6280, "lon": 77.0950},
    {"name": "Mukherjee Nagar", "ward_no": "11", "lat": 28.7100, "lon": 77.2100},
    {"name": "Janak Puri West", "ward_no": "117", "lat": 28.6230, "lon": 77.0800},
    {"name": "Janak Puri South", "ward_no": "118", "lat": 28.6160, "lon": 77.0950},
    {"name": "Milap Nagar", "ward_no": "119", "lat": 28.6180, "lon": 77.0650},
    {"name": "Sita Puri", "ward_no": "120", "lat": 28.6100, "lon": 77.0750},
    {"name": "Chhawla", "ward_no": "133", "lat": 28.5550, "lon": 76.9350},
    {"name": "Nangli Sakrawati", "ward_no": "134", "lat": 28.5800, "lon": 77.0050},
    {"name": "Kakraula", "ward_no": "135", "lat": 28.6050, "lon": 77.0280},
    {"name": "Khera", "ward_no": "140", "lat": 28.5950, "lon": 76.9550},
    {"name": "Dilshad Garden", "ward_no": "241", "lat": 28.6850, "lon": 77.3150},
    {"name": "New Seema Puri", "ward_no": "242", "lat": 28.6880, "lon": 77.3280},
    {"name": "Nand Nagri", "ward_no": "243", "lat": 28.6950, "lon": 77.3080},
    {"name": "Sunder Nagari", "ward_no": "244", "lat": 28.6980, "lon": 77.3180},
    {"name": "Durga Puri", "ward_no": "245", "lat": 28.6900, "lon": 77.2950},
    {"name": "Ashok Nagar", "ward_no": "246", "lat": 28.6960, "lon": 77.2930},
    {"name": "Ram Nagar", "ward_no": "247", "lat": 28.6780, "lon": 77.2870},
    {"name": "Welcome Colony", "ward_no": "248", "lat": 28.6780, "lon": 77.2750},
    {"name": "Chauhan Banger", "ward_no": "249", "lat": 28.6870, "lon": 77.2700},
    {"name": "Zaffrabad", "ward_no": "250", "lat": 28.6730, "lon": 77.2680},
    {"name": "Maujpur", "ward_no": "252", "lat": 28.6920, "lon": 77.2760},
    {"name": "Ghonda", "ward_no": "255", "lat": 28.6930, "lon": 77.2620},
    {"name": "Yamuna Vihar", "ward_no": "256", "lat": 28.7010, "lon": 77.2700},
    {"name": "Subhash Mohalla", "ward_no": "257", "lat": 28.6960, "lon": 77.2760},
    {"name": "Kardam Puri", "ward_no": "258", "lat": 28.6950, "lon": 77.2880},
    {"name": "Janta Colony", "ward_no": "259", "lat": 28.6830, "lon": 77.2800},
    {"name": "Babar Pur", "ward_no": "260", "lat": 28.6850, "lon": 77.2880},
    {"name": "Jiwanpur", "ward_no": "261", "lat": 28.7200, "lon": 77.2850},
    {"name": "Gokalpur", "ward_no": "262", "lat": 28.7080, "lon": 77.2920},
    {"name": "Saboli", "ward_no": "263", "lat": 28.7080, "lon": 77.3080},
    {"name": "Harsh Vihar", "ward_no": "264", "lat": 28.7050, "lon": 77.3230},
    {"name": "Shiv Vihar", "ward_no": "265", "lat": 28.7280, "lon": 77.2830},
    {"name": "Karawal Nagar East", "ward_no": "266", "lat": 28.7200, "lon": 77.2730},
    {"name": "Mustafabad", "ward_no": "268", "lat": 28.7100, "lon": 77.2700},
    {"name": "Khajoori Khas", "ward_no": "269", "lat": 28.7100, "lon": 77.2580},
    {"name": "Karawal Nagar West", "ward_no": "271", "lat": 28.7300, "lon": 77.2650},
    {"name": "Sonia Vihar", "ward_no": "272", "lat": 28.7350, "lon": 77.2500},
    {"name": "Nizamuddin", "ward_no": "154", "lat": 28.5950, "lon": 77.2500},
    {"name": "Bhogal", "ward_no": "156", "lat": 28.5780, "lon": 77.2550},
    {"name": "Kasturba Nagar", "ward_no": "157", "lat": 28.5820, "lon": 77.2350},
    {"name": "Amar Colony", "ward_no": "160", "lat": 28.5620, "lon": 77.2380},
    {"name": "Malviya Nagar", "ward_no": "161", "lat": 28.5380, "lon": 77.2050},
    {"name": "Hauz Rani", "ward_no": "162", "lat": 28.5320, "lon": 77.2150},
    {"name": "Andrewsganj", "ward_no": "159", "lat": 28.5720, "lon": 77.2320},
    {"name": "Vasant Vihar", "ward_no": "165", "lat": 28.5600, "lon": 77.1550},
    {"name": "Munirka", "ward_no": "166", "lat": 28.5580, "lon": 77.1750},
    {"name": "Nanak Pura", "ward_no": "168", "lat": 28.5800, "lon": 77.1700},
]

# Pollution sources
POLLUTION_SOURCES = ['Vehicular', 'Industrial', 'Construction Dust', 'Biomass Burning']

# Report Persistence
REPORTS_FILE = "reports.json"

def load_reports() -> List[Dict]:
    """Load citizen reports from JSON file"""
    if not os.path.exists(REPORTS_FILE):
        return []
    try:
        with open(REPORTS_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading reports: {e}")
        return []

def save_reports(reports: List[Dict]):
    """Save citizen reports to JSON file"""
    try:
        with open(REPORTS_FILE, "w") as f:
            json.dump(reports, f, indent=2)
    except Exception as e:
        print(f"Error saving reports: {e}")

# Fallback seed stations (used when APIs are unavailable)
FALLBACK_STATIONS = [
    {"station_name": "Anand Vihar", "lat": 28.6469, "lon": 77.3164, "aqi": 350, "source": "fallback"},
    {"station_name": "RK Puram", "lat": 28.5651, "lon": 77.1744, "aqi": 280, "source": "fallback"},
    {"station_name": "Dwarka", "lat": 28.5921, "lon": 77.0460, "aqi": 220, "source": "fallback"},
    {"station_name": "Rohini", "lat": 28.7495, "lon": 77.0565, "aqi": 290, "source": "fallback"},
    {"station_name": "Punjabi Bagh", "lat": 28.6683, "lon": 77.1167, "aqi": 310, "source": "fallback"},
    {"station_name": "Okhla", "lat": 28.5308, "lon": 77.2713, "aqi": 340, "source": "fallback"},
    {"station_name": "Bawana", "lat": 28.7762, "lon": 77.0511, "aqi": 320, "source": "fallback"},
    {"station_name": "Jahangirpuri", "lat": 28.7298, "lon": 77.1723, "aqi": 360, "source": "fallback"},
    {"station_name": "Nehru Place", "lat": 28.5491, "lon": 77.2533, "aqi": 250, "source": "fallback"},
    {"station_name": "IGI Airport", "lat": 28.5562, "lon": 77.1000, "aqi": 200, "source": "fallback"},
]

# Global state
CURRENT_STATIONS: List[Dict] = FALLBACK_STATIONS.copy()
WARDS_DATA: List[Dict] = []
CITIZEN_REPORTS: List[Dict] = load_reports()
LAST_UPDATE: Optional[str] = None
DATA_SOURCE: str = "fallback"

# ============================================================================
# IDW INTERPOLATION
# ============================================================================

def calculate_idw_aqi(ward_lat: float, ward_lon: float, stations: List[Dict], power: float = 2) -> int:
    """
    Inverse Distance Weighting (IDW) Interpolation for AQI
    """
    if not stations:
        return 200  # Default if no stations
    
    weights = []
    values = []
    
    for station in stations:
        lat = station.get("lat", 0)
        lon = station.get("lon", 0)
        aqi = station.get("aqi", 0)
        
        if aqi <= 0:
            continue
        
        distance = np.sqrt((ward_lat - lat)**2 + (ward_lon - lon)**2)
        
        if distance < 0.001:
            return int(aqi)
        
        weight = 1 / (distance ** power)
        weights.append(weight)
        values.append(aqi)
    
    if not weights:
        return 200
    
    weights = np.array(weights)
    values = np.array(values)
    interpolated_aqi = np.sum(weights * values) / np.sum(weights)
    
    # Small variation for realism
    variation = random.uniform(-0.05, 0.05)
    final_aqi = int(interpolated_aqi * (1 + variation))
    
    return max(0, min(500, final_aqi))

def calculate_idw_pollutants(ward_lat: float, ward_lon: float, stations: List[Dict], power: float = 2) -> Dict[str, Optional[float]]:
    """
    IDW Interpolation for all pollutants (pm25, pm10, no2, so2, co, o3)
    Returns interpolated values for each pollutant
    """
    pollutants = ["pm25", "pm10", "no2", "so2", "co", "o3"]
    result = {}
    
    for pollutant in pollutants:
        weights = []
        values = []
        
        for station in stations:
            lat = station.get("lat", 0)
            lon = station.get("lon", 0)
            value = station.get(pollutant)
            
            # Skip if no value for this pollutant
            if value is None or value <= 0:
                continue
            
            distance = np.sqrt((ward_lat - lat)**2 + (ward_lon - lon)**2)
            
            # If very close to a station, use that value directly
            if distance < 0.001:
                result[pollutant] = round(float(value), 2)
                break
            
            weight = 1 / (distance ** power)
            weights.append(weight)
            values.append(float(value))
        else:
            # Calculate interpolated value if we have data
            if weights:
                weights = np.array(weights)
                values = np.array(values)
                interpolated = np.sum(weights * values) / np.sum(weights)
                result[pollutant] = round(float(interpolated), 2)
            else:
                result[pollutant] = None
    
    return result

def get_aqi_color(aqi: int) -> str:
    """Get color code based on AQI value"""
    if aqi <= 50:
        return "Green"
    elif aqi <= 100:
        return "Yellow"
    elif aqi <= 150:
        return "Orange"
    elif aqi <= 200:
        return "Red"
    elif aqi <= 300:
        return "Purple"
    else:
        return "Maroon"

def get_recommendations(aqi: int, dominant_source: str) -> List[str]:
    """Generate actionable recommendations"""
    recommendations = []
    
    if aqi > 400:
        recommendations.extend([
            "🚨 EMERGENCY: Declare Public Health Emergency",
            "🏫 Close all schools and non-essential businesses",
            "🚗 Implement Odd-Even vehicle restrictions immediately",
            "💨 Deploy industrial-grade air purifiers in public spaces"
        ])
    elif aqi > 300:
        recommendations.extend([
            "⚠️ Close primary schools",
            "🏃 Cancel outdoor events and sports",
            "😷 Mandate N95 masks outdoors",
            "🏠 Issue work-from-home advisory"
        ])
    elif aqi > 200:
        recommendations.extend([
            "📢 Issue health advisory for sensitive groups",
            "🚴 Discourage outdoor exercise",
            "🏥 Increase hospital preparedness"
        ])
    elif aqi > 150:
        recommendations.extend([
            "👶 Keep children and elderly indoors during peak hours",
            "🪟 Keep windows closed"
        ])
    
    if dominant_source == "Vehicular":
        recommendations.extend(["🚦 Increase traffic police deployment", "🚌 Promote public transport"])
    elif dominant_source == "Industrial":
        recommendations.extend(["🏭 Conduct industrial emission audits", "⚡ Enforce stricter emission norms"])
    elif dominant_source == "Construction Dust":
        recommendations.extend(["💧 Deploy smog guns and water sprinklers", "🏗️ Mandate dust barriers"])
    elif dominant_source == "Biomass Burning":
        recommendations.extend(["🔥 Intensify stubble burning monitoring", "👮 Deploy ground patrol teams"])
    
    return recommendations[:6]

def generate_pollution_breakdown(dominant_source: str) -> Dict[str, float]:
    """Generate pollution source breakdown"""
    sources = {"traffic": 0, "industrial": 0, "construction_dust": 0, "biomass_burning": 0, "other": 0}
    source_mapping = {
        "Vehicular": "traffic",
        "Industrial": "industrial",
        "Construction Dust": "construction_dust",
        "Biomass Burning": "biomass_burning"
    }
    
    dominant_key = source_mapping.get(dominant_source, "other")
    sources[dominant_key] = random.uniform(35, 50)
    
    remaining = 100 - sources[dominant_key]
    other_keys = [k for k in sources.keys() if k != dominant_key]
    
    for i, key in enumerate(other_keys):
        if i == len(other_keys) - 1:
            sources[key] = round(remaining, 1)
        else:
            value = random.uniform(5, remaining / 2)
            sources[key] = round(value, 1)
            remaining -= value
    
    return sources

# ============================================================================
# DATA REFRESH LOGIC
# ============================================================================

async def refresh_data(force: bool = False, run_ai_analysis: bool = True):
    """Refresh pollution data from APIs and optionally run AI analysis"""
    global CURRENT_STATIONS, WARDS_DATA, LAST_UPDATE, DATA_SOURCE
    
    try:
        # Try to get live data
        stations = await get_live_stations(force_refresh=force)
        
        if stations and len(stations) > 0:
            CURRENT_STATIONS = stations
            DATA_SOURCE = "live"
            print(f"✅ Updated with {len(stations)} live stations")
        else:
            # Fall back to simulated data
            CURRENT_STATIONS = FALLBACK_STATIONS
            DATA_SOURCE = "fallback"
            print("⚠️ Using fallback station data")
        
    except Exception as e:
        print(f"❌ Error fetching live data: {e}")
        CURRENT_STATIONS = FALLBACK_STATIONS
        DATA_SOURCE = "fallback"
    
    # Recalculate ward AQI and pollutant values using current stations
    WARDS_DATA = []
    for i, ward_info in enumerate(DELHI_WARDS):
        aqi = calculate_idw_aqi(ward_info["lat"], ward_info["lon"], CURRENT_STATIONS)
        pollutants = calculate_idw_pollutants(ward_info["lat"], ward_info["lon"], CURRENT_STATIONS)
        
        ward = {
            "id": i + 1,
            "name": ward_info["name"],
            "ward_no": ward_info["ward_no"],
            "lat": ward_info["lat"],
            "lon": ward_info["lon"],
            "aqi": aqi,
            "pollutants": pollutants,  # NEW: interpolated pollutant values
            "color_code": get_aqi_color(aqi),
            "dominant_source": random.choice(POLLUTION_SOURCES),  # Will be overwritten by AI
            "trend": random.choice(["+12%", "+8%", "+5%", "-3%", "-5%", "-8%", "+15%", "-2%"]),
            "population": random.randint(50000, 500000),
            "area_sqkm": round(random.uniform(2, 15), 2)
        }
        WARDS_DATA.append(ward)
    
    LAST_UPDATE = datetime.now().isoformat()
    print(f"📊 Recalculated AQI and pollutants for {len(WARDS_DATA)} wards")
    
    # Run AI analysis for all wards (this saves results to ai_cache.json)
    if run_ai_analysis:
        try:
            print("🤖 Starting AI analysis (this may take a moment)...")
            await analyze_all_wards(WARDS_DATA)
            print("✅ AI analysis complete")
        except Exception as e:
            print(f"⚠️ AI analysis failed: {e} - using rule-based fallback")


# ============================================================================
# APP LIFECYCLE
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    print("🚀 Starting Delhi Pollution Action Dashboard API v2.0...")
    
    # Initial data refresh
    await refresh_data()
    
    # Log API status
    config = validate_config()
    print(f"📡 API Status: {config['available_apis']}")
    if config['missing']:
        print(f"⚠️ Missing API keys: {config['missing']}")
    
    yield
    
    print("👋 Shutting down...")

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="Delhi Pollution Action Dashboard API",
    description="Real-time Ward-Wise Pollution Monitoring with multiple API sources",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/", tags=["Health"])
def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "message": "Delhi Pollution Action Dashboard API v2.0",
        "version": "2.0.0",
        "data_source": DATA_SOURCE,
        "total_wards": len(WARDS_DATA),
        "total_stations": len(CURRENT_STATIONS),
        "last_update": LAST_UPDATE,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/sources", tags=["API Status"])
def get_sources():
    """Get status of all API data sources"""
    return get_api_status()

@app.get("/api/refresh", tags=["API Status"])
async def force_refresh():
    """Force refresh data from APIs"""
    await refresh_data(force=True)
    return {
        "status": "refreshed",
        "data_source": DATA_SOURCE,
        "stations_count": len(CURRENT_STATIONS),
        "wards_count": len(WARDS_DATA),
        "timestamp": LAST_UPDATE
    }

@app.get("/api/stations", tags=["API Status"])
def get_stations():
    """Get raw station data from APIs"""
    return {
        "source": DATA_SOURCE,
        "count": len(CURRENT_STATIONS),
        "stations": CURRENT_STATIONS,
        "last_update": LAST_UPDATE
    }

@app.get("/api/ai-status", tags=["AI Analysis"])
def get_ai_status():
    """Get status of AI analysis and cached weather"""
    weather = get_cached_weather()
    last_updated = ai_cache.get_last_updated()
    
    return {
        "ai_enabled": bool(GROQ_API_KEY),
        "weather_enabled": bool(OPENWEATHER_API_KEY),
        "last_analysis": last_updated,
        "weather": weather,
        "cached_wards": len(ai_cache._cache.get("wards", {}))
    }

@app.get("/api/ward/{ward_id}/pollutants", tags=["AI Analysis"])
def get_ward_pollutants(ward_id: int):
    """Get interpolated pollutant values for a ward"""
    ward = next((w for w in WARDS_DATA if w["id"] == ward_id), None)
    
    if not ward:
        raise HTTPException(status_code=404, detail=f"Ward with ID {ward_id} not found")
    
    ai_analysis = get_ward_ai_analysis(ward_id)
    
    return {
        "ward_id": ward_id,
        "ward_name": ward["name"],
        "aqi": ward["aqi"],
        "pollutants": ward.get("pollutants", {}),
        "ai_analysis": ai_analysis,
        "weather": get_cached_weather()
    }


@app.get("/wards", response_model=List[WardSummary], tags=["Wards"])
def get_all_wards():
    """Get all wards with current AQI data"""
    return [
        WardSummary(
            id=ward["id"],
            name=ward["name"],
            ward_no=ward["ward_no"],
            coordinates=Coordinates(lat=ward["lat"], lon=ward["lon"]),
            aqi=ward["aqi"],
            color_code=ward["color_code"],
            dominant_source=ward["dominant_source"],
            trend=ward["trend"]
        )
        for ward in WARDS_DATA
    ]

@app.get("/ward/{ward_id}", response_model=WardDetail, tags=["Wards"])
def get_ward_detail(ward_id: int):
    """Get detailed information for a specific ward with AI-powered analysis"""
    ward = next((w for w in WARDS_DATA if w["id"] == ward_id), None)
    
    if not ward:
        raise HTTPException(status_code=404, detail=f"Ward with ID {ward_id} not found")
    
    # Try to get AI analysis from cache
    ai_analysis = get_ward_ai_analysis(ward_id)
    
    if ai_analysis:
        # Use AI-predicted sources and recommendations
        breakdown_data = ai_analysis.get("sources", generate_pollution_breakdown(ward["dominant_source"]))
        recommendations = ai_analysis.get("recommendations", get_recommendations(ward["aqi"], ward["dominant_source"]))
        dominant_source = ai_analysis.get("dominant_source", ward["dominant_source"])
    else:
        # Fallback to rule-based analysis
        breakdown_data = generate_pollution_breakdown(ward["dominant_source"])
        recommendations = get_recommendations(ward["aqi"], ward["dominant_source"])
        dominant_source = ward["dominant_source"]
    
    return WardDetail(
        id=ward["id"],
        name=ward["name"],
        ward_no=ward["ward_no"],
        coordinates=Coordinates(lat=ward["lat"], lon=ward["lon"]),
        aqi=ward["aqi"],
        color_code=ward["color_code"],
        dominant_source=dominant_source,
        trend=ward["trend"],
        pollution_breakdown=PollutionBreakdown(**breakdown_data),
        recommendations=recommendations,
        population=ward["population"],
        area_sqkm=ward["area_sqkm"],
        last_updated=LAST_UPDATE or datetime.now().isoformat(),
        pollutants=ward.get("pollutants")
    )

@app.post("/simulate", response_model=List[WardSummary], tags=["Simulation"])
def simulate_scenario(request: SimulateRequest):
    """Simulate traffic reduction scenario"""
    reduction_rate = request.traffic_reduction_percentage / 100
    simulated_data = []
    
    for ward in WARDS_DATA:
        traffic_contribution = 0.40 if ward["dominant_source"] == "Vehicular" else 0.25
        reduction_factor = traffic_contribution * reduction_rate
        new_aqi = int(ward["aqi"] * (1 - reduction_factor))
        new_aqi = max(0, min(500, new_aqi))
        
        simulated_data.append(
            WardSummary(
                id=ward["id"],
                name=ward["name"],
                ward_no=ward["ward_no"],
                coordinates=Coordinates(lat=ward["lat"], lon=ward["lon"]),
                aqi=new_aqi,
                color_code=get_aqi_color(new_aqi),
                dominant_source=ward["dominant_source"],
                trend=f"-{int(reduction_factor * 100)}%" if reduction_factor > 0 else ward["trend"]
            )
        )
    
    return simulated_data

@app.post("/report", response_model=ReportResponse, tags=["Reports"])
def submit_report(report: ReportRequest):
    """Submit a citizen pollution report"""
    report_id = len(CITIZEN_REPORTS) + 1
    timestamp = datetime.now().isoformat()
    
    report_data = {
        "id": report_id,
        "lat": report.lat,
        "lon": report.lon,
        "issue_type": report.issue_type,
        "description": report.description,
        "timestamp": timestamp,
        "status": "pending"
    }
    
    CITIZEN_REPORTS.append(report_data)
    save_reports(CITIZEN_REPORTS)
    
    return ReportResponse(
        id=report_id,
        message=f"Report #{report_id} submitted successfully. Thank you for helping keep Delhi clean!",
        timestamp=timestamp
    )

@app.get("/reports", tags=["Reports"])
def get_all_reports():
    """Get all citizen reports"""
    return CITIZEN_REPORTS

@app.get("/stats", tags=["Statistics"])
def get_stats():
    """Get overall pollution statistics"""
    aqis = [w["aqi"] for w in WARDS_DATA]
    
    return {
        "total_wards": len(WARDS_DATA),
        "average_aqi": round(sum(aqis) / len(aqis), 1) if aqis else 0,
        "max_aqi": max(aqis) if aqis else 0,
        "min_aqi": min(aqis) if aqis else 0,
        "critical_wards": len([a for a in aqis if a > 300]),
        "good_wards": len([a for a in aqis if a <= 100]),
        "total_reports": len(CITIZEN_REPORTS),
        "data_source": DATA_SOURCE,
        "stations_count": len(CURRENT_STATIONS),
        "timestamp": datetime.now().isoformat()
    }

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    print("📍 API Documentation: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
