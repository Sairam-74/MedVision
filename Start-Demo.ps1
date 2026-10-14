param([switch]$UseCuda)
if ($UseCuda) {throw 'Use the isolated CPU feature environment.'}
& (Join-Path $PSScriptRoot 'Start-Feature.ps1')
