<#
.SYNOPSIS
    CUMCM 全流程工作流安装脚本（安装 / 校验 / 卸载）。

.DESCRIPTION
    安装 6 个技能到 <目标>\（默认 %USERPROFILE%\.codex\skills），并把查看版 DOCX 导出工具
    装到 <目标>\工具\，同时探测本机 Python 写入环境配置（不再携带打包者的机器路径）。

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\install.ps1
    powershell -ExecutionPolicy Bypass -File .\install.ps1 -Action Check
    powershell -ExecutionPolicy Bypass -File .\install.ps1 -Action Uninstall
    powershell -ExecutionPolicy Bypass -File .\install.ps1 -Destination "D:\my\skills" -SetupTools
#>
[CmdletBinding()]
param(
    [ValidateSet('Install','Check','Doctor','Uninstall')][string]$Action = 'Install',
    [string]$Destination = $(if ($env:CODEX_HOME) { Join-Path $env:CODEX_HOME 'skills' } elseif (Test-Path (Join-Path $env:USERPROFILE '.codex\skills')) { Join-Path $env:USERPROFILE '.codex\skills' } else { Join-Path $env:USERPROFILE '.agents\skills' }),
    [switch]$SetupTools,
    [switch]$Strict,
    [switch]$Network
)
$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [Text.UTF8Encoding]::new($false) } catch { }
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$srcSkills = Join-Path $here 'skills'
$srcTools = Join-Path $here 'tools'
$packageMetadata = Join-Path $here 'BUILD_METADATA.json'
$packageVersion = 'unknown'
$script:packageLabel = 'CUMCM全流程工作流 v1.1.0'
if (Test-Path -LiteralPath $packageMetadata -PathType Leaf) {
    try {
        $packageMeta = Get-Content -LiteralPath $packageMetadata -Raw -Encoding UTF8 | ConvertFrom-Json
        if (-not $packageMeta.version) { throw '缺少 version' }
        $packageVersion = [string]$packageMeta.version
        $script:packageLabel = 'CUMCM全流程工作流 v' + $packageVersion
    } catch { throw ('安装包 BUILD_METADATA.json 无效：' + $_.Exception.Message) }
} else {
    Write-Warning '安装包缺少 BUILD_METADATA.json；将以兼容模式继续，建议重新获取完整安装包。'
}
$base = [IO.Path]::GetFullPath($Destination)
$volumeRoot = [IO.Path]::GetPathRoot($base)
if ([string]::Equals($base.TrimEnd('\'), $volumeRoot.TrimEnd('\'), [StringComparison]::OrdinalIgnoreCase)) {
    throw ('拒绝把磁盘根目录作为安装目标：' + $base)
}
$packageRoot = [IO.Path]::GetFullPath($here).TrimEnd('\')
if ($base.StartsWith($packageRoot + '\', [StringComparison]::OrdinalIgnoreCase) -or
    [string]::Equals($base.TrimEnd('\'), $packageRoot, [StringComparison]::OrdinalIgnoreCase)) {
    throw ('安装目标不能位于安装包目录内：' + $base)
}
$toolsDst = Join-Path $base '工具'
$manifestName = '_workflow_tools.manifest.json'
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$parent = [IO.Directory]::GetParent($base)
if (-not $parent) { throw ('安装目标无安全父目录：' + $base) }
$backup = Join-Path $parent.FullName ('.cumcm-workflow-backups\' + $stamp + '-' + ([guid]::NewGuid().ToString('N').Substring(0,8)))
if (-not (Test-Path -LiteralPath $srcSkills -PathType Container)) { throw ('安装包缺少 skills 目录：' + $srcSkills) }
$ownershipManifestName = '_workflow_install.manifest.json'

function Assert-NoReparsePath([string]$path) {
    $current = [IO.Path]::GetFullPath($path)
    while ($current) {
        if (Test-Path -LiteralPath $current) {
            $item = Get-Item -LiteralPath $current -Force -ErrorAction Stop
            if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw ('路径含符号链接/junction，拒绝继续：' + $current)
            }
        }
        $next = Split-Path -Parent $current
        if (-not $next -or $next -eq $current) { break }
        $current = $next
    }
}

Assert-NoReparsePath $base
Assert-NoReparsePath $srcSkills
Assert-NoReparsePath $srcTools
$names = @(Get-ChildItem -LiteralPath $srcSkills -Directory | Where-Object { $_.Name -notmatch '^(__|\.)' } | Select-Object -ExpandProperty Name)
if ($names.Count -eq 0) { throw ('安装包没有可安装的技能目录：' + $srcSkills) }
foreach ($n in $names) {
    $skillPath = Join-Path (Join-Path $srcSkills $n) 'SKILL.md'
    if (-not (Test-Path -LiteralPath $skillPath -PathType Leaf)) { throw ('技能目录缺少 SKILL.md：' + $n) }
}
$toolFiles = @()
if (Test-Path -LiteralPath $srcTools) { $toolFiles = @(Get-ChildItem -LiteralPath $srcTools -File | Select-Object -ExpandProperty Name) }
function Get-Sha256([string]$path) {
    $sha = [Security.Cryptography.SHA256]::Create()
    $stream = [IO.File]::OpenRead($path)
    try { return [BitConverter]::ToString($sha.ComputeHash($stream)).Replace('-', '') }
    finally { $stream.Dispose(); $sha.Dispose() }
}

function Assert-NoReparseTree([string]$root) {
    if (-not (Test-Path -LiteralPath $root -PathType Container)) { return }
    foreach ($item in @(Get-ChildItem -LiteralPath $root -Recurse -Force -ErrorAction Stop)) {
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw ('目录含符号链接/junction，拒绝复制：' + $item.FullName)
        }
    }
}

function Get-FileRecords([string]$root) {
    $records = @()
    if (-not (Test-Path -LiteralPath $root -PathType Container)) { return $records }
    $rootFull = [IO.Path]::GetFullPath($root).TrimEnd('\')
    foreach ($item in @(Get-ChildItem -LiteralPath $root -File -Recurse -Force -ErrorAction Stop)) {
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw ('文件含符号链接/junction，拒绝处理：' + $item.FullName)
        }
        $relative = $item.FullName.Substring($rootFull.Length).TrimStart('\','/')
        $records += [ordered]@{
            path   = $relative.Replace('\','/')
            bytes  = [int64]$item.Length
            sha256 = (Get-Sha256 $item.FullName).ToLowerInvariant()
        }
    }
    return @($records | Sort-Object -Property path)
}

function Test-FileRecords([string]$root, $expected, [ref]$reason) {
    if (-not (Test-Path -LiteralPath $root -PathType Container)) {
        $reason.Value = '目录不存在'
        return $false
    }
    try { $actual = @(Get-FileRecords $root) } catch {
        $reason.Value = $_.Exception.Message
        return $false
    }
    $wanted = @($expected)
    if ($actual.Count -ne $wanted.Count) {
        $reason.Value = ('文件数变化（原 {0}，现 {1}）' -f $wanted.Count, $actual.Count)
        return $false
    }
    $map = @{}
    foreach ($item in $actual) { $map[[string]$item.path] = $item }
    foreach ($item in $wanted) {
        $key = [string]$item.path
        if (-not $map.ContainsKey($key)) {
            $reason.Value = '缺少文件：' + $key
            return $false
        }
        $got = $map[$key]
        if ([int64]$got.bytes -ne [int64]$item.bytes -or
            -not [string]::Equals([string]$got.sha256, [string]$item.sha256, [StringComparison]::OrdinalIgnoreCase)) {
            $reason.Value = '文件已修改：' + $key
            return $false
        }
    }
    return $true
}

function Write-JsonAtomic([string]$path, $value) {
    $parentPath = Split-Path -Parent $path
    New-Item -ItemType Directory -Force -Path $parentPath | Out-Null
    $tmp = $path + '.tmp-' + [guid]::NewGuid().ToString('N')
    ($value | ConvertTo-Json -Depth 8) | Set-Content -LiteralPath $tmp -Encoding UTF8
    Move-Item -LiteralPath $tmp -Destination $path -Force
}
if ($packageMeta) {
    $declared = @($packageMeta.skills | ForEach-Object { [string]$_.name })
    if ($declared.Count -ne $names.Count -or @($names | Where-Object { $_ -notin $declared }).Count -gt 0) {
        throw '安装包技能目录与 BUILD_METADATA.json 不一致'
    }
    foreach ($entry in @($packageMeta.skills)) {
        $sourceSkill = Join-Path (Join-Path $srcSkills ([string]$entry.name)) 'SKILL.md'
        $actualHash = Get-Sha256 $sourceSkill
        if (-not [string]::Equals($actualHash, [string]$entry.skill_sha256, [StringComparison]::OrdinalIgnoreCase)) {
            throw ('安装包 SKILL.md 哈希不符：' + $entry.name)
        }
    }
}

function Test-PythonCandidate([string]$candidate) {
    if (-not $candidate) { return $null }
    $candidate = $candidate.Trim().Trim('"')
    if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) { return $null }
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

function Find-Python {
    $cands = New-Object System.Collections.ArrayList
    foreach ($v in @($env:CUMCM_CODE_ENV, $env:CUMCM_PYTHON, $env:MODELING_PY)) {
        if ($v) { [void]$cands.Add($v) }
    }
    [void]$cands.Add((Join-Path $toolsDst 'md2docx_env\Scripts\python.exe'))
    foreach ($n in @('python.exe','python3.exe','python','python3')) {
        $cmd = Get-Command $n -ErrorAction SilentlyContinue
        if ($cmd -and $cmd.Source -notmatch 'WindowsApps') { [void]$cands.Add($cmd.Source) }
    }
    foreach ($version in @('311','312','313','314','315')) {
        [void]$cands.Add((Join-Path $env:LOCALAPPDATA ('Programs\Python\Python' + $version + '\python.exe')))
        [void]$cands.Add((Join-Path $env:ProgramFiles ('Python' + $version + '\python.exe')))
        if (${env:ProgramFiles(x86)}) {
            [void]$cands.Add((Join-Path ${env:ProgramFiles(x86)} ('Python' + $version + '\python.exe')))
        }
    }
    $runtime = Join-Path $env:USERPROFILE '.cache\codex-runtimes'
    if (Test-Path -LiteralPath $runtime) {
        $found = Get-ChildItem -LiteralPath $runtime -Filter python.exe -Recurse -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -match 'dependencies[\\/]python[\\/]python\.exe$' } | Select-Object -First 1
        if ($found) { [void]$cands.Add($found.FullName) }
    }
    $seen = @{}
    foreach ($c in $cands) {
        if (-not $c) { continue }
        $p = [string]$c
        if (Test-Path -LiteralPath $p -PathType Container) {
            $q = Join-Path $p 'Scripts\python.exe'
            if (-not (Test-Path -LiteralPath $q)) { $q = Join-Path $p 'python.exe' }
            $p = $q
        }
        $key = $p.ToLowerInvariant()
        if ($seen.ContainsKey($key)) { continue }
        $seen[$key] = $true
        $valid = Test-PythonCandidate $p
        if ($valid) { return $valid }
    }
    # The Python launcher can select a suitable 3.x interpreter even when it
    # is not on PATH as python.exe.  Resolve the real executable before saving
    # it into the portable environment configuration.
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
    return $null
}

function Write-EnvConfigs([string]$python) {
    $stampText = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    if ($python) {
        $pythonPathFile = Join-Path $toolsDst 'python.path'
        [IO.File]::WriteAllText($pythonPathFile, ($python + [Environment]::NewLine), (New-Object Text.UTF8Encoding($false)))
        $codeCfg = [ordered]@{
            skill          = 'cumcm-code-writer'
            installed_at   = $stampText
            source_package = $script:packageLabel
            code_env       = $python
            note           = '安装时探测写入；换机器请改这里或设置环境变量 CUMCM_CODE_ENV'
        }
        $codeCfgPath = Join-Path $base 'cumcm-code-writer\环境配置.json'
        if (Test-Path -LiteralPath (Split-Path -Parent $codeCfgPath)) {
            ($codeCfg | ConvertTo-Json -Depth 3) | Set-Content -LiteralPath $codeCfgPath -Encoding UTF8
        }
        $toolCfgPath = Join-Path $toolsDst '环境配置.json'
        if (Test-Path -LiteralPath $toolCfgPath) {
            try {
                $obj = Get-Content -LiteralPath $toolCfgPath -Raw -Encoding UTF8 | ConvertFrom-Json
                if ($obj.PSObject.Properties['python']) { $obj.python = $python }
                else { $obj | Add-Member -NotePropertyName python -NotePropertyValue $python -Force }
                if ($obj.PSObject.Properties['detected_at']) { $obj.detected_at = $stampText }
                $obj | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $toolCfgPath -Encoding UTF8
            } catch {
                # 配置文件损坏时写一个最小、可诊断的替代配置；旧实现引用了
                # 未定义的 $cfg，导致二次异常并掩盖真正原因。
                $cfgBackupDir = Join-Path $backup '工具'
                New-Item -ItemType Directory -Force -Path $cfgBackupDir | Out-Null
                $cfgBackup = Join-Path $cfgBackupDir ('环境配置.invalid-' + [guid]::NewGuid().ToString('N') + '.json')
                Move-Item -LiteralPath $toolCfgPath -Destination $cfgBackup
                $fallback = [ordered]@{
                    python         = $python
                    detected_at    = $stampText
                    source_package = $script:packageLabel
                    note           = '原环境配置无法解析，已备份后由安装程序重建；可手工补充其它字段。'
                }
                ($fallback | ConvertTo-Json -Depth 3) | Set-Content -LiteralPath $toolCfgPath -Encoding UTF8
                Write-Warning ('无效环境配置已备份到：' + $cfgBackup)
            }
        } else {
            $toolCfg = [ordered]@{
                python         = $python
                detected_at    = $stampText
                source_package = $script:packageLabel
                note           = '供 数学模型建立/论文导出 等技能使用；可用 MODELING_PY / CUMCM_PYTHON 覆盖；原生公式导出依赖见 setup-md2docx.ps1'
            }
            ($toolCfg | ConvertTo-Json -Depth 3) | Set-Content -LiteralPath $toolCfgPath -Encoding UTF8
        }
    }
}

function Invoke-CliDoctor([switch]$StrictMode, [switch]$NetworkMode) {
    $cli = Join-Path $toolsDst 'cumcm_flow.py'
    if (-not (Test-Path -LiteralPath $cli -PathType Leaf)) {
        $cli = Join-Path $srcTools 'cumcm_flow.py'
    }
    $python = Find-Python
    if (-not $python) {
        Write-Warning 'Doctor 无法启动：未找到可执行的 Python 3.11+。请安装 Python 或设置 CUMCM_PYTHON。'
        $script:lastDoctorCode = 1
        return
    }
    $cliArgs = @($cli, 'doctor')
    if ($StrictMode) { $cliArgs += '--strict' }
    if ($NetworkMode) { $cliArgs += '--network' }
    & $python @cliArgs
    $script:lastDoctorCode = $LASTEXITCODE
}

function Write-ToolManifest([string]$path, $records) {
    $manifest = [ordered]@{
        schema_version = 2
        source_package = $script:packageLabel
        version        = $packageVersion
        installed_at   = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
        files          = @($records)
    }
    Write-JsonAtomic $path $manifest
}

function Update-OwnershipGeneratedFiles {
    $ownershipPath = Join-Path $base $ownershipManifestName
    if (-not (Test-Path -LiteralPath $ownershipPath -PathType Leaf)) { return }
    try {
        $ownership = Get-Content -LiteralPath $ownershipPath -Raw -Encoding UTF8 | ConvertFrom-Json
        foreach ($entry in @($ownership.skills)) {
            if ([string]$entry.name -eq 'cumcm-code-writer') {
                $entry.files = @(Get-FileRecords (Join-Path $base 'cumcm-code-writer'))
            }
        }
        $toolConfig = Join-Path $toolsDst '环境配置.json'
        $toolEntries = @($ownership.tools | Where-Object { [string]$_.path -ne '环境配置.json' })
        if (Test-Path -LiteralPath $toolConfig -PathType Leaf) {
            $item = Get-Item -LiteralPath $toolConfig
            $toolEntries += [ordered]@{ path = '环境配置.json'; bytes = [int64]$item.Length; sha256 = (Get-Sha256 $toolConfig).ToLowerInvariant() }
        }
        $pythonPathFile = Join-Path $toolsDst 'python.path'
        $toolEntries = @($toolEntries | Where-Object { [string]$_.path -ne 'python.path' })
        if (Test-Path -LiteralPath $pythonPathFile -PathType Leaf) {
            $item = Get-Item -LiteralPath $pythonPathFile
            $toolEntries += [ordered]@{ path = 'python.path'; bytes = [int64]$item.Length; sha256 = (Get-Sha256 $pythonPathFile).ToLowerInvariant() }
        }
        $ownership.tools = @($toolEntries | Sort-Object -Property path)
        Write-JsonAtomic $ownershipPath $ownership
    } catch {
        Write-Warning ('无法更新安装所有权清单中的环境配置记录：' + $_.Exception.Message)
    }
}

if ($Action -eq 'Doctor') {
    Invoke-CliDoctor -StrictMode:$Strict -NetworkMode:$Network
    $doctorCode = $script:lastDoctorCode
    if ($doctorCode -ne 0) { throw ('Doctor 检测到硬失败（退出码 ' + $doctorCode + '）') }
    return
}

if ($Action -eq 'Check') {
    $bad = 0
    Assert-NoReparsePath $base
    foreach ($n in $names) {
        $t = Join-Path $base $n
        $ok = Test-Path -LiteralPath (Join-Path $t 'SKILL.md') -PathType Leaf
        if ($ok) {
            try { Assert-NoReparseTree $t } catch { $ok = $false; Write-Warning $_.Exception.Message }
        }
        if ($ok -and $packageMeta) {
            $entry = @($packageMeta.skills | Where-Object { [string]$_.name -eq $n }) | Select-Object -First 1
            if ($entry -and -not [string]::Equals((Get-Sha256 (Join-Path $t 'SKILL.md')), [string]$entry.skill_sha256, [StringComparison]::OrdinalIgnoreCase)) {
                $ok = $false
            }
        }
        if (-not $ok) { $bad++ }
        Write-Output ("{0}  {1}" -f ($(if ($ok) { 'OK ' } else { '缺失/不一致' }), $n))
    }
    foreach ($f in $toolFiles) {
        $source = Join-Path $srcTools $f
        $target = Join-Path $toolsDst $f
        $ok = (Test-Path -LiteralPath $target -PathType Leaf)
        if ($ok -and (Test-Path -LiteralPath $source -PathType Leaf)) {
            $ok = [string]::Equals((Get-Sha256 $source), (Get-Sha256 $target), [StringComparison]::OrdinalIgnoreCase)
        }
        if (-not $ok) { $bad++ }
        Write-Output ("{0}  工具\{1}" -f ($(if ($ok) { 'OK ' } else { '缺失/不一致' }), $f))
    }
    $py = Find-Python
    if ($py) {
        Write-Output ('Python：' + $py)
        $pandoc = ''
        try { $pandoc = (& $py -c "import pypandoc;print(pypandoc.get_pandoc_path())" 2>$null) } catch { $pandoc = '' }
        if ($pandoc) { Write-Output ('原生公式导出依赖：OK（pandoc ' + ([string]$pandoc).Trim() + '）') }
        else { Write-Output '原生公式导出依赖：未就绪，需要时运行 工具\setup-md2docx.ps1（首次需联网）' }
    } else {
        $bad++
        Write-Output 'Python：未找到（写码/计算/导出需要 Python 3.11+，可设置 CUMCM_PYTHON 指定）'
    }
    if ($bad -gt 0) { throw ("有 $bad 项未安装完整") }
    Write-Output '校验通过：技能、CLI 与工具链均已就位。需要更完整的陌生机器诊断时运行 -Action Doctor。'
    return
}

if ($Action -eq 'Uninstall') {
    $ownershipPath = Join-Path $base $ownershipManifestName
    if (-not (Test-Path -LiteralPath $ownershipPath -PathType Leaf)) {
        throw ('未找到本产品的所有权清单：' + $ownershipPath + '；为避免误删同名 Skill，未执行卸载。')
    }
    try { $ownership = Get-Content -LiteralPath $ownershipPath -Raw -Encoding UTF8 | ConvertFrom-Json }
    catch { throw ('所有权清单损坏，未执行卸载：' + $_.Exception.Message) }
    if ($ownership.destination -and -not [string]::Equals([IO.Path]::GetFullPath([string]$ownership.destination).TrimEnd('\'), $base.TrimEnd('\'), [StringComparison]::OrdinalIgnoreCase)) {
        throw '所有权清单与当前目标目录不匹配，未执行卸载。'
    }
    $moved = 0
    New-Item -ItemType Directory -Force -Path $backup | Out-Null
    foreach ($entry in @($ownership.skills)) {
        $n = [string]$entry.name
        if (-not $n -or $n.Contains('\') -or $n.Contains('/') -or $n -eq '.' -or $n -eq '..') { throw ('所有权清单含非法 Skill 名称：' + $n) }
        $target = Join-Path $base $n
        if (-not (Test-Path -LiteralPath $target)) { continue }
        $reason = ''
        $unchanged = Test-FileRecords $target @($entry.files) ([ref]$reason)
        if (-not $unchanged) { Write-Warning ('检测到用户修改，保留 Skill 不动：' + $n + '（' + $reason + '）'); continue }
        Assert-NoReparsePath $target
        Move-Item -LiteralPath $target -Destination (Join-Path $backup $n)
        $moved++
    }
    $toolBackup = Join-Path $backup '工具'
    foreach ($entry in @($ownership.tools)) {
        $rel = ([string]$entry.path).Replace('/','\')
        if (-not $rel -or $rel.StartsWith('\') -or $rel.Contains('..')) { throw ('所有权清单含非法工具路径：' + $rel) }
        $target = Join-Path $toolsDst $rel
        if (-not (Test-Path -LiteralPath $target -PathType Leaf)) { continue }
        $actualHash = Get-Sha256 $target
        if (-not [string]::Equals($actualHash, [string]$entry.sha256, [StringComparison]::OrdinalIgnoreCase)) {
            Write-Warning ('检测到用户修改，保留工具文件：' + $rel)
            continue
        }
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent (Join-Path $toolBackup $rel)) | Out-Null
        Move-Item -LiteralPath $target -Destination (Join-Path $toolBackup $rel)
        $moved++
    }
    $oldToolManifest = Join-Path $toolsDst $manifestName
    if (Test-Path -LiteralPath $oldToolManifest -PathType Leaf) {
        New-Item -ItemType Directory -Force -Path $toolBackup | Out-Null
        Move-Item -LiteralPath $oldToolManifest -Destination (Join-Path $toolBackup $manifestName)
        $moved++
    }
    if (Test-Path -LiteralPath $ownershipPath -PathType Leaf) {
        Move-Item -LiteralPath $ownershipPath -Destination (Join-Path $backup $ownershipManifestName)
        $moved++
    }
    Write-Output ('已卸载 ' + $moved + ' 个本包文件；用户修改过的文件已保留。备份在 ' + $backup)
    return
}

# Install: stage all files first, then commit with a rollback path.  This
# keeps a broken copy or a missing dependency from leaving half an installation.
Assert-NoReparseTree $srcSkills
Assert-NoReparseTree $srcTools
$staging = Join-Path $parent.FullName ('.cumcm-workflow-staging-' + [guid]::NewGuid().ToString('N'))
$stageSkills = Join-Path $staging 'skills'
$stageTools = Join-Path $staging 'tools'
$movedSkills = @()
$installedSkills = @()
$movedTools = @()
$installedTools = @()
$oldManifestMoved = $false
$oldOwnershipMoved = $false
try {
    New-Item -ItemType Directory -Force -Path $stageSkills, $stageTools | Out-Null
    foreach ($n in $names) {
        Copy-Item -LiteralPath (Join-Path $srcSkills $n) -Destination (Join-Path $stageSkills $n) -Recurse -Force
        if (-not (Test-Path -LiteralPath (Join-Path (Join-Path $stageSkills $n) 'SKILL.md') -PathType Leaf)) { throw ('暂存失败（缺 SKILL.md）：' + $n) }
    }
    foreach ($f in $toolFiles) {
        Copy-Item -LiteralPath (Join-Path $srcTools $f) -Destination (Join-Path $stageTools $f) -Force
    }
    New-Item -ItemType Directory -Force -Path $base, $backup | Out-Null
    $oldOwnershipPath = Join-Path $base $ownershipManifestName
    if (Test-Path -LiteralPath $oldOwnershipPath -PathType Leaf) {
        $oldOwnershipBackup = Join-Path $backup $ownershipManifestName
        Move-Item -LiteralPath $oldOwnershipPath -Destination $oldOwnershipBackup
        $oldOwnershipMoved = $true
    }
    foreach ($n in $names) {
        $target = Join-Path $base $n
        if (Test-Path -LiteralPath $target) {
            Assert-NoReparsePath $target
            $backupTarget = Join-Path $backup $n
            Move-Item -LiteralPath $target -Destination $backupTarget
            $movedSkills += [pscustomobject]@{ Target = $target; Backup = $backupTarget }
            Write-Output ('已备份旧版：' + $n)
        }
        Move-Item -LiteralPath (Join-Path $stageSkills $n) -Destination $target
        $installedSkills += $target
        Write-Output ('已安装：' + $n)
    }
    New-Item -ItemType Directory -Force -Path $toolsDst | Out-Null
    $oldManifestPath = Join-Path $toolsDst $manifestName
    if (Test-Path -LiteralPath $oldManifestPath -PathType Leaf) {
        $oldManifestBackup = Join-Path $backup ('工具\' + $manifestName)
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $oldManifestBackup) | Out-Null
        Move-Item -LiteralPath $oldManifestPath -Destination $oldManifestBackup
        $oldManifestMoved = $true
    }
    foreach ($f in $toolFiles) {
        $target = Join-Path $toolsDst $f
        if (Test-Path -LiteralPath $target) {
            Assert-NoReparsePath $target
            $backupTarget = Join-Path $backup ('工具\' + $f)
            New-Item -ItemType Directory -Force -Path (Split-Path -Parent $backupTarget) | Out-Null
            Move-Item -LiteralPath $target -Destination $backupTarget
            $movedTools += [pscustomobject]@{ Target = $target; Backup = $backupTarget }
        }
        Move-Item -LiteralPath (Join-Path $stageTools $f) -Destination $target
        $installedTools += $target
    }
    $toolRecords = @()
    foreach ($f in $toolFiles) {
        $p = Join-Path $toolsDst $f
        $toolRecords += [ordered]@{ path = $f.Replace('\','/'); bytes = (Get-Item -LiteralPath $p).Length; sha256 = (Get-Sha256 $p).ToLowerInvariant() }
    }
    $skillRecords = @()
    foreach ($n in $names) {
        $skillRecords += [ordered]@{ name = $n; files = @(Get-FileRecords (Join-Path $base $n)) }
    }
    Write-ToolManifest (Join-Path $toolsDst $manifestName) $toolRecords
    $ownership = [ordered]@{
        schema_version = 1
        package        = 'CUMCM全流程工作流'
        version        = $packageVersion
        destination    = $base
        installed_at   = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
        skills         = @($skillRecords)
        tools          = @($toolRecords)
    }
    Write-JsonAtomic (Join-Path $base $ownershipManifestName) $ownership
} catch {
    $partialManifest = Join-Path $toolsDst $manifestName
    if (Test-Path -LiteralPath $partialManifest -PathType Leaf) { Remove-Item -LiteralPath $partialManifest -Force -ErrorAction SilentlyContinue }
    $partialOwnership = Join-Path $base $ownershipManifestName
    if (Test-Path -LiteralPath $partialOwnership -PathType Leaf) { Remove-Item -LiteralPath $partialOwnership -Force -ErrorAction SilentlyContinue }
    foreach ($target in @($installedTools)) { if (Test-Path -LiteralPath $target) { Remove-Item -LiteralPath $target -Force -ErrorAction SilentlyContinue } }
    foreach ($target in @($installedSkills)) { if (Test-Path -LiteralPath $target) { Remove-Item -LiteralPath $target -Recurse -Force -ErrorAction SilentlyContinue } }
    foreach ($item in @($movedTools)) { if (Test-Path -LiteralPath $item.Backup) { Move-Item -LiteralPath $item.Backup -Destination $item.Target -Force -ErrorAction SilentlyContinue } }
    foreach ($item in @($movedSkills)) { if (Test-Path -LiteralPath $item.Backup) { Move-Item -LiteralPath $item.Backup -Destination $item.Target -Force -ErrorAction SilentlyContinue } }
    if ($oldManifestMoved -and (Test-Path -LiteralPath $oldManifestBackup)) { Move-Item -LiteralPath $oldManifestBackup -Destination $oldManifestPath -Force -ErrorAction SilentlyContinue }
    if ($oldOwnershipMoved -and (Test-Path -LiteralPath $oldOwnershipBackup)) { Move-Item -LiteralPath $oldOwnershipBackup -Destination $oldOwnershipPath -Force -ErrorAction SilentlyContinue }
    throw ('安装失败，已尝试回滚：' + $_.Exception.Message)
} finally {
    if (Test-Path -LiteralPath $staging) { Remove-Item -LiteralPath $staging -Recurse -Force -ErrorAction SilentlyContinue }
}

$pythonFound = Find-Python
Write-EnvConfigs $pythonFound
Update-OwnershipGeneratedFiles
if ($pythonFound) { Write-Output ('已写入环境配置，Python：' + $pythonFound) }
else { Write-Warning '未在本机找到 Python 3.11+：Skill 已安装，但写码/计算与 DOCX 导出暂不可用。请安装 Python 或设置 CUMCM_PYTHON 后运行 -Action Doctor。' }
if ($SetupTools -and $pythonFound) {
    $setup = Join-Path $toolsDst 'setup-md2docx.ps1'
    if (Test-Path -LiteralPath $setup) { & $setup -Python $pythonFound } else { Write-Warning ('未找到 ' + $setup) }
}
Write-Output ('完成，共 ' + $names.Count + ' 个技能 → ' + $base)
Write-Output 'CLI：在 工具 目录运行 cumcm-flow.cmd doctor；再用 init / seal / verify / status 管理运行目录。'
Invoke-CliDoctor
$doctorCode = $script:lastDoctorCode
if ($doctorCode -ne 0) { Write-Warning ('安装后 Doctor 报告硬失败，建议先处理后再开始竞赛流程（退出码 ' + $doctorCode + '）。') }
$setupPath = Join-Path $toolsDst 'setup-md2docx.ps1'
Write-Output ('若需要查看版 DOCX（Word 原生公式），运行：powershell -ExecutionPolicy Bypass -File "' + $setupPath + '"')
