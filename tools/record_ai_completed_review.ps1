param([Parameter(Mandatory=$true)][string]$Directory,[string]$Batch,[switch]$Complete)
$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$directoryPath=[IO.Path]::GetFullPath((Join-Path $root $Directory))
if (-not $directoryPath.StartsWith(($root+'\'),[StringComparison]::OrdinalIgnoreCase)) {throw 'Workspace actual review required'}
function File-Sha([string]$path) {(Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLowerInvariant()}
function Write-Json([string]$path,$value) {[IO.File]::WriteAllText($path,($value|ConvertTo-Json -Depth 15),(New-Object Text.UTF8Encoding($false)))}
$indexPath=Join-Path $directoryPath 'index.json';$index=Get-Content -Raw -LiteralPath $indexPath|ConvertFrom-Json
$notesPath=Join-Path $directoryPath 'actual_sheet_notes.json'
$notes=if(Test-Path -LiteralPath $notesPath){Get-Content -Raw -LiteralPath $notesPath|ConvertFrom-Json}else{[pscustomobject]@{actually_viewed=$true;index_sha256=(File-Sha $indexPath);sheets=@()}}
if($notes.index_sha256 -ne (File-Sha $indexPath)){throw 'Index changed during actual review'}
if(Test-Path -LiteralPath (Join-Path $directoryPath 'completion.json')){throw 'Completed review must be preserved'}
if($Batch){
    $batchPath=[IO.Path]::GetFullPath((Join-Path $root $Batch))
    if(-not $batchPath.StartsWith(($root+'\'),[StringComparison]::OrdinalIgnoreCase)){throw 'Workspace actual observations required'}
    $observed=@(Get-Content -Raw -LiteralPath $batchPath|ConvertFrom-Json)
    $start=@($notes.sheets).Count
    for($i=0;$i -lt $observed.Count;$i++){
        if(($start+$i) -ge @($index.sheets).Count){throw 'Too many actual sheets'}
        $sheet=$index.sheets[$start+$i]
        if($observed[$i].sheet -ne $sheet.sheet -or @($observed[$i].notes).Count -ne @($sheet.cases).Count){throw 'Actual observation order/count differs'}
        foreach($note in $observed[$i].notes){if($note -isnot [string] -or -not $note.Trim()){throw 'Actual per-case note required'}}
    }
    $notes.sheets=@($notes.sheets)+$observed
    Write-Json $notesPath $notes
}
if($Complete){
    if(-not $notes.actually_viewed -or @($notes.sheets).Count -ne @($index.sheets).Count){throw 'Every sheet must actually be viewed'}
    $auditPath=[IO.Path]::GetFullPath((Join-Path $root $index.audit))
    if(-not $auditPath.StartsWith(($root+'\'),[StringComparison]::OrdinalIgnoreCase)){throw 'Workspace completed audit required'}
    $casePath=Join-Path $auditPath 'per_case.json'
    if((File-Sha $casePath) -ne $index.cases_sha256){throw 'Completed audit cases changed'}
    $all=@(Get-Content -Raw -LiteralPath $casePath|ConvertFrom-Json);$byId=@{}
    foreach($case in $all){if($byId.ContainsKey($case.image_id)){throw 'Duplicate source case'};$byId[$case.image_id]=$case}
    $required=if($index.selection -eq 'normal_alerts'){@($all|Where-Object{-not $_.positive -and $_.review_alert_present})}elseif($index.selection -eq 'positive_segmentation_errors'){@($all|Where-Object{$_.positive -and $_.segmentation_failure_tags.Count -gt 0})}else{throw 'Unsupported selection'}
    $seen=@{};$rows=@()
    for($i=0;$i -lt @($index.sheets).Count;$i++){
        $sheet=$index.sheets[$i];$observed=$notes.sheets[$i]
        if($sheet.sheet -ne $observed.sheet -or @($sheet.cases).Count -ne @($observed.notes).Count){throw 'Actual sheet alignment differs'}
        for($j=0;$j -lt @($sheet.cases).Count;$j++){
            $member=$sheet.cases[$j];$case=$byId[$member.image_id];$note=$observed.notes[$j]
            if($seen.ContainsKey($case.image_id) -or -not $note.Trim()){throw 'Duplicate or empty actual case observation'}
            $seen[$case.image_id]=$true
            if($member.panel -ne $case.review_panel){throw 'Linked native panel differs'}
            $panelPath=[IO.Path]::GetFullPath((Join-Path $auditPath $member.panel))
            if(-not $panelPath.StartsWith(($auditPath+'\'),[StringComparison]::OrdinalIgnoreCase)){throw 'Native panel outside audit'}
            $panelSha=File-Sha $panelPath
            if($panelSha -ne $member.panel_sha256){throw 'Actually reviewed native panel changed'}
            $rows += [ordered]@{image_id=$case.image_id;panel=$case.review_panel;panel_sha256=$panelSha;sheet=$sheet.sheet;observed_note=$note;positive=$case.positive;mask_category=$case.category;alert_category=$case.review_alert_category;head_mask_group=$case.head_mask_group;head_score=$case.head_score;dice=$case.dice;iou=$case.iou;tp_pixels=$case.tp_pixels;fp_pixels=$case.fp_pixels;fn_pixels=$case.fn_pixels;source_view_flags=($case.flags|ConvertTo-Json -Compress);clinical_cause='Unadjudicated';clinical_subtype='Unavailable'}
        }
    }
    if($seen.Count -ne $required.Count){throw 'Incomplete selected-case visual coverage'}
    foreach($case in $required){if(-not $seen.ContainsKey($case.image_id)){throw 'Missing actual selected-case observation'}}
    $rowPath=Join-Path $directoryPath 'per_case_visual_review.json';Write-Json $rowPath $rows
    $rows|ForEach-Object{[pscustomobject]$_}|Export-Csv -LiteralPath (Join-Path $directoryPath 'per_case_visual_review.csv') -NoTypeInformation
    $result=[ordered]@{status=('completed_actual_native_'+$index.selection+'_review');audit=$index.audit;selection=$index.selection;actual_new_case_reviews=$rows.Count;previously_reviewed_selected_cases=0;total_selected_cases=$required.Count;actual_sheets_reviewed=@($index.sheets).Count;per_case_review_sha256=(File-Sha $rowPath);index_sha256=(File-Sha $indexPath);notes_sha256=(File-Sha $notesPath);recorder_sha256=(File-Sha $PSCommandPath);new_inference=$false;no_label_changes=$true;clinical_adjudication=$false}
    Write-Json (Join-Path $directoryPath 'completion.json') $result
    $result|ConvertTo-Json -Compress
}else{[ordered]@{actual_sheets_recorded=@($notes.sheets).Count;total_sheets=@($index.sheets).Count;review_completed=$false}|ConvertTo-Json -Compress}
