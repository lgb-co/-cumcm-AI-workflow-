<#
.SYNOPSIS
    CUMCM 工作流统一命令行入口。
.EXAMPLE
    .\cumcm-flow.ps1 doctor
    .\cumcm-flow.ps1 init "D:\工作区\运行\2026A-题目"
#>
[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Arguments
)
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$script = Join-Path $here 'cumcm_flow.py'
if (-not (Test-Path -LiteralPath $script -PathType Leaf)) { throw ('缺少 CLI：' + $script) }

function Resolve-Python {
    function Test-Candidate([string]$candidate) {
        if (-not $candidate) { return $null }
        $candidate = $candidate.Trim().Trim([char]34)
        if (Test-Path -LiteralPath $candidate -PathType Container) {
            $venv = Join-Path $candidate 'Scripts\python.exe'
            if (Test-Path -LiteralPath $venv -PathType Leaf) { $candidate = $venv }
            else { $candidate = Join-Path $candidate 'python.exe' }
        }
        if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) { return $null }
        if ($candidate -match '[\\/]WindowsApps[\\/]') { return $null }
        try {
            $probe = @(& $candidate -c 'import sys; print(sys.executable); print(sys.version_info[0], sys.version_info[1], sys.version_info[2])' 2>$null | ForEach-Object { [string]$_ })
            if ($LASTEXITCODE -ne 0 -or $probe.Count -lt 2) { return $null }
            $parts = @($probe[$probe.Count - 1].Trim() -split '\s+')
            if ($parts.Count -lt 2 -or ([int]$parts[0] -lt 3) -or ([int]$parts[0] -eq 3 -and [int]$parts[1] -lt 11)) { return $null }
            $resolved = $probe[$probe.Count - 2].Trim()
            if (Test-Path -LiteralPath $resolved -PathType Leaf) { return $resolved }
            return $candidate
        } catch { return $null }
    }
    $configured = @()
    $configPath = Join-Path $here 'python.path'
    if (Test-Path -LiteralPath $configPath -PathType Leaf) {
        try { $configured += (Get-Content -LiteralPath $configPath -Raw -ErrorAction Stop).Trim() } catch { }
    }
    foreach ($value in @($configured + $env:CUMCM_CODE_ENV, $env:CUMCM_PYTHON, $env:MODELING_PY)) {
        if (-not $value) { continue }
        # The value may point at a venv or interpreter.  Do not use a
        # localized relative path here; environment variables are portable.
        $candidate = Test-Candidate $value
        if ($candidate) { return $candidate }
    }
    foreach ($name in @('python.exe','python3.exe','python','python3')) {
        $command = Get-Command $name -ErrorAction SilentlyContinue
        if ($command -and $command.Source -notmatch 'WindowsApps') {
            $candidate = Test-Candidate $command.Source
            if ($candidate) { return $candidate }
        }
    }
    $launcher = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($launcher) {
        try {
            $probe = @(& $launcher.Source -3 -c 'import sys; print(sys.executable); print(sys.version_info[0], sys.version_info[1], sys.version_info[2])' 2>$null | ForEach-Object { [string]$_ })
            $parts = if ($probe.Count -ge 2) { @($probe[$probe.Count - 1].Trim() -split '\s+') } else { @() }
            if ($LASTEXITCODE -eq 0 -and $probe.Count -ge 2 -and $parts.Count -ge 2 -and ([int]$parts[0] -gt 3 -or ([int]$parts[0] -eq 3 -and [int]$parts[1] -ge 11))) {
                $resolved = $probe[$probe.Count - 2].Trim()
                if (Test-Path -LiteralPath $resolved -PathType Leaf) { return $resolved }
            }
        } catch { }
    }
    foreach ($version in @('311','312','313','314','315')) {
        foreach ($candidate in @(
            (Join-Path $env:LOCALAPPDATA ('Programs\Python\Python' + $version + '\python.exe')),
            (Join-Path $env:ProgramFiles ('Python' + $version + '\python.exe'))
        )) {
            $resolved = Test-Candidate $candidate
            if ($resolved) { return $resolved }
        }
    }
    return $null
}

$python = Resolve-Python
if (-not $python) { throw '找不到 Python 3.11+；请安装 Python 或设置 CUMCM_PYTHON。' }
if ([IO.Path]::GetFileName($python) -ieq 'py.exe') {
    & $python -3 $script @Arguments
} else {
    & $python $script @Arguments
}
exit $LASTEXITCODE
