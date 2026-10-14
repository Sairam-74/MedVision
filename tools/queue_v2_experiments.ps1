# Sequential, source-guarded experiments. Never evaluates the reserved test set.
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
$queueDirectory = 'experiments/session_20261006_p6p7'
$queueState = Join-Path $queueDirectory 'training_queue.json'
$guardFiles = @('medvision_ai.py','medvision_pipeline.py','tools/train_pipeline.py','tools/run_experiment.py','experiments/data_v2/manifest.json','FracAtlas.zip','best_model.pt')
$sourceGuards = @{}
foreach ($guardFile in $guardFiles) { $sourceGuards[$guardFile] = (Get-FileHash -LiteralPath $guardFile -Algorithm SHA256).Hash }
$queueRecord = @{status='waiting_for_E2';created=(Get-Date).ToUniversalTime().ToString('o');guards=$sourceGuards;runs=@('E3_v2_logits_bce_dice','E4_v2_logits_focal_tversky');test_evaluated=$false;runtime='.venv-demo torch2.14.1+cpu'}
$queueRecord | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $queueState
try {
    while ($true) {
        $precedingState = $null
        try { $precedingState = Get-Content -LiteralPath 'experiments/E2_corrected_baseline/state.json' -Raw | ConvertFrom-Json } catch {}
        if ($precedingState.status -eq 'completed') { break }
        # No independent trainer is launched over a still-active E2 run.
        Start-Sleep -Seconds 30
    }
    foreach ($planned in @(@{name='E3_v2_logits_bce_dice';loss='bce_dice'},@{name='E4_v2_logits_focal_tversky';loss='focal_tversky'})) {
        foreach ($guardFile in $guardFiles) {
            if ((Get-FileHash -LiteralPath $guardFile -Algorithm SHA256).Hash -ne $sourceGuards[$guardFile]) { throw "Source/artifact changed before queued run: $guardFile" }
        }
        $queueRecord.status='running';$queueRecord.current=$planned.name
        $queueRecord | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $queueState
        $env:OMP_NUM_THREADS='2';$env:MKL_NUM_THREADS='2'
        $runDirectory = 'experiments/' + $planned.name
        $runLog = Join-Path $queueDirectory ($planned.name + '.log')
        & '.venv-demo/Scripts/python.exe' tools/train_pipeline.py --out $runDirectory --manifest experiments/data_v2/manifest.json --epochs 12 --batch-size 2 --lr 0.0001 --size 256 --resize letterbox --blur 0 --normalization unit --loss $planned.loss --positive-fraction 0.5 --seed 42 --patience 5 --device cpu *> $runLog
        if ($LASTEXITCODE -ne 0) { throw "Queued training failed: $($planned.name). Preserve its checkpoint and inspect $runLog" }
    }
    $queueRecord.status='completed_training_only'
} catch {
    $queueRecord.status='failed';$queueRecord.error=$_.Exception.Message
} finally {
    $queueRecord.updated=(Get-Date).ToUniversalTime().ToString('o')
    $queueRecord | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $queueState
}
