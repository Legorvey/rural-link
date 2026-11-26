$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe = Join-Path $RepoRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $PythonExe)) {
    Write-Error "Virtual environment not found at $PythonExe. Run 'uv venv --python 3.12 .venv' and install requirements-dev.txt first."
    exit 1
}

Push-Location $RepoRoot
try {
    & $PythonExe -m uvicorn api.index:app --host 127.0.0.1 --port 8000 @args
} finally {
    Pop-Location
}
