param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("codex", "claude", "both")]
    [string]$Target,
    [switch]$Replace
)
$ErrorActionPreference = "Stop"
$Arguments = @((Join-Path $PSScriptRoot "install_skill.py"), "--target", $Target)
if ($Replace) { $Arguments += "--replace" }
if (Get-Command python -ErrorAction SilentlyContinue) {
    & python @Arguments
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 @Arguments
} else {
    throw "Python 3.11 or newer is required"
}
if ($LASTEXITCODE -ne 0) { throw "Skill installation failed" }
