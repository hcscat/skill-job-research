param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("codex", "claude", "both")]
    [string]$Target,
    [switch]$Replace
)

$Root = Split-Path -Parent $PSScriptRoot
$Source = Join-Path $Root "skills/job-research-match"

function Install-Skill([string]$Agent) {
    if ($Agent -eq "codex") {
        $Base = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
    } else {
        $Base = if ($env:CLAUDE_CONFIG_DIR) { $env:CLAUDE_CONFIG_DIR } else { Join-Path $HOME ".claude" }
    }
    $Parent = Join-Path $Base "skills"
    $BackupParent = Join-Path $Base "skill-backups"
    $Destination = Join-Path $Parent "job-research-match"
    New-Item -ItemType Directory -Force -Path $Parent | Out-Null
    if (Test-Path $Destination) {
        if (-not $Replace) {
            throw "Destination exists: $Destination (use -Replace)"
        }
        New-Item -ItemType Directory -Force -Path $BackupParent | Out-Null
        $Backup = Join-Path $BackupParent "job-research-match.backup.$(Get-Date -Format yyyyMMddHHmmss)"
        Move-Item $Destination $Backup
        Write-Output "Backed up existing skill to $Backup"
    }
    Copy-Item -Recurse $Source $Destination
    Get-ChildItem -Path $Destination -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
    Get-ChildItem -Path $Destination -Recurse -File -Include "*.pyc", ".DS_Store" | Remove-Item -Force
    $Python = Get-Command python -ErrorAction SilentlyContinue
    $PyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($Python) {
        & $Python.Source (Join-Path $Destination "scripts/local_state.py") init | Out-Null
        Write-Output "${Agent}: initialized private local state"
    } elseif ($PyLauncher) {
        & $PyLauncher.Source -3 (Join-Path $Destination "scripts/local_state.py") init | Out-Null
        Write-Output "${Agent}: initialized private local state"
    } else {
        Write-Warning "${Agent}: Python 3 not found; run local_state.py init before first use"
    }
    Write-Output "${Agent}: $Destination"
}

if ($Target -eq "both") {
    Install-Skill "codex"
    Install-Skill "claude"
} else {
    Install-Skill $Target
}
