# 📚 Academic Research Assistant

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A powerful AI-driven multi-agent system designed to streamline academic research by automating literature surveys, generating research drafts, and providing intelligent Q&A with advanced export capabilities.

---

## 🎯 Overview

The **Academic Research Assistant** is an all-in-one platform that leverages coordinated AI agents to simplify and enhance the academic research process. From literature discovery to document generation, this tool empowers researchers with cutting-edge technology.

### ✨ Key Features
- **🔍 Comprehensive Literature Discovery**: Retrieve papers from ArXiv, OpenAlex, CrossRef, and Semantic Scholar.
- **🤖 AI-Powered Analysis**: Utilize advanced semantic search and content analysis with large language models (LLMs).
- **📝 Automated Draft Generation**: Synthesize research findings into structured, professional documents.
- **💬 Interactive Q&A**: Ask questions about your research corpus and receive detailed, cited answers.
- **📄 Professional Exports**: Export to PDF, Word, LaTeX, and other formats for seamless sharing.
- **🔄 Reproducible Research**: Version control and session checkpoints for consistent workflows.

---

## 🏗️ System Architecture

```
academic_research_assistant/
├── 📂 src/                    # Core application source code
│   ├── 🤖 agents/            # Specialized AI agents
│   │   ├── literature_survey_agent.py    # Literature discovery and analysis
│   │   ├── qa_agent.py                   # Enhanced Q&A with semantic search
│   │   ├── note_taking_agent.py          # Research note organization
│   │   ├── theme_synthesizer_agent.py    # Content synthesis and theme extraction
│   │   ├── draft_writer_agent.py         # Document generation
│   │   └── citation_generator_agent.py   # Citation formatting
│   ├── 🎯 crew/              # Agent orchestration and workflows
│   │   └── research_crew.py              # Main crew coordination
│   ├── 💾 storage/           # Data persistence layer
│   │   ├── database.py                   # SQLite database management
│   │   └── models.py                     # Data models and schemas
│   ├── 🔧 tools/             # External API integrations
│   │   ├── arxiv_tool.py                 # ArXiv API client
│   │   ├── open_alex_tool.py             # OpenAlex integration
│   │   ├── cross_ref_tool.py             # CrossRef API client
│   │   ├── semantic_scholar_tool.py      # Semantic Scholar client
│   │   └── pdf_processor.py              # PDF text extraction
│   └── ⚙️ utils/             # Utility functions and helpers
│       ├── config.py                     # Configuration management
│       ├── export_manager.py             # Export functionality
│       ├── error_handler.py              # Error handling system
│       └── async_api_manager.py          # Async API management
├── 🧪 tests/                 # Comprehensive test suite
├── 📚 docs/                  # Detailed documentation
├── 🔧 scripts/               # Installation and utility scripts
├── ⚙️ config_backups/        # Configuration backups
├── 💽 data/                  # Research data and outputs
├── 📋 logs/                  # Application logs and debugging
└── 🚀 main.py                # CLI entry point
```

---

## 💡 Enhanced Q&A System

The advanced Q&A agent delivers intelligent, context-aware answers with cutting-edge features:

### 🧠 Semantic Search Engine
- **Sentence Embeddings**: Leverages transformer models for deep semantic understanding.
- **Vector Similarity**: Uses cosine similarity for precise paper matching.
- **Context Awareness**: Recognizes research domain and question intent.

### 🔍 Intelligent Question Classification
- **Question Types**: Automatically categorizes questions (e.g., comparisons, trends, challenges).
- **Adaptive Responses**: Tailors answers based on question type and context.
- **Domain Recognition**: Understands academic terminology for accurate responses.

### ⚡ Performance Optimization
- **Smart Caching**: Uses TTL-based caching for faster responses.
- **Parallel Processing**: Analyzes papers concurrently for improved speed.
- **BM25 Scoring**: Implements advanced relevance ranking algorithms.
- **Result Optimization**: Configurable limits and relevance thresholds.

