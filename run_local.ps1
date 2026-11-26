$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe = Join-Path $RepoRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $PythonExe)) {
    Write-Error "Virtual environment not found at $PythonExe. Run 'uv venv --python 3.12 .venv' and install requirements-dev.txt first."
    exit 1
}

Push-Location $RepoRoot
try {
    $env:STREAMLIT_BROWSER_GATHER_USAGE_STATS = "false"
    & $PythonExe -m streamlit run app.py @args
} finally {
    Pop-Location
}
