import { BarChart3, Users, Wind, TrendingUp, TrendingDown, Minus, Settings2 } from 'lucide-react';

/**
 * Sidebar Component - Glassmorphism Command Center
 * Shows: Global Metrics, Top Polluted Wards, Control Scenario Simulator
 */
function Sidebar({ topWards, stats, trafficReduction, onTrafficChange, onWardClick, lastUpdated }) {

    // Get AQI color based on value
    const getAqiColor = (aqi) => {
        if (aqi <= 50) return '#22c55e';       // Green
        if (aqi <= 100) return '#eab308';      // Yellow
        if (aqi <= 150) return '#f97316';      // Orange
        if (aqi <= 200) return '#ef4444';      // Red
        if (aqi <= 300) return '#a855f7';      // Purple
        return '#881337';                       // Maroon
    };

    // Get trend icon
    const getTrendIcon = (trend) => {
        if (trend.startsWith('+')) {
            return <TrendingUp className="w-3 h-3 text-red-500 ml-auto" />;
        } else if (trend.startsWith('-')) {
            return <TrendingDown className="w-3 h-3 text-green-500 ml-auto" />;
        }
        return <Minus className="w-3 h-3 text-slate-500 ml-auto" />;
    };

    return (
        <aside className="w-80 h-full border-r border-slate-800 bg-slate-900 flex flex-col z-50 overflow-hidden relative">
            <div className="p-6 space-y-6 overflow-y-auto flex-1">

                {/* Stats Grid */}
                <section className="space-y-4">
                    <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-widest flex items-center">
                        <BarChart3 className="w-4 h-4 mr-2" /> Global Metrics
                    </h2>
                    <div className="grid grid-cols-2 gap-3">
                        <div className="glass-panel p-3 rounded-xl border-slate-800">
                            <span className="text-xs text-slate-400 block">Avg AQI</span>
                            <span className="text-2xl font-bold text-white leading-tight">
                                {stats?.average_aqi ? Math.round(stats.average_aqi) : '--'}
                            </span>
                            <div className="flex items-center text-[10px] mt-1 font-medium text-red-400">
                                <TrendingUp className="w-3 h-3 mr-1" /> Critical
                            </div>
                        </div>
                        <div className="glass-panel p-3 rounded-xl border-slate-800">
                            <span className="text-xs text-slate-400 block">Hotspots</span>
                            <span className="text-2xl font-bold text-white leading-tight">
                                {stats?.critical_wards || '--'}
                            </span>
                            <div className="flex items-center text-[10px] mt-1 font-medium text-orange-400">
                                <Wind className="w-3 h-3 mr-1" /> Poor Air
                            </div>
                        </div>
                        <div className="glass-panel p-3 rounded-xl border-slate-800 col-span-2">
                            <span className="text-xs text-slate-400 block">Active Reports</span>
                            <div className="flex items-center justify-between">
                                <span className="text-2xl font-bold text-white">
                                    {stats?.total_reports || '0'}
                                </span>
                                <Users className="w-5 h-5 text-blue-500" />
                            </div>
                        </div>
                    </div>
                </section>

                {/* Leaderboard - Top Polluted Wards */}
                <section className="space-y-4">
                    <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-widest flex items-center">
                        <svg className="w-4 h-4 mr-2" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <polygon points="12 2 2 7 12 12 22 7 12 2" />
                            <polyline points="2 17 12 22 22 17" />
                            <polyline points="2 12 12 17 22 12" />
                        </svg>
                        Most Polluted Wards
                    </h2>
                    <div className="space-y-2">
                        {topWards && topWards.length > 0 ? (
                            topWards.map((ward, idx) => (
                                <button
                                    key={ward.id}
                                    onClick={() => onWardClick(ward)}
                                    className="w-full text-left p-3 rounded-xl bg-slate-800/50 hover:bg-slate-800 border border-transparent hover:border-slate-700 transition-all flex items-center justify-between group"
                                >
                                    <div className="flex items-center space-x-3">
                                        <span className="text-slate-500 font-mono text-sm">{idx + 1}</span>
                                        <div>
                                            <span className="text-sm font-medium block truncate w-32">{ward.name}</span>
                                            <span className="text-[10px] text-slate-500 uppercase">{ward.dominant_source}</span>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <div className="text-sm font-bold" style={{ color: getAqiColor(ward.aqi) }}>
                                            {ward.aqi}
                                        </div>
                                        {getTrendIcon(ward.trend)}
                                    </div>
                                </button>
                            ))
                        ) : (
                            <div className="text-xs text-slate-500 text-center py-4">
                                No data available
                            </div>
                        )}
                    </div>
                </section>

                {/* Control Scenario Simulator */}
                <section className="space-y-4 pt-4 border-t border-slate-800">
                    <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-widest flex items-center">
                        <Settings2 className="w-4 h-4 mr-2" /> Control Scenario
                    </h2>
                    <div className="glass-panel p-4 rounded-xl space-y-4 border-slate-800">
                        <div>
                            <div className="flex justify-between text-xs mb-2">
                                <span className="text-slate-400">Traffic Reduction</span>
                                <span className="text-blue-500 font-bold">{trafficReduction}%</span>
                            </div>
                            <input
                                type="range"
                                min="0"
                                max="100"
                                value={trafficReduction}
                                onChange={(e) => onTrafficChange(parseInt(e.target.value))}
                                className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-500"
                            />
                        </div>
                        <p className="text-[10px] text-slate-500 leading-relaxed italic">
                            Adjusting traffic volume will simulate changes in NOx levels and predicted AQI improvement across all monitoring points.
                        </p>
                    </div>
                </section>
            </div>

            {/* Footer */}
            <div className="p-4 bg-slate-950 border-t border-slate-800">
                <div className="text-[10px] text-slate-600 font-mono text-center">
                    DELHI_ENV_SYSTEM v4.0.2 // STABLE
                </div>
            </div>
        </aside>
    );
}

export default Sidebar;
