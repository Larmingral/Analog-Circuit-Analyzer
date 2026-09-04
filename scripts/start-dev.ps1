param(
    [string]$Python = "C:\Anaconda3\envs\slicap5_env\python.exe",
    [switch]$NoGradio
)

$ErrorActionPreference = "Stop"
$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$web = Join-Path $root "web-schematic"
$gradio = Join-Path $root "SLiCAP"
$logRoot = Join-Path $root "runs\service-logs"

function Get-PortConflict {
    param([int]$Port, [string]$Name)

    $connection = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($null -eq $connection) { return $null }
    $owner = Get-Process -Id $connection.OwningProcess -ErrorAction SilentlyContinue
    $processName = if ($null -eq $owner) { "unknown process" } else { $owner.ProcessName }
    return "$Name requires port $Port, currently used by PID $($connection.OwningProcess) ($processName)."
}

function Start-ServiceProcess {
    param(
        [string]$Name,
        [string]$FilePath,
        [string[]]$ArgumentList,
        [string]$WorkingDirectory,
        [string]$LogStem
    )

    $stdout = Join-Path $logRoot "$LogStem.out.log"
    $stderr = Join-Path $logRoot "$LogStem.err.log"
    $process = Start-Process -FilePath $FilePath -ArgumentList $ArgumentList `
        -WorkingDirectory $WorkingDirectory -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput $stdout -RedirectStandardError $stderr
    return [pscustomobject]@{
        Name = $Name
        Process = $process
        Stdout = $stdout
        Stderr = $stderr
    }
}

if (-not (Test-Path -LiteralPath $Python)) {
    throw "Python not found: $Python"
}

$version = & $Python -c "import sys, SLiCAP; print(f'{sys.version_info.major}.{sys.version_info.minor}|{SLiCAP.__version__}')"
if ($LASTEXITCODE -ne 0 -or $version.Trim() -ne "3.12|5.2.1") {
    throw "Expected Python 3.12 and SLiCAP 5.2.1, found: $version"
}

$requiredPorts = @(
    @{ Name = "Web schematic"; Port = 5173 },
    @{ Name = "FastAPI"; Port = 8000 }
)
if (-not $NoGradio) {
    $requiredPorts += @{ Name = "Gradio"; Port = 7860 }
}
$conflicts = @($requiredPorts | ForEach-Object { Get-PortConflict -Port $_.Port -Name $_.Name } |
    Where-Object { $_ })
if ($conflicts.Count -gt 0) {
    throw "Cannot start ISACA because required ports are occupied:`n$($conflicts -join "`n")`nStop the old services and run this command again."
}

$node = (Get-Command node.exe -ErrorAction Stop).Source
$vite = Join-Path $web "node_modules\vite\bin\vite.js"
if (-not (Test-Path -LiteralPath $vite)) {
    throw "Vite is not installed. Run 'npm install' in: $web"
}

New-Item -ItemType Directory -Path $logRoot -Force | Out-Null
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$previousPythonPath = $env:PYTHONPATH
$previousQtPlatform = $env:QT_QPA_PLATFORM
$env:PYTHONPATH = Join-Path $root "backend"
$env:QT_QPA_PLATFORM = "offscreen"
$processes = @()
try {
    $processes += Start-ServiceProcess -Name "FastAPI" -FilePath $Python `
        -ArgumentList @("-m", "uvicorn", "isaca_api.app:app", "--host", "127.0.0.1", "--port", "8000") `
        -WorkingDirectory $root -LogStem "$stamp-fastapi"
    $processes += Start-ServiceProcess -Name "Web schematic" -FilePath $node `
        -ArgumentList @($vite, "--host", "127.0.0.1", "--port", "5173") `
        -WorkingDirectory $web -LogStem "$stamp-web"
    if (-not $NoGradio) {
        $processes += Start-ServiceProcess -Name "Gradio" -FilePath $Python `
            -ArgumentList @("packup2.py") -WorkingDirectory $gradio -LogStem "$stamp-gradio"
    }

    Start-Sleep -Seconds 2
    foreach ($service in $processes) {
        if ($service.Process.HasExited) {
            $details = if (Test-Path -LiteralPath $service.Stderr) {
                (Get-Content -LiteralPath $service.Stderr -Tail 20) -join "`n"
            } else { "No stderr was captured." }
            throw "$($service.Name) exited during startup (PID $($service.Process.Id), exit $($service.Process.ExitCode)).`n$details`nLog: $($service.Stderr)"
        }
    }

    Write-Host "ISACA local services started:" -ForegroundColor Green
    Write-Host "  Web schematic: http://127.0.0.1:5173"
    Write-Host "  FastAPI docs:  http://127.0.0.1:8000/docs"
    if (-not $NoGradio) {
        Write-Host "  Gradio shell:  http://127.0.0.1:7860"
    }
    Write-Host "Press Ctrl+C to stop all services."
    Write-Host "Service logs: $logRoot"

    while ($true) {
        Start-Sleep -Seconds 2
        foreach ($service in $processes) {
            if ($service.Process.HasExited) {
                $details = if (Test-Path -LiteralPath $service.Stderr) {
                    (Get-Content -LiteralPath $service.Stderr -Tail 20) -join "`n"
                } else { "No stderr was captured." }
                throw "$($service.Name) exited unexpectedly (PID $($service.Process.Id), exit $($service.Process.ExitCode)).`n$details`nLog: $($service.Stderr)"
            }
        }
    }
}
finally {
    foreach ($service in $processes) {
        if (-not $service.Process.HasExited) {
            Stop-Process -Id $service.Process.Id -Force
        }
    }
    $env:PYTHONPATH = $previousPythonPath
    $env:QT_QPA_PLATFORM = $previousQtPlatform
}