### 📊 Advanced Analytics
- **Confidence Scoring**: Provides quantitative confidence metrics for answers.
- **Source Attribution**: Includes detailed citations with relevance scores.
- **Follow-up Suggestions**: Generates AI-driven related questions.
- **Performance Metrics**: Tracks response time and quality analytics.

---

## 📄 Export & Documentation

Create professional-grade research outputs with flexible export options:

### 📝 Supported Document Formats
- **PDF**: Publication-ready documents with professional formatting.
- **Word (DOCX)**: Compatible with Microsoft Office, including styles.
- **LaTeX**: Academic publishing standard with BibTeX support.
- **HTML**: Web-ready documents with responsive design.
- **Markdown**: Universal format for documentation platforms.

### 📚 Bibliography Management
- **BibTeX**: LaTeX-compatible citation format.
- **CSV**: Spreadsheet-compatible reference data.
- **JSON**: Structured data for programmatic access.
- **Custom Formats**: Extensible system for additional formats.

### 🎨 Professional Styling
- **Academic Templates**: Pre-configured layouts for various document types.
- **Citation Styles**: Supports APA, MLA, Chicago, IEEE, and custom formats.
- **Responsive Design**: Optimized for digital and print media.
- **Branding Support**: Customizable headers, footers, and styling.

---

## 🚀 Installation & Setup

### 📋 Prerequisites
- **Python 3.12+**: Latest Python version recommended.
- **pip**: Python package manager.
- **Git**: For version control (development).
- **4GB+ RAM**: For optimal performance with large datasets.

### ⚙️ Quick Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/moazhassan751/academic-research-assistant.git
   cd academic-research-assistant
   ```

2. **Install Core Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Enhanced Q&A Features**
   ```bash
   # Windows
   scripts\install_enhanced_qa.bat

   # Unix/Linux/macOS
   bash scripts/install_enhanced_qa.sh

   # Manual installation
   pip install sentence-transformers scikit-learn rank-bm25 torch
   ```

4. **Install Export Dependencies** (Optional)
   ```bash
   # Windows
   scripts\install_export_deps.bat

   # Unix/Linux/macOS
   bash scripts/install_export_deps.sh
   ```

5. **Configure Environment**
   ```bash
   # Copy environment template
   cp .env.example .env

   # Edit .env with your API keys
   nano .env  # or use your preferred editor
   ```

### 🔧 Environment Configuration

Add the following to your `.env` file:

```bash
# Required for AI features
GEMINI_API_KEY=your_gemini_api_key_here

# Required for better API rate limits
OPENALEX_EMAIL=your_email@example.com

# Optional for additional LLM support
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Database configuration
DATABASE_PATH=data/research.db

