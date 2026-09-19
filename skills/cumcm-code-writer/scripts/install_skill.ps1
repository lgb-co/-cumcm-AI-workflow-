# 把「数模代码编写」技能安装到 Codex 的全局技能目录。
#
# 用法：
#   powershell -ExecutionPolicy Bypass -File install_skill.ps1
#   powershell -ExecutionPolicy Bypass -File install_skill.ps1 -Force
#   powershell -ExecutionPolicy Bypass -File install_skill.ps1 -TargetRoot "D:\somewhere\.codex\skills"
#   powershell -ExecutionPolicy Bypass -File install_skill.ps1 -KeepOutputs
#
# 行为：复制技能文件到 <目标>/cumcm-code-writer；默认排除 work、output、__pycache__、.git、
#       环境配置.json 与算法库 out/ 运行产物；自动探测本机 Python 并写入 环境配置.json。
param(
    [string]$TargetRoot = "$env:USERPROFILE\.codex\skills",
    [switch]$Force,
    [switch]$KeepOutputs
)

$ErrorActionPreference = "Stop"
$skillDir = Split-Path -Parent $PSScriptRoot
$target = Join-Path $TargetRoot "cumcm-code-writer"

Write-Host "源目录：$skillDir"
Write-Host "目标目录：$target"

if ((Test-Path $target) -and -not $Force) {
    Write-Host "目标已存在。加 -Force 覆盖，或先手工备份。" -ForegroundColor Yellow
    exit 1
}

$resolvedRoot = [System.IO.Path]::GetFullPath($TargetRoot)
$resolvedTarget = [System.IO.Path]::GetFullPath($target)
if (-not $resolvedTarget.StartsWith($resolvedRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    Write-Host "拒绝执行：目标路径不在 $TargetRoot 之内。" -ForegroundColor Red
    exit 2
}

New-Item -ItemType Directory -Force -Path $target | Out-Null
$exclude = @("work", "output", "__pycache__", ".git", "环境配置.json")
Get-ChildItem -LiteralPath $skillDir -Force | Where-Object { $exclude -notcontains $_.Name } | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $target -Recurse -Force
}

if (-not $KeepOutputs) {
    Get-ChildItem -LiteralPath $target -Recurse -Directory -Filter "out" -ErrorAction SilentlyContinue | ForEach-Object {
        Remove-Item -LiteralPath $_.FullName -Recurse -Force
    }
    Write-Host "已剔除算法库 out/ 运行产物（如需保留用 -KeepOutputs）"
}

function Resolve-Python {
    $candidates = @(
        (Join-Path (Split-Path -Parent $skillDir) "工具\code_env\Scripts\python.exe"),
        (Join-Path $skillDir "工具\code_env\Scripts\python.exe")
    )
    foreach ($candidate in $candidates) {
        $full = [System.IO.Path]::GetFullPath($candidate)
        if (Test-Path $full) { return $full }
    }
    foreach ($command in @("py", "python", "python3")) {
        $exe = Get-Command $command -ErrorAction SilentlyContinue
        if (-not $exe) { continue }
        try {
            $resolved = & $exe.Source -c "import sys; print(sys.executable)" 2>$null
            if ($resolved -and (Test-Path $resolved.Trim())) { return $resolved.Trim() }
        } catch { }
    }
    return $null
}

$codeEnv = Resolve-Python
$hasDeps = $false
if ($codeEnv) {
    try {
        & $codeEnv -c "import numpy, scipy, matplotlib" 2>$null
        $hasDeps = ($LASTEXITCODE -eq 0)
    } catch { $hasDeps = $false }
}

$config = [ordered]@{
    skill = "cumcm-code-writer"
    installed_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    source_workspace = (Split-Path -Parent $skillDir)
    code_env = $codeEnv
    note = "code_env 为安装时探测到的 Python 解释器；换机器请改这里或设置环境变量 CUMCM_CODE_ENV"
}
$configPath = Join-Path $target "环境配置.json"
$config | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath $configPath -Encoding UTF8

$count = (Get-ChildItem -LiteralPath $target -Recurse -File | Measure-Object).Count
$sizeMB = [math]::Round(((Get-ChildItem -LiteralPath $target -Recurse -File | Measure-Object Length -Sum).Sum / 1MB), 2)
Write-Host "已复制 $count 个文件（$sizeMB MB）到 $target" -ForegroundColor Green
if ($codeEnv) {
    Write-Host "已记录运行环境：$codeEnv"
    if (-not $hasDeps) {
        Write-Host "注意：该解释器缺少 numpy/scipy/matplotlib，请先执行下面这条再使用：" -ForegroundColor Yellow
        Write-Host "  python $target\scripts\bootstrap_env.py --install-optional"
    }
} else {
    Write-Host "未找到可用 Python：请先安装 Python 3.10+，然后重跑本脚本 -Force。" -ForegroundColor Yellow
}
Write-Host "重启或新开一个 Codex 任务后，技能 cumcm-code-writer 即可被发现。"
Write-Host "在别的项目里使用时，设置 CUMCM_CODE_PROJECT=<项目目录>，产物会写到该目录下。"
