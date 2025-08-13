# Academic Research Assistant - Integrated UI

## Overview

The **Integrated Dashboard** provides a comprehensive web-based interface for the Academic Research Assistant, fully integrated with all core research functionality including:

- **Research Workflow Management** - Complete literature surveys and paper generation
- **Q&A Assistant** - Ask questions and get answers from academic literature  
- **Paper Database** - Search and browse collected research papers
- **Analytics** - Visualize research trends and statistics
- **Export System** - Export results in multiple formats (PDF, DOCX, LaTeX, etc.)

## Features

### 🔬 Research Workflow
- **Complete Literature Survey**: Automated paper collection from ArXiv, OpenAlex, and CrossRef
- **Intelligent Analysis**: AI-powered note extraction, theme synthesis, and gap identification
- **Draft Generation**: Automatic academic paper writing with proper citations
- **Progress Tracking**: Real-time workflow status with checkpoints
- **Customizable Parameters**: Control paper limits, date ranges, and research focus

### ❓ Q&A Assistant
- **Natural Language Queries**: Ask research questions in plain English
- **Literature-Based Answers**: Responses grounded in academic papers
- **Source Attribution**: See which papers contributed to each answer
- **Confidence Scoring**: Understand the reliability of answers
- **Topic Filtering**: Focus answers on specific research areas

### 📚 Paper Database
- **Advanced Search**: Find papers by title, abstract, authors, or keywords
- **Paper Cards**: Rich display with metadata, abstracts, and source information
- **Recent Papers**: Browse recently added research papers
- **Database Statistics**: Track your research collection growth

### 📈 Analytics
- **Source Distribution**: Visualize papers by database source
- **Citation Analysis**: Understand citation patterns and impact
- **Research Trends**: Identify emerging topics and methodologies
- **Progress Metrics**: Track research productivity over time

### 📤 Export System
- **Multiple Formats**: Export to PDF, DOCX, LaTeX, Markdown, HTML, JSON, CSV
- **Complete Packages**: Export entire research projects with all components
- **Bibliography Management**: Generate formatted citations in multiple styles
- **Organized Output**: Timestamped folders with all research artifacts

## Installation & Setup

### Prerequisites
```bash
# Required Python packages
pip install streamlit plotly pandas
pip install -r requirements.txt

# Optional export dependencies
pip install reportlab python-docx pdfkit
```

### Quick Start

#### Windows
```cmd
# From project root directory
launch_integrated_dashboard.bat
```

#### Linux/macOS
```bash
# From project root directory
chmod +x launch_integrated_dashboard.sh
./launch_integrated_dashboard.sh
```

#### Manual Launch
```bash
# From project root directory
streamlit run integrated_dashboard.py --server.port 8501
```

## Usage Guide

### 1. Research Workflow

1. **Navigate to "Research Workflow" tab**
2. **Enter Research Topic**: Specify your main research area
3. **Configure Parameters**:
   - Maximum papers to collect (10-200)
   - Paper type (survey, review, analysis)
   - Specific aspects to focus on
   - Date range for papers
4. **Start Workflow**: Click "Start Research Workflow"
5. **Monitor Progress**: Watch real-time status updates
6. **Review Results**: Examine generated draft and statistics

### 2. Q&A Assistant

1. **Navigate to "Q&A Assistant" tab**
2. **Enter Question**: Ask about any research topic
3. **Set Filters** (optional):
   - Topic filter for focused answers
   - Maximum papers to consider
4. **Get Answer**: Click "Get Answer" for literature-based response
5. **Review Sources**: Check which papers informed the answer

### 3. Paper Database

1. **Navigate to "Paper Database" tab**
2. **Search Papers**: Enter keywords to find specific papers
3. **Browse Results**: Review paper cards with detailed information
4. **Recent Papers**: See recently added papers to your database

### 4. Analytics

1. **Navigate to "Analytics" tab**
2. **View Statistics**: See overall database statistics
3. **Analyze Trends**: Examine charts and visualizations
4. **Source Distribution**: Understand your paper collection composition

### 5. Export Results

