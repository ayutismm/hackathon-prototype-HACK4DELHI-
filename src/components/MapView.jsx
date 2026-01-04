import { MapContainer, TileLayer, CircleMarker, Tooltip, useMap, GeoJSON } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { useEffect, useState, useCallback } from 'react';

// Delhi center coordinates
const DELHI_CENTER = [28.7041, 77.1025];

/**
 * Get color based on AQI value (returns hex color)
 */
const getAqiHexColor = (aqi) => {
    if (aqi <= 50) return '#22c55e';    // Green
    if (aqi <= 100) return '#eab308';   // Yellow
    if (aqi <= 150) return '#f97316';   // Orange
    if (aqi <= 200) return '#ef4444';   // Red
    if (aqi <= 300) return '#a855f7';   // Purple
    return '#881337';                    // Maroon
};

/**
 * Get marker size based on AQI (bigger = more polluted)
 */
const getMarkerRadius = (aqi) => {
    const baseSize = 8;
    const scale = Math.min(aqi / 100, 5);
    return baseSize + scale * 4;
};

/**
 * Component to handle map view updates when selected ward changes
 */
function MapUpdater({ selectedWard }) {
    const map = useMap();

    useEffect(() => {
        if (selectedWard) {
            map.flyTo([selectedWard.coordinates.lat, selectedWard.coordinates.lon], 13, {
                duration: 0.5
            });
        }
    }, [map, selectedWard]);

    return null;
}

/**
 * MapView Component
 * Renders interactive Leaflet map with ward markers and GeoJSON polygons
 */
