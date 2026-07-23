[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("ran-mouri-chibi", "porco-rosso-chibi", "mitsuha-miyamizu-chibi")]
    [string]$Pet
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
& (Join-Path $Root "pets\$Pet\ready-to-use\install.ps1")
