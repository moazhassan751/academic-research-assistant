"""
Network Configuration and DNS Fallback for Academic Research Assistant
Handles DNS resolution issues and provides fallback mechanisms
"""

import socket
import requests
import time
import logging
from typing import Dict, List, Optional, Callable, Any
from urllib.parse import urlparse
import json

logger = logging.getLogger(__name__)

class NetworkConfig:
    """Network configuration and fallback mechanisms"""
    
    def __init__(self):
        self.dns_servers = [
            "8.8.8.8",      # Google DNS
            "8.8.4.4",      # Google DNS Secondary  
            "1.1.1.1",      # Cloudflare DNS
            "208.67.222.222", # OpenDNS
        ]
        
        self.api_endpoints = {
            'gemini': [
                'generativelanguage.googleapis.com',
                'ai.google.dev'
            ],
            'huggingface': [
                'huggingface.co',
                'hf.co'
            ],
            'openalex': [
                'api.openalex.org'
            ],
            'crossref': [
                'api.crossref.org'
            ]
        }
        
        self.request_config = {
            'timeout': (30, 120),  # (connect_timeout, read_timeout)
            'max_retries': 3,
            'backoff_factor': 2,
            'retry_on_status': [500, 502, 503, 504, 520, 521, 522, 524],
            'retry_on_errors': [
                'DNS', 'getaddrinfo', 'Name resolution', 'Connection reset',
                'Socket', 'Timeout', 'Connection aborted', 'handshaker'
            ]
        }
    
    def check_dns_resolution(self, hostname: str) -> bool:
        """Check if hostname can be resolved"""
        try:
            socket.gethostbyname(hostname)
            return True
        except socket.gaierror:
            return False
    
    def check_internet_connectivity(self) -> bool:
        """Check basic internet connectivity"""
        test_urls = [
            'https://www.google.com',
            'https://www.cloudflare.com',
            'https://httpbin.org/get'
        ]
        
        for url in test_urls:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    logger.info(f"Internet connectivity confirmed via {url}")
                    return True
            except Exception:
                continue
        
        logger.warning("No internet connectivity detected")
        return False
    
    def get_resilient_session(self) -> requests.Session:
        """Create a requests session with robust retry logic"""
        session = requests.Session()
        
        # Configure retry strategy
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=self.request_config['max_retries'],
            backoff_factor=self.request_config['backoff_factor'],
            status_forcelist=self.request_config['retry_on_status'],
            allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set timeouts
        session.timeout = self.request_config['timeout']
        
        return session
    
    def test_api_endpoints(self) -> Dict[str, bool]:
        """Test connectivity to various API endpoints"""
        results = {}
        session = self.get_resilient_session()
        
        for service, endpoints in self.api_endpoints.items():
            results[service] = False
            for endpoint in endpoints:
                try:
                    # Simple connectivity test
                    url = f"https://{endpoint}"
                    response = session.head(url, timeout=10)
                    if response.status_code < 500:  # Any non-server error is good
                        results[service] = True
                        logger.info(f"✅ {service} connectivity via {endpoint}: OK")
                        break
                except Exception as e:
                    logger.debug(f"❌ {service} test failed for {endpoint}: {e}")
                    continue
            
            if not results[service]:
                logger.warning(f"⚠️  {service} connectivity: FAILED")
        
        return results
    
    def get_network_diagnostics(self) -> Dict[str, Any]:
        """Get comprehensive network diagnostics"""
        diagnostics = {
            'timestamp': time.time(),
            'internet_connectivity': self.check_internet_connectivity(),
            'dns_resolution': {},
            'api_connectivity': self.test_api_endpoints(),
            'recommendations': []
        }
        
        # Test DNS resolution for key services
        for service, endpoints in self.api_endpoints.items():
            diagnostics['dns_resolution'][service] = {}
            for endpoint in endpoints:
                diagnostics['dns_resolution'][service][endpoint] = self.check_dns_resolution(endpoint)
        
        # Generate recommendations
        if not diagnostics['internet_connectivity']:
            diagnostics['recommendations'].append("Check internet connection and firewall settings")
        
        failed_dns = []
        for service, endpoints in diagnostics['dns_resolution'].items():
            if not any(endpoints.values()):
                failed_dns.append(service)
        
        if failed_dns:
            diagnostics['recommendations'].append(
                f"DNS resolution failed for: {', '.join(failed_dns)}. Consider using alternative DNS servers."
            )
        
        failed_apis = [service for service, status in diagnostics['api_connectivity'].items() if not status]
        if failed_apis:
            diagnostics['recommendations'].append(
                f"API connectivity failed for: {', '.join(failed_apis)}. Check VPN/proxy settings."
            )
        
        return diagnostics
    
    def apply_network_optimizations(self):
        """Apply network optimizations and fallbacks"""
        try:
            # Set socket options for better reliability
            socket.setdefaulttimeout(30)
            
            # Configure requests with better defaults
            requests.adapters.DEFAULT_RETRIES = 3
            
            logger.info("Network optimizations applied")
            
        except Exception as e:
            logger.warning(f"Could not apply all network optimizations: {e}")

# Global instance
network_config = NetworkConfig()

def get_network_config() -> NetworkConfig:
    """Get the global network configuration instance"""
    return network_config

def run_network_diagnostics() -> Dict[str, Any]:
    """Run comprehensive network diagnostics"""
    return network_config.get_network_diagnostics()

def create_resilient_session() -> requests.Session:
    """Create a requests session with resilient configuration"""
    return network_config.get_resilient_session()
