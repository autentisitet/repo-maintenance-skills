#Requires -Version 5.1

<#
.SYNOPSIS
Removes only Codex skills installed by this repository on native Windows.

.DESCRIPTION
Removes junctions pointing to this checkout and copies bearing its installation marker.
Leaves unrelated links and directories untouched. Supports -WhatIf and -Confirm.

.EXAMPLE
.\scripts\links\uninstall.ps1 -WhatIf

.EXAMPLE
.\scripts\links\uninstall.ps1
#>
[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = "Medium")]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([System.Environment]::OSVersion.Platform -ne [System.PlatformID]::Win32NT) {
    throw "uninstall.ps1 is for native Windows only; use uninstall.sh on macOS, Linux, or WSL."
}

$Repo = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
$CodexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
$Dest = Join-Path $CodexHome "skills"
$MarkerName = ".repo-maintenance-skills-install"

if (-not (Test-Path -LiteralPath $Dest -PathType Container)) {
    Write-Host "No Codex skills directory: $Dest"
    return
}

Get-ChildItem -LiteralPath (Join-Path $Repo "skills") -Directory | ForEach-Object {
    $Name = $_.Name
    $Source = $_.FullName
    $Target = Join-Path $Dest $Name
    $Existing = Get-Item -LiteralPath $Target -Force -ErrorAction SilentlyContinue
    if ($null -eq $Existing) {
        return
    }

    $IsLink = ($Existing.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0
    $IsManaged = $false
    if ($IsLink -and $Existing.Target) {
        $LinkTarget = [System.IO.Path]::GetFullPath([string]$Existing.Target)
        $IsManaged = $LinkTarget -eq [System.IO.Path]::GetFullPath($Source)
    }
    elseif (-not $IsLink -and $Existing.PSIsContainer) {
        $Marker = Get-Item -LiteralPath (Join-Path $Target $MarkerName) -Force -ErrorAction SilentlyContinue
        if ($null -ne $Marker -and -not $Marker.PSIsContainer -and
            ($Marker.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -eq 0) {
            $IsManaged = (Get-Content -LiteralPath $Marker.FullName -Raw).Trim() -eq "repo-maintenance-skills:$Name"
        }
    }
    if (-not $IsManaged) {
        Write-Host "skip  $Name (unmanaged: $Target)"
        return
    }

    if ($PSCmdlet.ShouldProcess($Target, "Remove managed skill installation")) {
        if ($IsLink) {
            Remove-Item -LiteralPath $Target -Force
        }
        else {
            Remove-Item -LiteralPath $Target -Force -Recurse
        }
        Write-Host "remove  $Name"
    }
}
