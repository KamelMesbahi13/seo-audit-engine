param(
    [string]$Url,
    [int]$MaxPages = 10
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptDir

if (-not $Url) {
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "  InersiaLab Software Department - SEO Audit Engine" -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
    $Url = Read-Host "Enter target URL to audit"
    $pagesInput = Read-Host "Enter max pages to crawl (default 10)"
    if ($pagesInput) { $MaxPages = [int]$pagesInput }
}

$py = if (Test-Path "$scriptDir\.venv\Scripts\python.exe") { "$scriptDir\.venv\Scripts\python.exe" } else { "python" }
& $py "$scriptDir\agy_seo.py" audit $Url --max-pages $MaxPages
