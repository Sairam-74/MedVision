# Validation ONLY after full current E5/E6 completion. No test/calibration/promotion.
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
$session = 'experiments/session_20261007_ai_loop_01'
$recordFile = Join-Path $session 'audit_watch.json'
if (Test-Path -LiteralPath $recordFile) { throw 'Audit watcher already registered; inspect record/process before resuming.' }
$guardFiles = @('tools/ai_validation_audit.py','tools/analyze_ai_pair.py','tools/ai_error_groups.py','tools/ai_metrics.py','tools/evaluate_ai_baseline.py','medvision_ai.py','medvision_pipeline.py','experiments/data_v3_reliability_20261007/manifest.json','best_model.pt','BASELINE_MODEL_REPORT.md')
$guards = @{}
foreach ($file in $guardFiles) { $guards[$file] = (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash }
$record = @{status='waiting';created=(Get-Date).ToUniversalTime().ToString('o');guards=$guards;test_evaluated=$false;calibration_evaluated=$false;promotion=$false;device='cpu';current='E5';source_sha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash}
$record | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $recordFile
try {
    foreach ($plan in @(@{run='AI_E5_v3_BCE_reference';audit='AI_AUDIT_E5_v3'},@{run='AI_E6_v3_normal_BCE2';audit='AI_AUDIT_E6_v3'})) {
        $runDirectory = Join-Path 'experiments' $plan.run
        $statePath = Join-Path $runDirectory 'state.json'
        $record.current=$plan.run; $record.status='waiting_training_completion'
        $record | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $recordFile
        while ($true) {
            if (Test-Path -LiteralPath $statePath) {
                $state = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
                if ($state.status -eq 'completed' -and -not $state.smoke) { break }
            }
            $queue = Get-Content -LiteralPath 'experiments/session_20261007_ai_baseline/reliability_queue.json' -Raw | ConvertFrom-Json
            if ($queue.status -eq 'failed') { throw 'Current training queue failed; preserve logs/checkpoints and diagnose before continuing.' }
            $trainer = @(Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -match 'tools[\\/]train_reliability_candidate.py' })
            if ($trainer.Count -eq 0) {
                $queueProcess = @(Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'pwsh.exe' -and $_.CommandLine -match '-File .*queue_ai_reliability.ps1' })
                if ($queueProcess.Count -eq 0) { throw 'Incomplete training without live trainer/queue. Do not evaluate unfinished checkpoint.' }
            }
            Start-Sleep -Seconds 20
        }
        foreach ($file in $guardFiles) { if ((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash -ne $guards[$file]) { throw "Audit input changed: $file" } }
        $record.status='running_full_validation_audit'
        $record | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $recordFile
        $output = Join-Path 'experiments' $plan.audit
        if (Test-Path -LiteralPath $output) { throw "Audit output already exists: $output; never overwrite." }
        $env:OMP_NUM_THREADS='2'; $env:MKL_NUM_THREADS='2'
        & '.venv-phase2/Scripts/python.exe' tools/ai_validation_audit.py --run $runDirectory --out $output --device cpu 1> (Join-Path $session ($plan.audit+'.log')) 2> (Join-Path $session ($plan.audit+'.stderr.log'))
        if ($LASTEXITCODE -ne 0) { throw "Validation audit failed: $($plan.audit). Preserve output and inspect." }
        & '.venv-phase2/Scripts/python.exe' tools/ai_error_groups.py --audit $output --out (Join-Path 'experiments' ($plan.audit+'_error_groups')) 1> (Join-Path $session ($plan.audit+'_groups.log')) 2> (Join-Path $session ($plan.audit+'_groups.stderr.log'))
        if ($LASTEXITCODE -ne 0) { throw "Error group audit failed: $($plan.audit)." }
        & '.venv-demo/Scripts/python.exe' tools/record_ai_loop.py --observation "Full completed validation audit saved for $($plan.run); no calibration/test/promotion. Inspect actual failure panels before next intervention."
        if ($LASTEXITCODE -ne 0) { throw 'Progress recording failed' }
    }
    $record.status='comparing_pair'
    $record | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $recordFile
    & '.venv-phase2/Scripts/python.exe' tools/analyze_ai_pair.py --reference experiments/AI_AUDIT_E5_v3 --candidate experiments/AI_AUDIT_E6_v3 --out experiments/AI_E5_E6_PAIR_ANALYSIS 1> (Join-Path $session 'pair_analysis.log') 2> (Join-Path $session 'pair_analysis.stderr.log')
    if ($LASTEXITCODE -ne 0) { throw 'Pair comparison failed; preserve evidence and inspect' }
    & '.venv-demo/Scripts/python.exe' tools/record_ai_loop.py --observation 'E5/E6 and full matched validation/error-group audits completed. Pair analysis recorded; root must inspect failure masks/curves before choosing the next intervention. No automatic final test or promotion.'
    if ($LASTEXITCODE -ne 0) { throw 'Progress recording failed' }
    $record.status='completed_validation_audits_only'; $record.next='Inspect pair result, actual masks and dominant failures; register ONE next intervention if acceptance unmet. Test/calibration/promotion remain closed.'
} catch {
    $record.status='failed'; $record.error=$_.Exception.Message
} finally {
    $record.updated=(Get-Date).ToUniversalTime().ToString('o')
    $record | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $recordFile
}
