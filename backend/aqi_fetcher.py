"""
AQI Data Fetcher Module for Delhi Pollution Dashboard
======================================================
Multi-API data fetcher with automatic failover support.
Integrates: CPCB (data.gov.in), AQICN, and OpenAQ v3.

Author: AI Assistant for Hack4Delhi Hackathon
"""

import httpx
import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

from config import (
    CPCB_API_KEY, CPCB_API_URL,
    AQICN_TOKEN, AQICN_API_URL, DELHI_STATIONS,
    OPENAQ_API_URL,
    API_PRIORITY, validate_config
)
from cache import aqi_cache, CACHE_KEY_CPCB, CACHE_KEY_AQICN, CACHE_KEY_OPENAQ, CACHE_KEY_STATIONS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# BASE FETCHER CLASS
# ============================================================================

class APIFetcher(ABC):
    """Abstract base class for AQI API fetchers"""
    
    name: str = "base"
    
    @abstractmethod
    async def fetch(self) -> List[Dict[str, Any]]:
        """Fetch station data from the API"""
        pass
    
    def normalize_station(self, raw_data: Dict) -> Dict[str, Any]:
        """Normalize station data to common format"""
        return {
            "station_name": raw_data.get("station_name", "Unknown"),
            "lat": float(raw_data.get("lat", 0)),
            "lon": float(raw_data.get("lon", 0)),
            "aqi": int(raw_data.get("aqi", 0)),
            "pm25": raw_data.get("pm25"),
            "pm10": raw_data.get("pm10"),
            "no2": raw_data.get("no2"),
            "so2": raw_data.get("so2"),
            "co": raw_data.get("co"),
            "o3": raw_data.get("o3"),
            "dominant_pollutant": raw_data.get("dominant_pollutant", "pm25"),  # What's driving AQI
            "source": self.name,
            "timestamp": raw_data.get("timestamp", datetime.now().isoformat()),
            "reliability_score": raw_data.get("reliability_score", 0.8)
        }

# ============================================================================
# CPCB FETCHER (data.gov.in)
# ============================================================================

class CPCBFetcher(APIFetcher):
    """
    Fetch AQI data from Central Pollution Control Board via data.gov.in
    
    API Documentation: https://data.gov.in/resource/3b01bcb8-0b14-4abf-b6f2-c1bfd384ba69
    """
    
    name = "cpcb"
    
    async def fetch(self) -> List[Dict[str, Any]]:
        """Fetch Delhi station data from CPCB API"""
        
        if not CPCB_API_KEY:
            logger.warning("CPCB API key not configured")
            return []
        
        # Check cache first
        cached = aqi_cache.get(CACHE_KEY_CPCB)
        if cached:
            logger.info("Using cached CPCB data")
            return cached
        
        try:
            params = {
                "api-key": CPCB_API_KEY,
                "format": "json",
                "filters[city]": "Delhi",
                "limit": 100
            }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(CPCB_API_URL, params=params)
                response.raise_for_status()
                data = response.json()
            
            stations = []
            records = data.get("records", [])
            
            for record in records:
                try:
                    station = self.normalize_station({
                        "station_name": record.get("station", "Unknown"),
                        "lat": record.get("latitude", 0),
                        "lon": record.get("longitude", 0),
                        "aqi": self._calculate_aqi(record),
                        "pm25": record.get("pm25", {}).get("avg") if isinstance(record.get("pm25"), dict) else record.get("pm25"),
                        "pm10": record.get("pm10", {}).get("avg") if isinstance(record.get("pm10"), dict) else record.get("pm10"),
                        "no2": record.get("no2", {}).get("avg") if isinstance(record.get("no2"), dict) else record.get("no2"),
                        "so2": record.get("so2", {}).get("avg") if isinstance(record.get("so2"), dict) else record.get("so2"),
                        "co": record.get("co", {}).get("avg") if isinstance(record.get("co"), dict) else record.get("co"),
                        "o3": record.get("ozone", {}).get("avg") if isinstance(record.get("ozone"), dict) else record.get("ozone"),
                        "timestamp": record.get("last_update", datetime.now().isoformat()),
                        "reliability_score": 0.95  # Government data is highly reliable
                    })
                    stations.append(station)
                except Exception as e:
                    logger.error(f"Error parsing CPCB record: {e}")
                    continue
            
            if stations:
                aqi_cache.set(CACHE_KEY_CPCB, stations)
                logger.info(f"Fetched {len(stations)} stations from CPCB")
            
            return stations
            
        except httpx.HTTPError as e:
            logger.error(f"CPCB API request failed: {e}")
            return []
        except Exception as e:
            logger.error(f"CPCB fetch error: {e}")
            return []
    
    def _calculate_aqi(self, record: Dict) -> int:
        """Calculate AQI from pollutant values using Indian AQI standards"""
        try:
            # Try to get PM2.5 first (most common indicator)
            pm25 = record.get("pm25")
            if isinstance(pm25, dict):
                pm25 = pm25.get("avg")
            
            if pm25 and float(pm25) > 0:
                # Simplified AQI calculation from PM2.5
                pm25_val = float(pm25)
                if pm25_val <= 30:
                    return int(pm25_val * 50 / 30)
                elif pm25_val <= 60:
                    return int(50 + (pm25_val - 30) * 50 / 30)
                elif pm25_val <= 90:
                    return int(100 + (pm25_val - 60) * 100 / 30)
                elif pm25_val <= 120:
                    return int(200 + (pm25_val - 90) * 100 / 30)
                elif pm25_val <= 250:
                    return int(300 + (pm25_val - 120) * 100 / 130)
                else:
                    return int(400 + (pm25_val - 250) * 100 / 130)
            
            return 0
        except:
            return 0

