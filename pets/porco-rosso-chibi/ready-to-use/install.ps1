[CmdletBinding()]
param(
    [string]$CodexHome = $(if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" })
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Manifest = Join-Path $Root "pet.json"
$Spritesheet = Join-Path $Root "spritesheet.webp"
$Destination = Join-Path $CodexHome "pets\porco-rosso-chibi-v1"
foreach ($RequiredFile in @($Manifest, $Spritesheet)) {
    if (-not (Test-Path -LiteralPath $RequiredFile -PathType Leaf) -or (Get-Item -LiteralPath $RequiredFile).Length -le 0) {
        throw "Package incomplete: $RequiredFile"
    }
}
New-Item -ItemType Directory -Force -Path $Destination | Out-Null
Copy-Item -LiteralPath $Manifest -Destination (Join-Path $Destination "pet.json") -Force
Copy-Item -LiteralPath $Spritesheet -Destination (Join-Path $Destination "spritesheet.webp") -Force
Write-Host "Installed Porco Rosso Chibi Codex Pet to: $Destination"
Write-Host "Fully quit and restart Codex Desktop."
