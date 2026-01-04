# 🌫️ Delhi AQI Command - Ward-Wise Pollution Action Dashboard

<p align="center">
  <img src="https://img.shields.io/badge/React-19.2-61DAFB?style=for-the-badge&logo=react" />
  <img src="https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi" />
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python" />
  <img src="https://img.shields.io/badge/Vite-7.2-646CFF?style=for-the-badge&logo=vite" />
</p>

**Delhi AQI Command** is a real-time, ward-wise air quality monitoring and action dashboard for Delhi, India. It combines live pollution data from multiple APIs with AI-powered analysis to provide actionable insights for citizens and policymakers.

---

##  Features

### 📊 Real-Time Pollution Monitoring
- **Live AQI Data** from multiple sources (AQICN, OpenAQ, CPCB)
- **72+ Delhi Wards** with individual pollution tracking
- **Interactive Map** with color-coded AQI zones using Leaflet
- **Station Markers** showing actual monitoring station locations

###  AI-Powered Analysis
- **Inhouse Model Integration** for intelligent pollution source prediction
- **Weather-Aware Recommendations** using OpenWeatherMap data
- **Source Breakdown** (Vehicular, Industrial, Construction Dust, Biomass Burning)
- **Actionable Recommendations** tailored to pollution levels

###  Scientific Methodology
- **Inverse Distance Weighting (IDW)** interpolation for ward-level AQI estimates
- **Multi-pollutant analysis** (PM2.5, PM10, NO2, SO2, CO, O3)
- **Real-time data aggregation** from multiple API sources

###  Interactive Features
- **Traffic Reduction Simulator** - Model impact of reducing vehicular emissions
- **Citizen Report System** - Report pollution incidents (burning, dust, smoke)
- **Top Polluted Wards Leaderboard** - Track the most affected areas
- **Detailed Ward Panels** - Deep-dive into any ward's pollution data

---

##  Tech Stack

### Frontend
| Technology | Purpose |
|------------|---------|
| React 19 | UI Framework |
| Vite 7 | Build Tool & Dev Server |
| Leaflet + React-Leaflet | Interactive Maps |
| Recharts | Data Visualization |
| Tailwind CSS 4 | Styling |
| Axios | API Communication |
| Lucide React | Icons |

### Backend
| Technology | Purpose |
|------------|---------|
| FastAPI | REST API Framework |
| Uvicorn | ASGI Server |
| NumPy/SciPy | IDW Calculations |
| HTTPX | Async HTTP Client |
| Pydantic | Data Validation |
| Python-dotenv | Environment Config |

### APIs & Services
| Service | Purpose |
|---------|---------|
| AQICN (waqi.info) | Primary AQI Data |
| OpenAQ | Secondary AQI Data |
| CPCB (data.gov.in) | Government AQI Data |
| OpenWeatherMap | Weather Context |
| Inhouse AI Model | Pollution Analysis |

---

##  Quick Start

### Prerequisites
- **Node.js** 18+ with npm
- **Python** 3.10+
- **Git**

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/delhi-pollution-dashboard.git
cd delhi-pollution-dashboard
```

### 2. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys
```

### 3. Frontend Setup
```bash
# From project root
npm install
```

### 4. Run the Application

**Terminal 1 - Backend:**
```bash
cd backend
python main.py
# API runs at http://localhost:8000
# Docs at http://localhost:8000/docs
```

**Terminal 2 - Frontend:**
```bash
npm run dev
# App runs at http://localhost:5173
```

---

## ⚙️ Environment Configuration

Create `backend/.env` with the following:

```env
# Delhi Pollution Dashboard - Environment Variables

# CPCB API Key - Get from data.gov.in
CPCB_API_KEY=your_cpcb_api_key

# AQICN Token - Get from aqicn.org/data-platform/token
AQICN_TOKEN=your_aqicn_token

# Inhouse AI API Key - For pollution analysis
GROQ_API_KEY=your_ai_api_key

# OpenWeatherMap API Key - Get from openweathermap.org
OPENWEATHER_API_KEY=your_openweather_key

# Cache TTL in minutes
CACHE_TTL_MINUTES=5

# API Priority order
API_PRIORITY=aqicn,openaq
```

### Getting API Keys

| API | Registration URL |
|-----|------------------|
| AQICN | https://aqicn.org/data-platform/token/ |
| CPCB/data.gov.in | https://data.gov.in/user/register |
| OpenWeatherMap | https://openweathermap.org/api |

---

##  Project Structure

```
delhi-pollution-dashboard/
├──  backend/
│   ├── main.py              # FastAPI app & endpoints
│   ├── ai_analyzer.py       # AI-powered analysis module
│   ├── aqi_fetcher.py       # Multi-source data aggregation
│   ├── cache.py             # Caching layer
│   ├── config.py            # Configuration & station list
│   ├── requirements.txt     # Python dependencies
│   ├── .env.example         # Environment template
│   └── .env                  # Your API keys (gitignored)
│
├──  src/
│   ├── App.jsx              # Main React component
│   ├── main.jsx             # React entry point
│   ├── index.css            # Global styles
│   ├──  components/
│   │   ├── MapView.jsx      # Leaflet map component
│   │   ├── Sidebar.jsx      # Stats & controls sidebar
│   │   ├── DetailsPanel.jsx # Ward details panel
│   │   └── ReportModal.jsx  # Citizen report form
│   └──  assets/
│
├──  public/
│   └── Delhi_Wards.geojson  # Ward boundary data
│
├── package.json             # Node dependencies
├── vite.config.js           # Vite configuration
├── .gitignore               # Git ignore rules
└── README.md                # This file
```

---

##  API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check & status |
| `/wards` | GET | All wards with AQI data |
| `/ward/{id}` | GET | Detailed ward information |
| `/simulate` | POST | Traffic reduction simulation |
| `/report` | POST | Submit citizen report |
| `/reports` | GET | List all reports |
| `/stats` | GET | City-wide statistics |
| `/api/stations` | GET | Raw station data |
| `/api/sources` | GET | API source status |
| `/api/refresh` | GET | Force data refresh |
| `/api/ai-status` | GET | AI analysis status |

Full API documentation available at `http://localhost:8000/docs` when running.

---

##  AQI Color Scale

| AQI Range | Category | Color |
|-----------|----------|-------|
| 0-50 | Good | 🟢 Green |
| 51-100 | Moderate | 🟡 Yellow |
| 101-150 | Unhealthy for Sensitive | 🟠 Orange |
| 151-200 | Unhealthy | 🔴 Red |
| 201-300 | Very Unhealthy | 🟣 Purple |
| 301-500 | Hazardous | 🟤 Maroon |

---

##  Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

##  License

This project was developed for **Hack4Delhi Hackathon**.

---

##  Acknowledgments

- **AQICN** for providing comprehensive air quality data
- **OpenAQ** for open-source pollution data
- **Central Pollution Control Board (CPCB)** for official monitoring data
- **Delhi Government** for ward boundary GeoJSON data

---

