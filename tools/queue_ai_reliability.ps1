# Model research ONLY. Never reads calibration/test, promotes models or edits UI.
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
$sessionDirectory = 'experiments/session_20261007_ai_baseline'
$recordPath = Join-Path $sessionDirectory 'reliability_queue.json'
if (Test-Path -LiteralPath $recordPath) { throw 'Queue record exists; inspect it before explicitly registering another queue.' }
$guardFiles = @('medvision_ai.py','medvision_pipeline.py','tools/run_experiment.py','tools/ai_metrics.py','tools/train_reliability_candidate.py','experiments/data_v3_reliability_20261007/manifest.json','experiments/session_20261007_ai_baseline/RELIABILITY_EXPERIMENT_PROTOCOL.json','FracAtlas.zip','best_model.pt','BASELINE_MODEL_REPORT.md')
$guards = @{}
foreach ($file in $guardFiles) { $guards[$file] = (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash }
$record = @{status='waiting_for_E2';created=(Get-Date).ToUniversalTime().ToString('o');guards=$guards;run_ids=@('AI_E5_v3_BCE_reference','AI_E6_v3_normal_BCE2');single_factor='Normal-image BCE coefficient 1 vs 2; all other factors matched';test_evaluated=$false;calibration_evaluated=$false;promotion_authorized=$false;runtime='.venv-phase2 torch2.9.1+cu128';source_sha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash}
$record | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $recordPath
try {
    while ($true) {
        $preceding = Get-Content -LiteralPath 'experiments/E2_corrected_baseline/state.json' -Raw | ConvertFrom-Json
        if ($preceding.status -eq 'completed' -and -not $preceding.smoke) {
            # The trainer writes completion just before returning. Wait for its
            # short process-exit tail rather than falsely reporting a duplicate.
            for ($exitCheck=0; $exitCheck -lt 30; $exitCheck++) {
                $remaining = @(Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -match 'tools[\\/]train_baseline.py' -and $_.CommandLine -match 'E2_corrected_baseline' })
                if ($remaining.Count -eq 0) { break }
                Start-Sleep -Seconds 1
            }
            break
        }
        $active = @(Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -match 'tools[\\/]train_baseline.py' -and $_.CommandLine -match 'E2_corrected_baseline' })
        if ($active.Count -eq 0) { throw 'E2 is incomplete without a live trainer. Inspect its checkpoint/log; do not skip baseline completion.' }
        Start-Sleep -Seconds 20
    }
    foreach ($plan in @(@{name='AI_E5_v3_BCE_reference';weight=1},@{name='AI_E6_v3_normal_BCE2';weight=2})) {
        foreach ($file in $guardFiles) {
            if ((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash -ne $guards[$file]) { throw "Research input changed: $file" }
        }
        $active = @(Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -match 'tools[\\/]train_(baseline|pipeline|reliability_candidate).py' })
        if ($active.Count -gt 0) { throw 'Another trainer is still active; preserve runs and inspect before launching.' }
        $run = 'experiments/' + $plan.name
        if (Test-Path -LiteralPath $run) { throw "Run already exists: $run. Never overwrite it." }
        $record.status='training'; $record.current=$plan.name; $record.current_normal_bce_weight=$plan.weight
        $record | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $recordPath
        $env:OMP_NUM_THREADS='2'; $env:MKL_NUM_THREADS='2'
        $env:CUBLAS_WORKSPACE_CONFIG=':4096:8'
        $stdoutLog=Join-Path $sessionDirectory ($plan.name+'.log')
        $stderrLog=Join-Path $sessionDirectory ($plan.name+'.stderr.log')
        & '.venv-phase2/Scripts/python.exe' tools/train_reliability_candidate.py --out $run --manifest experiments/data_v3_reliability_20261007/manifest.json --epochs 12 --batch-size 2 --lr 0.0001 --size 256 --resize stretch --blur 3 --normalization unit --loss bce_dice --normal-bce-weight $plan.weight --seed 42 --patience 12 --device cuda 1> $stdoutLog 2> $stderrLog
        if ($LASTEXITCODE -ne 0) { throw "Candidate failed: $($plan.name). Preserve all evidence and inspect logs before resume." }
        if ($plan.weight -eq 2) {
            $referenceInitial=Get-Content -LiteralPath 'experiments/AI_E5_v3_BCE_reference/initial_parameters.json' -Raw | ConvertFrom-Json
            $candidateInitial=Get-Content -LiteralPath (Join-Path $run 'initial_parameters.json') -Raw | ConvertFrom-Json
            if ($referenceInitial.parameter_sha256 -ne $candidateInitial.parameter_sha256) { throw 'Matched model initialization differed; invalidate causal loss comparison.' }
        }
    }
    $record.status='completed_training_only'
    $record.next='Inspect both training/validation curves and FP/FN/native masks. Compare matched validation and original-model metrics on the SAME 463 validation IDs. Reject trade-offs outside protocol. Only then select/freeze, calibrate on149 calibration IDs and plan one final reserved test. No automatic promotion/test.'
} catch {
    $record.status='failed'; $record.error=$_.Exception.Message
} finally {
    $record.updated=(Get-Date).ToUniversalTime().ToString('o')
    $record | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $recordPath
}
