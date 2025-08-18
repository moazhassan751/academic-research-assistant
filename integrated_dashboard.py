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

# Import the actual research functionality
RESEARCH_AVAILABLE = False
import_errors = []

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

# Configure Streamlit page
st.set_page_config(
    page_title="Academic Research Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize logging
if RESEARCH_AVAILABLE:
    setup_logging('INFO')

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1e3a8a;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    .metric-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .search-container {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    
    .paper-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        transition: transform 0.2s ease;
    }
    
    .paper-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
    
    .sidebar-container {
        background: linear-gradient(180deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
    }
    
    .status-success {
        background: #10b981;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    
    .status-processing {
        background: #f59e0b;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    
    .status-error {
        background: #ef4444;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    
    .export-button {
        background: linear-gradient(45deg, #10b981, #059669);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        cursor: pointer;
        margin: 0.25rem;
        transition: all 0.3s ease;
    }
    
    .export-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4);
    }
    
    .filter-section {
        background: #f1f5f9;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .qa-section {
        background: #eff6ff;
        border: 2px solid #3b82f6;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .workflow-status {
        background: #fefefe;
        border-left: 4px solid #3b82f6;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'research_crew' not in st.session_state and RESEARCH_AVAILABLE:
    try:
        st.session_state.research_crew = ResearchCrew()
        st.session_state.qa_agent = QuestionAnsweringAgent()
    except Exception as e:
        st.error(f"Failed to initialize research crew: {e}")
        st.session_state.research_crew = None
        st.session_state.qa_agent = None

if 'research_results' not in st.session_state:
    st.session_state.research_results = None

if 'current_workflow_status' not in st.session_state:
    st.session_state.current_workflow_status = None

# Helper functions
@st.cache_data
def get_database_stats():
    """Get current database statistics"""
    if not RESEARCH_AVAILABLE:
        return {'papers': 0, 'notes': 0, 'themes': 0, 'citations': 0}
    
    try:
        return db.get_stats()
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        return {'papers': 0, 'notes': 0, 'themes': 0, 'citations': 0}

@st.cache_data
def get_recent_papers(limit: int = 10):
    """Get recently added papers from database"""
    if not RESEARCH_AVAILABLE:
        return []
    
    try:
        return db.get_recent_papers(limit)
    except Exception as e:
        logger.error(f"Error getting recent papers: {e}")
        return []

def format_paper_card(paper):
    """Format a paper as a card display"""
    authors_str = ", ".join(paper.authors[:3]) if paper.authors else "Unknown Authors"
    if paper.authors and len(paper.authors) > 3:
        authors_str += " et al."
    
    # Create the card HTML
    card_html = f"""
    <div class="paper-card">
        <h4 style="color: #1e40af; margin-bottom: 0.5rem;">{paper.title}</h4>
        <p style="color: #6b7280; margin-bottom: 0.5rem;"><strong>Authors:</strong> {authors_str}</p>
        <p style="color: #6b7280; margin-bottom: 0.5rem;"><strong>Year:</strong> {getattr(paper, 'year', 'Unknown')}</p>
        <p style="color: #6b7280; margin-bottom: 0.5rem;"><strong>Citations:</strong> {getattr(paper, 'citations', 0)}</p>
        <p style="color: #374151; font-size: 0.9rem;">{paper.abstract[:200] if paper.abstract else 'No abstract available'}...</p>
        <div style="margin-top: 1rem;">
            <span style="background: #e0f2fe; color: #0277bd; padding: 0.25rem 0.5rem; border-radius: 15px; font-size: 0.8rem; margin-right: 0.5rem;">
                {getattr(paper, 'venue', getattr(paper, 'source', 'Unknown Source'))}
            </span>
            <span style="background: #f3e5f5; color: #7b1fa2; padding: 0.25rem 0.5rem; border-radius: 15px; font-size: 0.8rem;">
                {getattr(paper, 'topic', 'General')}
            </span>
        </div>
    </div>
    """
    return card_html

def progress_callback(step: int, description: str):
    """Callback function for research workflow progress"""
    st.session_state.current_workflow_status = {
        'step': step,
        'description': description,
        'timestamp': datetime.now()
    }

# Main application
def main():
    # Header
    st.markdown('<div class="main-header">🎓 Academic Research Assistant</div>', unsafe_allow_html=True)
    
    if not RESEARCH_AVAILABLE:
        st.error("Research functionality is not available. Please check your installation and dependencies.")
        st.info("Make sure you're running from the project root directory and all dependencies are installed.")
        return
    
    # Sidebar configuration
    with st.sidebar:
        st.markdown('<div class="sidebar-container">', unsafe_allow_html=True)
        st.markdown("### 🔧 Configuration")
        
        # Display current configuration
        try:
            env = config.environment
            llm_config = config.llm_config
            
            st.info(f"**Environment:** {env}")
            st.info(f"**LLM Provider:** {llm_config.get('provider', 'Unknown')}")
            st.info(f"**Model:** {llm_config.get('model', 'Unknown')}")
            
            # Check available export formats
            if st.session_state.research_crew:
                available_formats = st.session_state.research_crew.get_available_export_formats()
                st.success(f"**Export Formats:** {', '.join(available_formats)}")
        except Exception as e:
            st.error(f"Configuration error: {e}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("### 📊 Database Statistics")
        stats = get_database_stats()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Papers", stats.get('papers', 0))
            st.metric("Themes", stats.get('themes', 0))
        with col2:
            st.metric("Notes", stats.get('notes', 0))
            st.metric("Citations", stats.get('citations', 0))
    
    # Main content area with tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔍 Research Workflow", 
        "❓ Q&A Assistant", 
        "📚 Paper Database", 
        "📈 Analytics", 
        "📤 Export Results"
    ])
    
    # Tab 1: Research Workflow
    with tab1:
        st.markdown("### 🔬 Start New Research")
        
        # Research form
        with st.form("research_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                research_topic = st.text_input(
                    "Research Topic*",
                    placeholder="e.g., Machine Learning for Healthcare",
                    help="Enter the main research topic you want to investigate"
                )
                
                max_papers = st.slider(
                    "Maximum Papers",
                    min_value=10,
                    max_value=200,
                    value=50,
                    help="Maximum number of papers to collect and analyze"
                )
                
                paper_type = st.selectbox(
                    "Paper Type",
                    ["survey", "review", "analysis", "systematic_review"],
                    help="Type of paper to generate"
                )
            
            with col2:
                specific_aspects = st.text_area(
                    "Specific Aspects (Optional)",
                    placeholder="Enter specific aspects to focus on, one per line",
                    help="Specific sub-topics or aspects to focus the research on"
                )
                
                date_from = st.date_input(
                    "Papers From Date (Optional)",
                    value=None,
                    help="Only include papers published after this date"
                )
                
                resume_checkpoint = st.checkbox(
                    "Resume from Checkpoint",
                    value=True,
                    help="Resume from saved checkpoints if available"
                )
            
            submit_button = st.form_submit_button("🚀 Start Research Workflow", use_container_width=True)
        
        # Execute research workflow
        if submit_button and research_topic and st.session_state.research_crew:
            # Parse specific aspects
            aspects_list = []
            if specific_aspects:
                aspects_list = [aspect.strip() for aspect in specific_aspects.split('\n') if aspect.strip()]
            
            # Convert date
            date_from_dt = datetime.combine(date_from, datetime.min.time()) if date_from else None
            
            st.markdown("### 🔄 Research Workflow Progress")
            
            # Progress tracking
            progress_bar = st.progress(0)
            status_container = st.empty()
            
            try:
                with st.spinner("Initializing research workflow..."):
                    # Execute the research workflow
                    def update_progress(step: int, description: str):
                        progress_value = min(step * 0.2, 1.0)  # 5 steps total
                        progress_bar.progress(progress_value)
                        status_container.markdown(f"""
                        <div class="workflow-status">
                            <strong>Step {step}/5:</strong> {description}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Run the research workflow
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
                    progress_bar.progress(1.0)
                    
                    if results['success']:
                        st.success("✅ Research workflow completed successfully!")
                        
                        # Display results summary
                        st.markdown("### 📊 Research Summary")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Papers Analyzed", results['statistics']['papers_found'])
                        with col2:
                            st.metric("Notes Extracted", results['statistics']['notes_extracted'])
                        with col3:
                            st.metric("Themes Identified", results['statistics']['themes_identified'])
                        with col4:
                            st.metric("Citations Generated", results['statistics']['citations_generated'])
                        
                        # Show execution time
                        st.info(f"⏱️ **Execution Time:** {results['execution_time']}")
                        
                        # Display draft preview
                        st.markdown("### 📝 Paper Draft Preview")
                        if 'draft' in results and results['draft']:
                            draft = results['draft']
                            
                            # Show abstract
                            if 'abstract' in draft:
                                st.markdown("**Abstract:**")
                                st.markdown(draft['abstract'])
                            
                            # Show sections overview
                            if 'sections' in draft:
                                st.markdown("**Sections:**")
                                for section_name in draft['sections'].keys():
                                    st.markdown(f"- {section_name.replace('_', ' ').title()}")
                    else:
                        st.error(f"❌ Research workflow failed: {results.get('error', 'Unknown error')}")
                        
            except Exception as e:
                st.error(f"❌ Error during research workflow: {str(e)}")
                logger.error(f"Research workflow error: {e}", exc_info=True)
    
    # Tab 2: Q&A Assistant
    with tab2:
        st.markdown("### ❓ Research Q&A Assistant")
        st.markdown("Ask questions about your research or any academic topic!")
        
        # Q&A interface
        question = st.text_area(
            "Your Question",
            placeholder="e.g., What are the main challenges in machine learning for healthcare?",
            help="Ask any research question and get answers based on academic literature"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            qa_topic_filter = st.text_input(
                "Topic Filter (Optional)",
                placeholder="e.g., machine learning",
                help="Filter papers by topic for more focused answers"
            )
        with col2:
            qa_paper_limit = st.slider(
                "Max Papers to Consider",
                min_value=5,
                max_value=50,
                value=10,
                help="Maximum number of papers to use for answering"
            )
        
        if st.button("🤔 Get Answer", use_container_width=True) and question and st.session_state.qa_agent:
            with st.spinner("Searching literature and generating answer..."):
                try:
                    answer_result = st.session_state.qa_agent.answer_question(
                        question=question,
                        research_topic=qa_topic_filter if qa_topic_filter else None,
                        paper_limit=qa_paper_limit
                    )
                    
                    if answer_result['confidence'] > 0:
                        st.markdown('<div class="qa-section">', unsafe_allow_html=True)
                        
                        # Display answer
                        st.markdown("### 📝 Answer")
                        st.markdown(answer_result['answer'])
                        
                        # Display metadata
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Confidence", f"{answer_result.get('confidence', 0.0):.2f}")
                        with col2:
                            st.metric("Papers Used", answer_result.get('paper_count', 0))
                        with col3:
                            st.metric("Top Papers", answer_result.get('top_papers_used', 0))
                        
                        # Display sources if available
                        if 'sources' in answer_result and answer_result['sources']:
                            st.markdown("### 📚 Sources")
                            for i, source in enumerate(answer_result['sources'][:5], 1):
                                st.markdown(f"{i}. {source}")
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                    else:
                        st.warning("⚠️ Could not find sufficient information to answer your question.")
                        st.info("Try rephrasing your question or using different keywords.")
                        
                except Exception as e:
                    st.error(f"❌ Error processing question: {str(e)}")
                    logger.error(f"Q&A error: {e}", exc_info=True)
    
    # Tab 3: Paper Database
    with tab3:
        st.markdown("### 📚 Paper Database")
        
        # Search interface
        col1, col2 = st.columns([3, 1])
        with col1:
            search_query = st.text_input(
                "Search Papers",
                placeholder="Enter keywords to search papers in database",
                help="Search by title, abstract, authors, or keywords"
            )
        with col2:
            search_limit = st.selectbox("Results", [10, 25, 50, 100], index=1)
        
        if search_query:
            try:
                search_results = db.search_papers(search_query, limit=search_limit)
                
                if search_results:
                    st.success(f"Found {len(search_results)} papers")
                    
                    # Display papers
                    for paper in search_results:
                        st.markdown(format_paper_card(paper), unsafe_allow_html=True)
                else:
                    st.warning("No papers found matching your search.")
            except Exception as e:
                st.error(f"Search error: {e}")
        else:
            # Show recent papers
            st.markdown("### 📈 Recently Added Papers")
            recent_papers = get_recent_papers(10)
            
            if recent_papers:
                for paper in recent_papers:
                    st.markdown(format_paper_card(paper), unsafe_allow_html=True)
            else:
                st.info("No papers in database yet. Run a research workflow to populate the database.")
    
    # Tab 4: Analytics
    with tab4:
        st.markdown("### 📈 Research Analytics")
        
        try:
            stats = get_database_stats()
            
            if stats['papers'] > 0:
                # Basic statistics
                col1, col2 = st.columns(2)
                
                with col1:
                    # Papers over time (mock visualization)
                    st.markdown("#### 📊 Papers by Source")
                    # This would need actual data from database
                    source_data = {"ArXiv": 40, "OpenAlex": 35, "CrossRef": 25}
                    fig_sources = px.pie(
                        values=list(source_data.values()),
                        names=list(source_data.keys()),
                        title="Distribution of Papers by Source"
                    )
                    st.plotly_chart(fig_sources, use_container_width=True)
                
                with col2:
                    # Citation distribution
                    st.markdown("#### 📈 Citation Analysis")
                    # This would show actual citation data
                    citation_ranges = ["0-10", "11-50", "51-100", "100+"]
                    citation_counts = [45, 30, 15, 10]
                    
                    fig_citations = px.bar(
                        x=citation_ranges,
                        y=citation_counts,
                        title="Papers by Citation Count",
                        labels={'x': 'Citation Range', 'y': 'Number of Papers'}
                    )
                    st.plotly_chart(fig_citations, use_container_width=True)
                
                # Research trends
                st.markdown("#### 🔍 Research Trends")
                # This would show actual trend data from the database
                st.info("Advanced analytics features will be displayed here based on your research data.")
                
            else:
                st.info("📊 Analytics will be available after you conduct some research.")
                
        except Exception as e:
            st.error(f"Analytics error: {e}")
    
    # Tab 5: Export Results
    with tab5:
        st.markdown("### 📤 Export Research Results")
        
        if st.session_state.research_results:
            results = st.session_state.research_results
            
            st.success("✅ Research results available for export!")
            
            # Export options
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📄 Export Draft")
                
                available_formats = st.session_state.research_crew.get_available_export_formats()
                draft_format = st.selectbox(
                    "Draft Format",
                    available_formats,
                    help="Choose format for exporting the research draft"
                )
                
                draft_filename = st.text_input(
                    "Draft Filename",
                    value=f"{results['research_topic'].replace(' ', '_')}_draft",
                    help="Filename without extension"
                )
                
                if st.button("📄 Export Draft", use_container_width=True):
                    try:
                        # Create output directory
                        output_dir = Path("data/outputs") / f"{results['research_topic'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        output_dir.mkdir(parents=True, exist_ok=True)
                        
                        # Export draft
                        output_path = output_dir / draft_filename
                        success = export_manager.export_draft(
                            results['draft'],
                            str(output_path),
                            draft_format
                        )
                        
                        if success:
                            st.success(f"✅ Draft exported successfully to: {output_path}.{draft_format}")
                        else:
                            st.error("❌ Failed to export draft")
                            
                    except Exception as e:
                        st.error(f"Export error: {e}")
            
            with col2:
                st.markdown("#### 📚 Export Bibliography")
                
                bib_format = st.selectbox(
                    "Bibliography Format",
                    ["txt", "csv", "json", "latex", "pdf", "docx"],
                    help="Choose format for exporting the bibliography"
                )
                
                bib_filename = st.text_input(
                    "Bibliography Filename",
                    value=f"{results['research_topic'].replace(' ', '_')}_bibliography",
                    help="Filename without extension"
                )
                
                if st.button("📚 Export Bibliography", use_container_width=True):
                    try:
                        # Create output directory
                        output_dir = Path("data/outputs") / f"{results['research_topic'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        output_dir.mkdir(parents=True, exist_ok=True)
                        
                        # Export bibliography
                        output_path = output_dir / bib_filename
                        success = export_manager.export_bibliography(
                            results.get('bibliography', ''),
                            results.get('papers', []),
                            str(output_path),
                            bib_format
                        )
                        
                        if success:
                            st.success(f"✅ Bibliography exported successfully to: {output_path}.{bib_format}")
                        else:
                            st.error("❌ Failed to export bibliography")
                            
                    except Exception as e:
                        st.error(f"Export error: {e}")
            
            # Complete export package
            st.markdown("#### 📦 Complete Export Package")
            st.info("Export all research results including draft, bibliography, notes, and themes.")
            
            if st.button("📦 Export Complete Package", use_container_width=True):
                try:
                    # Create timestamped output directory
                    output_dir = Path("data/outputs") / f"{results['research_topic'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    output_dir.mkdir(parents=True, exist_ok=True)
                    
                    exported_files = []
                    
                    # Export draft in multiple formats
                    for fmt in ['markdown', 'pdf', 'docx']:
                        if fmt in available_formats:
                            draft_path = output_dir / f"paper_draft"
                            if export_manager.export_draft(results['draft'], str(draft_path), fmt):
                                exported_files.append(f"paper_draft.{fmt}")
                    
                    # Export bibliography
                    bib_path = output_dir / f"bibliography"
                    if export_manager.export_bibliography(
                        results.get('bibliography', ''),
                        results.get('papers', []),
                        str(bib_path),
                        'txt'
                    ):
                        exported_files.append("bibliography.txt")
                    
                    # Export raw data as JSON
                    json_path = output_dir / "research_results.json"
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(results, f, indent=2, default=str)
                    exported_files.append("research_results.json")
                    
                    # Create papers list
                    papers_path = output_dir / "papers_list.txt"
                    with open(papers_path, 'w', encoding='utf-8') as f:
                        for i, paper in enumerate(results.get('papers', []), 1):
                            f.write(f"{i}. {paper.title}\n")
                            f.write(f"   Authors: {', '.join(paper.authors) if paper.authors else 'Unknown'}\n")
                            f.write(f"   Year: {getattr(paper, 'year', 'Unknown')}\n")
                            f.write(f"   Source: {paper.source}\n\n")
                    exported_files.append("papers_list.txt")
                    
                    st.success(f"✅ Complete package exported to: {output_dir}")
                    st.info(f"📁 Files exported: {', '.join(exported_files)}")
                    
                except Exception as e:
                    st.error(f"Package export error: {e}")
        else:
            st.info("🔍 No research results available. Complete a research workflow first.")

if __name__ == "__main__":
    main()

