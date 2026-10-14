param([int]$Port=8001)
$ErrorActionPreference='Stop'
Set-Location -LiteralPath $PSScriptRoot
$runtimePython=Join-Path $PSScriptRoot '.venv-feature/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $runtimePython)) {throw 'Run the environment setup in FEATURE_WORKFLOW.md first.'}
if (-not (Test-Path -LiteralPath 'dist/index.html')) {throw 'Run npm run build first.'}
$env:MEDVISION_DB=Join-Path $PSScriptRoot '.feature_data/app.sqlite3'
$env:MEDVISION_GENERATED_DIR=Join-Path $PSScriptRoot '.feature_data/storage'
$env:MEDVISION_CHECKPOINT=Join-Path $PSScriptRoot 'best_model.pt'
Remove-Item Env:MEDVISION_BUNDLE -ErrorAction SilentlyContinue
$env:MEDVISION_DEMO_PREFILL='0'
$env:OMP_NUM_THREADS='2'
$env:MKL_NUM_THREADS='2'
$env:PYTHONUTF8='1'
& $runtimePython tools/setup_feature.py
if ($LASTEXITCODE -ne 0) {throw 'Feature setup failed'}
Write-Host "Independent research workspace: http://localhost:$Port/login"
Write-Host 'Clinician: feature.clinician@example.invalid; password file .feature_data/clinician_password.txt'
Write-Host 'Administrator: feature.admin@example.invalid; password file .feature_data/admin_password.txt'
& $runtimePython -m uvicorn backend_service:app --host 127.0.0.1 --port $Port --no-proxy-headers --no-access-log --limit-concurrency 16 --timeout-keep-alive 5
