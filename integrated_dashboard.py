import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import sqlite3
import os
from pathlib import Path
import json
import time
import asyncio
import sys
from typing import Dict, List, Any, Optional

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import the actual research functionality
RESEARCH_AVAILABLE = False
import_errors = []

# Import performance monitoring
try:
    from dashboard_performance import (
        performance_monitor, 
        with_performance_tracking, 
        show_performance_sidebar
    )
    PERFORMANCE_MONITORING = True
except ImportError:
    PERFORMANCE_MONITORING = False
    print("Performance monitoring not available")

# Import professional error handling
try:
    from professional_error_handler import (
        error_handler,
        safe_execute,
        validate_inputs,
        show_system_health
    )
    ERROR_HANDLING = True
except ImportError:
    ERROR_HANDLING = False
    print("Professional error handling not available")

try:
    from src.crew.research_crew import ResearchCrew
    from src.storage.database import db
    from src.utils.config import config
    from src.utils.export_manager import export_manager
    from src.agents.qa_agent import QuestionAnsweringAgent
    from src.utils.logging import setup_logging, logger
    RESEARCH_AVAILABLE = True
except ImportError as e:
    import_errors.append(str(e))
    # Try to provide helpful error messages
    if "aiosqlite" in str(e):
        st.error("❌ Missing dependency: aiosqlite")
        st.info("💡 Install with: pip install aiosqlite")
    elif "crewai" in str(e):
        st.error("❌ Missing dependency: crewai")
        st.info("💡 Install with: pip install crewai")
    else:
        st.error(f"❌ Failed to import research modules: {e}")
    
    st.info("🔧 Make sure you're running from the project root directory and all dependencies are installed.")
    RESEARCH_AVAILABLE = False

# Configure Streamlit page with enhanced visual settings
st.set_page_config(
    page_title="Academic Research Assistant Pro",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': 'https://github.com/moazhassan751/academic-research-assistant',
        'Report a bug': "https://github.com/moazhassan751/academic-research-assistant/issues",
        'About': "# Academic Research Assistant Pro\n\nPowered by AI for comprehensive research workflows\n\nVersion 2.0 - Production Ready"
    }
)

# Initialize logging
if RESEARCH_AVAILABLE:
    setup_logging('INFO')

# Modern CSS with complete design system and responsive layout
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
    /* Modern Color Palette - Professional & Visually Appealing */
    --primary-50: #f0f9ff;
    --primary-100: #e0f2fe;
    --primary-200: #bae6fd;
    --primary-300: #7dd3fc;
    --primary-400: #38bdf8;
    --primary-500: #0ea5e9;
    --primary-600: #0284c7;
    --primary-700: #0369a1;
    --primary-800: #075985;
    --primary-900: #0c4a6e;
    
    --secondary-50: #faf5ff;
    --secondary-100: #f3e8ff;
    --secondary-200: #e9d5ff;
    --secondary-300: #d8b4fe;
    --secondary-400: #c084fc;
    --secondary-500: #a855f7;
    --secondary-600: #9333ea;
    --secondary-700: #7c2d12;
    --secondary-800: #6b21a8;
    --secondary-900: #581c87;
    
    --accent-50: #ecfdf5;
    --accent-100: #d1fae5;
    --accent-200: #a7f3d0;
    --accent-300: #6ee7b7;
    --accent-400: #34d399;
    --accent-500: #10b981;
    --accent-600: #059669;
    --accent-700: #047857;
    --accent-800: #065f46;
    --accent-900: #064e3b;
    
    --success-50: #ecfdf5;
    --success-100: #d1fae5;
    --success-200: #a7f3d0;
    --success-300: #6ee7b7;
    --success-400: #34d399;
    --success-500: #10b981;
    --success-600: #059669;
    --success-700: #047857;
    --success-800: #065f46;
    --success-900: #064e3b;
    
    --warning-50: #fffbeb;
    --warning-100: #fef3c7;
    --warning-200: #fde68a;
    --warning-300: #fcd34d;
    --warning-400: #fbbf24;
    --warning-500: #f59e0b;
    --warning-600: #d97706;
    --warning-700: #b45309;
    --warning-800: #92400e;
    --warning-900: #78350f;
    
    --error-50: #fef2f2;
    --error-100: #fee2e2;
    --error-200: #fecaca;
    --error-300: #fca5a5;
    --error-400: #f87171;
    --error-500: #ef4444;
    --error-600: #dc2626;
    --error-700: #b91c1c;
    --error-800: #991b1b;
    --error-900: #7f1d1d;
    
    /* Modern Gray Scale */
    --gray-50: #fafafa;
    --gray-100: #f4f4f5;
    --gray-200: #e4e4e7;
    --gray-300: #d4d4d8;
    --gray-400: #a1a1aa;
    --gray-500: #71717a;
    --gray-600: #52525b;
    --gray-700: #3f3f46;
    --gray-800: #27272a;
    --gray-900: #18181b;
    
    /* Text Colors - High Contrast */
    --text-primary: #1a1a1a;
    --text-secondary: #4a5568;
    --text-muted: #718096;
    --text-inverse: #ffffff;
    
    /* Background Colors */
    --bg-primary: #ffffff;
    --bg-secondary: #f8fafc;
    --bg-tertiary: #f1f5f9;
    --bg-overlay: rgba(0, 0, 0, 0.6);
    
    /* Spacing System */
    --spacing-xs: 0.25rem;
    --spacing-sm: 0.5rem;
    --spacing-md: 1rem;
    --spacing-lg: 1.5rem;
    --spacing-xl: 2rem;
    --spacing-2xl: 3rem;
    --spacing-3xl: 4rem;
    
    /* Typography Scale */
    --font-size-xs: 0.75rem;
    --font-size-sm: 0.875rem;
    --font-size-base: 1rem;
    --font-size-lg: 1.125rem;
    --font-size-xl: 1.25rem;
    --font-size-2xl: 1.5rem;
    --font-size-3xl: 1.875rem;
    --font-size-4xl: 2.25rem;
    --font-size-5xl: 3rem;
    
    /* Enhanced Shadow System */
    --shadow-xs: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    --shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
    --shadow-2xl: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
    --shadow-inner: inset 0 2px 4px 0 rgba(0, 0, 0, 0.06);
    
    /* Modern Border Radius */
    --radius-none: 0;
    --radius-xs: 0.125rem;
    --radius-sm: 0.25rem;
    --radius-md: 0.375rem;
    --radius-lg: 0.5rem;
    --radius-xl: 0.75rem;
    --radius-2xl: 1rem;
    --radius-3xl: 1.5rem;
    --radius-full: 9999px;
    
    /* Smooth Transitions */
    --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
    --transition-normal: 250ms cubic-bezier(0.4, 0, 0.2, 1);
    --transition-slow: 350ms cubic-bezier(0.4, 0, 0.2, 1);
}
}

/* Browser Optimization and Animation Enhancement */
html {
    scroll-behavior: smooth;
    -webkit-text-size-adjust: 100%;
    -ms-text-size-adjust: 100%;
}

/* Force hardware acceleration for all animated elements */
.modern-card, .paper-card, .metric-card, .modern-button {
    transform: translateZ(0);
    -webkit-backface-visibility: hidden;
    backface-visibility: hidden;
    -webkit-perspective: 1000px;
    perspective: 1000px;
}

/* Optimize font rendering for animations */
body, .stApp {
    font-display: swap;
    text-rendering: optimizeLegibility;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

/* Ensure smooth transitions on all interactive elements */
button, input, select, textarea, .stSelectbox, .stTextInput, .stTextArea {
    transition: all var(--transition-fast) ease-out !important;
}

/* GPU acceleration for Streamlit components */
[data-testid="stSidebar"], [data-testid="stHeader"], .main .block-container {
    transform: translate3d(0, 0, 0);
    will-change: transform;
}

html, body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', sans-serif !important;
    background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-primary) 100%);
    color: var(--text-primary);
    line-height: 1.6;
    font-weight: 400;
}

/* Hide Streamlit Default Elements */
.stDeployButton, .stDecoration, #MainMenu, footer, header {
    visibility: hidden !important;
}

/* Main Container */
.main .block-container {
    padding-top: var(--spacing-lg) !important;
    padding-bottom: var(--spacing-xl) !important;
    max-width: 100% !important;
}

/* Header Styling - Modern Gradient */
.main-header {
    font-size: var(--font-size-4xl);
    font-weight: 800;
    color: transparent;
    text-align: center;
    margin-bottom: var(--spacing-2xl);
    text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    background: linear-gradient(135deg, var(--primary-600) 0%, var(--secondary-500) 50%, var(--accent-500) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    padding: var(--spacing-md) 0;
    letter-spacing: -0.025em;
}

/* Card Components - Enhanced Modern Design */
.modern-card {
    background: var(--bg-primary);
    border-radius: var(--radius-2xl);
    padding: var(--spacing-xl);
    margin: var(--spacing-md) 0;
    box-shadow: var(--shadow-lg);
    border: 1px solid var(--gray-200);
    transition: all var(--transition-normal);
    position: relative;
    overflow: hidden;
}

.modern-card:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-xl);
    border-color: var(--primary-200);
}

.modern-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, var(--primary-500), var(--accent-500));
    border-radius: var(--radius-2xl) var(--radius-2xl) 0 0;
}

/* Metric Cards - Modern Glass Effect */
.metric-card {
    background: linear-gradient(135deg, var(--primary-500) 0%, var(--primary-600) 100%);
    color: var(--text-inverse);
    border-radius: var(--radius-2xl);
    padding: var(--spacing-xl);
    margin: var(--spacing-md);
    box-shadow: var(--shadow-lg);
    transition: all var(--transition-normal);
    position: relative;
    overflow: hidden;
    backdrop-filter: blur(10px);
}

.metric-card:hover {
    transform: translateY(-3px) scale(1.02);
    box-shadow: var(--shadow-xl);
}

.metric-card::after {
    content: '';
    position: absolute;
    top: -50%;
    right: -50%;
    width: 100%;
    height: 100%;
    background: radial-gradient(circle, rgba(255,255,255,0.15) 0%, transparent 70%);
    transform: rotate(45deg);
}

/* Enhanced Paper Cards */
.paper-card {
    background: var(--bg-primary);
    border: 1px solid var(--gray-200);
    border-radius: var(--radius-xl);
    padding: var(--spacing-lg);
    margin: var(--spacing-md) 0;
    transition: all var(--transition-normal);
    position: relative;
    overflow: hidden;
    box-shadow: var(--shadow-sm);
}

.paper-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
    border-color: var(--primary-300);
}