# Logging configuration
LOG_LEVEL=INFO
LOG_TO_FILE=true
```

---

## 🎮 Usage Guide

### 🔍 Basic Research Workflow

1. **Conduct Literature Survey**
   ```bash
   # Basic research on a topic
   python main.py research "machine learning in healthcare"

   # Advanced research with specific parameters
   python main.py research "quantum computing" --papers 50 --depth comprehensive

   # Research with immediate export
   python main.py research "climate change" --export-formats pdf docx --save-session
   ```

2. **Interactive Q&A Session**
   ```bash
   # Ask questions about your research corpus
   python main.py ask "What are the main challenges in deep learning?"

   # Ask with specific context
   python main.py ask "Compare neural networks vs traditional ML" --topic "machine learning"

   # Enhanced Q&A with detailed analysis
   python main.py ask "Latest trends in AI" --enhanced --limit 15 --confidence-threshold 0.8
   ```

3. **Export and Documentation**
   ```bash
   # Export research to multiple formats
   python main.py export data/outputs/Topic_20250812_123456 --formats pdf docx latex

   # Create bibliography in specific format
   python main.py bibliography --format bibtex --output references.bib

   # Generate comprehensive report
   python main.py report --template academic --style apa --include-appendix
   ```

### 🛠️ Advanced Features

4. **Session Management**
   ```bash
   # List saved research sessions
   python main.py sessions list

   # Resume previous session
   python main.py sessions resume session_20250812_123456

   # Export session data
   python main.py sessions export session_20250812_123456 --format json
   ```

5. **Database Operations**
   ```bash
   # View database statistics
   python main.py db stats

   # Search existing papers
   python main.py db search "neural networks" --limit 20

   # Clean and optimize database
   python main.py db optimize
   ```

6. **Configuration Management**
   ```bash
   # View current configuration
   python main.py config show

   # Update configuration
   python main.py config set research.max_papers 100

   # Reset to defaults
   python main.py config reset
   ```

---

## 📊 API Integrations

The system connects to leading academic databases and AI services:

### 🔍 Literature Sources
- **ArXiv**: Pre-print papers in physics, mathematics, and computer science.
- **OpenAlex**: 200M+ academic works with comprehensive metadata.
- **CrossRef**: DOI resolution and scholarly content metadata.
- **Semantic Scholar**: AI-powered search with paper insights.

### 🤖 AI Language Models
- **Google Gemini**: Primary LLM for content generation and analysis.
- **OpenAI GPT**: Optional support for specific tasks.
- **Anthropic Claude**: Additional LLM for complex reasoning.

### 📄 Export Services
- **LaTeX Compilation**: Professional document generation.
- **PDF Generation**: High-quality rendering for publications.
- **Cloud Storage**: Optional integration with cloud services.

---

## 🧪 Testing & Quality Assurance

### 📂 Test Suite Structure
```
tests/
├── test_agents/              # Agent-specific tests
├── test_integration/         # End-to-end workflow tests
├── test_api/                 # External API integration tests
├── test_export/              # Export functionality tests
├── test_database/            # Database operation tests
└── test_performance/         # Performance and load tests
```

### ✅ Running Tests
```bash
# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/test_agents/ -v
pytest tests/test_integration/ -v

# Run with coverage report
pytest tests/ --cov=src --cov-report=html

# Performance benchmarks
pytest tests/test_performance/ --benchmark-only
```

---

## 🔧 Configuration

### ⚙️ Main Configuration (`config.yaml`)
```yaml
# Research settings
research:
  max_papers: 50
  search_depth: "comprehensive"
  prefer_recent: true
  min_relevance_score: 0.3

# Q&A system configuration
qa:
  use_semantic_embeddings: true
  enable_caching: true
  max_context_length: 8000
  confidence_threshold: 0.5

# Export settings
export:
  default_format: "pdf"
  include_bibliography: true
  citation_style: "apa"

# Database settings
database:
  auto_backup: true
  cleanup_interval: "7d"
  max_cache_size: "1GB"
