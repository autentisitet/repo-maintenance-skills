---
name: powershell-quality
description: Use when writing, modifying, or reviewing PowerShell scripts (.ps1) or modules (.psm1), including cmdlet/CIM/.NET selection, resource and handle cleanup, parameter and pipeline design, error handling, and sensitive operations. Do not use for cmd.exe batch files, other scripting languages, or one-off commands that do not need a script file.
metadata:
  short-description: Review PowerShell scripts for cmdlets, cleanup, and errors
---

# PowerShell Quality

## Tool Selection

- Prefer built-in cmdlets and CIM (`Get-CimInstance`) over WMI (`Get-WmiObject`, removed in PowerShell 6+) and over COM. Use .NET classes only when no cmdlet or CIM equivalent exists, and COM only when no .NET API exists.
- Prefer PowerShell-native commands over cmd.exe built-ins inside `.ps1` files.
- Default to a plain script or advanced function. Do not create third-party module dependencies unless the task requires them; when a module is required, state it explicitly.

---

## Resource and Handle Cleanup

When a .NET call returns a handle, stream, or other disposable object, release it with
`try/finally` and call `Dispose()` in `finally`. PowerShell `using` imports namespaces,
modules, or assemblies; it is not C#'s resource-disposal statement:

```powershell
$fs = [System.IO.File]::OpenWrite('C:\file.txt')
try {
    $fs.Write([byte[]]@(1, 2, 3), 0, 3)
}
finally {
    $fs.Dispose()
}
```

---

## Conventions

- Put `$null` on the left in comparisons: `if ($null -eq $obj) { ... }`.
- Parse values with `[type]::TryParse($value, [ref]$parsed)` first, `[type]::Parse($value)` second, and direct casts last. Avoid `[ref]` otherwise; if it is needed, reconsider whether the pipeline or a hashtable would be cleaner.
- Avoid `[System.*]` calls when a cmdlet does the same job; when a .NET call is justified, mention why.
- Do not create persistent environment variables or machine-scope settings by default. If one is needed, tell the user first.
- Prefer data-driven, pipeline-oriented code over object-oriented or functional abstractions. Use splatting for parameter binding:

```powershell
$params = @{
    Path = $path
    Recurse = $true
    Filter = '*.log'
    Force = $true
    ErrorAction = 'SilentlyContinue'
}
Get-ChildItem @params
```

Must not:

- Elevate with `Start-Process -Verb RunAs` merely to sidestep permission errors; request explicit user approval instead.
- Use COM (`Shell.Application`, `WScript.Shell`) for file operations; use native cmdlets or .NET.
- Emit tokens, environment variables, authorization headers, or user data to output; redact before external output.

---

## Script Structure

- Add `[CmdletBinding()]` and `param()` to scripts and advanced functions.
- Declare dependencies with `#Requires` instead of hand-written checks:

```powershell
#Requires -Version 5.1
#Requires -RunAsAdministrator
#Requires -Modules @{ ModuleName = 'PSReadLine'; ModuleVersion = '2.0' }
```

- Use `#region` / `#endregion` only for large logical groups.
- Add comment-based help (`<# .SYNOPSIS ... #>`) with `SYNOPSIS`, `DESCRIPTION`, `PARAMETER`, `EXAMPLE`, and `NOTES`.
- Enable `Set-StrictMode -Version Latest`.
- Resolve sibling files with `$PSScriptRoot`; use `$MyInvocation` for script name, path, and line logging.
- Name custom functions with an approved verb-noun pair.

---

## Parameters

- Support `-Verbose` and `-WhatIf` for state-changing operations; support `-Confirm` for destructive operations.
- Keep parameters typed and keep splat keys aligned with real parameter or property names; an unknown key raises a parameter-binding error.

---

## Pipeline

- Stream objects instead of collecting them: `Get-Process | Where-Object { $_.CPU -gt 10 } | Stop-Process` beats storing intermediate arrays.
- Combine conditions into one `Where-Object` instead of chaining several.
- Use `-Filter` for provider-level filtering where the provider supports it. `-Include` filters after enumeration and only applies with `-Recurse` or a wildcard path; it is not a faster alternative to `Where-Object`.
- Do not call `Format-*` inside loops; format once for final output.
- For large collections, prefer `List[T]` (or `ArrayList`) over repeated `$array +=` concatenation, which copies the whole array each time.
- Suppress output with `[void]` or `$null = ...` rather than `Out-Null`.

---

## Error Handling

- Keep `$ErrorActionPreference` at its default (`Continue`) unless the whole script must stop on the first non-terminating error. Setting it to `Stop` promotes non-terminating errors to terminating ones for that scope; it does not terminate the operating system process.
- `try/catch/finally` handles terminating errors only. A `catch` that swallows an error without rethrowing hides it from outer scopes and breaks the error chain; rethrow or report deliberately.
- `-ErrorAction` (including `SilentlyContinue`) affects only non-terminating errors. It does not downgrade a terminating error, such as a failing .NET method, into a non-terminating one; handle those with `try/catch`.
- Standard cmdlets usually emit non-terminating errors; .NET calls and `throw` emit terminating errors. Use `-ErrorAction Stop` to promote a non-terminating error so `try/catch` can handle it.
- External or native commands set `$LASTEXITCODE` and do not populate `$Error` or honor `-ErrorAction`; check `$LASTEXITCODE -ne 0` explicitly (or enable `$PSNativeCommandUseErrorActionPreference` in PowerShell 7.3+).
- `Write-Warning` prints a warning without affecting logic. `Write-Error` emits a non-terminating error. `throw` emits a terminating error.
- `$Error` holds the session error list; `$?` reports whether the previous command succeeded.

---

## Sensitive Operations

- Do not run `Set-ExecutionPolicy`, UAC changes, registry writes (for example drive mapping), `Diskpart`, or similar sensitive commands automatically. Show the command and its rationale and let the user run it manually.
- Do not change persistent environment variables, machine state, or execution policy without the user's explicit instruction.

---

## Gotchas

- `[void]$x` and `$null = $x` both suppress output; `[void]` is faster.
- `Write-Progress` has no `-ForegroundColor` parameter; an unknown splat key raises a parameter-binding error.
- `Get-WmiObject` is removed in PowerShell 6+; use `Get-CimInstance`.

---

## Report

Report the script's purpose, the cmdlet/CIM/.NET/COM choices made and why, resources that are created and how they are released, the error-handling approach, and any sensitive operations left for the user to run manually.
