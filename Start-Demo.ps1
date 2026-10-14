param([switch]$UseCuda)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$runtimePython = Join-Path $PSScriptRoot '.venv-demo/Scripts/python.exe'
if ($UseCuda) {
    throw 'The current GPU has Windows Code 43; use the patched CPU demo runtime.'
}
if (-not (Test-Path -LiteralPath $runtimePython)) {
    throw 'Prepare the selected environment as described in DEMO.md first.'
}
if (-not (Test-Path -LiteralPath 'dist/index.html')) {
    throw 'Run npm run build before starting the demo.'
}
if (-not $env:MEDVISION_DEMO_PASSWORD) {
    $credentialDirectory = Join-Path $PSScriptRoot '.local_demo'
    New-Item -ItemType Directory -Force -Path $credentialDirectory | Out-Null
    $credentialFile = Join-Path $credentialDirectory 'demo_password.txt'
    if (-not (Test-Path -LiteralPath $credentialFile)) {
        [guid]::NewGuid().ToString('N') | Set-Content -LiteralPath $credentialFile
    }
    $env:MEDVISION_DEMO_PASSWORD = (Get-Content -LiteralPath $credentialFile -Raw).Trim()
}
$env:OMP_NUM_THREADS = '4'
$env:MEDVISION_DEMO_PREFILL = '1'
if (-not $env:MEDVISION_DEMO_RECOVERY_CODE) {
    New-Item -ItemType Directory -Force -Path (Join-Path $PSScriptRoot '.local_demo') | Out-Null
    $recoveryFile = Join-Path $PSScriptRoot '.local_demo/demo_recovery_code.txt'
    if (-not (Test-Path -LiteralPath $recoveryFile)) { ([guid]::NewGuid().ToString('N') + [guid]::NewGuid().ToString('N')) | Set-Content -LiteralPath $recoveryFile }
    $env:MEDVISION_DEMO_RECOVERY_CODE = (Get-Content -LiteralPath $recoveryFile -Raw).Trim()
}
$env:MKL_NUM_THREADS = '4'
if (-not $env:MEDVISION_BUNDLE -and (Test-Path -LiteralPath 'experiments/FINAL_v2_20261006/deployment.json')) {
    $deployment = Get-Content -LiteralPath 'experiments/FINAL_v2_20261006/deployment.json' -Raw | ConvertFrom-Json
    $bundlePath = [IO.Path]::GetFullPath($deployment.bundle)
    $expectedRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot 'experiments/FINAL_v2_20261006')) + [IO.Path]::DirectorySeparatorChar
    if (-not $bundlePath.StartsWith($expectedRoot, [StringComparison]::OrdinalIgnoreCase) -or -not $deployment.api_verified -or -not $deployment.final_test_evaluated) { throw 'Final bundle delivery record is invalid; inspect it before launch.' }
    if ((Get-FileHash -LiteralPath $bundlePath -Algorithm SHA256).Hash -ne $deployment.bundle_sha256) { throw 'Final bundle changed after verification.' }
    $env:MEDVISION_BUNDLE = $bundlePath
    Write-Host 'Selecting the frozen v2 research bundle verified against the real API. Human review remains required.'
}
Write-Host 'Local research demo: http://localhost:8000/login'
Write-Host 'Local account: demo.clinician@example.invalid'
Write-Host 'Password: your MEDVISION_DEMO_PASSWORD value or .local_demo/demo_password.txt'
Write-Host 'Use research images only. Ctrl+C stops the server.'
& $runtimePython -m uvicorn backend_service:app --host 127.0.0.1 --port 8000 --no-proxy-headers --limit-concurrency 16 --timeout-keep-alive 5
