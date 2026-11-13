#Requires -Version 5.1

<#
.SYNOPSIS
Installs this repository's Codex skills on native Windows.

.DESCRIPTION
Creates junctions by default or managed copies with -Copy. Existing targets are skipped unless
-Force is supplied, and -Force replaces only targets previously managed by this repository.

.PARAMETER Copy
Copies each skill instead of creating a junction.

.PARAMETER Force
Replaces an existing managed junction or copy. Unmanaged targets are never removed.

.EXAMPLE
.\scripts\links\install.ps1

.EXAMPLE
.\scripts\links\install.ps1 -Copy -Force -WhatIf

.NOTES
Use install.sh on macOS, Linux, or WSL. The script does not require elevation or modify persistent
environment variables.
#>
[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = "Medium")]
param(
    [switch]$Copy,
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([System.Environment]::OSVersion.Platform -ne [System.PlatformID]::Win32NT) {
    throw "install.ps1 is for native Windows only; use install.sh on macOS, Linux, or WSL."
}

$Repo = (Resolve-Path (Join-Path $PSScriptRoot "../..")).Path
$CodexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
$Dest = Join-Path $CodexHome "skills"
$MarkerName = ".repo-maintenance-skills-install"

if (-not (Test-Path -LiteralPath $Dest -PathType Container)) {
    if ($PSCmdlet.ShouldProcess($Dest, "Create Codex skills directory")) {
        $null = New-Item -ItemType Directory -Path $Dest -Force
    }
}
Write-Host "Install destination: $Dest"

Get-ChildItem (Join-Path $Repo "skills") -Directory | ForEach-Object {
    $Name = $_.Name
    $Source = $_.FullName
    $Target = Join-Path $Dest $Name
    $Existing = Get-Item -LiteralPath $Target -Force -ErrorAction SilentlyContinue

    if ($null -ne $Existing -and -not $Force) {
        Write-Host "skip  $Name (already exists: $Target)"
    }
    else {
        if ($null -ne $Existing) {
            $IsLink = ($Existing.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0
            $IsManaged = $false
            if ($IsLink -and $Existing.Target) {
                # Resolve both sides with .NET because junction targets are not normalized by Get-Item.
                $LinkTarget = [System.IO.Path]::GetFullPath([string]$Existing.Target)
                $IsManaged = $LinkTarget -eq [System.IO.Path]::GetFullPath($Source)
            }
            else {
                $Marker = Join-Path $Target $MarkerName
                if (Test-Path -LiteralPath $Marker -PathType Leaf) {
                    $IsManaged = (Get-Content -LiteralPath $Marker -Raw).Trim() -eq "repo-maintenance-skills:$Name"
                }
            }
            if (-not $IsManaged) {
                throw "Refusing to replace an unmanaged skill: $Target. Back it up or move it explicitly first."
            }
        }

        $Action = if ($Copy) { "Install managed skill copy" } else { "Install skill junction" }
        if ($null -ne $Existing) {
            $Action = "Replace managed target and $($Action.ToLowerInvariant())"
        }
        if (-not $PSCmdlet.ShouldProcess($Target, $Action)) {
            return
        }

        if ($null -ne $Existing) {
            if ($IsLink) {
                Remove-Item -LiteralPath $Target -Force
            }
            else {
                Remove-Item -LiteralPath $Target -Force -Recurse
            }
        }

        if ($Copy) {
            Copy-Item -LiteralPath $Source -Destination $Target -Recurse
            Set-Content -LiteralPath (Join-Path $Target $MarkerName) -Value "repo-maintenance-skills:$Name"
            Write-Host "copy  $Name"
        }
        else {
            $null = New-Item -ItemType Junction -Path $Target -Target $Source
            Write-Host "link  $Name"
        }
    }
}

Write-Host 'Done. Invoke a skill in Codex with $<skill-name>.'
