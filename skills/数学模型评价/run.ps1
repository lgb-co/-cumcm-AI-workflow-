param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Arguments)
$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$env:PYTHONUTF8='1'
function Find-Python {
 if($env:CUMCM_PYTHON -and (Test-Path -LiteralPath $env:CUMCM_PYTHON)){return $env:CUMCM_PYTHON}
 foreach($name in @('python.exe','python3.exe','python','python3')) {
  $cmd=Get-Command $name -ErrorAction SilentlyContinue
  if($cmd -and $cmd.Source -notmatch 'WindowsApps'){return $cmd.Source}
 }
 $runtime=Join-Path $env:USERPROFILE '.cache\codex-runtimes'
 if(Test-Path -LiteralPath $runtime) {
  $found=Get-ChildItem -LiteralPath $runtime -Filter python.exe -Recurse -ErrorAction SilentlyContinue|Where-Object {$_.FullName -match 'dependencies[\\/]python[\\/]python.exe$'}|Select-Object -First 1
  if($found){return $found.FullName}
 }
 throw 'Python 3 was not found. Install Python 3.11+ or set CUMCM_PYTHON to its executable. The skill instructions can still be read by Codex.'
}
$python=Find-Python
$savedPythonPath=$env:PYTHONPATH
$runtimePath=Join-Path $PSScriptRoot '.runtime'
if(Test-Path -LiteralPath $runtimePath){$env:PYTHONPATH=$runtimePath+[IO.Path]::PathSeparator+$savedPythonPath}
try {
 if(!$Arguments -or $Arguments.Count -eq 0){$Arguments=@('environment')}
 if($Arguments[0] -eq 'extract'){
  $remaining=@();if($Arguments.Count -gt 1){$remaining=$Arguments[1..($Arguments.Count-1)]}
  & $python (Join-Path $PSScriptRoot 'scripts\extract.py') @remaining
 } else {& $python (Join-Path $PSScriptRoot 'scripts\review.py') @Arguments}
 $result=$LASTEXITCODE
} finally {$env:PYTHONPATH=$savedPythonPath}
if($result -ne 0){throw ('Review command failed with exit code '+$result)}
