param([Parameter(Mandatory=$true)][string]$InputPath,[Parameter(Mandatory=$true)][string]$OutputPath)
$ErrorActionPreference='Stop'
$source=(Resolve-Path -LiteralPath $InputPath).Path
$destination=[IO.Path]::GetFullPath($OutputPath)
if ($source -eq $destination) { throw 'Output must differ from source.' }
[IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($destination)) | Out-Null
$app=$null
$document=$null
try {
 if ([IO.Path]::GetExtension($source) -eq '.doc') {
  $app=New-Object -ComObject Word.Application
  $app.Visible=$false
  $app.DisplayAlerts=0
  $app.AutomationSecurity=3
  $document=$app.Documents.Open($source,$false,$true,$false)
  $text=$document.Content.Text
  [IO.File]::WriteAllText($destination,$text,[Text.UTF8Encoding]::new($false))
 } elseif ([IO.Path]::GetExtension($source) -eq '.ppt') {
  $app=New-Object -ComObject PowerPoint.Application
  $app.AutomationSecurity=3
  $document=$app.Presentations.Open($source,$true,$false,$false)
  $parts=[Collections.Generic.List[string]]::new()
  foreach($slide in $document.Slides) {
   $parts.Add(('## Slide '+$slide.SlideIndex))
   foreach($shape in $slide.Shapes) {
    if($shape.HasTextFrame -and $shape.TextFrame.HasText) {$parts.Add($shape.TextFrame.TextRange.Text)}
    if($shape.HasTable) {foreach($row in $shape.Table.Rows) {foreach($cell in $row.Cells) {$parts.Add($cell.Shape.TextFrame.TextRange.Text)}}}
   }
  }
  [IO.File]::WriteAllText($destination,($parts -join "`n"),[Text.UTF8Encoding]::new($false))
 } else {throw 'Only .doc and .ppt are supported.'}
} finally {
 if($null -ne $document) {if([IO.Path]::GetExtension($source) -eq '.doc'){$document.Close(0)}else{$document.Close()};[Runtime.InteropServices.Marshal]::FinalReleaseComObject($document)|Out-Null}
 if($null -ne $app) {$app.Quit();[Runtime.InteropServices.Marshal]::FinalReleaseComObject($app)|Out-Null}
}
