import { useState } from 'react';
import { X, AlertCircle, Send, Camera } from 'lucide-react';

/**
 * ReportModal Component - Glassmorphism
 * Citizen pollution incident reporting form
 */
function ReportModal({ onClose, onSubmit }) {
    const [formData, setFormData] = useState({
        lat: 28.6139,
        lon: 77.2090,
        issue_type: 'Burning',
        description: ''
    });
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsSubmitting(true);
        setError(null);
        try {
            await onSubmit(formData);
        } catch (err) {
            setError('Failed to submit report. Please try again.');
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center z-[100] p-4 animate-in">
            <div className="w-full max-w-lg glass-panel rounded-3xl overflow-hidden shadow-2xl">
                {/* Header */}
                <header className="p-6 border-b border-slate-800 flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                        <AlertCircle className="w-5 h-5 text-red-500" />
                        <h2 className="text-xl font-bold">Citizen Pollution Report</h2>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-slate-800 rounded-full transition-colors"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </header>

                {/* Form */}
                <form onSubmit={handleSubmit} className="p-6 space-y-6">
                    <div className="space-y-4">
                        {/* Issue Type */}
                        <div className="space-y-2">
                            <label className="text-xs font-bold text-slate-400 uppercase tracking-widest">
                                Issue Type
                            </label>
                            <select
                                value={formData.issue_type}
                                onChange={(e) => setFormData({ ...formData, issue_type: e.target.value })}
                                className="w-full bg-slate-900 border border-slate-700 rounded-xl p-3 focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                            >
                                <option value="Burning">Waste/Biomass Burning</option>
                                <option value="Construction">Illegal Construction Dust</option>
                                <option value="Industrial">Industrial Smoke Emission</option>
                                <option value="Traffic">Excessive Traffic Congestion</option>
                                <option value="Other">Other Environmental Concern</option>
                            </select>
                        </div>

                        {/* Description */}
                        <div className="space-y-2">
                            <label className="text-xs font-bold text-slate-400 uppercase tracking-widest">
                                Incident Description
                            </label>
                            <textarea
                                required
                                rows={4}
                                value={formData.description}
                                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                placeholder="Describe the incident, exact location, and severity..."
                                className="w-full bg-slate-900 border border-slate-700 rounded-xl p-3 focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                            />
                        </div>

                        {/* Action Buttons */}
                        <div className="grid grid-cols-2 gap-4">
                            <button
                                type="button"
                                className="flex items-center justify-center space-x-2 p-3 border border-slate-700 rounded-xl hover:bg-slate-800 transition-all text-xs font-bold uppercase"
                            >
                                <Camera className="w-4 h-4" />
                                <span>Attach Photo</span>
                            </button>
                            <button
                                type="button"
                                onClick={() => {
                                    navigator.geolocation.getCurrentPosition(pos => {
                                        setFormData({ ...formData, lat: pos.coords.latitude, lon: pos.coords.longitude });
                                    });
                                }}
                                className="flex items-center justify-center space-x-2 p-3 border border-slate-700 rounded-xl hover:bg-slate-800 transition-all text-xs font-bold uppercase"
                            >
                                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z" />
                                    <circle cx="12" cy="10" r="3" />
                                </svg>
                                <span>Get Current Location</span>
                            </button>
                        </div>
                    </div>

                    {error && (
                        <p className="text-xs text-red-500 bg-red-500/10 p-2 rounded-lg">{error}</p>
                    )}

                    {/* Submit Button */}
                    <button
                        disabled={isSubmitting}
                        className="w-full py-4 bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white font-black uppercase tracking-widest rounded-xl transition-all shadow-lg flex items-center justify-center space-x-2"
                    >
                        {isSubmitting ? (
                            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        ) : (
                            <>
                                <Send className="w-5 h-5" />
                                <span>Submit Critical Report</span>
                            </>
                        )}
                    </button>
                </form>
            </div>
        </div>
    );
}

export default ReportModal;
