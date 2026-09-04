param(
    [string]$Python = "C:\Anaconda3\envs\slicap5_env\python.exe"
)

$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..")

& $Python -c "import sys, SLiCAP, fastapi, pydantic; print('Python', sys.version.split()[0]); print('SLiCAP', SLiCAP.__version__); print('FastAPI', fastapi.__version__); print('Pydantic', pydantic.__version__)"
if ($LASTEXITCODE -ne 0) { throw "Python environment check failed." }

Push-Location (Join-Path $root "web-schematic")
try {
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "Web schematic build failed." }
}
finally {
    Pop-Location
}

$env:PYTHONPATH = Join-Path $root "backend"
$env:PYTHONDONTWRITEBYTECODE = "1"
& $Python -m pytest (Join-Path $root "backend\tests") -q -p no:cacheprovider
if ($LASTEXITCODE -ne 0) { throw "Backend tests failed." }

