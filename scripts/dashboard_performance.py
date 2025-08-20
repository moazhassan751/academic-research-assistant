"""
Dashboard Performance Monitor & Health Check
Ensures 100% efficiency and professional operation
"""
import time
import psutil
import threading
from datetime import datetime
from typing import Dict, Any
import streamlit as st

class DashboardPerformanceMonitor:
    def __init__(self):
        self.start_time = time.time()
        self.performance_metrics = {}
        self.error_count = 0
        self.last_health_check = time.time()
        
    def start_operation(self, operation_name: str) -> str:
        """Start timing an operation"""
        operation_id = f"{operation_name}_{int(time.time() * 1000)}"
        self.performance_metrics[operation_id] = {
            'name': operation_name,
            'start_time': time.time(),
            'status': 'running'
        }
        return operation_id
    
    def end_operation(self, operation_id: str, status: str = 'success'):
        """End timing an operation"""
        if operation_id in self.performance_metrics:
            end_time = time.time()
            self.performance_metrics[operation_id].update({
                'end_time': end_time,
                'duration': end_time - self.performance_metrics[operation_id]['start_time'],
                'status': status
            })
            
            if status == 'error':
                self.error_count += 1
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system performance metrics"""
        try:
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('.').percent,
                'uptime': time.time() - self.start_time,
                'error_count': self.error_count,
                'active_operations': len([m for m in self.performance_metrics.values() if m['status'] == 'running'])
            }
        except:
            return {'error': 'Unable to get system metrics'}
    
    def health_check(self) -> Dict[str, str]:
        """Perform comprehensive health check"""
        health = {
            'overall': 'healthy',
            'database': 'unknown',
            'ai_agents': 'unknown',
            'performance': 'good'
        }
        
        try:
            # Check system resources
            memory_usage = psutil.virtual_memory().percent
            cpu_usage = psutil.cpu_percent()
            
            if memory_usage > 90:
                health['performance'] = 'critical'
                health['overall'] = 'warning'
            elif memory_usage > 70 or cpu_usage > 80:
                health['performance'] = 'warning'
            
            # Check error rate
            if self.error_count > 10:
                health['overall'] = 'critical'
            elif self.error_count > 5:
                health['overall'] = 'warning'
                
            self.last_health_check = time.time()
            return health
            
        except Exception as e:
            return {'overall': 'error', 'error': str(e)}
    
    def get_performance_report(self) -> str:
        """Generate performance report"""
        metrics = self.get_system_metrics()
        recent_ops = [m for m in self.performance_metrics.values() 
                     if m.get('end_time', 0) > time.time() - 300]  # Last 5 minutes
        
        avg_duration = sum(op.get('duration', 0) for op in recent_ops) / max(len(recent_ops), 1)
        
        report = f"""
        📊 **Performance Report**
        - **System Uptime**: {metrics.get('uptime', 0)/3600:.1f} hours
        - **Memory Usage**: {metrics.get('memory_percent', 0):.1f}%
        - **CPU Usage**: {metrics.get('cpu_percent', 0):.1f}%
        - **Recent Operations**: {len(recent_ops)}
        - **Average Response**: {avg_duration:.2f}s
        - **Error Count**: {self.error_count}
        """
        
        return report

# Global performance monitor instance
performance_monitor = DashboardPerformanceMonitor()

def with_performance_tracking(operation_name: str):
    """Decorator for performance tracking"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            op_id = performance_monitor.start_operation(operation_name)
            try:
                result = func(*args, **kwargs)
                performance_monitor.end_operation(op_id, 'success')
                return result
            except Exception as e:
                performance_monitor.end_operation(op_id, 'error')
                st.error(f"Error in {operation_name}: {str(e)}")
                raise
        return wrapper
    return decorator

def show_performance_sidebar():
    """Show performance metrics in sidebar"""
    with st.sidebar:
        st.markdown("### 📊 System Performance")
        
        metrics = performance_monitor.get_system_metrics()
        health = performance_monitor.health_check()
        
        # Overall health indicator
        health_color = {
            'healthy': '🟢',
            'warning': '🟡', 
            'critical': '🔴',
            'error': '⚠️'
        }
        
        st.markdown(f"**Status**: {health_color.get(health['overall'], '❓')} {health['overall'].upper()}")
        
        # Key metrics
        if 'error' not in metrics:
            st.metric("Memory", f"{metrics.get('memory_percent', 0):.1f}%")
            st.metric("CPU", f"{metrics.get('cpu_percent', 0):.1f}%") 
            st.metric("Uptime", f"{metrics.get('uptime', 0)/3600:.1f}h")
            st.metric("Errors", metrics.get('error_count', 0))
        
        # Performance tips
        if metrics.get('memory_percent', 0) > 70:
            st.warning("⚡ High memory usage detected. Consider clearing cache.")
        
        if performance_monitor.error_count > 3:
            st.error("🚨 Multiple errors detected. Check system health.")
