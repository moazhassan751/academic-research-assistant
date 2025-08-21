import streamlit as st
from dataclasses import dataclass
from typing import List

# Mock paper class for testing
@dataclass
class MockPaper:
    title: str
    authors: List[str] 
    abstract: str
    year: int
    citations: int
    venue: str
    source: str
    topic: str
    url: str

def format_paper_card_test(paper):
    """Test version of the paper card formatting"""
    authors_str = ", ".join(paper.authors[:3]) if paper.authors else "Unknown Authors"
    if paper.authors and len(paper.authors) > 3:
        authors_str += f" +{len(paper.authors) - 3} more"
    
    # Truncate abstract intelligently
    abstract = paper.abstract if paper.abstract else 'No abstract available'
    if len(abstract) > 300:
        abstract = abstract[:297] + '...'
    
    # Get paper metrics
    year = getattr(paper, 'year', 'Unknown')
    citations = getattr(paper, 'citations', 0)
    venue = getattr(paper, 'venue', getattr(paper, 'source', 'Unknown Source'))
    topic = getattr(paper, 'topic', 'General')
    
    # Create a container using Streamlit components with inline styles
    card_html = f"""
    <div style="
        background: white;
        border: 1px solid #e4e4e7;
        border-radius: 12px;
        padding: 20px;
        margin: 12px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    ">
        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
            <h4 style="color: #0369a1; margin: 0; font-weight: 600; line-height: 1.3; flex: 1;">
                {paper.title}
            </h4>
            <span style="background: #ecfdf5; color: #059669; padding: 4px 8px; border-radius: 6px; font-size: 12px; margin-left: 12px;">
                📊 {citations}
            </span>
        </div>
        
        <div style="margin-bottom: 12px;">
            <p style="margin: 8px 0; color: #4a5568;">
                <strong>👥 Authors:</strong> {authors_str}
            </p>
            <div style="display: flex; gap: 12px; margin: 8px 0;">
                <span style="color: #718096; font-size: 14px;">📅 {year}</span>
                <span style="color: #718096; font-size: 14px;">📖 {venue}</span>
            </div>
        </div>
        
        <p style="color: #4a5568; line-height: 1.5; margin: 12px 0;">
            {abstract}
        </p>
        
        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 16px;">
            <div style="display: flex; gap: 8px;">
                <span style="background: #f0f9ff; color: #0369a1; padding: 4px 8px; border-radius: 6px; font-size: 12px;">
                    🏷️ {topic}
                </span>
                <span style="background: #f4f4f5; color: #52525b; padding: 4px 8px; border-radius: 6px; font-size: 12px;">
                    🔗 {paper.source}
                </span>
            </div>
            <a href="{getattr(paper, 'url', '#')}" target="_blank" style="
                background: #0ea5e9; 
                color: white; 
                padding: 6px 12px; 
                border-radius: 6px; 
                text-decoration: none; 
                font-size: 12px;
                font-weight: 500;
            ">📖 Read</a>
        </div>
    </div>
    """
    return card_html

# Test page
st.set_page_config(page_title="Paper Card Test", layout="wide")

st.title("🧪 Paper Card Rendering Test")

# Create sample papers
sample_papers = [
    MockPaper(
        title="Global Warming versus Climate Change and the Influence of Labeling on Public Perceptions",
        authors=["Jonathon P. Schuldt", "Sarah H. Konrath", "Norbert Schwarz"],
        abstract="This study investigates how different terminology affects public perception of climate issues. We found significant differences in how people respond to the terms 'global warming' versus 'climate change' across different political affiliations.",
        year=2017,
        citations=245,
        venue="Journal of Environmental Psychology",
        source="OpenAlex",
        topic="Climate Change",
        url="https://example.com/paper1"
    ),
    MockPaper(
        title="A Survey of Global Impacts of Climate Change: Replication, Survey Methods, and a Statistical Analysis",
        authors=["William Nordhaus", "Andrew Moffat", "Robert Smith"],
        abstract="A comprehensive survey examining the global economic impacts of climate change through multiple methodological approaches and statistical analysis techniques.",
        year=2023,
        citations=156,
        venue="Nature Climate Change",
        source="CrossRef",
        topic="Climate Economics",
        url="https://example.com/paper2"
    )
]

st.markdown("### 📄 Sample Paper Cards")

for paper in sample_papers:
    st.markdown(format_paper_card_test(paper), unsafe_allow_html=True)

st.markdown("---")
st.markdown("✅ **If these cards render properly with clean styling, the fix is working!**")
st.markdown("❌ **If you still see raw HTML, there may be a deeper Streamlit configuration issue.**")
