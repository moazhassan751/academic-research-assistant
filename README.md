# Academic Research Assistant

AI-based multi-agent system for academic research with comprehensive export capabilities.

## ✨ New Export Features

The Academic Research Assistant now supports multiple export formats for research drafts and bibliographies:

- **📄 PDF** - Professional documents ready for sharing
- **📝 Word (DOCX)** - Microsoft Office compatibility  
- **📐 LaTeX** - Academic publishing standard
- **🌐 HTML** - Web-compatible format
- **📊 CSV** - Spreadsheet-compatible bibliography data
- **🔗 BibTeX** - LaTeX bibliography format
- **📋 JSON** - Structured data format

### Quick Start with Export

```bash
# Research with PDF and Word export
python main.py research "machine learning" --export-formats pdf docx

# Export existing results to different formats
python main.py export data/outputs/Topic_20250811_123456 --export-formats pdf

# Check available export formats
python main.py export-formats
```

### Installation for Export Features

```bash
# Install export dependencies
pip install reportlab python-docx pdfkit jinja2

# Or use the provided installation script
./install_export_deps.sh  # Linux/macOS
install_export_deps.bat   # Windows
```

For complete export documentation, see [EXPORT_FEATURES.md](EXPORT_FEATURES.md).

## Features

- Multi-agent research workflow
- Academic database integration (OpenAlex, CrossRef, ArXiv, Semantic Scholar)
- Intelligent literature survey and synthesis
- Citation generation and formatting
- **Multiple export formats** for drafts and bibliographies
- Interactive research sessions
- Progress tracking and checkpoints
