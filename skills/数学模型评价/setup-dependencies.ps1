$ErrorActionPreference='Stop'
# Core intake/scoring/report checks use the Python standard library only.
$python=$env:CUMCM_PYTHON
if(!$python){$candidate=Get-Command python.exe -ErrorAction SilentlyContinue;if($candidate -and $candidate.Source -notmatch 'WindowsApps'){$python=$candidate.Source}}
if(!$python){$root=Join-Path $env:USERPROFILE '.cache\codex-runtimes';$candidate=Get-ChildItem -LiteralPath $root -Filter python.exe -Recurse -ErrorAction SilentlyContinue|Where-Object {$_.FullName -match 'dependencies[\\/]python[\\/]python.exe$'}|Select-Object -First 1;if($candidate){$python=$candidate.FullName}}
if(!$python){throw 'Set CUMCM_PYTHON to a Python 3.11+ executable.'}
& $python -m pip install --target (Join-Path $PSScriptRoot '.runtime') -r (Join-Path $PSScriptRoot 'requirements-extraction.txt') --disable-pip-version-check
if($LASTEXITCODE -ne 0){throw 'Optional extraction dependency installation failed. Core review tools remain usable.'}