1. **Complete Research Workflow** first
2. **Navigate to "Export Results" tab**
3. **Choose Export Options**:
   - **Draft Export**: Select format and filename
   - **Bibliography Export**: Choose citation format
   - **Complete Package**: Export everything together
4. **Download Files**: Access exported files in `data/outputs/`

## Configuration

### Environment Setup
The dashboard automatically detects your configuration:
- **LLM Provider**: OpenAI, Gemini, or other configured providers
- **API Keys**: Loaded from environment variables or config files
- **Database**: SQLite database for paper storage
- **Export Formats**: Available based on installed dependencies

### Customization
Modify `integrated_dashboard.py` to customize:
- **UI Styling**: Edit CSS in the markdown sections
- **Default Parameters**: Change default values for forms
- **Export Options**: Add new format support
- **Analytics**: Implement custom visualizations

## Troubleshooting

### Common Issues

**Import Errors**
```bash
# Ensure you're in the project root directory
cd /path/to/academic-research-assistant

# Check Python path
python -c "import sys; print('\\n'.join(sys.path))"

# Install missing dependencies
pip install -r requirements.txt
```

**Database Connection Issues**
```bash
# Check database file permissions
ls -la data/research.db

# Reset database if corrupted
python -c "from src.storage.database import db; db.init_database()"
```

**Export Format Not Available**
```bash
# Install export dependencies
pip install reportlab python-docx pdfkit

# For PDF export via pdfkit, install wkhtmltopdf:
# Ubuntu/Debian: apt-get install wkhtmltopdf
# macOS: brew install wkhtmltopdf
# Windows: Download from wkhtmltopdf.org
```

**LLM Connection Issues**
```bash
# Check API keys
echo $OPENAI_API_KEY
echo $GEMINI_API_KEY

# Verify configuration
python -c "from src.utils.config import config; print(config.llm_config)"
```

### Performance Optimization

**Large Datasets**
- Use search filters to limit results
- Adjust `max_papers` parameter for workflows
- Enable caching for better performance

**Memory Management**
- Close unused browser tabs
- Restart dashboard for long sessions
- Monitor system resources

## Advanced Features

### Custom Workflows
Extend the dashboard by adding custom research workflows:

```python
# Add to integrated_dashboard.py
def custom_research_workflow(topic, parameters):
    """Implement your custom research logic"""
    # Your implementation here
    pass
```

### Plugin Integration
The dashboard supports integration with additional tools:
- Citation managers (Zotero, Mendeley)
- Document processors
- Visualization libraries
- External APIs

### Batch Processing
For large-scale research projects:
- Use the command-line interface for batch operations
- Export results programmatically
- Automate workflows with scripts

## API Reference

### Core Components

**ResearchCrew**
```python
crew = ResearchCrew()
results = crew.execute_research_workflow(
    research_topic="Machine Learning",
    max_papers=50,
    paper_type="survey"
)
```

**QuestionAnsweringAgent**
```python
qa_agent = QuestionAnsweringAgent()
answer = qa_agent.answer_question(
    question="What are the challenges in deep learning?",
    paper_limit=10
)
```

**Export Manager**
```python
from src.utils.export_manager import export_manager
success = export_manager.export_draft(
    draft_data, 
    "output_path", 
    "pdf"
)
```

## Support & Contribution

### Getting Help
- Check the troubleshooting section above
- Review log files in `logs/` directory
- Examine configuration in `config.yaml`

### Contributing
To contribute to the integrated dashboard:
1. Fork the repository
2. Create feature branch
3. Add your improvements
4. Submit pull request

### Feedback
Report issues or suggest features:
- Use the project's issue tracker
- Include error logs and system information
- Describe expected vs actual behavior

## Security & Privacy

### Data Protection
- All research data stored locally
- No data transmitted to third parties
- API keys secured through environment variables

### Best Practices
- Regularly backup your database
- Keep API keys secure
- Update dependencies regularly
- Monitor system resources

---

*The Integrated Dashboard represents the complete Academic Research Assistant experience, bringing together all research capabilities in a user-friendly web interface.*
