# Registered research pair only; no automatic CAL/test/deployment/paper actions.
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
$session = 'experiments/session_20261007_ai_loop_01'
$recordPath = Join-Path $session 'presence_queue.json'
if (Test-Path -LiteralPath $recordPath) { throw 'Presence queue already registered; inspect before recovery.' }
$smoke = Get-Content -LiteralPath 'experiments/AI_PRESENCE_MODEL_SMOKE_20261007/completion.json' -Raw | ConvertFrom-Json
if ($smoke.status -ne 'passed_TRAIN_only_smoke') { throw 'TRAIN-only architecture/gradient/restore checks must pass first.' }
$smokeConfig = Get-Content -LiteralPath 'experiments/AI_PRESENCE_MODEL_SMOKE_20261007/config.json' -Raw | ConvertFrom-Json
foreach ($entry in $smokeConfig.source_hashes.PSObject.Properties) {
    if ((Get-FileHash -LiteralPath $entry.Name -Algorithm SHA256).Hash.ToLower() -ne $entry.Value) { throw "Smoke source changed: $($entry.Name)" }
}
$guardFiles = @('medvision_ai.py','medvision_pipeline.py','tools/ai_presence_model.py','tools/train_ai_presence_candidate.py','tools/ai_cached_dataset.py','tools/cache_ai_training_inputs.py','tools/train_reliability_candidate.py','tools/run_experiment.py','tools/ai_metrics.py','experiments/data_v3_reliability_20261007/manifest.json','experiments/session_20261007_ai_loop_01/PRESENCE_EXPERIMENT_PROTOCOL.json','experiments/AI_E5_v3_BCE_reference/best_model.pt','experiments/AI_E5_E6_PAIR_ANALYSIS/comparison.json','FracAtlas.zip','best_model.pt','best_model_threshold.json','BASELINE_MODEL_REPORT.md')
$guards = @{}
foreach ($file in $guardFiles) { $guards[$file] = (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash }
$record = @{status='registered';created=(Get-Date).ToUniversalTime().ToString('o');guards=$guards;run_ids=@('AI_E7_v3_presence_reference','AI_E8_v3_presence_supervision');single_factor='Supervised shared presence branch balanced BCE coefficient0 vs1';test_evaluated=$false;calibration_fit=$false;promotion=$false;source_sha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash}
$record | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $recordPath
try {
    foreach ($plan in @(@{name='AI_E7_v3_presence_reference';weight=0},@{name='AI_E8_v3_presence_supervision';weight=1})) {
        foreach ($file in $guardFiles) {
            if ((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash -ne $guards[$file]) { throw "Registered input changed: $file" }
        }
        $active = @(Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -match 'tools[\\/]train_(baseline|pipeline|reliability_candidate|ai_presence_candidate).py' })
        if ($active.Count -gt 0) { throw 'Another workspace trainer remains active; do not duplicate GPU work.' }
        $run = 'experiments/'+$plan.name
        if (Test-Path -LiteralPath $run) { throw "Candidate output exists: $run; never overwrite." }
        $record.status='training';$record.current=$plan.name;$record.presence_weight=$plan.weight
        $record | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $recordPath
        $env:OMP_NUM_THREADS='2';$env:MKL_NUM_THREADS='2';$env:CUBLAS_WORKSPACE_CONFIG=':4096:8'
        & '.venv-phase2/Scripts/python.exe' tools/train_ai_presence_candidate.py --out $run --presence-weight $plan.weight 1> (Join-Path $session ($plan.name+'.log')) 2> (Join-Path $session ($plan.name+'.stderr.log'))
        if ($LASTEXITCODE -ne 0) { throw "Trainer failed: $($plan.name); retain evidence and diagnose/resume." }
        & '.venv-phase2/Scripts/python.exe' tools/record_ai_loop.py --observation "Completed registered $($plan.name) training; head-only accuracy is insufficient, full independent native mask audit and conservative alert burden remain required. No CAL/test/promotion."
        if ($LASTEXITCODE -ne 0) { throw 'Research progress recording failed.' }
    }
    $leftInitial = Get-Content -LiteralPath 'experiments/AI_E7_v3_presence_reference/initial_parameters.json' -Raw | ConvertFrom-Json
    $rightInitial = Get-Content -LiteralPath 'experiments/AI_E8_v3_presence_supervision/initial_parameters.json' -Raw | ConvertFrom-Json
    if ($leftInitial.full_parameter_sha256 -ne $rightInitial.full_parameter_sha256) { throw 'Matched initial tensors differed; do not claim a causal branch effect.' }
    $record.status='completed_training_only';$record.initialization_matched=$true
    $record.next='Full same463 native audits, head/mask/four-group failures, calibration diagnostics and matched learning curves; reject unmet gates and continue the evidence-based loop. No automatic CAL/test/promotion.'
} catch {
    $record.status='failed';$record.error=$_.Exception.Message
} finally {
    $record.updated=(Get-Date).ToUniversalTime().ToString('o')
    $record | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $recordPath
}
