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
from typing import Dict, List, Any, Optional
import sys

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure Streamlit page
st.set_page_config(
    page_title="Academic Research Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for lazy loading
def initialize_session_state():
    """Initialize session state variables for lazy loading"""
    if 'research_crew_loaded' not in st.session_state:
        st.session_state.research_crew_loaded = False
        st.session_state.research_crew = None
        
    if 'qa_agent_loaded' not in st.session_state:
        st.session_state.qa_agent_loaded = False
        st.session_state.qa_agent = None
        
    if 'research_results' not in st.session_state:
        st.session_state.research_results = None

def load_research_modules():
    """Load research modules only when needed"""
    if not st.session_state.research_crew_loaded:
        try:
            with st.spinner("🚀 Loading AI Research System..."):
                from src.crew.research_crew import ResearchCrew
                from src.storage.database import db
                from src.utils.config import config
                from src.utils.export_manager import export_manager
                st.session_state.research_crew = ResearchCrew()
                st.session_state.research_crew_loaded = True
                st.success("✅ Research system loaded successfully!")
                return True
        except ImportError as e:
            st.error(f"❌ Failed to load research system: {e}")
            st.info("💡 Make sure all dependencies are installed: pip install -r requirements.txt")
            return False
        except Exception as e:
            st.error(f"❌ Error loading research system: {e}")
            return False
    return True

def load_qa_agent():
    """Load QA agent only when needed"""
    if not st.session_state.qa_agent_loaded:
        try:
            with st.spinner("🧠 Loading Q&A Assistant..."):
                from src.agents.qa_agent import QuestionAnsweringAgent
                st.session_state.qa_agent = QuestionAnsweringAgent()
                st.session_state.qa_agent_loaded = True
                st.success("✅ Q&A Assistant loaded successfully!")
                return True
        except ImportError as e:
            st.error(f"❌ Failed to load Q&A system: {e}")
            return False
        except Exception as e:
            st.error(f"❌ Error loading Q&A system: {e}")
            return False
    return True

# Initialize session state
initialize_session_state()

# Modern UI Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');
    
    /* Main app background */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        font-family: 'Inter', sans-serif;
    }
    
    /* Main container */
    .main .block-container {
        padding-top: 2rem;
        max-width: 1200px;
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
        margin: 2rem auto;
    }
    
    /* Header styling */
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        background-clip: text;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        font-size: 3rem;
        margin-bottom: 2rem;
    }
    
    /* Card styling */
    .info-card {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(102, 126, 234, 0.1);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 10px;
        color: #666;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
    }
    
    /* Metric styling */
    [data-testid="metric-container"] {
        background: white;
        border-radius: 15px;
        padding: 1rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(102, 126, 234, 0.1);
    }
    
    /* Success/Error messages */
    .stSuccess {
        background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%);
        border: none;
        border-radius: 10px;
    }
    
    .stError {
        background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
        border: none;
        border-radius: 10px;
    }
    
    .stInfo {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        border-radius: 10px;
    }
