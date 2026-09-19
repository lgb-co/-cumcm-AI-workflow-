<#
.SYNOPSIS  为「查看/编辑版 DOCX（Word 原生公式）」建立独立导出环境。
.DESCRIPTION
  在 工具\md2docx_env 建 venv，安装 pypandoc_binary（自带 pandoc）与 python-docx，
  并把解释器与 pandoc 路径写入 工具\环境配置.json。安装包脚本 install.ps1 -SetupTools 会调用本脚本。
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\setup-md2docx.ps1
  powershell -ExecutionPolicy Bypass -File .\setup-md2docx.ps1 -EnvPath D:\venvs\md2docx -Force
#>
[CmdletBinding()]
param(
    [string]$EnvPath,
    [string]$Python,
    [switch]$Force
)
$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [Text.UTF8Encoding]::new($false) } catch { }
$env:PYTHONUTF8 = '1'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path

function Find-Python {
    param([string]$Hint)
    if ($Hint -and (Test-Path -LiteralPath $Hint)) { return $Hint }
    foreach ($name in @($env:CUMCM_PYTHON, $env:MODELING_PY, $env:CUMCM_CODE_ENV)) {
        if (-not $name) { continue }
        $cand = $name
        if (Test-Path -LiteralPath $cand -PathType Container) {
            $cand = Join-Path $cand 'Scripts\python.exe'
            if (-not (Test-Path -LiteralPath $cand)) { $cand = Join-Path $name 'python.exe' }
        }
        if (Test-Path -LiteralPath $cand) { return $cand }
    }
    foreach ($name in @('python.exe', 'python3.exe', 'python', 'python3')) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if ($cmd -and $cmd.Source -notmatch 'WindowsApps') { return $cmd.Source }
    }
    $runtime = Join-Path $env:USERPROFILE '.cache\codex-runtimes'
    if (Test-Path -LiteralPath $runtime) {
        $found = Get-ChildItem -LiteralPath $runtime -Filter python.exe -Recurse -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -match 'dependencies[\\/]python[\\/]python\.exe$' } | Select-Object -First 1
        if ($found) { return $found.FullName }
    }
    throw '找不到可用 Python。请安装 Python 3.11+，或设置 CUMCM_PYTHON 指向解释器后重试。'
}

if (-not $EnvPath) { $EnvPath = Join-Path $here 'md2docx_env' }
$EnvPath = [IO.Path]::GetFullPath($EnvPath)
$venvPy = Join-Path $EnvPath 'Scripts\python.exe'
if (-not (Test-Path -LiteralPath $venvPy)) {
    $py = Find-Python -Hint $Python
    Write-Output ('创建导出环境，使用解释器：' + $py)
    $venvArgs = @('-m', 'venv')
    if ($Force) { $venvArgs += '--clear' }
    $venvArgs += $EnvPath
    & $py @venvArgs
    if ($LASTEXITCODE -ne 0) { throw '创建 venv 失败（python -m venv）。' }
}
$req = Join-Path $here 'requirements-tools.txt'
if (-not (Test-Path -LiteralPath $req)) { throw ('缺少依赖清单：' + $req) }
Write-Output '安装 pypandoc_binary / python-docx（首次需联网）…'
& $venvPy -m pip install --disable-pip-version-check -r $req
if ($LASTEXITCODE -ne 0) { throw 'pip 安装失败：可配置代理，或先用离线 wheel 装好后重跑本脚本。' }

$pandoc = ''
try { $pandoc = (& $venvPy -c "import pypandoc;print(pypandoc.get_pandoc_path())" 2>$null).Trim() } catch { $pandoc = '' }
$cfg = [ordered]@{
    python       = $venvPy
    pandoc       = $pandoc
    env_path     = $EnvPath
    installed_at = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
    note         = '由 setup-md2docx.ps1 生成；可用 CUMCM_PYTHON / MODELING_PY 覆盖'
}
$cfgPath = Join-Path $here '环境配置.json'
($cfg | ConvertTo-Json -Depth 3) | Set-Content -LiteralPath $cfgPath -Encoding utf8
Write-Output ''
Write-Output ('导出环境就绪：' + $venvPy)
if ($pandoc) { Write-Output ('pandoc：' + $pandoc) } else { Write-Warning '未取到 pandoc 路径；md2docx_native.py 首次运行时会自行补装。' }
Write-Output ('配置已写入：' + $cfgPath)
Write-Output ''
Write-Output '用法：'
Write-Output ('  & "' + $venvPy + '" "' + (Join-Path $here 'md2docx_native.py') + '" <输入.md> <输出.docx>')
