# Academic Research Assistant - PowerShell Launcher
# Cross-platform launcher with enhanced Windows support

param(
    [switch]$Health,
    [switch]$Config,
    [switch]$Setup,
    [switch]$Status,
    [switch]$Stop,
    [int]$Port
)

# Set location to script directory
Set-Location $PSScriptRoot

# Banner
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║               Academic Research Assistant                        ║" -ForegroundColor Cyan  
Write-Host "║                   PowerShell Launcher                           ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Check Python
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Python detected: $pythonVersion" -ForegroundColor Green
    } else {
        throw "Python not found"
    }
} catch {
    Write-Host "❌ Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "💡 Please install Python from https://www.python.org/downloads/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Build Python command arguments
$args = @("launch.py")

if ($Health) { $args += "--health" }
if ($Config) { $args += "--config" }
if ($Setup) { $args += "--setup" }
if ($Status) { $args += "--status" }  
if ($Stop) { $args += "--stop" }
if ($Port) { $args += "--port", $Port }

Write-Host "🚀 Launching Academic Research Assistant..." -ForegroundColor Green
Write-Host ""

try {
    # Run the Python launcher
    & python $args
} catch {
    Write-Host "❌ Failed to launch: $_" -ForegroundColor Red
} finally {
    Write-Host ""
    Write-Host "👋 Session ended" -ForegroundColor Yellow
    if (-not $Health -and -not $Config -and -not $Setup -and -not $Status -and -not $Stop) {
        Read-Host "Press Enter to exit"
    }
}
