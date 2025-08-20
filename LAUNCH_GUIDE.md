# 🚀 Academic Research Assistant - Launch Guide

## Quick Start

### Windows Users (Easiest)
1. **Double-click `START_HERE.bat`** - This will automatically launch the dashboard
2. Wait for your browser to open with the dashboard
3. That's it! 🎉

### Advanced Users

#### Python Launcher (Cross-platform)
```bash
# Launch main dashboard
python launch.py

# Run health check
python launch.py --health

# Validate configuration
python launch.py --config

# Setup environment
python launch.py --setup

# Check system status  
python launch.py --status

# Stop all services
python launch.py --stop

# Use custom port
python launch.py --port 8080
```

#### PowerShell (Windows)
```powershell
# Launch main dashboard
.\launch.ps1

# Run health check
.\launch.ps1 -Health

# Validate configuration
.\launch.ps1 -Config

# Setup environment
.\launch.ps1 -Setup

# Check system status
.\launch.ps1 -Status

# Stop all services
.\launch.ps1 -Stop

# Use custom port
.\launch.ps1 -Port 8080
```

## What Happens When You Launch

1. **🔍 Dependency Check** - Verifies all required packages are installed
2. **⚙️ Configuration Validation** - Checks your API keys and settings
3. **🗄️ Database Check** - Ensures database connectivity
4. **📁 Directory Setup** - Creates necessary folders
5. **🚀 Dashboard Launch** - Starts the Streamlit dashboard
6. **🌐 Browser Open** - Automatically opens your browser to the dashboard

## Default URLs

- **Main Dashboard**: http://localhost:8501
- **Health Check**: http://localhost:8502

## Troubleshooting

### Python Not Found
- Install Python from https://www.python.org/downloads/
- Make sure to check "Add Python to PATH" during installation

### Missing Dependencies
Run: `pip install -r requirements.txt`

### Port Already in Use
Use a custom port: `python launch.py --port 8080`

### Configuration Issues
Run: `python launch.py --config` to validate your settings

## System Requirements

- **Python**: 3.8 or higher
- **RAM**: 4GB recommended
- **Disk Space**: 2GB free space
- **Internet**: Required for API calls and paper downloads

## Features

✅ **Automatic dependency checking**  
✅ **Configuration validation**  
✅ **Database connectivity testing**  
✅ **Health monitoring**  
✅ **Cross-platform support**  
✅ **Multiple launch options**  
✅ **Graceful shutdown**  
✅ **Browser auto-launch**  
✅ **Port management**  
✅ **Process monitoring**  

## Need Help?

1. Run `python launch.py --health` to check system health
2. Run `python launch.py --config` to validate configuration
3. Check the logs in the `logs/` folder
4. Review the documentation in the `docs/` folder

---

**Happy Researching! 🔬📚**
