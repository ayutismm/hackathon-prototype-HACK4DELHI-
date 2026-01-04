"""
AI Analyzer Module for Delhi Pollution Dashboard
=================================================
Uses Groq LLM to analyze pollutants and predict pollution sources.
Integrates weather data for context-aware recommendations.
"""

import httpx
import json
import os
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

from config import GROQ_API_KEY, OPENWEATHER_API_KEY

logger = logging.getLogger(__name__)

# Delhi coordinates for weather
DELHI_LAT = 28.6139
DELHI_LON = 77.2090

# AI Cache file
AI_CACHE_FILE = os.path.join(os.path.dirname(__file__), "ai_cache.json")


class WeatherFetcher:
    """Fetches current weather data from OpenWeatherMap API"""
    
    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
    
    async def get_weather(self) -> Optional[Dict[str, Any]]:
        """Fetch current Delhi weather"""
        if not OPENWEATHER_API_KEY:
            logger.warning("OpenWeatherMap API key not configured")
            return self._get_default_weather()
        
        try:
            params = {
                "lat": DELHI_LAT,
                "lon": DELHI_LON,
                "appid": OPENWEATHER_API_KEY,
                "units": "metric"
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()
            
            weather = {
                "temperature": data.get("main", {}).get("temp", 20),
                "humidity": data.get("main", {}).get("humidity", 50),
                "wind_speed": data.get("wind", {}).get("speed", 5),
                "wind_direction": data.get("wind", {}).get("deg", 0),
                "conditions": data.get("weather", [{}])[0].get("main", "Clear"),
                "description": data.get("weather", [{}])[0].get("description", "clear sky"),
                "pressure": data.get("main", {}).get("pressure", 1013),
                "visibility": data.get("visibility", 10000) / 1000,  # Convert to km
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Fetched weather: {weather['temperature']}°C, {weather['conditions']}")
            return weather
            
        except Exception as e:
            logger.error(f"Weather fetch error: {e}")
            return self._get_default_weather()
    
    def _get_default_weather(self) -> Dict[str, Any]:
        """Return default weather when API unavailable"""
        return {
            "temperature": 18,
            "humidity": 65,
            "wind_speed": 5,
            "wind_direction": 270,
            "conditions": "Unknown",
            "description": "weather data unavailable",
            "pressure": 1013,
            "visibility": 5,
            "timestamp": datetime.now().isoformat()
        }


class GroqAnalyzer:
    """Uses Groq LLM to analyze pollution data and predict sources"""
    
    BASE_URL = "https://api.groq.com/openai/v1/chat/completions"
    MODEL = "llama-3.1-70b-versatile"  # Fast and capable
    
    def __init__(self):
        self.api_key = GROQ_API_KEY
    
    async def analyze_ward(
        self, 
        ward_name: str,
        pollutants: Dict[str, float], 
        weather: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze pollutants for a ward and predict pollution sources.
        
        Args:
            ward_name: Name of the ward
            pollutants: Dict with pm25, pm10, no2, so2, co, o3 values
            weather: Current weather data
            
        Returns:
            Dict with sources breakdown, recommendations, and weather impact
        """
        if not self.api_key:
            logger.warning("Groq API key not configured, using rule-based analysis")
            return self._rule_based_analysis(pollutants, weather)
        
        prompt = self._build_prompt(ward_name, pollutants, weather)
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert air quality analyst for Delhi, India. Analyze pollution data and provide actionable insights. ALWAYS respond with valid JSON only, no markdown, no code blocks, no extra text."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 500
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.BASE_URL, 
                    headers=headers, 
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
            
            # Parse the AI response
            ai_response = data["choices"][0]["message"]["content"]
            result = json.loads(ai_response)
            
            # Validate and normalize the response
            return self._normalize_response(result)
            
        except json.JSONDecodeError as e:
            logger.error(f"Groq response parse error: {e}")
            return self._rule_based_analysis(pollutants, weather)
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return self._rule_based_analysis(pollutants, weather)
    
    async def analyze_city(
        self,
        city_pollutants: Dict[str, float],
        weather: Dict[str, Any],
        avg_aqi: int,
        min_aqi: int,
        max_aqi: int
    ) -> Dict[str, Any]:
        """
        Analyze city-wide pollution data with ONE API call.
        Returns sources breakdown and recommendations for the entire city.
        """
        if not self.api_key:
            logger.warning("Groq API key not configured, using rule-based analysis")
            return self._rule_based_analysis(city_pollutants, weather)
        
        prompt = f"""Analyze city-wide air pollution data for Delhi, India.

CITY-WIDE AVERAGE POLLUTANT LEVELS:
- PM2.5: {city_pollutants.get('pm25', 'N/A')} µg/m³
- PM10: {city_pollutants.get('pm10', 'N/A')} µg/m³
- NO2: {city_pollutants.get('no2', 'N/A')} ppb
- SO2: {city_pollutants.get('so2', 'N/A')} ppb
- CO: {city_pollutants.get('co', 'N/A')} ppm
- O3: {city_pollutants.get('o3', 'N/A')} ppb

AQI STATISTICS:
- Average AQI: {avg_aqi}
- AQI Range: {min_aqi} - {max_aqi}

CURRENT WEATHER:
- Temperature: {weather.get('temperature', 'N/A')}°C
- Humidity: {weather.get('humidity', 'N/A')}%
- Wind Speed: {weather.get('wind_speed', 'N/A')} m/s
- Conditions: {weather.get('conditions', 'N/A')}

Based on pollutant patterns and weather, respond with JSON only:
{{"sources": {{"traffic": <0-100>, "industrial": <0-100>, "construction_dust": <0-100>, "biomass_burning": <0-100>, "other": <0-100>}}, "dominant_source": "<top contributor>", "recommendations": ["<action 1>", "<action 2>", "<action 3>", "<action 4>", "<action 5>"], "weather_impact": "<how weather affects pollution>"}}

Sources must sum to 100. Use pollutant patterns: High NO2=vehicular, High PM10/PM2.5 ratio=construction, High SO2=industrial, High CO+PM2.5=biomass."""

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": "You are an expert air quality analyst. Respond with valid JSON only, no markdown."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 600
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.BASE_URL, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
            
            ai_response = data["choices"][0]["message"]["content"]
            # Try to extract JSON from response
            ai_response = ai_response.strip()
            if ai_response.startswith("```"):
                ai_response = ai_response.split("```")[1]
                if ai_response.startswith("json"):
                    ai_response = ai_response[4:]
            
            result = json.loads(ai_response)
            logger.info("City-wide AI analysis complete")
            return self._normalize_response(result)
            
        except json.JSONDecodeError as e:
            logger.error(f"Groq response parse error: {e}")
            return self._rule_based_analysis(city_pollutants, weather)
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return self._rule_based_analysis(city_pollutants, weather)
    
    def _build_prompt(
        self, 
        ward_name: str,
        pollutants: Dict[str, float], 
        weather: Dict[str, Any]
    ) -> str:
        """Build the analysis prompt for the LLM"""
        return f"""Analyze air pollution data for {ward_name} ward in Delhi, India.

POLLUTANT LEVELS:
- PM2.5: {pollutants.get('pm25', 'N/A')} µg/m³
- PM10: {pollutants.get('pm10', 'N/A')} µg/m³  
- NO2: {pollutants.get('no2', 'N/A')} ppb
- SO2: {pollutants.get('so2', 'N/A')} ppb
- CO: {pollutants.get('co', 'N/A')} ppm
- O3: {pollutants.get('o3', 'N/A')} ppb

CURRENT WEATHER:
- Temperature: {weather.get('temperature', 'N/A')}°C
- Humidity: {weather.get('humidity', 'N/A')}%
- Wind Speed: {weather.get('wind_speed', 'N/A')} m/s
- Conditions: {weather.get('conditions', 'N/A')}
- Visibility: {weather.get('visibility', 'N/A')} km

Based on pollutant ratios and weather, respond with JSON:
{{
    "sources": {{
        "vehicular": <0-100>,
        "industrial": <0-100>,
        "construction": <0-100>,
        "biomass_burning": <0-100>,
        "other": <0-100>
    }},
    "dominant_source": "<top contributor>",
    "recommendations": ["<action 1>", "<action 2>", "<action 3>"],
    "weather_impact": "<how weather affects pollution levels>"
}}

The sources percentages must sum to 100. Be specific based on pollutant patterns:
- High NO2 = vehicular emissions
- High PM10 vs PM2.5 = construction/dust
- High SO2 = industrial
- High CO with PM2.5 = biomass burning"""

    def _normalize_response(self, result: Dict) -> Dict[str, Any]:
        """Normalize and validate the AI response"""
        # Ensure sources exist and sum to 100
        sources = result.get("sources", {})
        default_sources = {
            "vehicular": 25,
            "industrial": 20,
            "construction": 20,
            "biomass_burning": 20,
            "other": 15
        }
        
        # Normalize source keys
        normalized_sources = {
            "traffic": sources.get("vehicular", sources.get("traffic", default_sources["vehicular"])),
            "industrial": sources.get("industrial", default_sources["industrial"]),
            "construction_dust": sources.get("construction", sources.get("construction_dust", default_sources["construction"])),
            "biomass_burning": sources.get("biomass_burning", sources.get("biomass", default_sources["biomass_burning"])),
            "other": sources.get("other", default_sources["other"])
        }
        
        # Ensure sums to 100
        total = sum(normalized_sources.values())
        if total != 100 and total > 0:
            factor = 100 / total
            normalized_sources = {k: round(v * factor, 1) for k, v in normalized_sources.items()}
        
        # Map dominant source
        dominant_source = result.get("dominant_source", "Vehicular")
        source_mapping = {
            "vehicular": "Vehicular",
            "traffic": "Vehicular",
            "industrial": "Industrial",
            "construction": "Construction Dust",
            "construction_dust": "Construction Dust",
            "biomass_burning": "Biomass Burning",
            "biomass": "Biomass Burning"
        }
        dominant_source = source_mapping.get(dominant_source.lower().replace(" ", "_"), dominant_source)
        
        return {
            "sources": normalized_sources,
            "dominant_source": dominant_source,
            "recommendations": result.get("recommendations", [
                "Wear N95 mask outdoors",
                "Limit outdoor activities",
                "Use air purifiers indoors"
            ])[:5],
            "weather_impact": result.get("weather_impact", "Weather conditions affecting pollution dispersion")
        }
    
    def _rule_based_analysis(
        self, 
        pollutants: Dict[str, float], 
        weather: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback rule-based analysis when AI unavailable"""
        pm25 = pollutants.get("pm25", 100)
        pm10 = pollutants.get("pm10", 150)
        no2 = pollutants.get("no2", 30)
        so2 = pollutants.get("so2", 10)
        co = pollutants.get("co", 5)
        
        # Calculate source contributions based on pollutant ratios
        sources = {
            "traffic": 25,
            "industrial": 20,
            "construction_dust": 20,
            "biomass_burning": 20,
            "other": 15
        }
        
        # Adjust based on pollutant patterns
        if no2 and no2 > 40:
            sources["traffic"] += 15
            sources["other"] -= 15
        
        if pm10 and pm25 and pm10 > pm25 * 1.5:
            sources["construction_dust"] += 10
            sources["traffic"] -= 10
        
        if so2 and so2 > 20:
            sources["industrial"] += 10
            sources["biomass_burning"] -= 10
        
        if co and co > 8 and pm25 > 100:
            sources["biomass_burning"] += 10
            sources["other"] -= 10
        
        # Normalize to 100
        total = sum(sources.values())
        sources = {k: round(v * 100 / total, 1) for k, v in sources.items()}
        
        # Determine dominant source
        dominant_key = max(sources, key=sources.get)
        source_names = {
            "traffic": "Vehicular",
            "industrial": "Industrial",
            "construction_dust": "Construction Dust",
            "biomass_burning": "Biomass Burning",
            "other": "Mixed Sources"
        }
        
        # Weather impact
        wind_speed = weather.get("wind_speed", 5)
        humidity = weather.get("humidity", 50)
        
        if wind_speed < 3:
            weather_impact = "Low wind speed causing pollutants to accumulate near ground level"
        elif wind_speed > 10:
            weather_impact = "Strong winds helping disperse pollutants"
        elif humidity > 80:
            weather_impact = "High humidity causing pollutants to settle"
        else:
            weather_impact = "Moderate weather conditions with normal pollutant dispersion"
        
        return {
            "sources": sources,
            "dominant_source": source_names[dominant_key],
            "recommendations": [
                "Wear N95 mask when outdoors",
                "Avoid outdoor exercise during peak pollution hours",
                "Use air purifiers in homes and offices",
                "Keep windows closed during high pollution",
                "Monitor AQI before planning outdoor activities"
            ],
            "weather_impact": weather_impact
        }


class AICache:
    """Manages caching of AI analysis results"""
    
    def __init__(self, cache_file: str = AI_CACHE_FILE):
        self.cache_file = cache_file
        self._cache: Dict[str, Any] = {}
        self._load_cache()
    
    def _load_cache(self):
        """Load cache from file"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    self._cache = json.load(f)
                logger.info(f"Loaded AI cache with {len(self._cache.get('wards', {}))} wards")
        except Exception as e:
            logger.error(f"Error loading AI cache: {e}")
            self._cache = {}
    
    def save_cache(self):
        """Save cache to file"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self._cache, f, indent=2)
            logger.info(f"Saved AI cache with {len(self._cache.get('wards', {}))} wards")
        except Exception as e:
            logger.error(f"Error saving AI cache: {e}")
    
    def get_ward_analysis(self, ward_id: int) -> Optional[Dict[str, Any]]:
        """Get cached analysis for a ward"""
        wards = self._cache.get("wards", {})
        return wards.get(str(ward_id))
    
    def set_ward_analysis(self, ward_id: int, analysis: Dict[str, Any]):
        """Cache analysis for a ward"""
        if "wards" not in self._cache:
            self._cache["wards"] = {}
        self._cache["wards"][str(ward_id)] = analysis
    
    def set_weather(self, weather: Dict[str, Any]):
        """Cache weather data"""
        self._cache["weather"] = weather
    
    def get_weather(self) -> Optional[Dict[str, Any]]:
        """Get cached weather"""
        return self._cache.get("weather")
    
    def set_last_updated(self):
        """Update last refresh timestamp"""
        self._cache["last_updated"] = datetime.now().isoformat()
    
    def get_last_updated(self) -> Optional[str]:
        """Get last refresh timestamp"""
        return self._cache.get("last_updated")
    
    def clear(self):
        """Clear the cache"""
        self._cache = {}
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)


# Global instances
weather_fetcher = WeatherFetcher()
groq_analyzer = GroqAnalyzer()
ai_cache = AICache()


async def analyze_all_wards(wards_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze all wards using ONE Groq API call for city-wide analysis.
    Then apply the city-wide insights to each ward based on their pollutant levels.
    """
    logger.info(f"Starting AI analysis for {len(wards_data)} wards (1 city-wide call)...")
    
    # Fetch weather first
    weather = await weather_fetcher.get_weather()
    ai_cache.set_weather(weather)
    
    # Step 1: Calculate city-wide statistics
    all_pollutants = {"pm25": [], "pm10": [], "no2": [], "so2": [], "co": [], "o3": []}
    all_aqis = []
    
    for ward in wards_data:
        pollutants = ward.get("pollutants", {})
        for key in all_pollutants:
            val = pollutants.get(key)
            if val is not None:
                all_pollutants[key].append(val)
        all_aqis.append(ward.get("aqi", 0))
    
    # Calculate averages
    city_averages = {}
    for key, values in all_pollutants.items():
        city_averages[key] = round(sum(values) / len(values), 2) if values else None
    
    avg_aqi = round(sum(all_aqis) / len(all_aqis)) if all_aqis else 200
    max_aqi = max(all_aqis) if all_aqis else 350
    min_aqi = min(all_aqis) if all_aqis else 100
    
    # Step 2: Make ONE city-wide Groq API call
    city_analysis = await groq_analyzer.analyze_city(city_averages, weather, avg_aqi, min_aqi, max_aqi)
    
    # Step 3: Apply city-wide analysis to each ward (locally, no API calls)
    for ward in wards_data:
        ward_id = ward.get("id")
        pollutants = ward.get("pollutants", {})
        
        # Adjust sources slightly based on ward's individual pollutant values
        adjusted_sources = adjust_sources_for_ward(city_analysis["sources"], pollutants, city_averages)
        
        # Determine this ward's dominant source based on adjusted values
        dominant_key = max(adjusted_sources, key=adjusted_sources.get)
        source_names = {
            "traffic": "Vehicular",
            "industrial": "Industrial", 
            "construction_dust": "Construction Dust",
            "biomass_burning": "Biomass Burning",
            "other": "Mixed Sources"
        }
        
        ai_cache.set_ward_analysis(ward_id, {
            "pollutants": pollutants,
            "sources": adjusted_sources,
            "dominant_source": source_names.get(dominant_key, city_analysis["dominant_source"]),
            "recommendations": city_analysis["recommendations"],
            "weather_impact": city_analysis["weather_impact"]
        })
    
    # Save cache to file
    ai_cache.set_last_updated()
    ai_cache.save_cache()
    
    logger.info(f"AI analysis complete for {len(wards_data)} wards (1 API call)")
    
    return {
        "analyzed_wards": len(wards_data),
        "weather": weather,
        "city_analysis": city_analysis,
        "last_updated": ai_cache.get_last_updated()
    }


def adjust_sources_for_ward(city_sources: Dict[str, float], ward_pollutants: Dict, city_averages: Dict) -> Dict[str, float]:
    """
    Adjust city-wide source percentages based on this ward's pollutant levels.
    If a ward has higher NO2 than average, increase vehicular contribution, etc.
    """
    adjusted = city_sources.copy()
    
    # Get ward's pollutant values
    pm25 = ward_pollutants.get("pm25") or 0
    pm10 = ward_pollutants.get("pm10") or 0
    no2 = ward_pollutants.get("no2") or 0
    so2 = ward_pollutants.get("so2") or 0
    
    # Get city averages
    avg_pm25 = city_averages.get("pm25") or 100
    avg_no2 = city_averages.get("no2") or 30
    avg_so2 = city_averages.get("so2") or 10
    
    # Adjust based on deviations from city average
    if no2 > avg_no2 * 1.2:  # 20% above average
        adjusted["traffic"] = min(adjusted["traffic"] + 8, 60)
        adjusted["other"] = max(adjusted["other"] - 8, 5)
    elif no2 < avg_no2 * 0.8:  # 20% below average
        adjusted["traffic"] = max(adjusted["traffic"] - 5, 15)
        adjusted["construction_dust"] = min(adjusted["construction_dust"] + 5, 40)
    
    if pm10 > pm25 * 1.8:  # High dust ratio
        adjusted["construction_dust"] = min(adjusted["construction_dust"] + 10, 50)
        adjusted["traffic"] = max(adjusted["traffic"] - 10, 15)
    
    if so2 > avg_so2 * 1.5:  # High SO2 = industrial
        adjusted["industrial"] = min(adjusted["industrial"] + 10, 45)
        adjusted["other"] = max(adjusted["other"] - 10, 5)
    
    # Normalize to 100%
    total = sum(adjusted.values())
    if total > 0:
        adjusted = {k: round(v * 100 / total, 1) for k, v in adjusted.items()}
    
    return adjusted


def get_ward_ai_analysis(ward_id: int) -> Optional[Dict[str, Any]]:
    """Get cached AI analysis for a ward (fast, no API call)"""
    return ai_cache.get_ward_analysis(ward_id)


def get_cached_weather() -> Optional[Dict[str, Any]]:
    """Get cached weather data"""
    return ai_cache.get_weather()