# ============================================================================
# AQICN FETCHER
# ============================================================================

class AQICNFetcher(APIFetcher):
    """
    Fetch AQI data from AQICN (World Air Quality Index)
    
    API Documentation: https://aqicn.org/json-api/doc/
    """
    
    name = "aqicn"
    
    async def fetch(self) -> List[Dict[str, Any]]:
        """Fetch Delhi station data from AQICN API"""
        
        if not AQICN_TOKEN:
            logger.warning("AQICN token not configured")
            return []
        
        # Check cache first
        cached = aqi_cache.get(CACHE_KEY_AQICN)
        if cached:
            logger.info("Using cached AQICN data")
            return cached
        
        stations = []
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # First try simple "delhi" endpoint
                try:
                    simple_url = f"{AQICN_API_URL}/feed/delhi/?token={AQICN_TOKEN}"
                    response = await client.get(simple_url)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("status") == "ok":
                            info = data.get("data", {})
                            city = info.get("city", {})
                            iaqi = info.get("iaqi", {})
                            station = self.normalize_station({
                                "station_name": city.get("name", "Delhi"),
                                "lat": city.get("geo", [28.6, 77.2])[0],
                                "lon": city.get("geo", [28.6, 77.2])[1],
                                "aqi": info.get("aqi", 0),
                                "pm25": iaqi.get("pm25", {}).get("v"),
                                "pm10": iaqi.get("pm10", {}).get("v"),
                                "no2": iaqi.get("no2", {}).get("v"),
                                "so2": iaqi.get("so2", {}).get("v"),
                                "co": iaqi.get("co", {}).get("v"),
                                "o3": iaqi.get("o3", {}).get("v"),
                                "dominant_pollutant": info.get("dominentpol", "pm25"),
                                "timestamp": info.get("time", {}).get("iso", datetime.now().isoformat()),
                                "reliability_score": 0.92
                            })
                            stations.append(station)
                            logger.info("Got data from simple delhi endpoint")
                except Exception as e:
                    logger.debug(f"Simple delhi endpoint failed: {e}")
                
                # Fetch data for each known Delhi station
                tasks = [
                    self._fetch_station(client, station_id)
                    for station_id in DELHI_STATIONS
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, dict) and result:
                        stations.append(result)
            
            if stations:
                aqi_cache.set(CACHE_KEY_AQICN, stations)
                logger.info(f"Fetched {len(stations)} stations from AQICN")
            
            return stations
            
        except Exception as e:
            logger.error(f"AQICN fetch error: {e}")
            return []
    
    async def _fetch_station(self, client: httpx.AsyncClient, station_id: str) -> Optional[Dict]:
        """Fetch data for a single station"""
        try:
            url = f"{AQICN_API_URL}/feed/{station_id}/?token={AQICN_TOKEN}"
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") != "ok":
                return None
            
            info = data.get("data", {})
            city = info.get("city", {})
            iaqi = info.get("iaqi", {})
            
            return self.normalize_station({
                "station_name": city.get("name", station_id),
                "lat": city.get("geo", [0, 0])[0],
                "lon": city.get("geo", [0, 0])[1],
                "aqi": info.get("aqi", 0),
                "pm25": iaqi.get("pm25", {}).get("v"),
                "pm10": iaqi.get("pm10", {}).get("v"),
                "no2": iaqi.get("no2", {}).get("v"),
                "so2": iaqi.get("so2", {}).get("v"),
                "co": iaqi.get("co", {}).get("v"),
                "o3": iaqi.get("o3", {}).get("v"),
                "dominant_pollutant": info.get("dominentpol", "pm25"),  # AQICN spells it "dominentpol"
                "timestamp": info.get("time", {}).get("iso", datetime.now().isoformat()),
                "reliability_score": 0.90
            })
            
        except Exception as e:
            logger.debug(f"Failed to fetch AQICN station {station_id}: {e}")
            return None

