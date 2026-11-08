$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
foreach ($command in 'py', 'npm.cmd', 'ollama') {
    if (-not (Get-Command $command -ErrorAction SilentlyContinue)) {
        throw "Missing $command. Install the prerequisites listed in README.md."
    }
}
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    py -3.12 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Python environment creation failed' }
}
& '.\.venv\Scripts\python.exe' -m pip install -c requirements.lock.txt -e '.[dev]'
if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed' }
if (-not (Test-Path -LiteralPath '.env')) {
    Copy-Item -LiteralPath '.env.example' -Destination '.env'
}
Push-Location -LiteralPath 'frontend'
try {
    npm.cmd ci
    if ($LASTEXITCODE -ne 0) { throw 'Frontend dependency installation failed' }
    npm.cmd run build
    if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed' }
} finally { Pop-Location }
& '.\.venv\Scripts\python.exe' scripts/install_models.py
if ($LASTEXITCODE -ne 0) { throw 'Ollama model setup failed' }
& '.\.venv\Scripts\python.exe' -m cybersrs.tools ingest
if ($LASTEXITCODE -ne 0) { throw 'Knowledge ingestion failed' }
$preflight = & '.\.venv\Scripts\python.exe' -m cybersrs.tools preflight
if ($LASTEXITCODE -ne 0) { throw 'Runtime preflight failed' }
$status = ($preflight -join [Environment]::NewLine) | ConvertFrom-Json
if (-not $status.model.ready -or -not $status.model.embedding_ready) {
    throw 'The configured generation or embedding model is unavailable'
}
$preflight
Write-Host 'Setup complete. Run .\start.cmd to launch CyberSRS.'
