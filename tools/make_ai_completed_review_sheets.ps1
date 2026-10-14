param(
    [Parameter(Mandatory=$true)][string]$Audit,
    [Parameter(Mandatory=$true)][string]$Out,
    [Parameter(Mandatory=$true)][ValidateSet('normal_alerts','positive_segmentation_errors')][string]$Selection
)
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$auditPath = [IO.Path]::GetFullPath((Join-Path $root $Audit))
$outPath = [IO.Path]::GetFullPath((Join-Path $root $Out))
$prefix = $root.TrimEnd('\') + '\'
foreach ($path in @($auditPath,$outPath)) {
    if (-not $path.StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase)) { throw 'Workspace paths required' }
}
if (Test-Path -LiteralPath $outPath) { throw 'Exclusive output directory required' }
function File-Sha([string]$path) { (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLowerInvariant() }
$completion = Get-Content -Raw -LiteralPath (Join-Path $auditPath 'completion.json') | ConvertFrom-Json
if ($completion.status -ne 'completed') { throw 'Completed audit required' }
$casePath = Join-Path $auditPath 'per_case.json'
$casesSha = File-Sha $casePath
if ($casesSha -ne $completion.cases_sha256 -or
    (File-Sha (Join-Path $auditPath 'metrics.json')) -ne $completion.metrics_sha256) { throw 'Completed audit hashes differ' }
$all = @(Get-Content -Raw -LiteralPath $casePath | ConvertFrom-Json)
if ($all.Count -ne 463 -or @($all.image_id | Sort-Object -Unique).Count -ne 463) { throw 'Full unique validation cases required' }
if ($Selection -eq 'normal_alerts') {
    $selected = @($all | Where-Object { -not $_.positive -and $_.review_alert_present })
    $perSheet = 9; $columns = 3; $tileW = 614
} else {
    $selected = @($all | Where-Object { $_.positive -and $_.segmentation_failure_tags.Count -gt 0 })
    $perSheet = 6; $columns = 2; $tileW = 900
}
Add-Type -AssemblyName System.Drawing
$null = New-Item -ItemType Directory -Path $outPath
$font = New-Object Drawing.Font('Arial',11)
$smallFont = New-Object Drawing.Font('Arial',10)
$sheets = @()
try {
    for ($start = 0; $start -lt $selected.Count; $start += $perSheet) {
        $sheet = New-Object Drawing.Bitmap(($columns*$tileW),1500)
        $canvas = [Drawing.Graphics]::FromImage($sheet)
        $canvas.Clear([Drawing.Color]::Black)
        $canvas.InterpolationMode = [Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
        $members = @()
        try {
            $take = [Math]::Min($perSheet,$selected.Count-$start)
            for ($offset = 0; $offset -lt $take; $offset++) {
                $case = $selected[$start+$offset]
                $panelPath = [IO.Path]::GetFullPath((Join-Path $auditPath $case.review_panel))
                if (-not $panelPath.StartsWith(($auditPath+'\'),[StringComparison]::OrdinalIgnoreCase)) { throw 'Native panel outside audit' }
                $panelSha = File-Sha $panelPath
                $panel = [Drawing.Image]::FromFile($panelPath)
                try {
                    if ($panel.Height -ne 454 -or $panel.Width % 3 -ne 0) { throw 'Complete native three-column panel required' }
                    $columnW = [int]($panel.Width/3)
                    $row = [int][Math]::Floor($offset/$columns); $column = $offset % $columns
                    $x = $column*$tileW; $y = $row*500
                    $caption = if ($Selection -eq 'normal_alerts') { 'Original | independent mask (red)' } else { 'Original | annotation (green) | independent mask (red)' }
                    $label = if ($case.positive) { '{0} {1} Dice={2:F3} IoU={3:F3}' -f $case.image_id,$case.category,$case.dice,$case.iou } else { '{0} mask{1} score={2:F3}' -f $case.image_id,$case.category,$case.case_score }
                    $canvas.DrawString($label,$font,[Drawing.Brushes]::White,[single]($x+5),[single]($y+3))
                    $canvas.DrawString($caption,$smallFont,[Drawing.Brushes]::White,[single]($x+5),[single]($y+24))
                    if ($Selection -eq 'normal_alerts') {
                        $scale = [Math]::Min($tileW/(2.0*$columnW),445.0/384)
                        $dw = [single]($columnW*$scale); $dh = [single](384*$scale)
                        $canvas.DrawImage($panel,(New-Object Drawing.RectangleF($x,($y+50),$dw,$dh)),(New-Object Drawing.RectangleF(0,70,$columnW,384)),[Drawing.GraphicsUnit]::Pixel)
                        $canvas.DrawImage($panel,(New-Object Drawing.RectangleF(($x+$dw),($y+50),$dw,$dh)),(New-Object Drawing.RectangleF((2*$columnW),70,$columnW,384)),[Drawing.GraphicsUnit]::Pixel)
                    } else {
                        $scale = [Math]::Min($tileW/[double]$panel.Width,445.0/$panel.Height)
                        $canvas.DrawImage($panel,[single]$x,[single]($y+50),[single]($panel.Width*$scale),[single]($panel.Height*$scale))
                    }
                    $members += [ordered]@{image_id=$case.image_id; panel=$case.review_panel; panel_sha256=$panelSha; positive=$case.positive; category=$case.category; dice=$case.dice; iou=$case.iou; tags=$case.segmentation_failure_tags; case_score=$case.case_score}
                } finally { $panel.Dispose() }
            }
            $name = 'sheet_{0:D2}.jpg' -f ([int]($start/$perSheet)+1)
            $sheet.Save((Join-Path $outPath $name),[Drawing.Imaging.ImageFormat]::Jpeg)
            $sheets += [ordered]@{sheet=$name; cases=$members}
        } finally { $canvas.Dispose(); $sheet.Dispose() }
    }
} finally { $font.Dispose(); $smallFont.Dispose() }
if ((File-Sha $casePath) -ne $casesSha) { throw 'Completed cases changed during sheet generation' }
$index = [ordered]@{audit=$Audit.Replace('/','\'); selection=$Selection; images=$selected.Count; sheets=$sheets; total_selected_cases=$selected.Count; previously_reviewed_selected_ids=@(); excluded_review_directories=@(); source_sha256=(File-Sha $PSCommandPath); cases_sha256=$casesSha; inference_performed=$false; clinical_adjudication=$false; visual_review_completed=$false; scope='Complete actual retained native panels; generation is not actual viewing'}
[IO.File]::WriteAllText((Join-Path $outPath 'index.json'),($index | ConvertTo-Json -Depth 12),(New-Object Text.UTF8Encoding($false)))
[ordered]@{images=$selected.Count;sheets=$sheets.Count;visual_review_completed=$false} | ConvertTo-Json -Compress
