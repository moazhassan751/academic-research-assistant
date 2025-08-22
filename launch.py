#!/usr/bin/env python3
import sys
import os
import subprocess
import time
import argparse
import webbrowser
from pathlib import Path
from datetime import datetime

# Fix Windows encoding issues
if sys.platform.startswith('win'):
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

class AcademicResearchLauncher:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.processes = []
        self.ports = {
            'dashboard': 8501,
            'health': 8502
        }
    
    def print_banner(self):
        """Print the application banner"""
        banner = """
╔══════════════════════════════════════════════════════════════════╗
║               Academic Research Assistant Launcher               ║
║                        Version 2.0                              ║
╚══════════════════════════════════════════════════════════════════╝
"""
        print(banner)
        print(f"🚀 Starting from: {self.project_root}")
        print(f"⏰ Launch Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    def check_dependencies(self):
        """Check if required dependencies are installed"""
        print("🔍 Checking dependencies...")
        
        required_packages = [
            'streamlit', 'pandas', 'numpy', 'sqlite3', 
            'yaml', 'pathlib', 'datetime', 'json'
        ]
        
        missing = []
        for package in required_packages:
            try:
                __import__(package)
                print(f"  ✅ {package}")
            except ImportError:
                missing.append(package)
                print(f"  ❌ {package} - MISSING")
        
        if missing:
            print(f"\n🚨 Missing packages: {', '.join(missing)}")
            print("💡 Run: pip install -r requirements.txt")
            return False
        
        print("✅ All dependencies satisfied!")
        return True
    
    def validate_configuration(self):
        """Validate system configuration"""
        print("\n⚙️  Validating configuration...")
        
        try:
            from src.utils.config import config
            print("  ✅ Configuration loaded")
            print(f"  🌍 Environment: {config.environment}")
            print(f"  🤖 LLM Provider: {config.llm_config.get('provider', 'Unknown')}")
            print(f"  🔑 API Keys: {'Valid' if config.validate_api_keys() else 'Invalid'}")
            print(f"  🗄️  Database: {config.database_path}")
            return True
        except Exception as e:
            print(f"  ❌ Configuration error: {e}")
            return False
    
    def check_database(self):
        """Check database connectivity"""
        print("\n🗄️  Checking database...")
        
        try:
            db_path = Path("data/research.db")
            if db_path.exists():
                print(f"  ✅ Database found: {db_path}")
                print(f"  📊 Size: {db_path.stat().st_size / 1024:.1f} KB")
                return True
            else:
                print("  ⚠️  Database will be created on first use")
                return True
        except Exception as e:
            print(f"  ❌ Database error: {e}")
            return False
    
    def setup_environment(self):
        """Setup the environment"""
        print("\n🛠️  Setting up environment...")
        
        # Create necessary directories
        directories = ['data', 'logs', 'data/papers', 'data/cache', 'data/outputs']
        for dir_path in directories:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            print(f"  ✅ Created/verified: {dir_path}")
        
        # Check .env file
        env_file = Path(".env")
        if env_file.exists():
            print("  ✅ Environment file found")
        else:
            print("  ⚠️  No .env file found, using .env.example as template")
            if Path(".env.example").exists():
                subprocess.run(["copy", ".env.example", ".env"], shell=True, check=False)
        
        return True
    
    def run_health_check(self, auto_open=True):
        """Run the health check dashboard"""
        print("\n🏥 Launching Health Check Dashboard...")
        
        try:
            port = self.ports['health']
            cmd = [
                sys.executable, "-m", "streamlit", "run",
                str(self.project_root / "scripts" / "dashboard_health_check.py"),
                "--server.port", str(port),
                "--server.headless", "false",
                "--server.runOnSave", "false",
                "--browser.serverAddress", "localhost"
            ]
            
            print(f"🌐 Health Check URL: http://localhost:{port}")
            process = subprocess.Popen(cmd, cwd=self.project_root)
            self.processes.append(process)
            
            # Only open browser if requested
            if auto_open:
                time.sleep(3)
                print("🌐 Opening health check in browser...")
                webbrowser.open(f"http://localhost:{port}")
            
            return process
        except Exception as e:
            print(f"❌ Failed to launch health check: {e}")
            return None
    
    def launch_dashboard(self, port=None, auto_open=True):
        """Launch the main dashboard"""
        print("\n🚀 Launching Academic Research Assistant Dashboard...")
        
        try:
            if port is None:
                port = self.ports['dashboard']
            
            cmd = [
                sys.executable, "-m", "streamlit", "run",
                str(self.project_root / "integrated_dashboard.py"),
                "--server.port", str(port),
                "--server.headless", "false",
                "--server.runOnSave", "false",
                "--browser.serverAddress", "localhost"
            ]
            
            print(f"🌐 Dashboard URL: http://localhost:{port}")
            print("📱 Network URL: Available on your local network")
            print("🔧 Use Ctrl+C to stop the dashboard")
            
            process = subprocess.Popen(cmd, cwd=self.project_root)
            self.processes.append(process)
            
            # Only open browser if requested and wait a bit
            if auto_open:
                time.sleep(3)
                print("🌐 Opening dashboard in browser...")
                webbrowser.open(f"http://localhost:{port}")
            
            return process
        except Exception as e:
            print(f"❌ Failed to launch dashboard: {e}")
            return None
    
    def check_system_status(self):
        """Check the current system status"""
        print("\n📊 System Status Check...")
        
        # Check if services are running
        import socket
        
        services = {
            'Dashboard': self.ports['dashboard'],
            'Health Check': self.ports['health']
        }
        
        for service, port in services.items():
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            
            if result == 0:
                print(f"  ✅ {service}: Running on port {port}")
            else:
                print(f"  ❌ {service}: Not running on port {port}")
        
        # Check processes
        print(f"\n🔄 Active Processes: {len(self.processes)}")
        for i, process in enumerate(self.processes):
            if process.poll() is None:
                print(f"  ✅ Process {i+1}: Running (PID: {process.pid})")
            else:
                print(f"  ❌ Process {i+1}: Stopped")
    
    def stop_all_services(self):
        """Stop all running services"""
        print("\n🛑 Stopping all services...")
        
        for i, process in enumerate(self.processes):
            try:
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=5)
                    print(f"  ✅ Stopped process {i+1}")
                else:
                    print(f"  ℹ️  Process {i+1} already stopped")
            except subprocess.TimeoutExpired:
                process.kill()
                print(f"  ⚠️  Force killed process {i+1}")
            except Exception as e:
                print(f"  ❌ Error stopping process {i+1}: {e}")
        
        self.processes.clear()
        print("✅ All services stopped")
    
    def run_full_startup(self, auto_open=True):
        """Run complete startup sequence"""
        self.print_banner()
        
        # Pre-flight checks
        if not self.check_dependencies():
            print("\n🚨 Dependency check failed. Please install missing packages.")
            return False
        
        if not self.validate_configuration():
            print("\n🚨 Configuration validation failed.")
            return False
        
        if not self.check_database():
            print("\n🚨 Database check failed.")
            return False
        
        print("\n✅ All pre-flight checks passed!")
        print("\n🚀 Launching dashboard...")
        
        dashboard_process = self.launch_dashboard(auto_open=auto_open)
        if dashboard_process:
            print("\n🎉 Academic Research Assistant is ready!")
            print("\n📋 Available Commands:")
            print("  • Ctrl+C - Stop the dashboard")
            print("  • python launch.py --health - Run health check")
            print("  • python launch.py --status - Check system status")
            print("  • python launch.py --no-browser - Launch without opening browser")
            
            try:
                dashboard_process.wait()
            except KeyboardInterrupt:
                print("\n\n🛑 Shutdown requested...")
                self.stop_all_services()
                print("👋 Goodbye!")
        
        return True

