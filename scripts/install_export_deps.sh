#!/bin/bash
# Installation script for Academic Research Assistant Export Dependencies

echo "🔧 Installing Academic Research Assistant Export Dependencies..."

# Install Python dependencies
echo "📦 Installing Python packages..."
pip install reportlab
pip install python-docx
pip install pdfkit
pip install jinja2

# Check if wkhtmltopdf is installed (required for pdfkit)
if command -v wkhtmltopdf &> /dev/null; then
    echo "✅ wkhtmltopdf is already installed"
else
    echo "⚠️  wkhtmltopdf is not installed"
    echo "📝 To enable HTML to PDF conversion, please install wkhtmltopdf:"
    echo ""
    
    # Detect OS and provide installation instructions
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "   Ubuntu/Debian: sudo apt-get install wkhtmltopdf"
        echo "   CentOS/RHEL:   sudo yum install wkhtmltopdf"
        echo "   Arch Linux:    sudo pacman -S wkhtmltopdf"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "   macOS:         brew install wkhtmltopdf"
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        echo "   Windows:       Download from https://wkhtmltopdf.org/downloads.html"
        echo "                  Or use chocolatey: choco install wkhtmltopdf"
    else
        echo "   Download from: https://wkhtmltopdf.org/downloads.html"
    fi
    echo ""
fi

# Test installation
echo "🧪 Testing export functionality..."
python -c "
try:
    from src.utils.export_manager import export_manager
    formats = export_manager.get_supported_formats()
    available = [fmt for fmt, avail in formats.items() if avail]
    unavailable = [fmt for fmt, avail in formats.items() if not avail]
    
    print('✅ Available export formats:', ', '.join(available))
    if unavailable:
        print('❌ Unavailable formats:', ', '.join(unavailable))
    else:
        print('🎉 All export formats are available!')
        
except Exception as e:
    print(f'❌ Error testing export functionality: {e}')
    print('Please check your installation and make sure you are running from the project root directory.')
"

echo ""
echo "✅ Installation complete!"
echo ""
echo "🚀 You can now use the new export features:"
echo "   python main.py export-formats              # Show available formats"
echo "   python main.py research 'topic' -f pdf docx # Research with PDF and Word export"
echo "   python main.py export path/to/results -f pdf # Export existing results to PDF"
