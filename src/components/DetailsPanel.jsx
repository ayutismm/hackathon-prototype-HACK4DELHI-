import { X, Users, Info, ChevronRight } from 'lucide-react';

/**
 * Get AQI category and color
 */
const getAqiColor = (aqi) => {
    if (aqi <= 50) return '#22c55e';       // Green
    if (aqi <= 100) return '#eab308';      // Yellow
    if (aqi <= 150) return '#f97316';      // Orange
    if (aqi <= 200) return '#ef4444';      // Red
    if (aqi <= 300) return '#a855f7';      // Purple
    return '#881337';                       // Maroon
};

const getAqiLabel = (aqi) => {
    if (aqi <= 50) return 'Good';
    if (aqi <= 100) return 'Satisfactory';
    if (aqi <= 150) return 'Moderate';
    if (aqi <= 200) return 'Poor';
    if (aqi <= 300) return 'Very Poor';
    return 'Severe';
};

/**
 * DetailsPanel Component - Glassmorphism
 * Floating right panel with ward details
 */
function DetailsPanel({ wardDetails, onClose }) {
    const sourceColors = {
        traffic: 'bg-blue-500',
        industrial: 'bg-purple-500',
        construction_dust: 'bg-yellow-500',
        biomass_burning: 'bg-red-500',
        other: 'bg-slate-500'
    };

    return (
        <div className="absolute top-4 right-4 bottom-4 w-96 glass-panel z-30 rounded-2xl flex flex-col shadow-2xl overflow-hidden slide-in-from-right">
            {/* Header */}
            <header className="p-6 border-b border-slate-800 flex items-center justify-between">
                <div>
                    <h2 className="text-xl font-bold">{wardDetails.name}</h2>
                    <span className="text-xs text-slate-400 uppercase tracking-widest">
                        Ward No: {wardDetails.ward_no}
                    </span>
                </div>
                <button
                    onClick={onClose}
                    className="p-2 hover:bg-slate-800 rounded-full text-slate-400 transition-colors"
                >
                    <X className="w-5 h-5" />
                </button>
            </header>

            {/* AQI Summary */}
            <div className="flex-1 overflow-y-auto p-6 space-y-8">
                <section className="text-center p-6 bg-slate-800/40 rounded-2xl border border-slate-700/50">
                    <div className="text-[10px] text-slate-400 uppercase tracking-widest mb-1 font-bold">
                        Current AQI
                    </div>
                    <div
                        className="text-6xl font-black mb-2"
                        style={{ color: getAqiColor(wardDetails.aqi) }}
                    >
                        {wardDetails.aqi}
                    </div>
                    <div
                        className="inline-block px-3 py-1 rounded-full text-xs font-bold text-white uppercase"
                        style={{ backgroundColor: getAqiColor(wardDetails.aqi) }}
                    >
                        {getAqiLabel(wardDetails.aqi)}
                    </div>
                </section>

                {/* Population & Area */}
                <div className="grid grid-cols-2 gap-4">
                    <div className="flex items-center space-x-3 p-3 bg-slate-900/50 rounded-xl">
                        <Users className="w-5 h-5 text-blue-500" />
                        <div>
                            <div className="text-[10px] text-slate-500 uppercase">Population</div>
                            <div className="text-sm font-bold">{(wardDetails.population / 1000).toFixed(1)}k</div>
                        </div>
                    </div>
                    <div className="flex items-center space-x-3 p-3 bg-slate-900/50 rounded-xl">
                        <svg className="w-5 h-5 text-indigo-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <polygon points="12 2 2 7 12 12 22 7 12 2" />
                            <polyline points="2 17 12 22 22 17" />
                            <polyline points="2 12 12 17 22 12" />
                        </svg>
                        <div>
                            <div className="text-[10px] text-slate-500 uppercase">Area (sqkm)</div>
                            <div className="text-sm font-bold">{wardDetails.area_sqkm}</div>
                        </div>
                    </div>
                </div>

                {/* Individual Pollutants */}
                {wardDetails.pollutants && (
                    <section className="space-y-3">
                        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center">
                            <svg className="w-4 h-4 mr-2" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z" />
                                <path d="M12 6v6l4 2" />
                            </svg>
                            Pollutant Levels
                        </h3>
                        <div className="grid grid-cols-3 gap-2">
                            {[
                                { key: 'pm25', label: 'PM2.5', unit: 'µg/m³', color: 'text-red-400', limit: 60 },
                                { key: 'pm10', label: 'PM10', unit: 'µg/m³', color: 'text-orange-400', limit: 100 },
                                { key: 'no2', label: 'NO₂', unit: 'ppb', color: 'text-yellow-400', limit: 80 },
                                { key: 'so2', label: 'SO₂', unit: 'ppb', color: 'text-purple-400', limit: 80 },
                                { key: 'co', label: 'CO', unit: 'ppm', color: 'text-blue-400', limit: 10 },
                                { key: 'o3', label: 'O₃', unit: 'ppb', color: 'text-green-400', limit: 100 },
                            ].map((pollutant) => {
                                const value = wardDetails.pollutants[pollutant.key];
                                const isHigh = value && value > pollutant.limit;
                                return (
                                    <div
                                        key={pollutant.key}
                                        className={`p-3 rounded-xl border ${isHigh ? 'bg-red-500/10 border-red-500/30' : 'bg-slate-800/50 border-slate-700/50'}`}
                                    >
                                        <div className="text-[10px] text-slate-500 uppercase font-medium">{pollutant.label}</div>
                                        <div className={`text-lg font-bold ${isHigh ? 'text-red-400' : pollutant.color}`}>
                                            {value !== null && value !== undefined ? value.toFixed(1) : '--'}
                                        </div>
                                        <div className="text-[9px] text-slate-600">{pollutant.unit}</div>
                                    </div>
                                );
                            })}
                        </div>
                    </section>
                )}

                {/* Pollution Breakdown */}
                <section className="space-y-4">
                    <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center">
                        <Info className="w-4 h-4 mr-2" /> Pollution Sources
                    </h3>
                    <div className="space-y-4">
                        {Object.entries(wardDetails.pollution_breakdown).map(([key, value]) => (
                            <div key={key} className="space-y-1.5">
                                <div className="flex justify-between text-xs capitalize">
                                    <span className="text-slate-300">{key.replace('_', ' ')}</span>
                                    <span className="font-bold">{value}%</span>
                                </div>
                                <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                                    <div
                                        className={`h-full ${sourceColors[key]} transition-all duration-1000`}
                                        style={{ width: `${value}%` }}
                                    />
                                </div>
                            </div>
                        ))}
                    </div>
                </section>

                {/* Recommendations */}
                <section className="space-y-4">
                    <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center">
                        <svg className="w-4 h-4 mr-2" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10" />
                            <path d="m9 12 2 2 4-4" />
                        </svg>
                        Mitigation Plan
                    </h3>
                    <div className="space-y-2">
                        {wardDetails.recommendations && wardDetails.recommendations.map((rec, i) => (
                            <div
                                key={i}
                                className="p-3 bg-blue-500/5 border border-blue-500/20 rounded-xl flex items-start space-x-3"
                            >
                                <ChevronRight className="w-4 h-4 text-blue-500 shrink-0 mt-0.5" />
                                <span className="text-xs leading-relaxed text-slate-300">{rec}</span>
                            </div>
                        ))}
                    </div>
                </section>
            </div>

            {/* Footer */}
            <footer className="p-4 border-t border-slate-800 bg-slate-900/50">
                <button className="w-full py-3 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold uppercase tracking-widest rounded-xl transition-all border border-slate-700">
                    Generate Detailed PDF Report
                </button>
            </footer>
        </div>
    );
}

export default DetailsPanel;