```

### 🛠️ Advanced Configuration
- **API Rate Limiting**: Configure throttling for external services.
- **Caching Strategy**: Customize cache behavior and storage limits.
- **Export Templates**: Define custom document templates and styles.
- **Agent Behavior**: Fine-tune individual agent parameters.
- **Logging Options**: Enable detailed logging for debugging.

---

## 🤝 Contributing

We welcome contributions from researchers and developers!

### 🚀 Development Setup
```bash
# Clone the development branch
git clone -b develop https://github.com/moazhassan751/academic-research-assistant.git

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run development server
python main.py --dev-mode
```

### 📋 Contribution Guidelines
1. **Fork the Repository**: Create your own fork for contributions.
2. **Create Feature Branch**: Use descriptive names (e.g., `feature/enhanced-search`).
3. **Write Tests**: Ensure comprehensive test coverage for new features.
4. **Follow Code Style**: Adhere to Black formatting and PEP 8 guidelines.
5. **Update Documentation**: Include documentation for new features.
6. **Submit Pull Request**: Provide a detailed description of changes.

### 🌟 Areas for Contribution
- **New Literature Sources**: Add support for additional academic databases.
- **Export Formats**: Implement new document export options.
- **Language Models**: Integrate additional AI model providers.
- **UI/UX Improvements**: Enhance the command-line interface.
- **Performance Optimization**: Improve speed and resource efficiency.

---

## 📋 Roadmap

### 🗓️ Version 2.0 (Q3 2025)
- **🌐 Web Interface**: Browser-based research dashboard.
- **👥 Collaboration Features**: Multi-user research sessions.
- **📊 Advanced Analytics**: Research trend analysis and insights.
- **🔗 Plugin System**: Extensible architecture for custom tools.

### 🗓️ Version 2.1 (Q4 2025)
- **📱 Mobile Support**: Cross-platform mobile application.
- **🤖 Enhanced AI Agents**: Specialized agents for specific research domains.
- **🌍 Internationalization**: Multi-language support for global research.
- **☁️ Cloud Deployment**: SaaS offering with managed infrastructure.

### 🔮 Long-Term Vision
- **🎯 Domain Specialization**: Tailored versions for specific academic fields.
- **📈 Predictive Analytics**: AI-driven research trend prediction.
- **🔬 Laboratory Integration**: Connect with experimental tools and data.
- **📚 Knowledge Graph**: Build comprehensive academic knowledge networks.

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).

### 🔗 Third-Party Licenses
- **Sentence Transformers**: Apache License 2.0
- **Scikit-learn**: BSD 3-Clause License
- **PyTorch**: BSD-style License
- **ReportLab**: BSD License

---

## 👥 Authors & Acknowledgments

### 🧑‍💻 Core Team
- **[moazhassan751](https://github.com/moazhassan751)**: Project Lead & Architecture
- **AI Research Community**: Inspiration and guidance

### 🙏 Acknowledgments
- **OpenAlex Team**: Comprehensive academic database access.
- **Hugging Face**: Transformer models and community support.
- **ArXiv**: Open access to scientific literature.
- **Academic Research Community**: Valuable feedback and feature suggestions.

---

## 📞 Support & Community

### 🆘 Getting Help
- **📖 Documentation**: Comprehensive guides in the `docs/` folder.
- **🐛 Issue Tracker**: Report bugs on [GitHub Issues](https://github.com/moazhassan751/academic-research-assistant/issues).
- **💬 Discussions**: Join community discussions and Q&A.
- **📧 Email Support**: Contact us for complex issues.

### 🤝 Community Guidelines
- **Be Respectful**: Maintain professional and courteous communication.
- **Stay On Topic**: Focus on academic research and development.
- **Share Knowledge**: Contribute to the community’s growth.
- **Follow Standards**: Adhere to academic and software best practices.

---

## 📊 Project Statistics

- **🏷️ Current Version**: 1.0.0
- **📅 Last Updated**: August 12, 2025
- **🔧 Python Version**: 3.12+
- **📦 Dependencies**: 25+ core packages
- **🧪 Test Coverage**: 85%+
- **📝 Documentation**: Comprehensive guides and API docs

---

<div align="center">

**⭐ Star this repository if you find it helpful!**

[Report Bug](https://github.com/moazhassan751/academic-research-assistant/issues) • [Request Feature](https://github.com/moazhassan751/academic-research-assistant/issues) • [Documentation](docs/) • [Contributing Guidelines](CONTRIBUTING.md)

</div>

---

### Key Improvements Made
1. **Consistent Formatting**: Standardized section headings, emojis, and spacing for a polished look.
2. **Improved Readability**: Broke up dense sections with concise subheadings and bullet points.
3. **Streamlined Code Blocks**: Unified code block formatting with clear comments.
4. **Visual Hierarchy**: Used Markdown elements like horizontal rules (`---`) and centered calls-to-action for better structure.
5. **Concise Language**: Simplified some descriptions without losing detail to enhance clarity.
6. **Consistent Emoji Usage**: Ensured emojis align with content and are used sparingly for emphasis.
7. **Professional Tone**: Adjusted wording to maintain a professional yet approachable tone suitable for academic and developer audiences.