param(
    [string]$Python = "C:\Anaconda3\envs\slicap5_env\python.exe",
    [switch]$NoGradio
)

$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$web = Join-Path $root "web-schematic"
$gradio = Join-Path $root "SLiCAP"

if (-not (Test-Path -LiteralPath $Python)) {
    throw "Python not found: $Python"
}

$version = & $Python -c "import sys, SLiCAP; print(f'{sys.version_info.major}.{sys.version_info.minor}|{SLiCAP.__version__}')"
if ($LASTEXITCODE -ne 0 -or $version.Trim() -ne "3.12|5.2.1") {
    throw "Expected Python 3.12 and SLiCAP 5.2.1, found: $version"
}

$processes = @()
try {
    $processes += Start-Process -FilePath $Python `
        -ArgumentList @("-m", "uvicorn", "isaca_api.app:app", "--host", "127.0.0.1", "--port", "8000", "--reload") `
        -WorkingDirectory $root -WindowStyle Hidden -PassThru
    $processes += Start-Process -FilePath "npm.cmd" `
        -ArgumentList @("run", "dev") -WorkingDirectory $web -WindowStyle Hidden -PassThru
    if (-not $NoGradio) {
        $processes += Start-Process -FilePath $Python `
            -ArgumentList @("packup2.py") -WorkingDirectory $gradio -WindowStyle Hidden -PassThru
    }

    Write-Host "ISACA local services started:" -ForegroundColor Green
    Write-Host "  Web schematic: http://127.0.0.1:5173"
    Write-Host "  FastAPI docs:  http://127.0.0.1:8000/docs"
    if (-not $NoGradio) {
        Write-Host "  Gradio shell:  http://127.0.0.1:7860"
    }
    Write-Host "Press Ctrl+C to stop all services."

    while ($true) {
        Start-Sleep -Seconds 2
        foreach ($process in $processes) {
            if ($process.HasExited) {
                throw "A local service exited unexpectedly (PID $($process.Id), exit $($process.ExitCode))."
            }
        }
    }
}
finally {
    foreach ($process in $processes) {
        if (-not $process.HasExited) {
            Stop-Process -Id $process.Id -Force
        }
    }
}

