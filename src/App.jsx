import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import Sidebar from './components/Sidebar';
import MapView from './components/MapView';
import DetailsPanel from './components/DetailsPanel';
import ReportModal from './components/ReportModal';
import { AlertTriangle } from 'lucide-react';
import './index.css';

const API_BASE = 'http://localhost:8000';

function App() {
  // State management
  const [wards, setWards] = useState([]);
  const [selectedWard, setSelectedWard] = useState(null);
  const [wardDetails, setWardDetails] = useState(null);
  const [isDetailsPanelOpen, setIsDetailsPanelOpen] = useState(false);
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const [trafficReduction, setTrafficReduction] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const [showStations, setShowStations] = useState(true);

  // Fetch wards data
  const fetchWards = useCallback(async (reduction = 0) => {
    try {
      let response;
      if (reduction > 0) {
        response = await axios.post(`${API_BASE}/simulate`, {
          traffic_reduction_percentage: reduction
        });
      } else {
        response = await axios.get(`${API_BASE}/wards`);
      }
      setWards(response.data);
      setLastUpdated(new Date().toLocaleTimeString());
      setError(null);
    } catch (err) {
      console.error('Error fetching wards:', err);
      setError('Failed to connect to backend. Make sure the server is running on port 8000.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Fetch stats
  const fetchStats = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE}/stats`);
      setStats(response.data);
    } catch (err) {
      console.error('Error fetching stats:', err);
    }
  }, []);

  // Initial load
  useEffect(() => {
    fetchWards();
    fetchStats();
  }, [fetchWards, fetchStats]);

  // Poll for updates every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      fetchWards(trafficReduction);
      fetchStats();
    }, 30000);
    return () => clearInterval(interval);
  }, [fetchWards, fetchStats, trafficReduction]);

  // Handle ward selection
  const handleWardClick = async (ward) => {
    setSelectedWard(ward);
    setIsDetailsPanelOpen(true);

    // If it's an interpolated ward (client-side only), use the data we already have
    if (typeof ward.id === 'string' && ward.id.startsWith('feature-')) {
      setWardDetails(ward);
      return;
    }

    try {
      const response = await axios.get(`${API_BASE}/ward/${ward.id}`);
      setWardDetails(response.data);
    } catch (err) {
      console.error('Error fetching ward details:', err);
    }
  };

  // Handle traffic simulation
  const handleTrafficSimulation = (value) => {
    setTrafficReduction(value);
    fetchWards(value);
  };

  // Handle report submission
  const handleReportSubmit = async (reportData) => {
    try {
      await axios.post(`${API_BASE}/report`, reportData);
      setIsReportModalOpen(false);
      alert('Report submitted successfully! Thank you for helping keep Delhi clean.');
    } catch (err) {
      console.error('Error submitting report:', err);
      alert('Failed to submit report. Please try again.');
    }
  };

  // Close details panel
  const closeDetailsPanel = () => {
    setIsDetailsPanelOpen(false);
    setSelectedWard(null);
    setWardDetails(null);
  };

  // Get sorted wards for leaderboard (top 5 most polluted)
  const topPollutedWards = [...wards]
    .sort((a, b) => b.aqi - a.aqi)
    .slice(0, 5);

  // Error Boundary Component
  const ErrorFallback = ({ error }) => (
    <div className="flex items-center justify-center h-screen bg-gray-900 text-white p-4">
      <div className="text-center max-w-lg">
        <AlertTriangle size={48} className="text-red-500 mx-auto mb-4" />
        <h2 className="text-2xl font-bold mb-2">Something went wrong</h2>
        <pre className="bg-gray-800 p-4 rounded text-left overflow-auto text-sm mb-4 text-red-300">
          {error.message}
        </pre>
        <button
          onClick={() => window.location.reload()}
          className="px-4 py-2 bg-blue-600 rounded hover:bg-blue-700"
        >
          Reload Application
        </button>
      </div>
    </div>
  );

  try {
    return (
      <div className="flex h-screen w-screen overflow-hidden bg-slate-950 text-slate-100 selection:bg-blue-500/30">
        {/* Left Sidebar */}
        <Sidebar
          topWards={topPollutedWards}
          stats={stats}
          trafficReduction={trafficReduction}
          onTrafficChange={handleTrafficSimulation}
          onWardClick={handleWardClick}
          lastUpdated={lastUpdated}
        />

        {/* Main Map Area */}
        <main className="relative flex-1 flex flex-col h-full overflow-hidden">
          {/* Header Bar - Glassmorphism */}
          <header className="h-16 border-b border-slate-800 glass-panel flex items-center justify-between px-6 z-20">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center glow-blue">
                  <AlertTriangle className="w-5 h-5 text-white" />
                </div>
                <h1 className="text-xl font-bold tracking-tight">DELHI <span className="text-blue-500">AQI</span> COMMAND</h1>
              </div>

              <div className="h-6 w-px bg-slate-700 hidden md:block" />

              <div className="hidden md:flex items-center space-x-2 text-xs font-medium uppercase tracking-widest text-slate-400">
                <div className={`w-2 h-2 rounded-full ${isLoading ? 'bg-yellow-500 animate-pulse' : error ? 'status-offline' : 'status-online'}`} />
                <span>System: {isLoading ? 'Syncing' : error ? 'Offline' : 'Live'}</span>
              </div>
              {lastUpdated && !isLoading && !error && (
                <span className="text-xs text-slate-500 hidden lg:inline">
                  • Updated: {lastUpdated}
                </span>
              )}
            </div>

            <div className="flex items-center space-x-4">
              <button
                onClick={() => setShowStations(!showStations)}
                className={`flex items-center space-x-2 px-3 py-1.5 rounded-md text-sm transition-all border ${showStations
                  ? 'bg-blue-600/20 border-blue-500 text-blue-400 shadow-[0_0_10px_rgba(59,130,246,0.2)]'
                  : 'bg-slate-800 border-slate-700 text-slate-400 hover:bg-slate-700'
                  }`}
              >
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z" />
                  <circle cx="12" cy="10" r="3" />
                </svg>
                <span className="hidden sm:inline">Stations</span>
              </button>

              <button
                onClick={() => setIsReportModalOpen(true)}
                className="flex items-center space-x-2 px-4 py-1.5 bg-red-600 hover:bg-red-500 text-white rounded-md text-sm font-semibold transition-all shadow-[0_0_15px_rgba(239,68,68,0.3)]">
                <AlertTriangle className="w-4 h-4" />
                <span>Report Incident</span>
              </button>
            </div>
          </header>

          {/* Map Container */}
          <div className="flex-1 relative">

            {/* Loading State */}
            {isLoading && (
              <div className="absolute inset-0 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm z-[2000]">
                <div className="text-center">
                  <div className="loading-spinner mx-auto mb-4"></div>
                  <p className="text-slate-300">Loading pollution data...</p>
                </div>
              </div>
            )}

            {/* Error State */}
            {error && (
              <div className="absolute inset-0 flex items-center justify-center bg-slate-950/90 backdrop-blur-sm z-[2000]">
                <div className="text-center max-w-md p-6 glass-panel rounded-xl border-red-500/50">
                  <AlertTriangle size={48} className="text-red-500 mx-auto mb-4" />
                  <h3 className="text-xl font-semibold text-slate-100 mb-2">Connection Error</h3>
                  <p className="text-slate-300 mb-4">{error}</p>
                  <button
                    onClick={() => {
                      setError(null);
                      setIsLoading(true);
                      fetchWards();
                    }}
                    className="btn-primary"
                  >
                    Retry Connection
                  </button>
                </div>
              </div>
            )}

            {/* Map Component */}
            <MapView
              wards={wards}
              selectedWard={selectedWard}
              onWardClick={handleWardClick}
              showStations={showStations}
              trafficReduction={trafficReduction}
            />
          </div>
        </main>

        {/* Right Details Panel */}
        {isDetailsPanelOpen && wardDetails && (
          <DetailsPanel
            wardDetails={wardDetails}
            onClose={closeDetailsPanel}
          />
        )}

        {/* Report Modal */}
        {isReportModalOpen && (
          <ReportModal
            onClose={() => setIsReportModalOpen(false)}
            onSubmit={handleReportSubmit}
          />
        )}
      </div>
    );
  } catch (error) {
    return <ErrorFallback error={error} />;
  }
}

export default App;
