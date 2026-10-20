[CmdletBinding()]
param(
    [switch]$Copy,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

if ([System.Environment]::OSVersion.Platform -ne [System.PlatformID]::Win32NT) {
    throw "install.ps1 只用于原生 Windows；macOS、Linux 或 WSL 请运行 install.sh。"
}

$Repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$CodexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
$Dest = Join-Path $CodexHome "skills"
$MarkerName = ".repo-maintenance-skills-install"

New-Item -ItemType Directory -Path $Dest -Force | Out-Null
Write-Host "安装目标: $Dest"

Get-ChildItem (Join-Path $Repo "skills") -Directory | ForEach-Object {
    $Name = $_.Name
    $Source = $_.FullName
    $Target = Join-Path $Dest $Name
    $Existing = Get-Item -LiteralPath $Target -Force -ErrorAction SilentlyContinue

    if ($Existing -and -not $Force) {
        Write-Host "skip  $Name（已存在：$Target）"
    }
    else {
        if ($Existing) {
            $IsLink = ($Existing.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0
            $IsManaged = $false
            if ($IsLink -and $Existing.Target) {
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
                throw "拒绝替换非本项目管理的 skill: $Target。请先手动备份或移走该目录。"
            }
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
            New-Item -ItemType Junction -Path $Target -Target $Source | Out-Null
            Write-Host "link  $Name"
        }
    }
}

Write-Host '完成。在 Codex 中用 $<skill-name> 调用。'
