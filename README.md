# Capital Laughs - Comedy Ticket Sales Analysis

## 📊 Overview

This project analyzes ticket sales data for comedy shows across weekdays, providing insights into:
- **Time Series Analysis**: Trends and patterns over time
- **Purchase Timing**: When customers buy tickets relative to show dates
- **Customer Behavior**: Repeat customers and purchasing patterns
- **Geographic Analysis**: Customer distribution by location
- **Holiday Impact**: How US holidays affect ticket sales
- **Payment & Ticket Patterns**: Payment methods and ticket quantity preferences

## 🚀 Quick Start

### Option 1: Docker Setup (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/judeha/capital-laughs.git
   cd capital-laughs
   ```

2. **Build and run with Docker**
   ```bash
   docker-compose -f .devcontainer/docker-compose.yml up -d
   ```

3. **Run the analysis**
   ```bash
   # Basic analysis (uses only Python standard library)
   docker exec devcontainer-jupyter-1 python3 src/basic_analysis.py
   ```

4. **Launch the dashboard for visualization**
   ```bash   
   docker exec -d devcontainer-jupyter-1 streamlit run src/dashboard.py --server.port 8503 --server.address 0.0.0.0 --server.headless true
   ```

5. **Access the applications**
   - **Dashboard**: http://localhost:8503

### Option 2: Local Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run analysis**
   ```bash
   # Basic analysis
   python3 src/basic_analysis.py
   ```

3. **Launch dashboards**
   ```bash
   streamlit run src/dashboard.py --server.port 8503
   ```

## 📁 Project Structure

```
capital-laughs/
├── src/
│   ├── data/                          # CSV data files
│   │   ├── Monday.csv
│   │   ├── Tuesday.csv
│   │   ├── Wednesday.csv
│   │   ├── Thursday.csv
│   │   ├── Friday.csv
│   │   └── Saturday.csv
│   ├── basic_analysis.py              # Simple analysis outputs to console + JSON
│   ├── show_insights.py               # Show-level analysis (individual shows)
│   ├── advanced_time_series.py        # Advanced time series analysis module
│   └── dashboard.py                   # Analysis dashboard
├── .devcontainer/
│   ├── docker-compose.yml             # Docker configuration
│   └── devcontainer.json              # VS Code dev container config
├── Dockerfile                         # Docker image definition
├── requirements.txt                   # Python dependencies
└── README.md                          # This file
```

**🎯 Key Feature: Single Show Day Filtering**
- Filter ALL analyses to focus on specific show days (Monday vs Thursday vs Saturday etc.)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's running on the port
   lsof -i :8501
   # Kill the process if needed
   kill -9 <PID>
   ```

2. **Docker Container Issues**
   ```bash
   # Rebuild container
   docker-compose -f .devcontainer/docker-compose.yml down
   docker-compose -f .devcontainer/docker-compose.yml build --no-cache
   docker-compose -f .devcontainer/docker-compose.yml up -d
   ```

3. **Missing Dependencies**
   ```bash
   # Install in container
   docker exec devcontainer-jupyter-1 pip install -r requirements.txt
   ```