function MapView({ wards, selectedWard, onWardClick, showStations, trafficReduction = 0 }) {
    const [stations, setStations] = useState([]);
    const [geoJsonData, setGeoJsonData] = useState(null);
    const [selectedFeatureId, setSelectedFeatureId] = useState(null);

    // Load GeoJSON and Stations on mount
    useEffect(() => {
        // Fetch GeoJSON
        fetch('/Delhi_Wards.geojson')
            .then(response => response.json())
            .then(data => {
                // Add unique IDs to features if not present
                data.features = data.features.map((f, idx) => ({
                    ...f,
                    id: f.id || `feature-${idx}`
                }));
                setGeoJsonData(data);
            })
            .catch(err => {
                console.log('GeoJSON not found, using circle markers instead:', err);
            });

        // Fetch Stations
        fetch('http://localhost:8000/api/stations')
            .then(response => response.json())
            .then(data => {
                if (data && data.stations) {
                    setStations(data.stations);
                }
            })
            .catch(err => console.error('Error fetching stations:', err));
    }, []);

    // Reset selected feature when selectedWard is cleared
    useEffect(() => {
        if (!selectedWard) {
            setSelectedFeatureId(null);
        }
    }, [selectedWard]);

    /**
     * Match GeoJSON feature to ward data - ONLY by Ward_No property
     * Returns null if no exact match to avoid showing wrong ward data
     */
    const findWardForFeature = useCallback((feature) => {
        if (!feature || !wards.length) return null;

        // ONLY match by Ward_No property - no fallback to prevent wrong data
        if (feature.properties && feature.properties.Ward_No) {
            const wardNo = String(feature.properties.Ward_No);
            const matchedWard = wards.find(w => String(w.ward_no) === wardNo);
            if (matchedWard) return matchedWard;
        }

        // No match found - return null instead of wrong data
        return null;
    }, [wards]);

    /**
     * Get interpolated AQI for wards not in backend data
     */
    /**
     * Calculate centroid of a feature
     */
    const getFeatureCentroid = useCallback((feature) => {
        if (!feature?.geometry) return null;

        let coords;
        if (feature.geometry.type === 'MultiPolygon') {
            coords = feature.geometry.coordinates[0][0];
        } else {
            coords = feature.geometry.coordinates[0];
        }

        if (!coords?.length) return null;

        const sumLon = coords.reduce((sum, c) => sum + c[0], 0);
        const sumLat = coords.reduce((sum, c) => sum + c[1], 0);
        return {
            lat: sumLat / coords.length,
            lon: sumLon / coords.length
        };
    }, []);

    /**
     * Get interpolated AQI for wards not in backend data
     */
    const getInterpolatedAqi = useCallback((feature) => {
        if (!stations.length) return 180;

        const centroid = getFeatureCentroid(feature);
        if (!centroid) return 180;

        // IDW interpolation
        let weightSum = 0, valueSum = 0;
        stations.forEach(station => {
            const dist = Math.sqrt(
                Math.pow(station.lat - centroid.lat, 2) +
                Math.pow(station.lon - centroid.lon, 2)
            );
            const weight = 1 / Math.max(dist * dist, 0.0001);
            weightSum += weight;
            valueSum += weight * station.aqi;
        });

        const rawAqi = weightSum > 0 ? Math.round(valueSum / weightSum) : 180;

        // Apply traffic reduction simulation if active
        if (trafficReduction > 0) {
            // Assume 40% contribution from traffic for general interpolation
            const reductionFactor = 0.40 * (trafficReduction / 100);
            return Math.round(rawAqi * (1 - reductionFactor));
        }

        return rawAqi;
    }, [stations, getFeatureCentroid, trafficReduction]);

    /**
     * Style function for GeoJSON features
     */
    const getFeatureStyle = useCallback((feature) => {
        const ward = findWardForFeature(feature);
        // Use backend AQI if available, otherwise interpolate
        const aqi = ward ? ward.aqi : getInterpolatedAqi(feature);
        const color = getAqiHexColor(aqi);

        // ONLY highlight the exact clicked feature
        const isSelected = feature.id === selectedFeatureId;

        return {
            fillColor: color,
            fillOpacity: isSelected ? 0.8 : 0.5,
            color: isSelected ? '#ffffff' : 'rgba(255,255,255,0.3)',
            weight: isSelected ? 3 : 1,
            opacity: isSelected ? 1 : 0.3
        };
    }, [findWardForFeature, selectedFeatureId, getInterpolatedAqi]);

    /**
     * Event handlers for each GeoJSON feature
     */
    const onEachFeature = useCallback((feature, layer) => {
        const ward = findWardForFeature(feature);
        const wardName = feature.properties?.Ward_Name || ward?.name || 'Unknown Ward';

        // Use backend data or interpolation
        const aqi = ward ? ward.aqi : getInterpolatedAqi(feature);
        const color = getAqiHexColor(aqi);
        const isEstimated = !ward;

        // Bind tooltip
        layer.bindTooltip(`
            <div style="text-align: center; font-family: 'Inter', sans-serif;">
                <p style="font-weight: 600; font-size: 13px; margin: 0 0 4px 0;">${wardName}</p>
                <p style="font-size: 16px; font-weight: 700; color: ${color}; margin: 0;">
                    AQI: ${aqi}
                </p>
                ${isEstimated ? '<p style="font-size: 10px; color: #fbbf24; margin: 2px 0 0 0; font-style: italic;">(Estimated)</p>' : ''}
                ${ward ? `<p style="font-size: 11px; color: #94a3b8; margin: 4px 0 0 0;">${ward.dominant_source}</p>` : ''}
            </div>
        `, {
            direction: 'top',
            className: 'custom-tooltip'
        });

        // Click handler - select THIS specific feature
        layer.on('click', () => {
            setSelectedFeatureId(feature.id);

            if (ward) {
                onWardClick(ward);
            } else {
                // Calculate real centroid for the temporary ward
                const centroid = getFeatureCentroid(feature) || { lat: 28.7041, lon: 77.1025 };

                // Interpolate pollutants from nearby stations
                const interpolatedPollutants = {};
                const pollutantKeys = ['pm25', 'pm10', 'no2', 'so2', 'co', 'o3'];

                pollutantKeys.forEach(key => {
                    let weightSum = 0, valueSum = 0;
                    stations.forEach(station => {
                        const value = station[key];
                        if (value !== null && value !== undefined && value > 0) {
                            const dist = Math.sqrt(
                                Math.pow(station.lat - centroid.lat, 2) +
                                Math.pow(station.lon - centroid.lon, 2)
                            );
                            const weight = 1 / Math.max(dist * dist, 0.0001);
                            weightSum += weight;
                            valueSum += weight * value;
                        }
                    });
                    interpolatedPollutants[key] = weightSum > 0 ? Math.round(valueSum / weightSum * 100) / 100 : null;
                });

                // Vary population and area based on ward number hash
                const wardNoHash = (feature.properties?.Ward_No || '0').toString().split('').reduce((a, c) => a + c.charCodeAt(0), 0);
                const population = 80000 + (wardNoHash * 1234) % 400000;
                const area = 2.5 + (wardNoHash * 0.17) % 12;

                // Create a temporary ward object for display
                onWardClick({
                    id: feature.id,
                    name: wardName,
                    ward_no: feature.properties?.Ward_No || 'N/A',
                    aqi: aqi,
                    dominant_source: 'Estimated',
                    pollution_breakdown: {
                        traffic: 30,
                        industrial: 20,
                        construction_dust: 20,
                        biomass_burning: 15,
                        other: 15
                    },
                    pollutants: interpolatedPollutants,
                    recommendations: [
                        "AQI data estimated from nearby stations",
                        "Wear N95 mask when outdoors",
                        "Limit outdoor activities during peak hours",
                        "Keep windows closed",
                        "Use air purifiers indoors"
                    ],
                    coordinates: centroid,
                    population: population,
                    area_sqkm: Math.round(area * 10) / 10,
                    trend: 'Stable',
                    last_updated: new Date().toISOString()
                });
            }
        });

        // Hover effects
        layer.on('mouseover', () => {
            layer.setStyle({
                fillOpacity: 0.8,
                weight: 2,
                opacity: 0.6
            });
        });

        layer.on('mouseout', () => {
            const isSelected = feature.id === selectedFeatureId;
            layer.setStyle({
                fillOpacity: isSelected ? 0.8 : 0.5,
                color: isSelected ? '#ffffff' : 'rgba(255,255,255,0.3)',
                weight: isSelected ? 3 : 1,
                opacity: isSelected ? 1 : 0.3
            });
        });
    }, [findWardForFeature, onWardClick, selectedFeatureId, getInterpolatedAqi]);

    return (
        <div className="relative h-full w-full">
            <MapContainer
                center={DELHI_CENTER}
                zoom={11}
                style={{ height: '100%', width: '100%' }}
                zoomControl={true}
                className="z-0"
            >
                {/* Dark themed map tiles - CartoDB Dark Matter */}
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
                    url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                />

                {/* Map updater for selected ward */}
                <MapUpdater selectedWard={selectedWard} />

                {/* GeoJSON Polygons if available */}
                {geoJsonData && wards.length > 0 && (
                    <GeoJSON
                        key={`geojson-${selectedFeatureId || 'none'}-${wards.length}-${stations.length}`}
                        data={geoJsonData}
                        style={getFeatureStyle}
                        onEachFeature={onEachFeature}
                    />
                )}

                {/* Fallback Circle Markers if no GeoJSON */}
                {!geoJsonData && wards.map((ward) => {
                    const isSelected = selectedWard?.id === ward.id;
                    const color = getAqiHexColor(ward.aqi);
                    const radius = getMarkerRadius(ward.aqi);

                    return (
                        <CircleMarker
                            key={ward.id}
                            center={[ward.coordinates.lat, ward.coordinates.lon]}
                            radius={isSelected ? radius * 1.5 : radius}
                            pathOptions={{
                                fillColor: color,
                                fillOpacity: isSelected ? 0.9 : 0.7,
                                color: isSelected ? '#fff' : color,
                                weight: isSelected ? 3 : 1,
                            }}
                            eventHandlers={{
                                click: () => onWardClick(ward),
                            }}
                        >
                            <Tooltip direction="top" offset={[0, -10]} permanent={false}>
                                <div className="text-center">
                                    <p className="font-bold text-sm">{ward.name}</p>
                                    <p className="text-lg font-bold" style={{ color }}>
                                        AQI: {ward.aqi}
                                    </p>
                                    <p className="text-xs opacity-75">{ward.dominant_source}</p>
                                </div>
                            </Tooltip>
                        </CircleMarker>
                    );
                })}

                {/* Monitoring Stations Layer */}
                {showStations && stations && stations.length > 0 && stations.map((station, idx) => (
                    <CircleMarker
                        key={`station-${idx}`}
                        center={[station.lat, station.lon]}
                        radius={6}
                        pathOptions={{
                            fillColor: getAqiHexColor(station.aqi),
                            fillOpacity: 0.9,
                            color: '#ffffff',
                            weight: 2,
                        }}
                    >
                        <Tooltip direction="top" offset={[0, -10]}>
                            <div className="text-center">
                                <p className="font-bold text-sm text-black mb-1">{station.station_name}</p>
                                <div className="flex items-center justify-center gap-2">
                                    <span className="text-xs font-semibold text-gray-600">Station AQI:</span>
                                    <span className="text-sm font-bold" style={{ color: getAqiHexColor(station.aqi) }}>
                                        {station.aqi}
                                    </span>
                                </div>
                            </div>
                        </Tooltip>
                    </CircleMarker>
                ))}
            </MapContainer>

            {/* Map Overlay Key */}
            <div className="absolute bottom-6 left-6 glass-panel p-4 rounded-xl z-[400] space-y-2 pointer-events-none border-slate-800">
                <h4 className="text-[10px] uppercase tracking-widest text-slate-400 font-bold mb-3">AQI Scale</h4>
                <div className="space-y-1">
                    {[
                        { label: 'Good (0-50)', color: '#22c55e' },
                        { label: 'Satisfactory (51-100)', color: '#eab308' },
                        { label: 'Moderate (101-150)', color: '#f97316' },
                        { label: 'Poor (151-200)', color: '#ef4444' },
                        { label: 'Very Poor (201-300)', color: '#a855f7' },
                        { label: 'Severe (>300)', color: '#881337' }
                    ].map(item => (
                        <div key={item.label} className="flex items-center space-x-2">
                            <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: item.color }} />
                            <span className="text-[10px] text-slate-300">{item.label}</span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

export default MapView;
