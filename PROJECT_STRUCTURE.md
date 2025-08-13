# 🏗️ Project Structure Documentation

This document describes the organized structure of the Academic Research Assistant project.

## 📁 Directory Structure

```
academic_research_assistant/
├── 📄 main.py                           # Main CLI application entry point
├── 📄 integrated_dashboard.py           # Streamlit web interface
├── 📄 config.yaml                      # Main configuration file
├── 📄 requirements.txt                 # Python dependencies
├── 📄 README.md                        # Project documentation
├── 📄 .env.example                     # Environment variables template
├── 📄 .gitignore                       # Git ignore rules
│
├── 📁 src/                             # Core application source code
│   ├── 📁 agents/                      # AI agent implementations
│   │   ├── literature_survey_agent.py
│   │   ├── qa_agent.py
│   │   ├── note_taking_agent.py
│   │   ├── theme_synthesizer_agent.py
│   │   ├── draft_writer_agent.py
│   │   └── citation_generator_agent.py
│   │
│   ├── 📁 crew/                        # Agent orchestration
│   │   └── research_crew.py
│   │
│   ├── 📁 llm/                         # LLM client implementations
│   │   ├── llm_factory.py
│   │   ├── gemini_client.py
│   │   └── openai_client.py
│   │
│   ├── 📁 storage/                     # Data persistence layer
│   │   ├── database.py
│   │   └── models.py
│   │
│   ├── 📁 tools/                       # External API integrations
│   │   ├── arxiv_tool.py
│   │   ├── Open_Alex_tool.py
│   │   ├── Cross_Ref_tool.py
│   │   ├── semantic_scholar_tool.py
│   │   ├── citation_formatter.py
│   │   └── pdf_processor.py
│   │
│   └── 📁 utils/                       # Utility functions and helpers
│       ├── config.py
│       ├── logging.py
│       ├── validators.py
│       ├── error_handler.py
│       ├── export_manager.py
│       ├── performance_optimizer.py
│       ├── database_optimizer.py
│       ├── resource_manager.py
│       ├── health_monitor.py
│       ├── async_api_manager.py
│       ├── adaptive_config.py
│       └── enhanced_config.py
│
├── 📁 ui/                              # User interface components
│   ├── 📄 streamlit_dashboard.py       # Alternative Streamlit interface
│   ├── 📄 api_server.py               # FastAPI backend server
│   ├── 📄 config_manager.py           # UI configuration management
│   ├── 📄 database_manager.py         # UI database interface
│   ├── 📄 start_functional.bat        # Windows UI launcher
│   ├── 📄 start_ui.bat                # Windows UI launcher (alternative)
│   ├── 📄 README.md                   # UI-specific documentation
│   └── 📁 frontend/                   # React frontend components
│       ├── package.json
│       └── src/
│           ├── App.tsx
│           ├── theme.ts
│           ├── types/index.ts
│           ├── pages/Dashboard.tsx
│           └── services/api.ts
│
├── 📁 tests/                          # Test suite
│   ├── 📄 README.md                   # Testing documentation
│   ├── 📄 conftest.py                 # Pytest configuration
│   ├── 📄 clean_test.py               # Clean test runner
│   ├── 📄 verify_fixes.py             # Fix verification script
│   ├── 📄 quick_test.py               # Quick functionality test
│   ├── 📄 performance_test.py         # Performance benchmarks
│   ├── 📄 performance_demo.py         # Performance demonstration
│   ├── 📄 demo_qa_feature.py          # Q&A feature demo
│   ├── 📄 debug_qa.py                 # Q&A debugging utilities
│   ├── 📄 debug_test.py               # General debugging tests
│   ├── 📄 Open_Alex_test.py           # OpenAlex API tests
│   │
│   ├── 📁 unit/                       # Unit tests
│   │   ├── test_database.py
│   │   ├── test_validators.py
│   │   ├── test_error_handler.py
│   │   ├── test_enhanced_config.py
│   │   ├── test_async_api_manager.py
│   │   ├── test_fixes.py
│   │   ├── test_literature_survey.py
│   │   ├── test_qa_feature.py
│   │   └── test_validator_errors.py
│   │
│   └── 📁 integration/                # Integration tests
│       ├── comprehensive_test.py
│       └── complete_workflow_test.py
│
├── 📁 scripts/                        # Automation and utility scripts
│   ├── 📄 README.md                   # Scripts documentation
│   ├── 📄 install_enhanced_qa.bat     # Q&A dependencies installer (Windows)
│   ├── 📄 install_export_deps.bat     # Export dependencies installer (Windows)
│   ├── 📄 install_export_deps.sh      # Export dependencies installer (Unix)
│   ├── 📄 final_status_report.py      # Status reporting script
│   ├── 📄 error_resolution_summary.py # Error resolution summary generator
│   │
│   └── 📁 launch/                     # Application launchers
│       ├── launch_integrated_dashboard.bat  # Windows dashboard launcher
│       ├── launch_integrated_dashboard.sh   # Unix dashboard launcher
│       ├── launch_clean.bat               # Windows clean launch
│       └── launch_clean.sh                # Unix clean launch
│
├── 📁 docs/                           # Documentation
│   ├── 📄 README.md                   # Documentation index
│   ├── 📄 README_ALTERNATIVE.md       # Alternative README version
│   ├── 📄 EXPORT_FEATURES.md          # Export functionality guide
│   ├── 📄 QA_FEATURE_GUIDE.md         # Q&A system guide
│   ├── 📄 QA_ENHANCEMENT_PLAN.md      # Q&A enhancement roadmap
│   ├── 📄 QA_ENHANCEMENT_SUMMARY.md   # Q&A enhancement summary
│   ├── 📄 DATABASE_ENHANCEMENT_SUMMARY.md # Database improvements
│   ├── 📄 ENHANCED_QA_IMPLEMENTATION_GUIDE.md # Q&A implementation guide
│   ├── 📄 PERFORMANCE_OPTIMIZATION_GUIDE.md # Performance optimization guide
│   ├── 📄 PERFORMANCE_OPTIMIZATION_COMPLETE.md # Performance completion summary
│   ├── 📄 PROJECT_OPTIMIZATION_COMPLETE.md # Project optimization summary
│   ├── 📄 PROJECT_STRUCTURE_OPTIMIZATION.md # Structure optimization guide
│   ├── 📄 SYSTEM_OPTIMIZATION_COMPLETE.md # System optimization summary
│   ├── 📄 ERROR_RESOLUTION_SUMMARY.md # Error resolution documentation
│   │
│   ├── 📁 status_reports/             # Project status and progress reports
│   │   ├── ERROR_FIXES_SUMMARY.md
│   │   ├── ERROR_RESOLUTION_FINAL.md
│   │   ├── FINAL_STATUS_COMPLETE.md
│   │   └── OPENALEX_FIX_COMPLETE.md
│   │
│   └── 📁 ui/                         # UI-specific documentation
│       ├── INTEGRATED_UI_GUIDE.md
│       ├── UI_CLEANUP_SUMMARY.md
│       └── UI_INTEGRATION_COMPARISON.md
│
├── 📁 config/                         # Configuration files
│   └── performance.json               # Performance optimization settings
│
├── 📁 config_backups/                 # Configuration backups
│   ├── config_backup.yaml
│   ├── config_correct.yaml
│   └── config_minimal.yaml
│
├── 📁 data/                           # Data storage
│   ├── 📄 research.db                 # Main SQLite database
│   ├── 📄 backup_research_db_*.db     # Database backups
│   │
│   ├── 📁 cache/                      # Caching system
│   │   └── checkpoint_*.json          # Research checkpoints
│   │
│   ├── 📁 outputs/                    # Generated research outputs
│   │   └── [topic]_[timestamp]/       # Individual research results
│   │
│   └── 📁 papers/                     # Downloaded paper storage
│
└── 📁 logs/                           # Application logs
    ├── research_assistant.log
    ├── research_assistant.json
    └── errors.log
```