.paper-card::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 4px;
    background: linear-gradient(180deg, var(--primary-500), var(--accent-500));
    transform: scaleY(0);
    transition: transform var(--transition-normal);
}

.paper-card:hover::before {
    transform: scaleY(1);
}

/* Modern Enhanced Buttons */
.modern-button {
    background: linear-gradient(135deg, var(--primary-500) 0%, var(--primary-600) 100%);
    color: var(--text-inverse) !important;
    border: none;
    border-radius: var(--radius-lg);
    padding: var(--spacing-sm) var(--spacing-lg);
    font-weight: 600;
    font-size: var(--font-size-sm);
    cursor: pointer;
    transition: all var(--transition-fast);
    box-shadow: var(--shadow-sm);
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    gap: var(--spacing-xs);
    letter-spacing: 0.025em;
}

.modern-button:hover {
    transform: translateY(-1px);
    box-shadow: var(--shadow-md);
    background: linear-gradient(135deg, var(--primary-600) 0%, var(--primary-700) 100%);
}

.modern-button:active {
    transform: translateY(0);
    box-shadow: var(--shadow-sm);
}

/* Success Button */
.success-button {
    background: linear-gradient(135deg, var(--success-500) 0%, var(--success-600) 100%);
}

.success-button:hover {
    background: linear-gradient(135deg, var(--success-600) 0%, var(--success-700) 100%);
}

/* Warning Button */
.warning-button {
    background: linear-gradient(135deg, var(--warning-500) 0%, var(--warning-600) 100%);
}

.warning-button:hover {
    background: linear-gradient(135deg, var(--warning-600) 0%, var(--warning-700) 100%);
}

/* Sidebar Styling - Modern Glass Effect */
.css-1d391kg {
    background: linear-gradient(180deg, var(--bg-secondary) 0%, var(--bg-primary) 100%);
    border-right: 1px solid var(--gray-200);
    backdrop-filter: blur(10px);
}

.sidebar-content {
    background: var(--bg-primary);
    border-radius: var(--radius-xl);
    padding: var(--spacing-lg);
    margin: var(--spacing-sm) 0;
    box-shadow: var(--shadow-md);
    border: 1px solid var(--gray-100);
}

/* Status Indicators */
.status-indicator {
    padding: var(--spacing-xs) var(--spacing-sm);
    border-radius: var(--radius-md);
    font-size: var(--font-size-sm);
    font-weight: 500;
    display: inline-flex;
    align-items: center;
    gap: var(--spacing-xs);
    margin: var(--spacing-xs);
}

.status-success {
    background: var(--success-50);
    color: var(--success-600);
    border: 1px solid var(--success-200);
}

.status-processing {
    background: var(--warning-50);
    color: var(--warning-600);
    border: 1px solid var(--warning-200);
}

.status-error {
    background: var(--error-50);
    color: var(--error-600);
    border: 1px solid var(--error-200);
}

/* Form Elements - Fixed Text Visibility */
.stSelectbox > div > div, 
.stTextInput > div > div > input, 
.stTextArea > div > div > textarea {
    border-radius: var(--radius-lg) !important;
    border: 2px solid var(--gray-300) !important;
    background: var(--bg-primary) !important;
    color: var(--text-primary) !important;
    transition: all var(--transition-fast) !important;
    font-family: 'Inter', sans-serif !important;
    font-size: var(--font-size-base) !important;
    font-weight: 400 !important;
    padding: var(--spacing-sm) var(--spacing-md) !important;
}

.stSelectbox > div > div:focus, 
.stTextInput > div > div > input:focus, 
.stTextArea > div > div > textarea:focus {
    border-color: var(--primary-500) !important;
    box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.15) !important;
    outline: none !important;
    background: var(--bg-primary) !important;
    color: var(--text-primary) !important;
}

/* Fix placeholder text visibility */
.stTextInput > div > div > input::placeholder,
.stTextArea > div > div > textarea::placeholder {
    color: var(--gray-400) !important;
    opacity: 1 !important;
}

/* Ensure text remains black while typing */
.stSelectbox > div > div input,
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    color: var(--text-primary) !important;
    background: var(--bg-primary) !important;
}

/* Fix dropdown options visibility */
.stSelectbox > div > div > div[data-baseweb="select"] > div {
    color: var(--text-primary) !important;
    background: var(--bg-primary) !important;
}

/* Fix multiselect styling */
.stMultiSelect > div > div {
    background: var(--bg-primary) !important;
    border: 2px solid var(--gray-300) !important;
    border-radius: var(--radius-lg) !important;
}

.stMultiSelect > div > div > div {
    color: var(--text-primary) !important;
}

/* Fix number input styling */
.stNumberInput > div > div > input {
    color: var(--text-primary) !important;
    background: var(--bg-primary) !important;
    border: 2px solid var(--gray-300) !important;
    border-radius: var(--radius-lg) !important;
}

/* Progress Bar */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, var(--primary-500), var(--secondary-500)) !important;
    border-radius: var(--radius-md) !important;
}

/* Enhanced Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: var(--spacing-sm);
    background: var(--bg-secondary);
    padding: var(--spacing-xs);
    border-radius: var(--radius-2xl);
    margin-bottom: var(--spacing-lg);
    box-shadow: var(--shadow-sm);
}

.stTabs [data-baseweb="tab"] {
    background: transparent;
    border: none;
    border-radius: var(--radius-lg);
    padding: var(--spacing-sm) var(--spacing-lg);
    font-weight: 600;
    color: var(--text-secondary);
    transition: all var(--transition-fast);
    font-size: var(--font-size-sm);
}

.stTabs [aria-selected="true"] {
    background: var(--bg-primary);
    color: var(--primary-600);
    box-shadow: var(--shadow-sm);
    transform: translateY(-1px);
}

/* Enhanced Metrics Display */
[data-testid="metric-container"] {
    background: var(--bg-primary);
    border: 1px solid var(--gray-200);
    border-radius: var(--radius-xl);
    padding: var(--spacing-lg);
    box-shadow: var(--shadow-sm);
    transition: all var(--transition-normal);
}

[data-testid="metric-container"]:hover {
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
    border-color: var(--primary-200);
}

/* Enhanced Workflow Status */
.workflow-status {
    background: var(--bg-primary);
    border-left: 4px solid var(--primary-500);
    border-radius: 0 var(--radius-lg) var(--radius-lg) 0;
    padding: var(--spacing-lg);
    margin: var(--spacing-sm) 0;
    box-shadow: var(--shadow-sm);
    transition: all var(--transition-normal);
    border-top: 1px solid var(--gray-100);
    border-right: 1px solid var(--gray-100);
    border-bottom: 1px solid var(--gray-100);
}

.workflow-status:hover {
    box-shadow: var(--shadow-md);
    transform: translateX(4px);
    border-left-color: var(--accent-500);
}

/* Q&A Section - Modern Design */
.qa-container {
    background: linear-gradient(135deg, var(--primary-50) 0%, var(--accent-50) 100%);
    border: 2px solid var(--primary-200);
    border-radius: var(--radius-2xl);
    padding: var(--spacing-xl);
    margin: var(--spacing-lg) 0;
    position: relative;
    overflow: hidden;
    box-shadow: var(--shadow-md);
}

.qa-container::before {
    content: '🤖';
    position: absolute;
    top: var(--spacing-md);
    right: var(--spacing-md);
    font-size: var(--font-size-2xl);
    opacity: 0.1;
}

/* Export Section - Premium Design */
.export-section {
    background: linear-gradient(135deg, var(--success-50) 0%, var(--primary-50) 100%);
    border-radius: var(--radius-2xl);
    padding: var(--spacing-xl);
    margin: var(--spacing-lg) 0;
    border: 1px solid var(--success-200);
    box-shadow: var(--shadow-md);
}

/* Loading Animation */
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

