@echo off
REM Installation script for Academic Research Assistant Export Dependencies (Windows)

echo 🔧 Installing Academic Research Assistant Export Dependencies...

REM Install Python dependencies
echo 📦 Installing Python packages...
pip install reportlab>=4.0.0
pip install python-docx>=0.8.11
pip install pdfkit>=1.0.0
pip install jinja2>=3.1.0

REM Check if wkhtmltopdf is installed
where wkhtmltopdf >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ wkhtmltopdf is already installed
) else (
    echo ⚠️  wkhtmltopdf is not installed
    echo 📝 To enable HTML to PDF conversion, please install wkhtmltopdf:
    echo.
    echo    Download from: https://wkhtmltopdf.org/downloads.html
    echo    Or use chocolatey: choco install wkhtmltopdf
    echo    Or use winget: winget install wkhtmltopdf
    echo.
)

REM Test installation
echo 🧪 Testing export functionality...
python -c "try:
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
    print('Please check your installation and make sure you are running from the project root directory.')"

echo.
echo ✅ Installation complete!
echo.
echo 🚀 You can now use the new export features:
echo    python main.py export-formats              # Show available formats
echo    python main.py research "topic" -f pdf docx # Research with PDF and Word export
echo    python main.py export path/to/results -f pdf # Export existing results to PDF

pause