## 🎯 Key Components

### **Core Application**
- `main.py` - Command-line interface with all research features
- `integrated_dashboard.py` - Web-based interface using Streamlit

### **AI Agents (`src/agents/`)**
- **Literature Survey Agent** - Discovers and analyzes academic papers
- **Q&A Agent** - Answers questions based on research corpus
- **Draft Writer Agent** - Generates structured research documents
- **Citation Generator Agent** - Formats citations and bibliographies

### **User Interfaces (`ui/`)**
- **Streamlit Dashboard** - Primary web interface
- **FastAPI Server** - Backend API for React frontend
- **React Frontend** - Modern web interface components

### **Testing Strategy**
- **Unit Tests** (`tests/unit/`) - Individual component testing
- **Integration Tests** (`tests/integration/`) - Full workflow testing
- **Performance Tests** - Benchmarking and optimization validation

### **Documentation Structure**
- **Main Docs** (`docs/`) - User guides and technical documentation
- **Status Reports** (`docs/status_reports/`) - Development progress tracking
- **UI Documentation** (`docs/ui/`) - Interface-specific guides

## 🚀 Quick Start

### Web Interface (Recommended)
```bash
# Windows
scripts\launch\launch_integrated_dashboard.bat

# Linux/macOS
./scripts/launch/launch_integrated_dashboard.sh
```

### Command Line Interface
```bash
python main.py research "your topic" --export-formats pdf markdown
```

## 🧪 Testing

### Run All Tests
```bash
python -m pytest tests/ -v
```

### Quick Functionality Test
```bash
python tests/quick_test.py
```

### Performance Benchmarks
```bash
python tests/performance_test.py
```

This structure provides clear separation of concerns, easy navigation, and maintainable organization for both developers and users.