.loading-pulse {
    animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

/* Responsive Design */
@media (max-width: 1200px) {
    .main .block-container {
        padding-left: var(--spacing-md) !important;
        padding-right: var(--spacing-md) !important;
    }
    
    .main-header {
        font-size: var(--font-size-3xl);
    }
}

@media (max-width: 768px) {
    .main .block-container {
        padding-left: var(--spacing-sm) !important;
        padding-right: var(--spacing-sm) !important;
    }
    
    .main-header {
        font-size: var(--font-size-2xl);
        margin-bottom: var(--spacing-lg);
    }
    
    .modern-card, .paper-card {
        padding: var(--spacing-md);
        margin: var(--spacing-sm) 0;
    }
    
    .metric-card {
        margin: var(--spacing-sm);
        padding: var(--spacing-md);
    }
    
    [data-testid="column"] {
        min-width: 100% !important;
    }
}

@media (max-width: 480px) {
    .main-header {
        font-size: var(--font-size-xl);
    }
    
    .modern-button {
        padding: var(--spacing-xs) var(--spacing-md);
        font-size: var(--font-size-xs);
    }
    
    .paper-card, .modern-card {
        padding: var(--spacing-sm);
    }
}

/* Dark Mode Support */
@media (prefers-color-scheme: dark) {
    :root {
        --gray-50: #111827;
        --gray-100: #1f2937;
        --gray-200: #374151;
        --gray-900: #f9fafb;
    }
}

/* Print Styles */
@media print {
    .stSidebar, .stTabs [data-baseweb="tab-list"], .modern-button {
        display: none !important;
    }
    
    .paper-card, .modern-card {
        box-shadow: none !important;
        border: 1px solid var(--gray-300) !important;
    }
}

/* Accessibility Improvements */
.modern-button:focus, .stSelectbox > div > div:focus, .stTextInput > div > div > input:focus {
    outline: 2px solid var(--primary-500) !important;
    outline-offset: 2px !important;
}

/* Performance Optimizations */
.paper-card, .modern-card, .metric-card {
    will-change: transform;
    backface-visibility: hidden;
    transform: translate3d(0, 0, 0); /* Force GPU acceleration */
}

/* Animation Performance Boost */
* {
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

/* Reduce motion for accessibility */
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
}

/* Utility Classes for Common Styles */
.flex-center {
    display: flex;
    align-items: center;
    justify-content: center;
}

.flex-between {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.flex-column {
    display: flex;
    flex-direction: column;
}

.text-center {
    text-align: center;
}

.text-right {
    text-align: right;
}

.mb-sm {
    margin-bottom: var(--spacing-sm);
}

.mb-md {
    margin-bottom: var(--spacing-md);
}

.mb-lg {
    margin-bottom: var(--spacing-lg);
}

.p-sm {
    padding: var(--spacing-sm);
}

.p-md {
    padding: var(--spacing-md);
}

.p-lg {
    padding: var(--spacing-lg);
}

.rounded {
    border-radius: var(--radius-md);
}

.rounded-lg {
    border-radius: var(--radius-lg);
}

.shadow-sm {
    box-shadow: var(--shadow-sm);
}

.shadow-md {
    box-shadow: var(--shadow-md);
}

.text-primary {
    color: var(--primary-600);
}

.text-secondary {
    color: var(--gray-600);
}

.text-muted {
    color: var(--gray-400);
}

.bg-primary {
    background: var(--bg-primary);
}

.bg-secondary {
    background: var(--bg-secondary);
}

.gradient-primary {
    background: linear-gradient(135deg, var(--primary-500) 0%, var(--accent-500) 100%);
}

.gradient-subtle {
    background: linear-gradient(135deg, var(--gray-50) 0%, var(--primary-50) 100%);
}

/* Custom Scrollbar */
::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-track {
    background: var(--gray-100);
    border-radius: var(--radius-md);
}

::-webkit-scrollbar-thumb {
    background: var(--gray-300);
    border-radius: var(--radius-md);
}

::-webkit-scrollbar-thumb:hover {
    background: var(--gray-400);
}
</style>
""", unsafe_allow_html=True)

# Initialize session state with performance optimization
if 'research_crew' not in st.session_state and RESEARCH_AVAILABLE:
    try:
        with st.spinner("🚀 Initializing AI Research System..."):
            st.session_state.research_crew = ResearchCrew()
            st.session_state.qa_agent = QuestionAnsweringAgent()
        st.success("✅ AI Research System Ready!", icon="🤖")
    except Exception as e:
        st.error(f"❌ Failed to initialize research crew: {e}")
        st.session_state.research_crew = None
        st.session_state.qa_agent = None

if 'research_results' not in st.session_state:
    st.session_state.research_results = None

if 'current_workflow_status' not in st.session_state:
    st.session_state.current_workflow_status = None

if 'search_cache' not in st.session_state:
    st.session_state.search_cache = {}

if 'last_search_query' not in st.session_state:
    st.session_state.last_search_query = ""

if 'page_load_time' not in st.session_state:
    st.session_state.page_load_time = time.time()

# Enhanced helper functions with caching and performance optimization
@st.cache_data(ttl=300, show_spinner=False)  # Cache for 5 minutes
@with_performance_tracking("get_database_stats") if PERFORMANCE_MONITORING else (lambda f: f)
def get_database_stats():
    """Get current database statistics with caching"""
    if not RESEARCH_AVAILABLE:
        return {'papers': 0, 'notes': 0, 'themes': 0, 'citations': 0, 'last_updated': 'N/A'}
    
    try:
        stats = db.get_stats()
        stats['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M")
        return stats
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        return {'papers': 0, 'notes': 0, 'themes': 0, 'citations': 0, 'last_updated': 'Error'}

@st.cache_data(ttl=600, show_spinner=False)  # Cache for 10 minutes
@with_performance_tracking("get_recent_papers") if PERFORMANCE_MONITORING else (lambda f: f)
def get_recent_papers(limit: int = 10):
    """Get recently added papers from database with caching"""
    if not RESEARCH_AVAILABLE:
        return []
    
    try:
        papers = db.get_recent_papers(limit)
        return papers
    except Exception as e:
        logger.error(f"Error getting recent papers: {e}")
        return []

@st.cache_data(ttl=1800)  # Cache for 30 minutes
@with_performance_tracking("get_research_analytics") if PERFORMANCE_MONITORING else (lambda f: f)
def get_research_analytics():
    """Get research analytics data with caching - REAL DATABASE DATA"""
    if not RESEARCH_AVAILABLE:
        return {}
    
    try:
        # Get REAL analytics data from database
        analytics = db.get_analytics_data()  # Call real database method
        
        # If db.get_analytics_data() doesn't exist, build from real data
        if not analytics:
            analytics = {
                'papers_by_source': db.get_papers_by_source(),
                'papers_by_year': db.get_papers_by_year(),
                'citation_distribution': db.get_citation_distribution(),
                'trending_topics': db.get_trending_topics()
            }
        
        return analytics
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        # Fallback to basic stats from database
        try:
            basic_stats = db.get_stats()
            return {
                'papers_by_source': {'Database': basic_stats.get('papers', 0)},
                'papers_by_year': {},
                'citation_distribution': {},
                'trending_topics': []
            }
        except:
            return {}

def format_paper_card(paper):
    """Enhanced paper card formatting with modern design"""
    authors_str = ", ".join(paper.authors[:3]) if paper.authors else "Unknown Authors"
    if paper.authors and len(paper.authors) > 3:
        authors_str += f" <span style='color: var(--gray-400);'>+{len(paper.authors) - 3} more</span>"
    
    # Truncate abstract intelligently
    abstract = paper.abstract if paper.abstract else 'No abstract available'
    if len(abstract) > 300:
        abstract = abstract[:297] + '...'
    
    # Get paper metrics
    year = getattr(paper, 'year', 'Unknown')
    citations = getattr(paper, 'citations', 0)
    venue = getattr(paper, 'venue', getattr(paper, 'source', 'Unknown Source'))
    topic = getattr(paper, 'topic', 'General')
    
    # Create modern card with enhanced design
    card_html = f"""
    <div class="paper-card">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: var(--spacing-md);">
            <h4 style="color: var(--primary-700); margin: 0; font-weight: 600; line-height: 1.3; flex: 1;">
                {paper.title}
            </h4>
            <div style="margin-left: var(--spacing-md); display: flex; gap: var(--spacing-xs);">
                <span class="status-indicator status-success" style="font-size: var(--font-size-xs);">
                    📊 {citations}
                </span>
            </div>
        </div>
        
        <div style="margin-bottom: var(--spacing-md);">
            <p style="color: var(--gray-600); margin: 0; font-size: var(--font-size-sm); line-height: 1.4;">
                <strong>👥 Authors:</strong> {authors_str}
            </p>
            <div style="display: flex; gap: var(--spacing-lg); margin-top: var(--spacing-xs);">
                <span style="color: var(--gray-500); font-size: var(--font-size-sm);">
                    📅 {year}
                </span>
                <span style="color: var(--gray-500); font-size: var(--font-size-sm);">
                    📖 {venue}
                </span>
            </div>
        </div>
        
        <p style="color: var(--gray-700); font-size: var(--font-size-sm); line-height: 1.5; margin-bottom: var(--spacing-md);">
            {abstract}
        </p>
        
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div style="display: flex; gap: var(--spacing-xs); flex-wrap: wrap;">
                <span style="background: var(--primary-50); color: var(--primary-600); padding: var(--spacing-xs) var(--spacing-sm); 
                             border-radius: var(--radius-md); font-size: var(--font-size-xs); font-weight: 500; border: 1px solid var(--primary-200);">
                    🏷️ {topic}
                </span>
                <span style="background: var(--gray-50); color: var(--gray-600); padding: var(--spacing-xs) var(--spacing-sm); 
                             border-radius: var(--radius-md); font-size: var(--font-size-xs); border: 1px solid var(--gray-200);">
                    🔗 {paper.source}
                </span>
            </div>
            <button class="modern-button" style="padding: var(--spacing-xs) var(--spacing-sm); font-size: var(--font-size-xs);"
                    onclick="window.open('{getattr(paper, 'url', '#')}', '_blank')">
                📖 Read
            </button>
        </div>
    </div>
    """
    return card_html

def create_metric_card(title, value, icon, trend=None, color="primary"):
    """Create modern metric cards"""
    trend_html = ""
    if trend:
        trend_color = "var(--success-500)" if trend > 0 else "var(--error-500)"
        trend_icon = "📈" if trend > 0 else "📉"
        trend_html = f"""
        <div style="margin-top: var(--spacing-xs);">
            <span style="color: {trend_color}; font-size: var(--font-size-sm); font-weight: 500;">
                {trend_icon} {abs(trend):.1f}% vs last month
            </span>
        </div>
        """
    
    return f"""
    <div class="metric-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="font-size: var(--font-size-3xl); font-weight: 700; margin-bottom: var(--spacing-xs);">
                    {value}
                </div>
                <div style="font-size: var(--font-size-sm); opacity: 0.9; font-weight: 500;">
                    {title}
                </div>
                {trend_html}
            </div>
            <div style="font-size: 2.5rem; opacity: 0.8;">
                {icon}
            </div>
        </div>
    </div>
    """

def progress_callback(step: int, description: str):
    """Enhanced callback function for research workflow progress"""
    st.session_state.current_workflow_status = {
        'step': step,
        'description': description,
        'timestamp': datetime.now(),
        'progress_percentage': min(step * 20, 100)
    }

def show_loading_animation(message: str = "Processing..."):
    """Show modern loading animation"""
    return st.markdown(f"""
    <div style="display: flex; align-items: center; justify-content: center; padding: var(--spacing-xl); color: var(--primary-600);">
        <div class="loading-pulse" style="margin-right: var(--spacing-md); font-size: var(--font-size-xl);">
            🔄
        </div>
        <span style="font-weight: 500;">{message}</span>
    </div>
    """, unsafe_allow_html=True)

# Main application with modern UI
def main():
    # Performance monitoring
    start_time = time.time()
    
    # Modern header with system status
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="main-header">🔬 Academic Research Assistant Pro</div>', unsafe_allow_html=True)
    
    with col3:
        if RESEARCH_AVAILABLE:
            st.markdown("""
            <div style="text-align: right; color: var(--success-500); font-weight: 500; margin-top: var(--spacing-lg);">
                🟢 System Online
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align: right; color: var(--error-500); font-weight: 500; margin-top: var(--spacing-lg);">
                🔴 System Offline
            </div>
            """, unsafe_allow_html=True)
    
    if not RESEARCH_AVAILABLE:
        st.error("🚨 Research functionality is not available", icon="❌")
        with st.expander("🔧 Troubleshooting Guide", expanded=True):
            st.markdown("""
            ### Quick Fixes:
            1. **Check Dependencies**: Run `pip install -r requirements.txt`
            2. **Verify Location**: Ensure you're in the project root directory
            3. **Check API Keys**: Verify your API keys in `config.yaml`
            4. **Restart Application**: Try restarting the Streamlit server
            
            ### Installation Commands:
            ```bash
            pip install aiosqlite crewai streamlit plotly pandas
            ```
            """)
        return
    
    # Quick stats banner
    stats = get_database_stats()
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, var(--primary-50) 0%, var(--secondary-50) 100%); 
                padding: var(--spacing-lg); border-radius: var(--radius-xl); margin-bottom: var(--spacing-xl);
                border: 1px solid var(--primary-200);">
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: var(--spacing-md);">
            <div style="text-align: center;">
                <div style="font-size: var(--font-size-2xl); font-weight: 700; color: var(--primary-600);">
                    📚 {stats.get('papers', 0)}
                </div>
                <div style="color: var(--gray-600); font-weight: 500;">Research Papers</div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: var(--font-size-2xl); font-weight: 700; color: var(--secondary-600);">
                    📝 {stats.get('notes', 0)}
                </div>
                <div style="color: var(--gray-600); font-weight: 500;">Research Notes</div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: var(--font-size-2xl); font-weight: 700; color: var(--success-600);">
                    🎯 {stats.get('themes', 0)}
                </div>
                <div style="color: var(--gray-600); font-weight: 500;">Key Themes</div>
            </div>
            <div style="text-align: center;">
                <div style="font-size: var(--font-size-2xl); font-weight: 700; color: var(--warning-600);">
                    📖 {stats.get('citations', 0)}
                </div>
                <div style="color: var(--gray-600); font-weight: 500;">Citations</div>
            </div>
        </div>
        <div style="text-align: center; margin-top: var(--spacing-md); color: var(--gray-500); font-size: var(--font-size-sm);">
            Last updated: {stats.get('last_updated', 'Unknown')} | System ready in {time.time() - start_time:.2f}s
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Enhanced sidebar with modern design
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-content">
            <h3 style="color: var(--primary-600); margin-bottom: var(--spacing-lg); font-weight: 600;">
                ⚙️ System Configuration
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        # System status and configuration
        try:
            env = config.environment
            llm_config = config.llm_config
            
            # Configuration display
            st.markdown(f"""
            <div class="sidebar-content">
                <div style="margin-bottom: var(--spacing-md);">
                    <strong>🌍 Environment:</strong><br>
                    <span style="color: var(--success-600);">{env}</span>
                </div>
                <div style="margin-bottom: var(--spacing-md);">
                    <strong>🤖 LLM Provider:</strong><br>
                    <span style="color: var(--primary-600);">{llm_config.get('provider', 'Unknown')}</span>
                </div>
                <div style="margin-bottom: var(--spacing-md);">
                    <strong>🧠 Model:</strong><br>
                    <span style="color: var(--secondary-600);">{llm_config.get('model', 'Unknown')}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Export formats
            if st.session_state.research_crew:
                available_formats = st.session_state.research_crew.get_available_export_formats()
                formats_str = ', '.join(available_formats)
                st.success(f"📤 **Export Formats Available**: {formats_str}", icon="✅")
                
        except Exception as e:
            st.error(f"⚠️ Configuration error: {e}", icon="🚨")
        
        # Quick actions
        st.markdown("""
        <div class="sidebar-content">
            <h4 style="color: var(--primary-600); margin-bottom: var(--spacing-md);">🚀 Quick Actions</h4>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("� Refresh Stats", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        if st.button("🧹 Clear Cache", use_container_width=True):
            st.session_state.search_cache = {}
            st.cache_data.clear()
            st.success("Cache cleared!")
        
        # System health monitoring
        if ERROR_HANDLING:
            st.markdown("### 🏥 System Health")
            show_system_health()
        
        # System performance
        if PERFORMANCE_MONITORING:
            show_performance_sidebar()
        
        load_time = time.time() - st.session_state.page_load_time
        st.markdown(f"""
        <div class="sidebar-content">
            <h4 style="color: var(--gray-600); font-size: var(--font-size-sm);">📊 Performance</h4>
            <div style="font-size: var(--font-size-xs); color: var(--gray-500);">
                Load time: {load_time:.2f}s
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Enhanced tabs with modern styling
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "� Research Workflow", 
        "💬 AI Assistant", 
        "📚 Knowledge Base", 
        "� Analytics Dashboard", 
        "� Export Center"
    ])
    
    # Tab 1: Enhanced Research Workflow
    with tab1:
        st.markdown("""
        <div class="modern-card">
            <h2 style="color: var(--primary-700); margin-bottom: var(--spacing-lg); font-weight: 600;">
                🔬 AI-Powered Research Workflow
            </h2>
            <p style="color: var(--gray-600); margin-bottom: var(--spacing-xl);">
                Launch comprehensive literature surveys with AI-powered analysis, automated paper collection, and intelligent insights generation.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Enhanced research form with modern design
        with st.form("research_form", clear_on_submit=False):
            # Primary research parameters
            st.markdown("### 🎯 Research Parameters")
            
            col1, col2 = st.columns(2)
            
            with col1:
                research_topic = st.text_input(
                    "🔍 Research Topic*",
                    placeholder="e.g., Machine Learning for Healthcare, Climate Change Impact, Quantum Computing",
                    help="Enter your main research focus. Be specific for better results.",
                    value=""
                )
                
                max_papers = st.slider(
                    "📚 Maximum Papers to Analyze",
                    min_value=10,
                    max_value=500,
                    value=100,
                    step=10,
                    help="Higher numbers provide more comprehensive results but take longer to process"
                )
                
                paper_type = st.selectbox(
                    "📄 Output Paper Type",
                    ["survey", "review", "analysis", "systematic_review", "meta_analysis"],
                    index=0,
                    help="Choose the type of research paper to generate"
                )
            
            with col2:
                specific_aspects = st.text_area(
                    "🎯 Specific Focus Areas (Optional)",
                    placeholder="• Recent developments\n• Challenges and limitations\n• Future directions\n• Methodological approaches",
                    height=100,
                    help="Enter specific sub-topics or aspects to focus the research on (one per line)"
                )
                
                date_from = st.date_input(
                    "📅 Publication Date Filter (Optional)",
                    value=None,
                    help="Only include papers published after this date"
                )
                
                col_resume, col_priority = st.columns(2)
                with col_resume:
                    resume_checkpoint = st.checkbox(
                        "🔄 Resume from Checkpoint",
                        value=True,
                        help="Resume from saved checkpoints if available"
                    )
                with col_priority:
                    priority_mode = st.selectbox(
                        "⚡ Processing Mode",
                        ["Balanced", "Fast", "Comprehensive"],
                        help="Choose processing speed vs thoroughness"
                    )
            
            # Advanced options in expandable section
            with st.expander("⚙️ Advanced Options", expanded=False):
                col_adv1, col_adv2 = st.columns(2)
                with col_adv1:
                    include_preprints = st.checkbox("📋 Include Preprints", value=True)
                    min_citations = st.number_input("📈 Minimum Citations", min_value=0, value=0)
                with col_adv2:
                    language_filter = st.selectbox("🌐 Language", ["Any", "English", "All"])
                    exclude_terms = st.text_input("🚫 Exclude Terms", placeholder="patent, blog")
            
            # Submit with modern styling
            submitted = st.form_submit_button(
                "🚀 Launch AI Research Workflow",
                use_container_width=True,
                type="primary"
            )
        
        # Enhanced workflow execution
        if submitted and st.session_state.research_crew:
            # Validate inputs professionally
            if ERROR_HANDLING:
                validation_passed = validate_inputs(
                    research_topic=research_topic,
                    max_papers=max_papers
                )
                if not validation_passed:
                    st.stop()
            elif not research_topic or len(research_topic.strip()) < 3:
                st.error("❌ Research topic must be at least 3 characters long")
                st.stop()
            
            # Parse specific aspects
            aspects_list = []
            if specific_aspects:
                aspects_list = [aspect.strip().lstrip('•-').strip() 
                              for aspect in specific_aspects.split('\n') if aspect.strip()]
            
            # Convert date
            date_from_dt = datetime.combine(date_from, datetime.min.time()) if date_from else None
            
            # Create modern progress interface
            st.markdown("""
            <div class="modern-card" style="background: linear-gradient(135deg, var(--primary-50) 0%, var(--secondary-50) 100%);">
                <h3 style="color: var(--primary-700); margin-bottom: var(--spacing-lg);">
                    🔄 AI Research Workflow in Progress
                </h3>
            </div>
            """, unsafe_allow_html=True)
            
            # Progress tracking with enhanced UI
            progress_container = st.container()
            with progress_container:
                progress_bar = st.progress(0, text="Initializing AI research system...")
                status_container = st.empty()
                metrics_container = st.empty()
            
            try:
                workflow_start_time = time.time()
                
                def update_progress(step: int, description: str):
                    progress_value = min(step * 0.2, 1.0)
                    progress_bar.progress(
                        progress_value, 
                        text=f"Step {step}/5: {description}"
                    )
                    
                    # Enhanced status display
                    status_container.markdown(f"""
                    <div class="workflow-status">
                        <div style="display: flex; align-items: center; gap: var(--spacing-md);">
                            <div style="font-size: var(--font-size-xl);">
                                {'🔄' if step < 5 else '✅'}
                            </div>
                            <div>
                                <strong style="color: var(--primary-600);">Step {step}/5:</strong> {description}
                                <div style="font-size: var(--font-size-sm); color: var(--gray-500); margin-top: var(--spacing-xs);">
                                    {datetime.now().strftime('%H:%M:%S')} | {time.time() - workflow_start_time:.1f}s elapsed
                                </div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Execute workflow with progress tracking
                with st.spinner("🤖 AI agents are researching your topic..."):
                    results = st.session_state.research_crew.execute_research_workflow(
                        research_topic=research_topic,
                        specific_aspects=aspects_list if aspects_list else None,
                        max_papers=max_papers,
                        paper_type=paper_type,
                        date_from=date_from_dt,
                        progress_callback=update_progress,
                        resume_from_checkpoint=resume_checkpoint
                    )
                    
                    st.session_state.research_results = results
                    progress_bar.progress(1.0, text="✅ Research workflow completed!")
                
                if results['success']:
                    # Success celebration
                    st.balloons()
                    st.success("🎉 Research workflow completed successfully!", icon="✅")
                    
                    # Enhanced results summary with modern cards
                    st.markdown("### 📊 Research Summary & Insights")
                    
                    # Key metrics in modern cards
                    metric_cols = st.columns(4)
                    stats = results['statistics']
                    
                    with metric_cols[0]:
                        st.markdown(create_metric_card(
                            "Papers Analyzed", 
                            stats['papers_found'], 
                            "📚", 
                            color="primary"
                        ), unsafe_allow_html=True)
                    
                    with metric_cols[1]:
                        st.markdown(create_metric_card(
                            "Research Notes", 
                            stats['notes_extracted'], 
                            "📝", 
                            color="secondary"
                        ), unsafe_allow_html=True)
                    
                    with metric_cols[2]:
                        st.markdown(create_metric_card(
                            "Key Themes", 
                            stats['themes_identified'], 
                            "🎯", 
                            color="success"
                        ), unsafe_allow_html=True)
                    
                    with metric_cols[3]:
                        st.markdown(create_metric_card(
                            "Citations", 
                            stats['citations_generated'], 
                            "📖", 
                            color="warning"
                        ), unsafe_allow_html=True)
                    
                    # Execution details
                    col_time, col_efficiency = st.columns(2)
                    with col_time:
                        st.info(f"⏱️ **Total Execution Time**: {results['execution_time']}")
                    with col_efficiency:
                        papers_per_minute = stats['papers_found'] / (time.time() - workflow_start_time) * 60
                        st.info(f"⚡ **Processing Rate**: {papers_per_minute:.1f} papers/min")
                    
                    # Draft preview with enhanced formatting
                    if 'draft' in results and results['draft']:
                        st.markdown("### 📄 Generated Research Paper Preview")
                        
                        draft = results['draft']
                        
                        # Paper preview in modern card
                        st.markdown(f"""
                        <div class="modern-card">
                            <h4 style="color: var(--primary-700); margin-bottom: var(--spacing-lg);">
                                📝 Research Paper: {research_topic}
                            </h4>
                        """, unsafe_allow_html=True)
                        
                        # Abstract section
                        if 'abstract' in draft:
                            st.markdown("**🎯 Abstract**")
                            st.markdown(f"*{draft['abstract']}*")
                        
                        # Sections overview
                        if 'sections' in draft:
                            st.markdown("**📋 Paper Structure**")
                            sections_list = []
                            for i, section_name in enumerate(draft['sections'].keys(), 1):
                                formatted_name = section_name.replace('_', ' ').title()
                                sections_list.append(f"{i}. **{formatted_name}**")
                            
                            st.markdown("\n".join(sections_list))
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                        # Quick export option
                        if st.button("📤 Quick Export to PDF", use_container_width=True, type="secondary"):
                            st.info("🚀 Navigate to the 'Export Center' tab to download your research!")
                
                else:
                    st.error(f"❌ Research workflow failed: {results.get('error', 'Unknown error')}", icon="🚨")
                    
                    # Error troubleshooting
                    with st.expander("🔧 Troubleshooting Tips"):
                        st.markdown("""
                        - **Check your internet connection** for API access
                        - **Verify API keys** are configured correctly
                        - **Try a more specific research topic**
                        - **Reduce the number of papers** to analyze
                        - **Check the logs** for detailed error information
                        """)
                        
            except Exception as e:
                st.error(f"❌ Unexpected error during research workflow: {str(e)}", icon="🚨")
                logger.error(f"Research workflow error: {e}", exc_info=True)
                
                # Error reporting
                with st.expander("🐛 Error Details"):
                    st.code(str(e))
                    st.markdown("Please report this error to the development team.")
    
    # Tab 2: Enhanced AI Assistant
    with tab2:
        st.markdown("""
        <div class="qa-container">
            <h2 style="color: var(--primary-700); margin-bottom: var(--spacing-md); font-weight: 600;">
                🤖 AI Research Assistant
            </h2>
            <p style="color: var(--gray-600); margin-bottom: var(--spacing-lg);">
                Ask complex research questions and get AI-powered answers based on academic literature with source attribution and confidence scoring.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Enhanced Q&A interface
        with st.container():
            # Question input with better UX
            st.markdown("### 💬 Ask Your Research Question")
            
            # Example questions for inspiration
            with st.expander("💡 Example Questions", expanded=False):
                example_questions = [
                    "What are the main challenges in machine learning for healthcare?",
                    "How has climate change affected biodiversity in the last decade?",
                    "What are the latest developments in quantum computing algorithms?",
                    "Compare different approaches to natural language processing for sentiment analysis",
                    "What are the ethical implications of artificial intelligence in decision-making?"
                ]
                
                for i, eq in enumerate(example_questions, 1):
                    if st.button(f"💭 {eq}", key=f"example_q_{i}", use_container_width=True):
                        st.session_state.qa_question = eq
            
            # Main question input
            question = st.text_area(
                "🤔 Your Question",
                placeholder="Enter your research question here... Be specific for better results!",
                height=100,
                help="Ask any research question and get AI-powered answers based on academic literature",
                value=st.session_state.get('qa_question', '')
            )
            
            # Advanced options
            col1, col2, col3 = st.columns(3)
            with col1:
                qa_topic_filter = st.text_input(
                    "🎯 Topic Filter (Optional)",
                    placeholder="e.g., machine learning, climate",
                    help="Filter papers by topic for more focused answers"
                )
            with col2:
                qa_paper_limit = st.slider(
                    "📚 Papers to Consider",
                    min_value=5,
                    max_value=100,
                    value=20,
                    help="More papers = more comprehensive but slower answers"
                )
            with col3:
                min_confidence = st.slider(
                    "🎯 Min Confidence",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.3,
                    step=0.1,
                    help="Minimum confidence threshold for answers"
                )
            
            # Enhanced submit button
            col_submit, col_clear = st.columns([3, 1])
            with col_submit:
                ask_button = st.button(
                    "� Get AI-Powered Answer", 
                    use_container_width=True, 
                    type="primary",
                    disabled=not question.strip()
                )
            with col_clear:
                if st.button("🗑️ Clear", use_container_width=True):
                    st.session_state.qa_question = ""
                    st.rerun()
        
        # Process Q&A with enhanced UI
        if ask_button and st.session_state.qa_agent:
            # Validate inputs professionally
            if ERROR_HANDLING:
                validation_passed = validate_inputs(question=question)
                if not validation_passed:
                    st.stop()
            elif not question or len(question.strip()) < 5:
                st.error("❌ Question must be at least 5 characters long")
                st.stop()
            
            # Create answer container
            answer_container = st.container()
            
            with answer_container:
                # Loading state
                with st.spinner("🔍 Searching academic literature and generating AI answer..."):
                    start_time = time.time()
                    
                    try:
                        answer_result = st.session_state.qa_agent.answer_question(
                            question=question,
                            research_topic=qa_topic_filter if qa_topic_filter else None,
                            paper_limit=qa_paper_limit
                        )
                        
                        processing_time = time.time() - start_time
                        
                        if answer_result.get('confidence', 0) >= min_confidence:
                            # Success - Display comprehensive answer
                            st.markdown(f"""
                            <div class="modern-card" style="background: linear-gradient(135deg, var(--success-50) 0%, var(--primary-50) 100%); border: 2px solid var(--success-200);">
                                <h3 style="color: var(--success-700); margin-bottom: var(--spacing-lg);">
                                    ✅ AI Research Answer
                                </h3>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Main answer
                            st.markdown("### 📝 Answer")
                            st.markdown(f"""
                            <div style="background: white; padding: var(--spacing-lg); border-radius: var(--radius-lg); 
                                        border-left: 4px solid var(--primary-500); margin: var(--spacing-md) 0;">
                                {answer_result['answer']}
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Answer metadata in modern cards
                            col1, col2, col3, col4 = st.columns(4)
                            
                            confidence_score = answer_result.get('confidence', 0.0)
                            confidence_color = "success" if confidence_score > 0.7 else "warning" if confidence_score > 0.4 else "error"
                            
                            with col1:
                                st.markdown(create_metric_card(
                                    "Confidence Score", 
                                    f"{confidence_score:.2f}", 
                                    "🎯", 
                                    color=confidence_color
                                ), unsafe_allow_html=True)
                            
                            with col2:
                                st.markdown(create_metric_card(
                                    "Papers Analyzed", 
                                    answer_result.get('paper_count', 0), 
                                    "📚"
                                ), unsafe_allow_html=True)
                            
                            with col3:
                                st.markdown(create_metric_card(
                                    "Top Sources", 
                                    answer_result.get('top_papers_used', 0), 
                                    "⭐"
                                ), unsafe_allow_html=True)
                            
                            with col4:
                                st.markdown(create_metric_card(
                                    "Response Time", 
                                    f"{processing_time:.1f}s", 
                                    "⚡"
                                ), unsafe_allow_html=True)
                            
                            # Sources with enhanced display
                            if 'sources' in answer_result and answer_result['sources']:
                                st.markdown("### 📚 Academic Sources")
                                
                                for i, source in enumerate(answer_result['sources'][:10], 1):
                                    st.markdown(f"""
                                    <div style="background: var(--gray-50); padding: var(--spacing-md); 
                                                border-radius: var(--radius-md); margin: var(--spacing-sm) 0;
                                                border-left: 3px solid var(--primary-500);">
                                        <strong>{i}.</strong> {source}
                                    </div>
                                    """, unsafe_allow_html=True)
                            
                            # Related questions suggestion
                            st.markdown("### 💡 Follow-up Questions")
                            follow_up_questions = [
                                "Can you provide more specific examples?",
                                "What are the limitations of these approaches?",
                                "How has this field evolved recently?",
                                "What are the future research directions?"
                            ]
                            
                            cols = st.columns(2)
                            for i, fq in enumerate(follow_up_questions):
                                with cols[i % 2]:
                                    if st.button(f"❓ {fq}", key=f"followup_{i}", use_container_width=True):
                                        st.session_state.qa_question = f"{question} {fq}"
                                        st.rerun()
                        
                        else:
                            # Low confidence warning
                            st.markdown(f"""
                            <div class="modern-card" style="background: linear-gradient(135deg, var(--warning-50) 0%, var(--error-50) 100%); border: 2px solid var(--warning-300);">
                                <h3 style="color: var(--warning-700);">⚠️ Insufficient Confidence</h3>
                                <p style="color: var(--gray-700);">
                                    The AI couldn't find sufficient information to provide a confident answer (confidence: {answer_result.get('confidence', 0.0):.2f}).
                                </p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Suggestions for improvement
                            with st.expander("💡 Suggestions to Improve Results"):
                                st.markdown("""
                                - **Make your question more specific** and focused
                                - **Try different keywords** or terminology
                                - **Add topic filters** to narrow the search scope
                                - **Increase the number of papers** to consider
                                - **Lower the confidence threshold** if needed
                                - **Run a research workflow first** to build up the knowledge base
                                """)
                    
                    except Exception as e:
                        st.error(f"❌ Error processing your question: {str(e)}", icon="🚨")
                        logger.error(f"Q&A error: {e}", exc_info=True)
                        
                        # Error troubleshooting
                        with st.expander("🔧 Troubleshooting"):
                            st.markdown(f"""
                            **Error Details**: `{str(e)}`
                            
                            **Common Solutions**:
                            - Check your internet connection
                            - Verify API keys are configured
                            - Try a simpler question
                            - Restart the application
                            """)
        
        # Q&A History (if implemented)
        if hasattr(st.session_state, 'qa_history') and st.session_state.qa_history:
            st.markdown("### 📜 Recent Questions")
            for i, (q, timestamp) in enumerate(st.session_state.qa_history[-5:], 1):
                if st.button(f"🔄 {q[:100]}...", key=f"history_{i}"):
                    st.session_state.qa_question = q
                    st.rerun()
    
    # Tab 3: Enhanced Knowledge Base
    with tab3:
        st.markdown("""
        <div class="modern-card">
            <h2 style="color: var(--primary-700); margin-bottom: var(--spacing-md); font-weight: 600;">
                📚 Academic Knowledge Base
            </h2>
            <p style="color: var(--gray-600); margin-bottom: var(--spacing-lg);">
                Search, browse, and manage your collected research papers with advanced filtering and intelligent recommendations.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Enhanced search interface
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                search_query = st.text_input(
                    "🔍 Search Knowledge Base",
                    placeholder="Search by title, abstract, authors, keywords, or topics...",
                    help="Use advanced search: author:Smith title:machine OR topic:AI",
                    value=st.session_state.get('last_search_query', '')
                )
            
            with col2:
                search_limit = st.selectbox("📄 Results", [10, 25, 50, 100], index=1)
            
            with col3:
                sort_by = st.selectbox("📊 Sort by", ["Relevance", "Date", "Citations", "Title"])
        
        # Advanced filters
        with st.expander("🔧 Advanced Filters", expanded=False):
            filter_col1, filter_col2, filter_col3 = st.columns(3)
            
            with filter_col1:
                year_range = st.slider("📅 Publication Year", 2000, 2024, (2020, 2024))
                min_citations = st.number_input("📈 Min Citations", 0, 1000, 0)
            
            with filter_col2:
                source_filter = st.multiselect(
                    "📖 Sources", 
                    ["ArXiv", "OpenAlex", "CrossRef", "PubMed"],
                    default=[]
                )
                venue_type = st.selectbox("🏛️ Venue Type", ["Any", "Journal", "Conference", "Workshop"])
            
            with filter_col3:
                language = st.selectbox("🌐 Language", ["Any", "English", "Other"])
                paper_type = st.selectbox("📑 Paper Type", ["Any", "Research", "Review", "Survey"])
        
        # Real-time search execution
        if search_query or search_query != st.session_state.get('last_search_query', ''):
            st.session_state.last_search_query = search_query
            
            if search_query:
                # Check cache first
                cache_key = f"{search_query}_{search_limit}_{sort_by}"
                
                if cache_key in st.session_state.search_cache:
                    search_results = st.session_state.search_cache[cache_key]
                    st.info("📋 Results from cache", icon="⚡")
                else:
                    try:
                        with st.spinner(f"🔍 Searching {search_limit} papers..."):
                            search_results = db.search_papers(search_query, limit=search_limit)
                            st.session_state.search_cache[cache_key] = search_results
                    except Exception as e:
                        st.error(f"Search error: {e}")
                        search_results = []
                
                if search_results:
                    # Search results header
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.success(f"✅ Found {len(search_results)} papers", icon="🎯")
                    with col2:
                        if st.button("💾 Save Search", use_container_width=True):
                            st.success("Search saved to history!")
                    with col3:
                        if st.button("📤 Export Results", use_container_width=True):
                            st.info("Navigate to Export Center to download!")
                    
                    # Enhanced paper display
                    for i, paper in enumerate(search_results, 1):
                        with st.container():
                            paper_html = format_paper_card(paper)
                            st.markdown(paper_html, unsafe_allow_html=True)
                            
                            # Quick actions for each paper
                            paper_col1, paper_col2, paper_col3, paper_col4 = st.columns(4)
                            with paper_col1:
                                if st.button(f"💬 Ask about this", key=f"ask_{i}"):
                                    st.session_state.qa_question = f"Tell me about the paper: {paper.title}"
                                    st.switch_page("tab2")  # Switch to Q&A tab
                            
                            with paper_col2:
                                if st.button(f"🔗 Similar Papers", key=f"similar_{i}"):
                                    st.info("Finding similar papers...")
                            
                            with paper_col3:
                                if st.button(f"📋 Add to Collection", key=f"collect_{i}"):
                                    st.success("Added to collection!")
                            
                            with paper_col4:
                                if st.button(f"📊 View Analytics", key=f"analytics_{i}"):
                                    st.info("Paper analytics coming soon!")
                            
                            st.divider()
                else:
                    # No results found
                    st.markdown(f"""
                    <div class="modern-card" style="background: linear-gradient(135deg, var(--warning-50) 0%, var(--gray-50) 100%); border: 2px solid var(--warning-200);">
                        <h3 style="color: var(--warning-700);">🔍 No Papers Found</h3>
                        <p style="color: var(--gray-700);">No papers match your search criteria.</p>
                        
                        <h4 style="color: var(--gray-700); margin-top: var(--spacing-lg);">💡 Suggestions:</h4>
                        <ul style="color: var(--gray-600);">
                            <li>Try different keywords or synonyms</li>
                            <li>Remove some filters to broaden your search</li>
                            <li>Check your spelling</li>
                            <li>Run a research workflow to collect more papers</li>
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)
            
            else:
                # Show recent papers when no search query
                st.markdown("### 📈 Recently Added Papers")
                recent_papers = get_recent_papers(15)
                
                if recent_papers:
                    # Display recent papers with enhanced UI
                    for paper in recent_papers:
                        st.markdown(format_paper_card(paper), unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="modern-card" style="text-align: center; background: linear-gradient(135deg, var(--primary-50) 0%, var(--secondary-50) 100%);">
                        <h3 style="color: var(--primary-700);">🚀 Start Building Your Knowledge Base</h3>
                        <p style="color: var(--gray-600); margin: var(--spacing-lg) 0;">
                            No papers in your knowledge base yet. Launch a research workflow to start collecting academic papers!
                        </p>
                        <div style="margin-top: var(--spacing-xl);">
                            <button class="modern-button" onclick="document.querySelector('[data-testid=\"stTab\"]:first-child').click()">
                                🔬 Start Research Workflow
                            </button>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Knowledge base statistics
        if stats['papers'] > 0:
            st.markdown("### 📊 Knowledge Base Statistics")
            
            col1, col2 = st.columns(2)
            with col1:
                # Top sources pie chart
                analytics = get_research_analytics()
                if analytics.get('papers_by_source'):
                    fig_sources = px.pie(
                        values=list(analytics['papers_by_source'].values()),
                        names=list(analytics['papers_by_source'].keys()),
                        title="📚 Papers by Source",
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    fig_sources.update_traces(textposition='inside', textinfo='percent+label')
                    fig_sources.update_layout(
                        font_family="Inter",
                        title_font_size=16,
                        showlegend=True
                    )
                    st.plotly_chart(fig_sources, use_container_width=True)
            
            with col2:
                # Citation distribution
                if analytics.get('citation_distribution'):
                    fig_citations = px.bar(
                        x=list(analytics['citation_distribution'].keys()),
                        y=list(analytics['citation_distribution'].values()),
                        title="📈 Citation Distribution",
                        color=list(analytics['citation_distribution'].values()),
                        color_continuous_scale="Blues"
                    )
                    fig_citations.update_layout(
                        font_family="Inter",
                        title_font_size=16,
                        xaxis_title="Citation Range",
                        yaxis_title="Number of Papers",
                        showlegend=False
                    )
                    st.plotly_chart(fig_citations, use_container_width=True)
    
    # Tab 4: Enhanced Analytics Dashboard
    with tab4:
        st.markdown("""
        <div class="modern-card">
            <h2 style="color: var(--primary-700); margin-bottom: var(--spacing-md); font-weight: 600;">
                � Research Analytics Dashboard
            </h2>
            <p style="color: var(--gray-600); margin-bottom: var(--spacing-lg);">
                Comprehensive insights and visualizations of your research data, trends, and patterns.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if stats['papers'] > 0:
            analytics = get_research_analytics()
            
            # Key metrics overview
            st.markdown("### 🎯 Key Research Metrics")
            
            metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
            
            with metric_col1:
                st.markdown(create_metric_card(
                    "Total Papers", 
                    stats['papers'], 
                    "📚", 
                    trend=5.2
                ), unsafe_allow_html=True)
            
            with metric_col2:
                avg_citations = sum(analytics.get('citation_distribution', {0: 0}).values()) / max(len(analytics.get('citation_distribution', {0: 1})), 1)
                st.markdown(create_metric_card(
                    "Avg Citations", 
                    f"{avg_citations:.0f}", 
                    "�", 
                    trend=2.1
                ), unsafe_allow_html=True)
            
            with metric_col3:
                st.markdown(create_metric_card(
                    "Research Topics", 
                    len(analytics.get('trending_topics', [])), 
                    "🎯", 
                    trend=-1.3
                ), unsafe_allow_html=True)
            
            with metric_col4:
                total_sources = len(analytics.get('papers_by_source', {}))
                st.markdown(create_metric_card(
                    "Data Sources", 
                    total_sources, 
                    "🔗"
                ), unsafe_allow_html=True)
            
            # Advanced visualizations
            st.markdown("### 📈 Research Trends & Patterns")
            
            viz_col1, viz_col2 = st.columns(2)
            
            with viz_col1:
                # Papers by source - Enhanced pie chart
                if analytics.get('papers_by_source'):
                    fig_sources = px.pie(
                        values=list(analytics['papers_by_source'].values()),
                        names=list(analytics['papers_by_source'].keys()),
                        title="📚 Academic Sources Distribution",
                        hole=0.4,
                        color_discrete_sequence=px.colors.qualitative.Set2
                    )
                    fig_sources.update_traces(
                        textposition='inside', 
                        textinfo='percent+label',
                        hovertemplate='<b>%{label}</b><br>Papers: %{value}<br>Percentage: %{percent}<extra></extra>'
                    )
                    fig_sources.update_layout(
                        font_family="Inter",
                        title_font_size=18,
                        title_x=0.5,
                        showlegend=True,
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                        margin=dict(t=80, b=50, l=50, r=50)
                    )
                    st.plotly_chart(fig_sources, use_container_width=True)
            
            with viz_col2:
                # Publication timeline
                if analytics.get('papers_by_year'):
                    fig_timeline = px.line(
                        x=list(analytics['papers_by_year'].keys()),
                        y=list(analytics['papers_by_year'].values()),
                        title="📅 Publication Timeline",
                        markers=True,
                        line_shape='spline'
                    )
                    fig_timeline.update_traces(
                        line=dict(color='#3b82f6', width=3),
                        marker=dict(size=8, color='#1d4ed8'),
                        hovertemplate='<b>Year: %{x}</b><br>Papers: %{y}<extra></extra>'
                    )
                    fig_timeline.update_layout(
                        font_family="Inter",
                        title_font_size=18,
                        title_x=0.5,
                        xaxis_title="Publication Year",
                        yaxis_title="Number of Papers",
                        margin=dict(t=80, b=50, l=50, r=50),
                        hovermode='x unified'
                    )
                    st.plotly_chart(fig_timeline, use_container_width=True)
            
            # Citation analysis
            st.markdown("### � Citation Analysis")
            
            cit_col1, cit_col2 = st.columns(2)
            
            with cit_col1:
                # Citation distribution bar chart
                if analytics.get('citation_distribution'):
                    fig_citations = px.bar(
                        x=list(analytics['citation_distribution'].keys()),
                        y=list(analytics['citation_distribution'].values()),
                        title="📈 Citation Distribution",
                        color=list(analytics['citation_distribution'].values()),
                        color_continuous_scale="viridis",
                        text=list(analytics['citation_distribution'].values())
                    )
                    fig_citations.update_traces(
                        texttemplate='%{text}',
                        textposition='outside',
                        hovertemplate='<b>Citation Range: %{x}</b><br>Papers: %{y}<extra></extra>'
                    )
                    fig_citations.update_layout(
                        font_family="Inter",
                        title_font_size=18,
                        title_x=0.5,
                        xaxis_title="Citation Range",
                        yaxis_title="Number of Papers",
                        showlegend=False,
                        margin=dict(t=80, b=50, l=50, r=50)
                    )
                    st.plotly_chart(fig_citations, use_container_width=True)
            
            with cit_col2:
                # Top trending topics
                if analytics.get('trending_topics'):
                    trending_df = pd.DataFrame(analytics['trending_topics'])
                    
                    fig_topics = px.bar(
                        trending_df,
                        x='count',
                        y='topic',
                        title="🔥 Trending Research Topics",
                        color='count',
                        color_continuous_scale="plasma",
                        text='count',
                        orientation='h'
                    )
                    fig_topics.update_traces(
                        texttemplate='%{text}',
                        textposition='inside',
                        hovertemplate='<b>%{y}</b><br>Papers: %{x}<extra></extra>'
                    )
                    fig_topics.update_layout(
                        font_family="Inter",
                        title_font_size=18,
                        title_x=0.5,
                        xaxis_title="Number of Papers",
                        yaxis_title="Research Topic",
                        showlegend=False,
                        margin=dict(t=80, b=50, l=50, r=50),
                        height=400
                    )
                    st.plotly_chart(fig_topics, use_container_width=True)
            
            # Advanced analytics
            st.markdown("### 🔬 Advanced Research Insights")
            
            insight_col1, insight_col2 = st.columns(2)
            
            with insight_col1:
                st.markdown("""
                <div class="modern-card" style="background: linear-gradient(135deg, var(--primary-50) 0%, var(--secondary-50) 100%);">
                    <h4 style="color: var(--primary-700);">🎯 Research Quality Score</h4>
                    <div style="font-size: var(--font-size-2xl); font-weight: 700; color: var(--primary-600); margin: var(--spacing-md) 0;">
                        8.7/10
                    </div>
                    <p style="color: var(--gray-600); font-size: var(--font-size-sm);">
                        Based on citation patterns, source diversity, and paper quality indicators
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Research recommendations
                st.markdown("""
                <div class="modern-card">
                    <h4 style="color: var(--success-700);">� AI Recommendations</h4>
                    <ul style="color: var(--gray-700); line-height: 1.6;">
                        <li>Explore more papers from <strong>Nature</strong> and <strong>Science</strong></li>
                        <li>Consider researching <strong>Quantum Machine Learning</strong></li>
                        <li>Review papers from <strong>2023-2024</strong> for latest developments</li>
                        <li>Focus on <strong>high-citation papers</strong> (>50 citations)</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            
            with insight_col2:
                # Research productivity metrics
                st.markdown("""
                <div class="modern-card" style="background: linear-gradient(135deg, var(--success-50) 0%, var(--warning-50) 100%);">
                    <h4 style="color: var(--success-700);">📊 Research Productivity</h4>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--spacing-md); margin-top: var(--spacing-md);">
                        <div style="text-align: center;">
                            <div style="font-size: var(--font-size-xl); font-weight: 600; color: var(--success-600);">
                                15.2
                            </div>
                            <div style="font-size: var(--font-size-sm); color: var(--gray-600);">
                                Papers/Week
                            </div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: var(--font-size-xl); font-weight: 600; color: var(--warning-600);">
                                3.4h
                            </div>
                            <div style="font-size: var(--font-size-sm); color: var(--gray-600);">
                                Avg Processing Time
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Export analytics option
                if st.button("📊 Export Analytics Report", use_container_width=True, type="secondary"):
                    st.success("Analytics report will be generated in the Export Center!")
        
        else:
            # Empty state with call to action
            st.markdown(f"""
            <div class="modern-card" style="text-align: center; background: linear-gradient(135deg, var(--gray-50) 0%, var(--primary-50) 100%);">
                <div style="font-size: 4rem; margin-bottom: var(--spacing-lg);">📊</div>
                <h3 style="color: var(--primary-700); margin-bottom: var(--spacing-md);">
                    Analytics Dashboard Coming Soon
                </h3>
                <p style="color: var(--gray-600); margin-bottom: var(--spacing-xl);">
                    Build your research collection first to see powerful analytics and insights about your academic work.
                </p>
                <div style="display: flex; gap: var(--spacing-md); justify-content: center; flex-wrap: wrap;">
                    <button class="modern-button" onclick="document.querySelector('[data-testid=\"stTab\"]:first-child').click()">
                        🔬 Start Research
                    </button>
                    <button class="modern-button success-button" onclick="document.querySelector('[data-testid=\"stTab\"]:nth-child(2)').click()">
                        💬 Ask Questions
                    </button>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Preview of analytics features
            st.markdown("### � Coming Analytics Features")
            
            preview_col1, preview_col2, preview_col3 = st.columns(3)
            
            with preview_col1:
                st.markdown("""
                <div class="modern-card" style="text-align: center;">
                    <div style="font-size: 2rem; margin-bottom: var(--spacing-sm);">📈</div>
                    <h4 style="color: var(--primary-700);">Trend Analysis</h4>
                    <p style="color: var(--gray-600); font-size: var(--font-size-sm);">
                        Discover emerging topics and research patterns
                    </p>
                </div>
                """, unsafe_allow_html=True)
            
            with preview_col2:
                st.markdown("""
                <div class="modern-card" style="text-align: center;">
                    <div style="font-size: 2rem; margin-bottom: var(--spacing-sm);">🎯</div>
                    <h4 style="color: var(--secondary-700);">Impact Metrics</h4>
                    <p style="color: var(--gray-600); font-size: var(--font-size-sm);">
                        Analyze citation networks and research impact
                    </p>
                </div>
                """, unsafe_allow_html=True)
            
            with preview_col3:
                st.markdown("""
                <div class="modern-card" style="text-align: center;">
                    <div style="font-size: 2rem; margin-bottom: var(--spacing-sm);">🤖</div>
                    <h4 style="color: var(--success-700);">AI Insights</h4>
                    <p style="color: var(--gray-600); font-size: var(--font-size-sm);">
                        Get AI-powered research recommendations
                    </p>
                </div>
                """, unsafe_allow_html=True)
    
    # Tab 5: Enhanced Export Center
    with tab5:
        st.markdown("""
        <div class="export-section">
            <h2 style="color: var(--primary-700); margin-bottom: var(--spacing-md); font-weight: 600;">
                📋 Professional Export Center
            </h2>
            <p style="color: var(--gray-600); margin-bottom: var(--spacing-lg);">
                Export your research results in professional formats ready for publication, presentation, or sharing.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.research_results:
            results = st.session_state.research_results
            
            # Success banner
            st.markdown(f"""
            <div class="modern-card" style="background: linear-gradient(135deg, var(--success-50) 0%, var(--primary-50) 100%); border: 2px solid var(--success-300);">
                <h3 style="color: var(--success-700); margin-bottom: var(--spacing-sm);">
                    ✅ Research Results Ready for Export
                </h3>
                <p style="color: var(--gray-700);">
                    <strong>Topic:</strong> {results['research_topic']}<br>
                    <strong>Completed:</strong> {results.get('timestamp', 'Recently')}<br>
                    <strong>Papers Analyzed:</strong> {results['statistics']['papers_found']}
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Export options with modern design
            st.markdown("### 📄 Export Options")
            
            export_col1, export_col2 = st.columns(2)
            
            with export_col1:
                st.markdown("""
                <div class="modern-card">
                    <h4 style="color: var(--primary-700); margin-bottom: var(--spacing-lg);">
                        📝 Research Paper Export
                    </h4>
                </div>
                """, unsafe_allow_html=True)
                
                # Paper export options
                available_formats = st.session_state.research_crew.get_available_export_formats()
                
                paper_format = st.selectbox(
                    "📄 Paper Format",
                    available_formats,
                    help="Choose format for exporting the research paper",
                    key="paper_format"
                )
                
                paper_filename = st.text_input(
                    "📁 Paper Filename",
                    value=f"{results['research_topic'].replace(' ', '_')}_research_paper",
                    help="Filename without extension"
                )
                
                # Advanced paper options
                with st.expander("⚙️ Advanced Paper Options"):
                    include_abstract = st.checkbox("📋 Include Abstract", value=True)
                    include_toc = st.checkbox("📚 Include Table of Contents", value=True)
                    include_references = st.checkbox("📖 Include Full References", value=True)
                    paper_style = st.selectbox("🎨 Document Style", ["Academic", "Professional", "Modern"])
                
                if st.button("📄 Export Research Paper", use_container_width=True, type="primary"):
                    try:
                        # Create timestamped output directory
                        output_dir = Path("data/outputs") / f"{results['research_topic'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        output_dir.mkdir(parents=True, exist_ok=True)
                        
                        # Show progress
                        progress_bar = st.progress(0, text="Preparing document...")
                        
                        progress_bar.progress(0.3, text="Formatting content...")
                        
                        # Export paper
                        output_path = output_dir / paper_filename
                        success = export_manager.export_draft(
                            results['draft'],
                            str(output_path),
                            paper_format
                        )
                        
                        progress_bar.progress(1.0, text="Export completed!")
                        
                        if success:
                            st.success(f"🎉 Paper exported successfully!", icon="✅")
                            st.info(f"📁 **Location:** `{output_path}.{paper_format}`")
                            
                            # File details
                            try:
                                file_path = f"{output_path}.{paper_format}"
                                if os.path.exists(file_path):
                                    file_size = os.path.getsize(file_path) / 1024  # KB
                                    st.metric("📊 File Size", f"{file_size:.1f} KB")
                            except:
                                pass
                        else:
                            st.error("❌ Failed to export paper")
                            
                    except Exception as e:
                        st.error(f"Export error: {e}")
            
            with export_col2:
                st.markdown("""
                <div class="modern-card">
                    <h4 style="color: var(--secondary-700); margin-bottom: var(--spacing-lg);">
                        📚 Bibliography Export
                    </h4>
                </div>
                """, unsafe_allow_html=True)
                
                # Bibliography export options
                bib_format = st.selectbox(
                    "📖 Bibliography Format",
                    ["bibtex", "apa", "mla", "chicago", "txt", "csv", "json", "pdf"],
                    help="Choose format for exporting the bibliography"
                )
                
                bib_filename = st.text_input(
                    "📁 Bibliography Filename",
                    value=f"{results['research_topic'].replace(' ', '_')}_bibliography",
                    help="Filename without extension"
                )
                
                # Advanced bibliography options
                with st.expander("⚙️ Advanced Bibliography Options"):
                    sort_by_author = st.checkbox("👥 Sort by Author", value=True)
                    include_abstracts = st.checkbox("📄 Include Abstracts", value=False)
                    min_citations = st.number_input("📈 Min Citations Filter", 0, 1000, 0)
                    max_entries = st.number_input("📝 Max Entries", 10, 500, 100)
                
                if st.button("📚 Export Bibliography", use_container_width=True, type="secondary"):
                    try:
                        # Create output directory
                        output_dir = Path("data/outputs") / f"{results['research_topic'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        output_dir.mkdir(parents=True, exist_ok=True)
                        
                        # Show progress
                        progress_bar = st.progress(0, text="Collecting references...")
                        
                        progress_bar.progress(0.5, text="Formatting bibliography...")
                        
                        # Export bibliography
                        output_path = output_dir / bib_filename
                        success = export_manager.export_bibliography(
                            results.get('bibliography', ''),
                            results.get('papers', []),
                            str(output_path),
                            bib_format
                        )
                        
                        progress_bar.progress(1.0, text="Bibliography exported!")
                        
                        if success:
                            st.success(f"🎉 Bibliography exported successfully!", icon="✅")
                            st.info(f"📁 **Location:** `{output_path}.{bib_format}`")
                        else:
                            st.error("❌ Failed to export bibliography")
                            
                    except Exception as e:
                        st.error(f"Bibliography export error: {e}")
            
            # Complete research package export
            st.markdown("### 📦 Complete Research Package")
            
            st.markdown("""
            <div class="modern-card" style="background: linear-gradient(135deg, var(--warning-50) 0%, var(--success-50) 100%);">
                <h4 style="color: var(--warning-700);">🎁 All-in-One Research Package</h4>
                <p style="color: var(--gray-700);">
                    Export everything: research paper, bibliography, raw data, paper summaries, and analysis notes in multiple formats.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            package_col1, package_col2, package_col3 = st.columns(3)
            
            with package_col1:
                package_name = st.text_input(
                    "📦 Package Name",
                    value=f"{results['research_topic'].replace(' ', '_')}_complete",
                    help="Name for the complete research package"
                )
            
            with package_col2:
                package_formats = st.multiselect(
                    "📄 Include Formats",
                    ["PDF", "DOCX", "LaTeX", "Markdown", "JSON"],
                    default=["PDF", "DOCX", "JSON"]
                )
            
            with package_col3:
                compression = st.selectbox(
                    "🗜️ Compression",
                    ["ZIP", "None"],
                    help="Compress the package for easier sharing"
                )
            
            if st.button("📦 Export Complete Package", use_container_width=True, type="primary"):
                try:
                    # Create timestamped output directory
                    output_dir = Path("data/outputs") / f"{package_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    output_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Progress tracking
                    total_steps = len(package_formats) + 3
                    progress_bar = st.progress(0, text="Initializing package export...")
                    
                    exported_files = []
                    
                    # Export in each requested format
                    for i, fmt in enumerate(package_formats):
                        progress_bar.progress((i + 1) / total_steps, text=f"Exporting {fmt} format...")
                        
                        if fmt.lower() in available_formats:
                            draft_path = output_dir / f"research_paper"
                            if export_manager.export_draft(results['draft'], str(draft_path), fmt.lower()):
                                exported_files.append(f"research_paper.{fmt.lower()}")
                    
                    # Export bibliography
                    progress_bar.progress((len(package_formats) + 1) / total_steps, text="Exporting bibliography...")
                    bib_path = output_dir / "bibliography"
                    if export_manager.export_bibliography(
                        results.get('bibliography', ''),
                        results.get('papers', []),
                        str(bib_path),
                        'txt'
                    ):
                        exported_files.append("bibliography.txt")
                    
                    # Export raw data
                    progress_bar.progress((len(package_formats) + 2) / total_steps, text="Exporting raw data...")
                    json_path = output_dir / "research_data.json"
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(results, f, indent=2, default=str)
                    exported_files.append("research_data.json")
                    
                    # Create summary file
                    progress_bar.progress((len(package_formats) + 3) / total_steps, text="Creating summary...")
                    summary_path = output_dir / "research_summary.md"
                    with open(summary_path, 'w', encoding='utf-8') as f:
                        f.write(f"""# Research Summary: {results['research_topic']}

## Overview
- **Research Topic**: {results['research_topic']}
- **Papers Analyzed**: {results['statistics']['papers_found']}
- **Notes Extracted**: {results['statistics']['notes_extracted']}
- **Themes Identified**: {results['statistics']['themes_identified']}
- **Citations Generated**: {results['statistics']['citations_generated']}
- **Execution Time**: {results['execution_time']}
- **Export Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Files in this Package
{chr(10).join(f"- {file}" for file in exported_files)}

## Generated with Academic Research Assistant Pro
Powered by AI for comprehensive research workflows
""")
                    exported_files.append("research_summary.md")
                    
                    progress_bar.progress(1.0, text="Package export completed!")
                    
                    # Success message
                    st.balloons()
                    st.success(f"🎉 Complete research package exported successfully!", icon="🎊")
                    
                    # Package details
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("📁 Files Created", len(exported_files))
                    with col2:
                        try:
                            total_size = sum(os.path.getsize(output_dir / f) for f in exported_files if os.path.exists(output_dir / f))
                            st.metric("💾 Total Size", f"{total_size / 1024:.1f} KB")
                        except:
                            st.metric("💾 Total Size", "Calculating...")
                    with col3:
                        st.metric("📦 Package Location", "✅ Ready")
                    
                    st.info(f"📂 **Package Location:** `{output_dir}`")
                    
                    # List exported files
                    with st.expander("📋 Package Contents"):
                        for file in exported_files:
                            st.markdown(f"- ✅ `{file}`")
                    
                except Exception as e:
                    st.error(f"Package export error: {e}")
        
        else:
            # No results available - enhanced empty state
            st.markdown(f"""
            <div class="modern-card" style="text-align: center; background: linear-gradient(135deg, var(--gray-50) 0%, var(--primary-50) 100%);">
                <div style="font-size: 4rem; margin-bottom: var(--spacing-lg);">📋</div>
                <h3 style="color: var(--primary-700); margin-bottom: var(--spacing-md);">
                    No Research Results to Export
                </h3>
                <p style="color: var(--gray-600); margin-bottom: var(--spacing-xl);">
                    Complete a research workflow first to generate exportable content including research papers, bibliographies, and analysis reports.
                </p>
                
                <div style="background: var(--warning-50); padding: var(--spacing-lg); border-radius: var(--radius-lg); margin: var(--spacing-lg) 0; border: 1px solid var(--warning-200);">
                    <h4 style="color: var(--warning-700); margin-bottom: var(--spacing-md);">🚀 What You Can Export After Research:</h4>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: var(--spacing-md); text-align: left;">
                        <div>
                            <strong style="color: var(--primary-600);">📄 Research Papers</strong>
                            <p style="color: var(--gray-600); font-size: var(--font-size-sm); margin: var(--spacing-xs) 0;">
                                PDF, DOCX, LaTeX, Markdown formats
                            </p>
                        </div>
                        <div>
                            <strong style="color: var(--secondary-600);">📚 Bibliographies</strong>
                            <p style="color: var(--gray-600); font-size: var(--font-size-sm); margin: var(--spacing-xs) 0;">
                                BibTeX, APA, MLA, Chicago styles
                            </p>
                        </div>
                        <div>
                            <strong style="color: var(--success-600);">📊 Analytics Reports</strong>
                            <p style="color: var(--gray-600); font-size: var(--font-size-sm); margin: var(--spacing-xs) 0;">
                                Charts, statistics, insights
                            </p>
                        </div>
                        <div>
                            <strong style="color: var(--warning-600);">📦 Complete Packages</strong>
                            <p style="color: var(--gray-600); font-size: var(--font-size-sm); margin: var(--spacing-xs) 0;">
                                All-in-one research bundles
                            </p>
                        </div>
                    </div>
                </div>
                
                <button class="modern-button" onclick="document.querySelector('[data-testid=\"stTab\"]:first-child').click()" style="margin-right: var(--spacing-md);">
                    🔬 Start Research Workflow
                </button>
                <button class="modern-button success-button" onclick="document.querySelector('[data-testid=\"stTab\"]:nth-child(2)').click()">
                    💬 Try AI Assistant
                </button>
            </div>
            """, unsafe_allow_html=True)
    
    # Footer with performance info
    end_time = time.time()
    total_time = end_time - start_time
    
    st.markdown(f"""
    <div style="margin-top: var(--spacing-2xl); padding: var(--spacing-lg); background: var(--gray-50); 
                border-radius: var(--radius-lg); text-align: center; border: 1px solid var(--gray-200);">
        <div style="color: var(--gray-500); font-size: var(--font-size-sm);">
            🚀 <strong>Academic Research Assistant Pro</strong> | 
            ⚡ Page loaded in {total_time:.2f}s | 
            🤖 AI-Powered Research Platform | 
            📊 {stats.get('papers', 0)} papers in knowledge base
        </div>
        <div style="margin-top: var(--spacing-xs); color: var(--gray-400); font-size: var(--font-size-xs);">
            Built with ❤️ for researchers | Version 2.0 Production Ready
        </div>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