def main():
    parser = argparse.ArgumentParser(
        description='Academic Research Assistant Launcher',
        formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=(
                "Examples:\n"
                "  python launch.py                    # Launch main dashboard (one tab)\n"
                "  python launch.py --no-browser       # Launch without opening browser\n"
                "  python launch.py --health           # Run health check only\n"
                "  python launch.py --config           # Validate configuration only\n"
                "  python launch.py --setup            # Setup environment\n"
                "  python launch.py --status           # Check system status\n"
                "  python launch.py --stop             # Stop all services\n"
                "  python launch.py --port 8080        # Use custom port"
            )
    )
    
    parser.add_argument('--health', action='store_true', help='Run health check dashboard')
    parser.add_argument('--config', action='store_true', help='Validate configuration only')
    parser.add_argument('--setup', action='store_true', help='Setup environment')
    parser.add_argument('--status', action='store_true', help='Check system status')
    parser.add_argument('--stop', action='store_true', help='Stop all services')
    parser.add_argument('--port', type=int, help='Custom port for dashboard')
    parser.add_argument('--no-browser', action='store_true', help='Don\'t automatically open browser')
    
    args = parser.parse_args()
    launcher = AcademicResearchLauncher()
    
    try:
        if args.setup:
            launcher.print_banner()
            launcher.setup_environment()
        elif args.config:
            launcher.print_banner()
            launcher.validate_configuration()
        elif args.health:
            launcher.print_banner()
            if launcher.check_dependencies() and launcher.validate_configuration():
                process = launcher.run_health_check(auto_open=not args.no_browser)
                if process:
                    try:
                        process.wait()
                    except KeyboardInterrupt:
                        launcher.stop_all_services()
        elif args.status:
            launcher.print_banner()
            launcher.check_system_status()
        elif args.stop:
            launcher.print_banner()
            launcher.stop_all_services()
        else:
            # Default: Full startup (main dashboard only)
            launcher.run_full_startup(auto_open=not args.no_browser)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Interrupted by user")
        launcher.stop_all_services()
        print("👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        launcher.stop_all_services()
        sys.exit(1)

if __name__ == "__main__":
    main()
