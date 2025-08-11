# Export Features Documentation

## Overview

The Academic Research Assistant now supports multiple export formats for research drafts and bibliographies, making it easy to share and publish your research in various formats.

## Supported Export Formats

### Draft Formats
- **Markdown (.md)** - Default format, great for documentation and version control
- **PDF (.pdf)** - Professional documents, ready for sharing or publication
- **Word (.docx)** - Microsoft Office compatibility
- **LaTeX (.tex)** - Academic publishing standard
- **HTML (.html)** - Web-compatible format

### Bibliography Formats
- **Text (.txt)** - Plain text bibliography
- **CSV (.csv)** - Spreadsheet-compatible data
- **JSON (.json)** - Structured data format
- **BibTeX (.bib)** - LaTeX bibliography format

## Installation

### Required Dependencies

To use all export formats, install the required dependencies:

```bash
pip install reportlab>=4.0.0      # PDF generation
pip install python-docx>=0.8.11   # Word document generation
pip install pdfkit>=1.0.0         # HTML to PDF conversion
pip install jinja2>=3.1.0         # Template engine
```

### Quick Installation

Use the provided installation scripts:

**Linux/macOS:**
```bash
chmod +x install_export_deps.sh
./install_export_deps.sh
```

**Windows:**
```cmd
install_export_deps.bat
```

### Additional Requirements

For HTML to PDF conversion using pdfkit, you also need wkhtmltopdf:

- **Ubuntu/Debian:** `sudo apt-get install wkhtmltopdf`
- **macOS:** `brew install wkhtmltopdf`
- **Windows:** Download from https://wkhtmltopdf.org/downloads.html

## Usage

### Command Line Interface

#### Research with Export Formats

```bash
# Research with PDF and Word export
python main.py research "machine learning" --export-formats pdf docx

# Research with multiple formats
python main.py research "quantum computing" -f markdown pdf html latex

# Default formats (markdown and txt)
python main.py research "artificial intelligence"
```

#### Export Existing Results

```bash
# Export existing results to PDF
python main.py export data/outputs/Topic_20250811_123456 --export-formats pdf

# Export to multiple formats
python main.py export data/outputs/Topic_20250811_123456 -f pdf docx csv json
```

#### Check Available Formats

```bash
# Show all export formats and their availability
python main.py export-formats
```

### Interactive Mode

In interactive mode, you can check available formats:

```
research> formats
✅ Available formats: markdown, txt, json, csv, html, latex, pdf, docx
```

### Python API

```python
from src.crew.research_crew import ResearchCrew
from src.utils.export_manager import export_manager

# Initialize crew
crew = ResearchCrew()

# Check available formats
formats = crew.get_supported_export_formats()
available = crew.get_available_export_formats()

# Conduct research
results = crew.execute_research_workflow("topic")

# Save with custom export formats
output_path = crew.save_results(results, export_formats=['pdf', 'docx', 'latex'])

# Export draft separately
export_manager.export_draft(
    results['draft'], 
    "output/my_paper", 
    "pdf"
)

# Export bibliography separately
export_manager.export_bibliography(
    results['bibliography'],
    results['papers'], 
    "output/my_bibliography", 
    "bibtex"
)
```

## Export Format Details

### PDF Export
- Uses ReportLab for high-quality PDF generation
- Professional formatting with proper typography
- Includes title, abstract, sections, and references
- A4 page size with standard margins

### Word Document Export
- Creates .docx files compatible with Microsoft Word
- Maintains document structure with headings
- Supports complex formatting and styles
- Easy to edit and collaborate

### LaTeX Export
- Generates publication-ready LaTeX documents
- Includes standard academic document structure
- Properly escapes special characters
- Compatible with major LaTeX distributions

### HTML Export
- Clean, responsive web format
- Includes CSS styling for professional appearance
- Can be viewed in any web browser
- Easy to convert to other formats

### CSV Bibliography Export
- Structured data format for bibliographies
- Includes: title, authors, year, journal, DOI, URL, abstract
- Compatible with spreadsheet applications
- Easy to sort, filter, and analyze

### BibTeX Export
- Standard format for LaTeX bibliography management
- Proper citation keys and formatting
- Compatible with reference managers
- Ready for academic publishing

## Configuration

Export settings can be configured in `config.yaml`:

```yaml
export:
  default_formats: ['markdown', 'txt']
  pdf:
    page_size: 'A4'
    margins: 
      top: 72
      bottom: 72
      left: 72
      right: 72
  word:
    font_family: 'Times New Roman'
    font_size: 12
```

## Troubleshooting

### Common Issues

1. **Missing Dependencies**
   ```
   Error: Format pdf is not available (missing dependencies)
   ```
   **Solution:** Install required packages using the installation script

2. **wkhtmltopdf Not Found**
   ```
   Error: wkhtmltopdf not found
   ```
   **Solution:** Install wkhtmltopdf for your operating system

3. **Import Errors**
   ```
   Import "reportlab" could not be resolved
   ```
   **Solution:** Ensure you're in the correct Python environment and dependencies are installed

### Checking Installation

```bash
# Check available formats
python main.py export-formats

# Test export functionality
python -c "from src.utils.export_manager import export_manager; print(export_manager.get_supported_formats())"
```

## File Structure After Export

When using multiple export formats, your output directory will contain:

```
Topic_20250811_123456/
├── paper_draft.md           # Markdown (default)
├── paper_draft.pdf          # PDF export
├── paper_draft.docx         # Word export
├── paper_draft.tex          # LaTeX export
├── paper_draft.html         # HTML export
├── bibliography.txt         # Text bibliography (default)
├── bibliography.csv         # CSV bibliography
├── bibliography.json        # JSON bibliography
├── bibliography.bib         # BibTeX bibliography
├── citation_report.txt      # Citation analysis
├── papers_list.txt          # List of papers
└── research_results.json    # Complete results data
```

## Best Practices

1. **Choose appropriate formats** for your use case:
   - PDF for sharing and presentation
   - Word for collaboration and editing
   - LaTeX for academic publication
   - HTML for web publishing

2. **Install all dependencies** for maximum flexibility

3. **Use descriptive topics** as they become part of the filename

4. **Check format availability** before long research sessions

5. **Keep backups** of important research results

## Examples

### Academic Paper Workflow

```bash
# Conduct research with academic formats
python main.py research "deep learning in medical imaging" \
  --max-papers 100 \
  --paper-type survey \
  --export-formats pdf latex docx

# Export bibliography for reference manager
python main.py export data/outputs/Topic_20250811_123456 \
  --export-formats json csv
```

### Presentation Workflow

```bash
# Research for presentation
python main.py research "AI ethics" \
  --max-papers 50 \
  --export-formats pdf html

# The HTML can be easily copied to presentation slides
```

### Collaboration Workflow

```bash
# Research with collaborative formats
python main.py research "blockchain technology" \
  --export-formats docx html json

# Share the Word document for editing
# Use JSON for data analysis
# Use HTML for quick review
```
