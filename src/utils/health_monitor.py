# System Health Monitor
import time
import psutil
import logging
from datetime import datetime
from typing import Dict, Any, List
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class HealthMetrics:
    """System health metrics"""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    active_processes: int
    api_response_time: float = 0.0
    error_rate: float = 0.0
    warnings_count: int = 0

class SystemHealthMonitor:
    """Monitor system health and performance"""
    
    def __init__(self, check_interval: int = 300):  # 5 minutes default
        self.check_interval = check_interval
        self.metrics_history: List[HealthMetrics] = []
        self.max_history = 100
        self.thresholds = {
            'cpu_warning': 80.0,
            'memory_warning': 85.0,
            'disk_warning': 90.0,
            'error_rate_warning': 10.0,
            'api_response_warning': 30.0
        }
    
    def check_system_health(self) -> HealthMetrics:
        """Perform comprehensive system health check"""
        try:
            # System metrics
            cpu_usage = psutil.cpu_percent(interval=1)
            memory_info = psutil.virtual_memory()
            disk_info = psutil.disk_usage('/')
            
            # Process count
            active_processes = len(psutil.pids())
            
            # Create metrics
            metrics = HealthMetrics(
                timestamp=datetime.now(),
                cpu_usage=cpu_usage,
                memory_usage=memory_info.percent,
                disk_usage=disk_info.percent,
                active_processes=active_processes
            )
            
            # Add to history
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > self.max_history:
                self.metrics_history.pop(0)
            
            # Check for warnings
            self._check_thresholds(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error checking system health: {e}")
            return self._get_default_metrics()
    
    def _check_thresholds(self, metrics: HealthMetrics):
        """Check if metrics exceed warning thresholds"""
        warnings = []
        
        if metrics.cpu_usage > self.thresholds['cpu_warning']:
            warnings.append(f"High CPU usage: {metrics.cpu_usage:.1f}%")
        
        if metrics.memory_usage > self.thresholds['memory_warning']:
            warnings.append(f"High memory usage: {metrics.memory_usage:.1f}%")
        
        if metrics.disk_usage > self.thresholds['disk_warning']:
            warnings.append(f"High disk usage: {metrics.disk_usage:.1f}%")
        
        if metrics.api_response_time > self.thresholds['api_response_warning']:
            warnings.append(f"Slow API response: {metrics.api_response_time:.1f}s")
        
        if metrics.error_rate > self.thresholds['error_rate_warning']:
            warnings.append(f"High error rate: {metrics.error_rate:.1f}%")
        
        if warnings:
            logger.warning(f"System health warnings: {'; '.join(warnings)}")
            metrics.warnings_count = len(warnings)
    
    def _get_default_metrics(self) -> HealthMetrics:
        """Get default metrics when system check fails"""
        return HealthMetrics(
            timestamp=datetime.now(),
            cpu_usage=0.0,
            memory_usage=0.0,
            disk_usage=0.0,
            active_processes=0,
            warnings_count=1  # Indicates system check failed
        )
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get summary of system health"""
        if not self.metrics_history:
            latest = self.check_system_health()
        else:
            latest = self.metrics_history[-1]
        
        # Calculate averages from recent history
        recent_metrics = self.metrics_history[-10:]  # Last 10 checks
        
        if len(recent_metrics) > 1:
            avg_cpu = sum(m.cpu_usage for m in recent_metrics) / len(recent_metrics)
            avg_memory = sum(m.memory_usage for m in recent_metrics) / len(recent_metrics)
            avg_disk = sum(m.disk_usage for m in recent_metrics) / len(recent_metrics)
            total_warnings = sum(m.warnings_count for m in recent_metrics)
        else:
            avg_cpu = latest.cpu_usage
            avg_memory = latest.memory_usage
            avg_disk = latest.disk_usage
            total_warnings = latest.warnings_count
        
        return {
            'status': self._get_overall_status(latest),
            'timestamp': latest.timestamp.isoformat(),
            'current': {
                'cpu_usage': f"{latest.cpu_usage:.1f}%",
                'memory_usage': f"{latest.memory_usage:.1f}%",
                'disk_usage': f"{latest.disk_usage:.1f}%",
                'active_processes': latest.active_processes,
                'api_response_time': f"{latest.api_response_time:.1f}s",
                'error_rate': f"{latest.error_rate:.1f}%"
            },
            'averages': {
                'cpu_usage': f"{avg_cpu:.1f}%",
                'memory_usage': f"{avg_memory:.1f}%", 
                'disk_usage': f"{avg_disk:.1f}%"
            },
            'warnings_count': total_warnings,
            'checks_performed': len(self.metrics_history)
        }
    
    def _get_overall_status(self, metrics: HealthMetrics) -> str:
        """Determine overall system status"""
        if metrics.warnings_count > 0:
            if (metrics.cpu_usage > 90 or 
                metrics.memory_usage > 95 or 
                metrics.error_rate > 20):
                return "CRITICAL"
            else:
                return "WARNING"
        return "HEALTHY"
    
    def check_project_health(self, project_path: str = ".") -> Dict[str, Any]:
        """Check project-specific health"""
        project_path = Path(project_path)
        health_info = {}
        
        try:
            # Check critical files
            critical_files = [
                'main.py', 'config.yaml', 'requirements.txt',
                'src/crew/research_crew.py', 'src/utils/export_manager.py'
            ]
            
            missing_files = []
            for file_path in critical_files:
                if not (project_path / file_path).exists():
                    missing_files.append(file_path)
            
            health_info['missing_critical_files'] = missing_files
            
            # Check directories
            required_dirs = ['data', 'logs', 'src', 'data/outputs']
            missing_dirs = []
            for dir_path in required_dirs:
                if not (project_path / dir_path).exists():
                    missing_dirs.append(dir_path)
            
            health_info['missing_directories'] = missing_dirs
            
            # Check database
            db_path = project_path / 'data' / 'research.db'
            health_info['database_exists'] = db_path.exists()
            if db_path.exists():
                health_info['database_size'] = f"{db_path.stat().st_size / 1024 / 1024:.1f} MB"
            
            # Check logs
            log_path = project_path / 'logs' / 'research_assistant.log'
            health_info['log_file_exists'] = log_path.exists()
            if log_path.exists():
                health_info['log_file_size'] = f"{log_path.stat().st_size / 1024:.1f} KB"
            
            # Overall project status
            issues = len(missing_files) + len(missing_dirs)
            if issues == 0:
                health_info['project_status'] = "HEALTHY"
            elif issues <= 2:
                health_info['project_status'] = "WARNING"
            else:
                health_info['project_status'] = "CRITICAL"
                
        except Exception as e:
            logger.error(f"Error checking project health: {e}")
            health_info['project_status'] = "ERROR"
            health_info['error_message'] = str(e)
        
        return health_info
    
    def generate_health_report(self, project_path: str = ".") -> str:
        """Generate comprehensive health report"""
        system_health = self.get_health_summary()
        project_health = self.check_project_health(project_path)
        
        report = []
        report.append("🔍 ACADEMIC RESEARCH ASSISTANT - HEALTH REPORT")
        report.append("=" * 50)
        report.append(f"Report Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # System Health
        report.append("🖥️  SYSTEM HEALTH")
        report.append(f"Status: {system_health['status']}")
        report.append(f"CPU Usage: {system_health['current']['cpu_usage']}")
        report.append(f"Memory Usage: {system_health['current']['memory_usage']}")
        report.append(f"Disk Usage: {system_health['current']['disk_usage']}")
        report.append(f"Warnings: {system_health['warnings_count']}")
        report.append("")
        
        # Project Health
        report.append("📁 PROJECT HEALTH")
        report.append(f"Status: {project_health['project_status']}")
        
        if project_health.get('missing_critical_files'):
            report.append(f"Missing Files: {', '.join(project_health['missing_critical_files'])}")
        
        if project_health.get('missing_directories'):
            report.append(f"Missing Directories: {', '.join(project_health['missing_directories'])}")
        
        if project_health.get('database_exists'):
            report.append(f"Database: ✅ ({project_health.get('database_size', 'Unknown size')})")
        else:
            report.append("Database: ❌ Missing")
        
        if project_health.get('log_file_exists'):
            report.append(f"Log File: ✅ ({project_health.get('log_file_size', 'Unknown size')})")
        else:
            report.append("Log File: ❌ Missing")
        
        report.append("")
        report.append("✅ Health check completed")
        
        return "\n".join(report)

# Global health monitor instance
health_monitor = SystemHealthMonitor()