# ============================================================================
# OPENAQ FETCHER (v3)
# ============================================================================

class OpenAQFetcher(APIFetcher):
    """
    Fetch AQI data from OpenAQ v3 API
    
    API Documentation: https://docs.openaq.org/
    Note: OpenAQ provides raw pollutant values, not calculated AQI
    """
    
    name = "openaq"
    
    async def fetch(self) -> List[Dict[str, Any]]:
        """Fetch Delhi station data from OpenAQ v3 API"""
        
        # Check cache first
        cached = aqi_cache.get(CACHE_KEY_OPENAQ)
        if cached:
            logger.info("Using cached OpenAQ data")
            return cached
        
        try:
            # First get locations in Delhi
            async with httpx.AsyncClient(timeout=30.0) as client:
                locations_url = f"{OPENAQ_API_URL}/locations"
                params = {
                    "country": "IN",
                    "city": "Delhi",
                    "limit": 100
                }
                
                response = await client.get(locations_url, params=params)
                response.raise_for_status()
                data = response.json()
            
            stations = []
            results = data.get("results", [])
            
            for location in results:
                try:
                    # Get the latest measurements
                    parameters = location.get("parameters", [])
                    
                    # Find PM2.5 value if available
                    pm25 = None
                    pm10 = None
                    
                    for param in parameters:
                        if param.get("parameter") == "pm25":
                            pm25 = param.get("lastValue")
                        elif param.get("parameter") == "pm10":
                            pm10 = param.get("lastValue")
                    
                    # Calculate approximate AQI from PM2.5
                    aqi = self._pm25_to_aqi(pm25) if pm25 else 0
                    
                    coords = location.get("coordinates", {})
                    
                    station = self.normalize_station({
                        "station_name": location.get("name", "Unknown"),
                        "lat": coords.get("latitude", 0),
                        "lon": coords.get("longitude", 0),
                        "aqi": aqi,
                        "pm25": pm25,
                        "pm10": pm10,
                        "timestamp": location.get("lastUpdated", datetime.now().isoformat()),
                        "reliability_score": 0.85
                    })
                    stations.append(station)
                    
                except Exception as e:
                    logger.debug(f"Error parsing OpenAQ location: {e}")
                    continue
            
            if stations:
                aqi_cache.set(CACHE_KEY_OPENAQ, stations)
                logger.info(f"Fetched {len(stations)} stations from OpenAQ")
            
            return stations
            
        except httpx.HTTPError as e:
            logger.error(f"OpenAQ API request failed: {e}")
            return []
        except Exception as e:
            logger.error(f"OpenAQ fetch error: {e}")
            return []
    
    def _pm25_to_aqi(self, pm25: float) -> int:
        """Convert PM2.5 value to approximate AQI"""
        if pm25 is None:
            return 0
        try:
            pm25 = float(pm25)
            if pm25 <= 12:
                return int(pm25 * 50 / 12)
            elif pm25 <= 35.4:
                return int(50 + (pm25 - 12) * 50 / 23.4)
            elif pm25 <= 55.4:
                return int(100 + (pm25 - 35.4) * 50 / 20)
            elif pm25 <= 150.4:
                return int(150 + (pm25 - 55.4) * 50 / 95)
            elif pm25 <= 250.4:
                return int(200 + (pm25 - 150.4) * 100 / 100)
            elif pm25 <= 350.4:
                return int(300 + (pm25 - 250.4) * 100 / 100)
            else:
                return int(400 + (pm25 - 350.4) * 100 / 150)
        except:
            return 0