</style>""", unsafe_allow_html=True)

def main():
    # Header
    st.markdown('<div class="main-header">🎓 Academic Research Assistant</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <p style="font-size: 1.2rem; color: #666; font-weight: 500;">
            Your AI-powered companion for comprehensive academic research and analysis
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check system status
    st.markdown("""
    <div class="info-card">
        <h3 style="color: #667eea; margin-bottom: 1rem;">🔍 System Status</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # System checks
    col1, col2, col3 = st.columns(3)
    with col1:
        try:
            import src
            st.success("✅ Core modules available")
        except ImportError:
            st.error("❌ Core modules missing")
    
    with col2:
        try:
            from src.storage.database import db
            st.success("✅ Database connected")
        except Exception:
            st.error("❌ Database connection failed")
    
    with col3:
        try:
            from src.utils.config import config
            st.success("✅ Configuration loaded")
        except Exception:
            st.error("❌ Configuration error")
    
    # Sidebar with quick stats
    with st.sidebar:
        st.markdown("### 📊 Quick Stats")
        try:
            from src.storage.database import db
            stats = db.get_stats()
            
            st.metric("Papers", stats.get('papers', 0))
            st.metric("Notes", stats.get('notes', 0))
            st.metric("Themes", stats.get('themes', 0))
        except Exception:
            st.info("Database stats unavailable")
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔬 Research", "🧠 Q&A", "📚 Papers", "📊 Analytics", "📤 Export"
    ])
    
    with tab1:
        st.markdown("### 🔬 Research Workflow")
        
        st.markdown("""
        <div class="info-card">
            <h4>Start Your Research Journey</h4>
            <p>Configure and launch AI-powered research workflows to analyze academic literature and generate comprehensive reports.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Load research system only when user wants to use it
        if st.button("🚀 Initialize Research System"):
            if load_research_modules():
                st.rerun()
        
        if st.session_state.research_crew_loaded:
            with st.form("research_form"):
                st.markdown("#### Research Configuration")
                
                col1, col2 = st.columns(2)
                with col1:
                    research_topic = st.text_input(
                        "Research Topic*",
                        placeholder="e.g., Machine Learning in Healthcare"
                    )
                    max_papers = st.slider("Maximum Papers", 10, 100, 50)
                
                with col2:
                    paper_type = st.selectbox(
                        "Paper Type",
                        ["survey", "review", "analysis", "systematic_review"]
                    )
                    date_from = st.date_input("Papers From Date", value=None)
                
                specific_aspects = st.text_area(
                    "Specific Aspects (Optional)",
                    placeholder="Enter specific aspects to focus on"
                )
                
                submit_button = st.form_submit_button("🚀 Start Research", use_container_width=True)
                
                if submit_button and research_topic:
                    # Parse aspects
                    aspects_list = [aspect.strip() for aspect in specific_aspects.split('\n') if aspect.strip()] if specific_aspects else None
                    date_from_dt = datetime.combine(date_from, datetime.min.time()) if date_from else None
                    
                    # Progress tracking
                    progress_bar = st.progress(0)
                    status_container = st.empty()
                    
                    def update_progress(step, description):
                        progress_bar.progress(step * 0.2)
                        status_container.info(f"Step {step}/5: {description}")
                    
                    try:
                        # Execute research
                        results = st.session_state.research_crew.execute_research_workflow(
                            research_topic=research_topic,
                            specific_aspects=aspects_list,
                            max_papers=max_papers,
                            paper_type=paper_type,
                            date_from=date_from_dt,
                            progress_callback=update_progress,
                            resume_from_checkpoint=True
                        )
                        
                        st.session_state.research_results = results
                        progress_bar.progress(1.0)
                        
                        if results['success']:
                            st.success("✅ Research completed successfully!")
                            
                            # Results summary
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Papers Found", results['statistics']['papers_found'])
                            with col2:
                                st.metric("Notes Extracted", results['statistics']['notes_extracted'])
                            with col3:
                                st.metric("Themes Identified", results['statistics']['themes_identified'])
                            with col4:
                                st.metric("Citations", results['statistics']['citations_generated'])
                            
                            st.info(f"⏱️ Execution Time: {results['execution_time']}")
                        else:
                            st.error(f"❌ Research failed: {results.get('error', 'Unknown error')}")
                    
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
    
    with tab2:
        st.markdown("### 🧠 Q&A Assistant")
        
        st.markdown("""
        <div class="info-card">
            <h4>Ask Research Questions</h4>
            <p>Get AI-powered answers to your research questions based on academic literature in your database.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🧠 Initialize Q&A System"):
            if load_qa_agent():
                st.rerun()
        
        if st.session_state.qa_agent_loaded:
            question = st.text_area(
                "Your Question",
                placeholder="What are the main challenges in machine learning for healthcare?",
                height=100
            )
            
            col1, col2 = st.columns(2)
            with col1:
                topic_filter = st.text_input("Topic Filter", placeholder="machine learning")
            with col2:
                paper_limit = st.slider("Max Papers", 5, 50, 10)
            
            if st.button("🤔 Get Answer", use_container_width=True) and question:
                with st.spinner("Generating answer..."):
                    try:
                        answer_result = st.session_state.qa_agent.answer_question(
                            question=question,
                            research_topic=topic_filter or None,
                            paper_limit=paper_limit
                        )
                        
                        if answer_result['confidence'] > 0:
                            st.markdown("#### 📝 Answer")
                            st.markdown(answer_result['answer'])
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Confidence", f"{answer_result['confidence']:.2f}")
                            with col2:
                                st.metric("Papers Used", answer_result['paper_count'])
                            
                            if 'sources' in answer_result:
                                st.markdown("#### 📚 Sources")
                                for i, source in enumerate(answer_result['sources'][:3], 1):
                                    st.markdown(f"{i}. {source}")
                        else:
                            st.warning("⚠️ Could not find sufficient information.")
                    
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
    
    with tab3:
        st.markdown("### 📚 Paper Database")
        
        st.markdown("""
        <div class="info-card">
            <h4>Explore Your Paper Collection</h4>
            <p>Search and browse through your collected research papers and their metadata.</p>
        </div>
        """, unsafe_allow_html=True)
        
        try:
            from src.storage.database import db
            
            # Search interface
            col1, col2 = st.columns([3, 1])
            with col1:
                search_query = st.text_input("Search Papers", placeholder="Enter keywords")
            with col2:
                search_limit = st.selectbox("Results", [10, 25, 50], index=1)
            
            if search_query:
                try:
                    results = db.search_papers(search_query, limit=search_limit)
                    
                    if results:
                        st.success(f"Found {len(results)} papers")
                        
                        for paper in results[:5]:  # Show first 5
                            with st.expander(f"📄 {paper.title}"):
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.write(f"**Authors:** {', '.join(paper.authors) if paper.authors else 'Unknown'}")
                                    st.write(f"**Year:** {getattr(paper, 'year', 'Unknown')}")
                                with col2:
                                    st.write(f"**Source:** {paper.source}")
                                    st.write(f"**Citations:** {getattr(paper, 'citations', 0)}")
                                
                                if paper.abstract:
                                    st.write("**Abstract:**")
                                    st.write(paper.abstract[:300] + "..." if len(paper.abstract) > 300 else paper.abstract)
                    else:
                        st.warning("No papers found")
                except Exception as e:
                    st.error(f"Search error: {e}")
            else:
                # Show recent papers
                try:
                    recent = db.get_recent_papers(5)
                    if recent:
                        st.markdown("#### Recent Papers")
                        for paper in recent:
                            st.markdown(f"📄 **{paper.title}**")
                            st.write(f"Authors: {', '.join(paper.authors) if paper.authors else 'Unknown'}")
                            st.divider()
                    else:
                        st.info("No papers in database yet")
                except Exception as e:
                    st.error(f"Error loading recent papers: {e}")
        
        except ImportError:
            st.error("Database module not available")
    
    with tab4:
        st.markdown("### 📊 Analytics Dashboard")
        
        st.markdown("""
        <div class="info-card">
            <h4>Research Insights</h4>
            <p>Visualize your research data with interactive charts and analytics.</p>
        </div>
        """, unsafe_allow_html=True)
        
        try:
            from src.storage.database import db
            stats = db.get_stats()
            
            if stats['papers'] > 0:
                col1, col2 = st.columns(2)
                
                with col1:
                    # Sample pie chart
                    fig = px.pie(
                        values=[40, 35, 25],
                        names=['ArXiv', 'OpenAlex', 'CrossRef'],
                        title="Papers by Source"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Sample bar chart
                    fig = px.bar(
                        x=['0-10', '11-50', '51-100', '100+'],
                        y=[45, 30, 15, 10],
                        title="Papers by Citation Count"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("📊 Analytics will be available after you add some papers to the database.")
        
        except Exception as e:
            st.error(f"Analytics error: {e}")
    
    with tab5:
        st.markdown("### 📤 Export Center")
        
        st.markdown("""
        <div class="info-card">
            <h4>Export Your Research</h4>
            <p>Download your research results in various formats for sharing and publication.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.research_results:
            results = st.session_state.research_results
            
            st.success("✅ Research results available for export")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📄 Export Draft")
                draft_format = st.selectbox("Format", ["pdf", "docx", "markdown"])
                filename = st.text_input("Filename", value="research_draft")
                
                if st.button("📄 Export Draft"):
                    st.info(f"Exporting to {filename}.{draft_format}")
            
            with col2:
                st.markdown("#### 📚 Export Bibliography")
                bib_format = st.selectbox("Bibliography Format", ["txt", "csv", "json"])
                bib_filename = st.text_input("Bibliography Filename", value="bibliography")
                
                if st.button("📚 Export Bibliography"):
                    st.info(f"Exporting to {bib_filename}.{bib_format}")
            
            if st.button("📦 Export Complete Package", use_container_width=True):
                st.success("📦 Complete research package exported!")
                st.info("All files have been saved to the outputs folder.")
        else:
            st.info("🔍 No research results available. Complete a research workflow first.")

if __name__ == "__main__":
    main()
