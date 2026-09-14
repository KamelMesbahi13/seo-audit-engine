# PowerShell wrapper for agy-seo
$SkillDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe = Join-Path $SkillDir ".venv\Scripts\python.exe"
$AgySeoPy = Join-Path $SkillDir "agy_seo.py"

if (-not (Test-Path $PythonExe)) {
    Write-Error "Python virtual environment not found at $PythonExe"
    exit 1
}

& $PythonExe $AgySeoPy @args