# ============================================================================
# AGGREGATOR
# ============================================================================

class AQIAggregator:
    """
    Aggregates data from multiple AQI APIs with automatic failover.
    Prioritizes data sources based on configuration.
    """
    
    def __init__(self):
        self.fetchers = {
            "cpcb": CPCBFetcher(),
            "aqicn": AQICNFetcher(),
            "openaq": OpenAQFetcher()
        }
        self.last_fetch_status = {}
    
    async def get_stations(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get aggregated station data from all available APIs.
        
        Args:
            force_refresh: If True, bypass cache and fetch fresh data
            
        Returns:
            List of normalized station data
        """
        if force_refresh:
            aqi_cache.clear()
        
        # Check if we have cached aggregated data
        cached = aqi_cache.get(CACHE_KEY_STATIONS)
        if cached and not force_refresh:
            logger.info("Using cached aggregated station data")
            return cached
        
        all_stations = []
        
        # Fetch from each API in priority order
        for api_name in API_PRIORITY:
            if api_name not in self.fetchers:
                continue
            
            try:
                fetcher = self.fetchers[api_name]
                stations = await fetcher.fetch()
                
                if stations:
                    all_stations.extend(stations)
                    self.last_fetch_status[api_name] = {
                        "status": "success",
                        "count": len(stations),
                        "timestamp": datetime.now().isoformat()
                    }
                    logger.info(f"Got {len(stations)} stations from {api_name}")
                else:
                    self.last_fetch_status[api_name] = {
                        "status": "empty",
                        "count": 0,
                        "timestamp": datetime.now().isoformat()
                    }
                    
            except Exception as e:
                self.last_fetch_status[api_name] = {
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                logger.error(f"Failed to fetch from {api_name}: {e}")
        
        # Skip deduplication to show ALL data points as requested
        # unique_stations = self._deduplicate_stations(all_stations)
        
        # Filter out stations with invalid AQI (<= 0)
        valid_stations = [s for s in all_stations if s.get("aqi", 0) > 0]
        
        if valid_stations:
            aqi_cache.set(CACHE_KEY_STATIONS, valid_stations)
        
        return valid_stations
    
    def _deduplicate_stations(self, stations: List[Dict]) -> List[Dict]:
        """
        Remove duplicate stations by:
        1. Exact name match (case-insensitive)
        2. Geographic proximity (within ~1km)
        Keeps the station with highest reliability score.
        """
        unique_stations = []
        
        for station in stations:
            is_duplicate = False
            station_name = station["station_name"].lower().strip()
            station_lat = station["lat"]
            station_lon = station["lon"]
            
            for i, existing in enumerate(unique_stations):
                existing_name = existing["station_name"].lower().strip()
                existing_lat = existing["lat"]
                existing_lon = existing["lon"]
                
                # Check for name similarity or geographic proximity
                name_match = station_name == existing_name
                
                # Geographic proximity check (~1km = 0.01 degrees approximately)
                lat_diff = abs(station_lat - existing_lat)
                lon_diff = abs(station_lon - existing_lon)
                geo_match = lat_diff < 0.01 and lon_diff < 0.01
                
                if name_match or geo_match:
                    is_duplicate = True
                    # Keep the one with higher reliability, or higher AQI if same reliability
                    if station["reliability_score"] > existing["reliability_score"]:
                        unique_stations[i] = station
                    elif station["reliability_score"] == existing["reliability_score"] and station["aqi"] > existing["aqi"]:
                        unique_stations[i] = station
                    break
            
            if not is_duplicate:
                unique_stations.append(station)
        
        logger.info(f"Deduplicated {len(stations)} stations down to {len(unique_stations)}")
        return unique_stations
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all API sources"""
        config_status = validate_config()
        
        return {
            "config": config_status,
            "last_fetch": self.last_fetch_status,
            "cache": aqi_cache.get_stats(),
            "priority": API_PRIORITY
        }

# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

aggregator = AQIAggregator()

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def get_live_stations(force_refresh: bool = False) -> List[Dict[str, Any]]:
    """Get live station data from all APIs"""
    return await aggregator.get_stations(force_refresh)

def get_api_status() -> Dict[str, Any]:
    """Get status of all API integrations"""
    return aggregator.get_status()
