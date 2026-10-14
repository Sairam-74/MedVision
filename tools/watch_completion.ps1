# Finish the registered controlled comparison only after the existing queue ends.
# Does not start, stop or reconfigure training. Preserve any failed output.
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
$recordPath = 'experiments/session_20261006_completion_ui/completion_watch.json'
$queuePath = 'experiments/session_20261006_p6p7/training_queue.json'
$guardFiles = @('tools/complete_research.py','tools/refresh_manuscript.py','medvision_pipeline.py','medvision_ai.py','tools/run_experiment.py','experiments/data_v2/manifest.json','FracAtlas.zip','best_model.pt')
$guards = @{}
foreach ($name in $guardFiles) { $guards[$name] = (Get-FileHash -LiteralPath $name -Algorithm SHA256).Hash }
$record = @{status='waiting_for_training_queue'; created=(Get-Date).ToUniversalTime().ToString('o'); output='experiments/FINAL_v2_20261006'; final_test_evaluated=$false; guards=$guards}
$record | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $recordPath
try {
    while ($true) {
        $queue = $null
        try { $queue = Get-Content -LiteralPath $queuePath -Raw | ConvertFrom-Json } catch {}
        if ($queue.status -eq 'completed_training_only') { break }
        if ($queue.status -eq 'failed') { throw 'Training queue failed; preserve all runs and inspect its recorded error.' }
        Start-Sleep -Seconds 30
    }
    foreach ($name in $guardFiles) {
        if ((Get-FileHash -LiteralPath $name -Algorithm SHA256).Hash -ne $guards[$name]) { throw "Completion input changed: $name. Re-register after reviewing changes." }
    }
    $record.status='validation_freeze_then_reserved_test'
    $record | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $recordPath
    $env:OMP_NUM_THREADS='2'; $env:MKL_NUM_THREADS='2'
    & '.venv-demo/Scripts/python.exe' tools/complete_research.py --out $record.output --final-test *> 'experiments/session_20261006_completion_ui/final_evaluation.log'
    if ($LASTEXITCODE -ne 0) { throw 'Final evaluator failed; inspect preserved output. Never retune using test results.' }
    $record.final_test_evaluated=$true
    & '.venv-demo/Scripts/python.exe' tools/refresh_manuscript.py --final-dir $record.output *> 'experiments/session_20261006_completion_ui/final_manuscript.log'
    if ($LASTEXITCODE -ne 0) { throw 'Results saved, manuscript regeneration failed; inspect log.' }
    $completion = Get-Content -LiteralPath (Join-Path $record.output 'completion.json') -Raw | ConvertFrom-Json
    $bundle = Join-Path (Join-Path $record.output $completion.selected_run) 'calibrated_bundle.json'
    $apiReport = Join-Path $record.output 'selected_model_api.json'
    & '.venv-demo/Scripts/python.exe' tools/verify_secure_api.py --real --bundle $bundle --out $apiReport *> 'experiments/session_20261006_completion_ui/selected_model_api.log'
    if ($LASTEXITCODE -ne 0) { throw 'Selected model real API parity failed. Keep the original demo active.' }
    $bundleRecord = Get-Content -LiteralPath $bundle -Raw | ConvertFrom-Json
    @{bundle=(Resolve-Path -LiteralPath $bundle).Path;bundle_sha256=(Get-FileHash -LiteralPath $bundle -Algorithm SHA256).Hash;checkpoint_sha256=$bundleRecord.checkpoint_sha256;api_verified=$true;final_test_evaluated=$true;human_review_completed=$false} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $record.output 'deployment.json')
    $record.status='measured_results_paper_and_API_ready'
    $record.next='Start-Demo.ps1 will select the verified final bundle on its next launch; perform final browser/human review and package this model separately. Original checkpoint remains preserved.'
} catch {
    $record.status='failed'; $record.error=$_.Exception.Message
} finally {
    $record.updated=(Get-Date).ToUniversalTime().ToString('o')
    $record | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $recordPath
}
