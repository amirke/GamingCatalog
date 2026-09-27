param(
 [string]$SourceRoot=(Get-Location).Path,
 [string]$JabuPath='',
 [string]$OutputRoot='',
 [string]$Game='',
 [int]$ExpectedCount=0,
 [switch]$CheckOnly
)
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'gui-steps.ps1')
. (Join-Path $PSScriptRoot 'build-functions.ps1')
$SourceRoot=(Resolve-Path -LiteralPath $SourceRoot).Path
if(Test-Path -LiteralPath (Join-Path $SourceRoot 'CD_GAMES')){$SourceRoot=Join-Path $SourceRoot 'CD_GAMES'}
$parent=Split-Path $SourceRoot -Parent
if(-not $JabuPath){
 foreach($candidate in @((Join-Path $parent '_jabu_verified\Jabu'),(Join-Path $parent 'Jabu_PS2_FPKG'),(Join-Path $SourceRoot 'Jabu_PS2_FPKG'))){
  if(Test-Path -LiteralPath (Join-Path $candidate 'PS2-FPKG.exe')){$JabuPath=$candidate;break}
 }
}
if(-not $JabuPath){throw 'Jabu not found. Supply -JabuPath with the folder containing PS2-FPKG.exe.'}
$JabuPath=(Resolve-Path -LiteralPath $JabuPath).Path
foreach($file in @('PS2-FPKG.exe','stuff\pkg.exe','emus\Rogue v1\eboot.bin','emus\Rogue v1\ps2-emu-compiler.self')){
 if(-not(Test-Path -LiteralPath (Join-Path $JabuPath $file))){throw "Missing Jabu component: $file"}
}
$cues=@(Get-ChildItem -LiteralPath $SourceRoot -Filter '*.cue' -Recurse -File | Sort-Object FullName)
if($Game){$cues=@($cues|Where-Object {$_.Directory.Name -eq $Game})}
if(-not $cues.Count){throw 'No CUE files found. Run in CD_GAMES or its parent directory.'}
if($ExpectedCount -gt 0 -and $cues.Count -ne $ExpectedCount){throw "Expected $ExpectedCount games; found $($cues.Count)."}
$jobs=@();$seen=@{}
foreach($cue in $cues){
 $text=Get-Content -LiteralPath $cue.FullName -Raw
 $files=[regex]::Matches($text,'(?im)^FILE\s+"([^"]+)"\s+BINARY\s*$')
 $tracks=[regex]::Matches($text,'(?im)^\s*TRACK\s+\d+\s+(\S+)')
 if($files.Count -ne 1 -or $tracks.Count -ne 1){throw "Only single-file, single-track CUE supported: $($cue.FullName)"}
 $mode=$tracks[0].Groups[1].Value
 if($mode -notin @('MODE1/2048','MODE2/2352')){throw "Unsupported mode $mode : $($cue.FullName)"}
 $bin=[IO.Path]::GetFullPath((Join-Path $cue.DirectoryName $files[0].Groups[1].Value))
 if(-not $bin.StartsWith($cue.DirectoryName+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'CUE references a file outside its own directory'}
 if(-not(Test-Path -LiteralPath $bin -PathType Leaf)){throw "Missing BIN: $bin"}
 if($seen.ContainsKey($cue.Directory.Name)){throw "Duplicate output name: $($cue.Directory.Name)"};$seen[$cue.Directory.Name]=$true
 $jobs += [pscustomobject]@{Game=$cue.Directory.Name;Cue=$cue.FullName;Bin=$bin;Mode=$mode;Status='Pending';Pkg='';GameId='';SourceUnchanged=$false;Error=''}
}
Write-Host "Found $($jobs.Count) games. Emulator: Rogue v1. Other Jabu options: unchanged defaults."
if($CheckOnly){$jobs|Format-Table Game,Mode;Write-Host 'Preflight passed. No games rebuilt.';exit 0}
if(Get-Process -Name PS2-FPKG -ErrorAction SilentlyContinue){throw 'Close Jabu before starting, so another session cannot be changed.'}
if(-not $OutputRoot){$OutputRoot=Join-Path $parent ('PKG_ROGUE_'+(Get-Date -Format 'yyyyMMdd_HHmmss'))}
$OutputRoot=[IO.Path]::GetFullPath($OutputRoot)
if(Test-Path -LiteralPath $OutputRoot){throw 'Output directory already exists. Choose a new directory; existing files are never overwritten.'}
New-Item -ItemType Directory -Path $OutputRoot|Out-Null
$work=Join-Path $OutputRoot '_work';$logs=Join-Path $OutputRoot 'logs'
New-Item -ItemType Directory -Path $work,$logs|Out-Null
$logFile=Join-Path $OutputRoot 'progress.log'
function Log([string]$Message){$line="$(Get-Date -Format 'HH:mm:ss') $Message";Write-Host $line;Add-Content -LiteralPath $logFile -Value $line}
function Save-Report {
 $jobs|Export-Csv -LiteralPath (Join-Path $OutputRoot 'report.csv') -NoTypeInformation -Encoding UTF8
 ConvertTo-Json -InputObject @($jobs) -Depth 5|Set-Content -LiteralPath (Join-Path $OutputRoot 'report.json') -Encoding UTF8
}
function Hash([string]$Path){
 $stream=[IO.File]::OpenRead($Path);$sha=[Security.Cryptography.SHA256]::Create();$buffer=New-Object byte[] (4MB);$last=Get-Date
 try{
  while(($n=$stream.Read($buffer,0,$buffer.Length)) -gt 0){
   [void]$sha.TransformBlock($buffer,0,$n,$buffer,0)
   Write-Progress -Id 2 -ParentId 1 -Activity 'Checking file hash' -Status ([IO.Path]::GetFileName($Path)) -PercentComplete ([int](100*$stream.Position/[Math]::Max([long]1,$stream.Length)))
   if(((Get-Date)-$last).TotalSeconds -ge 5){Log "HASH $([IO.Path]::GetFileName($Path)) $([int](100*$stream.Position/$stream.Length))%";$last=Get-Date}
  }
  [void]$sha.TransformFinalBlock($buffer,0,0)
  return [BitConverter]::ToString($sha.Hash).Replace('-','')
 }finally{$stream.Dispose();$sha.Dispose();Write-Progress -Id 2 -Activity 'Checking file hash' -Completed}
}
function Copy-Disc([string]$From,[string]$To){
 $inputFile=[IO.File]::OpenRead($From);$outputFile=[IO.File]::Open($To,[IO.FileMode]::CreateNew);$buffer=New-Object byte[] (4MB);$last=Get-Date
 try{while(($n=$inputFile.Read($buffer,0,$buffer.Length)) -gt 0){
  $outputFile.Write($buffer,0,$n);$percent=[int](100*$inputFile.Position/$inputFile.Length)
  Write-Progress -Id 2 -ParentId 1 -Activity 'Copying disc' -Status "$percent%" -PercentComplete $percent
  if(((Get-Date)-$last).TotalSeconds -ge 5){Log "COPY $percent%";$last=Get-Date}
 }}finally{$inputFile.Dispose();$outputFile.Dispose();Write-Progress -Id 2 -Activity 'Copying disc' -Completed}
}
Add-Type @'
using System;using System.Runtime.InteropServices;
public class RogueSelect {
 [DllImport("user32.dll",EntryPoint="SendMessageW")] public static extern IntPtr Send(IntPtr h,uint m,IntPtr w,IntPtr l);
}
'@
$jabuProcess=$null;$done=0
try{
 Log 'Preparing isolated Jabu copy'
 $privateJabu=Join-Path $work 'Jabu'
 Copy-Item -LiteralPath $JabuPath -Destination $privateJabu -Recurse
 $pkgTool=Join-Path $privateJabu 'stuff\pkg.exe';$passcode='00000000000000000000000000000000'
 $jabuProcess=Start-Process -FilePath (Join-Path $privateJabu 'PS2-FPKG.exe') -WorkingDirectory $privateJabu -WindowStyle Hidden -PassThru
 Start-Sleep -Seconds 2
 foreach($w in [JabuUI]::Tops()){if([JabuUI]::Pid($w) -eq $jabuProcess.Id -and [JabuUI]::Text($w) -in @('Welcome to PS2-FPKG v0.7-Beta','PS2-FPKG v0.7-Beta - Convert PS2 games to PS4 fPKGs!')){[void][JabuUI]::ShowWindow($w,5)}}
 foreach($w in @(Get-JabuWindows)){if([JabuUI]::Text($w) -like 'Welcome*'){Click-Observed (Find-Only @(Get-JabuNodes $w) 'OK')}}
 $main=Wait-Window 'PS2-FPKG v0.7-Beta - Convert PS2 games to PS4 fPKGs!'
 foreach($job in $jobs){
  $number=$done+1;$baselineBin=$null;$baselineCue=$null;$stage=$null
  try{
   Write-Progress -Id 1 -Activity 'Rebuild with Rogue v1' -Status "$number/$($jobs.Count) $($job.Game)" -PercentComplete ([int](100*$done/$jobs.Count))
   Log "[$number/$($jobs.Count)] START $($job.Game)"
   $baselineBin=Hash $job.Bin;$baselineCue=Hash $job.Cue
   $drive=[IO.DriveInfo]::new([IO.Path]::GetPathRoot($OutputRoot));$size=(Get-Item -LiteralPath $job.Bin).Length
   if($drive.AvailableFreeSpace -lt (2*$size+1GB)){throw 'Insufficient free disk space for staging and new PKG'}
   $ext=if($job.Mode -eq 'MODE1/2048'){'.iso'}else{'.bin'}
   $stage=Join-Path $work ("disc-$number"+$ext)
   Log 'Copying source disc (original remains read-only)';Copy-Disc $job.Bin $stage
   if((Hash $stage) -ne $baselineBin){throw 'Staging copy hash mismatch'}
   Log 'Loading Disc1 and handling LIMG on the copy';$loaded=Open-DiscCopy $stage
   if($job.Mode -eq 'MODE2/2352' -and -not $loaded.Limg){throw 'LIMG confirmation was not observed for raw CD'}
   if([string]::IsNullOrWhiteSpace($loaded.Title)){
    $fallback=$job.Game -replace '\s*\([^()]*\)$','';$field=Row-Control @(Get-JabuNodes $main) 'Title:' '\.EDIT\.'
    [void][JabuUI]::SendMessage([IntPtr]$field.Handle,12,[IntPtr]::Zero,$fallback)
    if([JabuUI]::Text([IntPtr]$field.Handle) -ne $fallback){throw 'Failed to set missing title'}
   }
   # Observed in v0.7: General tab, Emulator label and adjacent WinForms ComboBox.
   $emu=Row-Control @(Get-JabuNodes $main) 'Emulator:' 'COMBOBOX'
   $idx=[JabuUI]::SendMessage([IntPtr]$emu.Handle,0x158,[IntPtr](-1),'Rogue v1')
   if($idx.ToInt64() -lt 0){throw 'Rogue v1 is not in the actual emulator dropdown'}
   [void][RogueSelect]::Send([IntPtr]$emu.Handle,0x14E,$idx,[IntPtr]::Zero)
   [void][JabuUI]::PostMessage([IntPtr]$emu.Parent,0x111,[IntPtr](($emu.Id -band 0xffff) -bor (1 -shl 16)),[IntPtr]$emu.Handle)
   Start-Sleep -Milliseconds 500
   foreach($warning in @(Get-JabuWindows)){
    $warningNodes=@(Get-JabuNodes $warning)
    if([JabuUI]::Text($warning) -eq 'This is still a Beta!' -and ($warningNodes.Text -join ' ') -match 'roque v1 emulator was not tested'){
     Log 'Jabu notice: Rogue v1 is not tested with all emulator features'
     Click-Observed (Find-Only $warningNodes 'OK')
    }
   }
   if([JabuUI]::Text([IntPtr]$emu.Handle) -ne 'Rogue v1'){throw 'Emulator selection failed'}
   Log 'Emulator selected: Rogue v1. Creating PKG'
   $job.GameId=$loaded.Id;$job.Status='Building';Save-Report
   $folder=Join-Path $work "build-$number"
   $built=Create-Package $loaded $folder ("game-$number")
   Log 'Validating title ID, embedded disc, emulator and package integrity'
   Validate-Pkg $built $loaded.Id $size ("game-$number")
   $fileTable=Get-Content -LiteralPath (Join-Path $logs "game-$number-files.txt")
   foreach($name in @('eboot.bin','ps2-emu-compiler.self')){
    $expectedSize=(Get-Item -LiteralPath (Join-Path $privateJabu "emus\Rogue v1\$name")).Length
    if(-not @($fileTable|Where-Object {$_ -match ('^F\s+'+$expectedSize+'\s+.*Image0/'+[regex]::Escape($name)+'$')}).Count){throw "Rogue component size mismatch: $name"}
   }
   $job.SourceUnchanged=((Hash $job.Bin) -eq $baselineBin -and (Hash $job.Cue) -eq $baselineCue)
   if(-not $job.SourceUnchanged){throw 'Source changed during conversion'}
   $target=Join-Path $OutputRoot ($job.Game+'.pkg')
   if(Test-Path -LiteralPath $target){throw 'Output exists; refusing overwrite'}
   Move-Item -LiteralPath $built -Destination $target
   $job.Pkg=$target;$job.Status='Verified';Log "VERIFIED $($job.Game)"
   # Delete only this run's single staged file, never a directory or original.
   if([IO.Path]::GetDirectoryName([IO.Path]::GetFullPath($stage)) -ne $work){throw 'Unsafe stage cleanup path'}
   Remove-Item -LiteralPath $stage
  }catch{
   $job.Status='Failed';$job.Error=$_.Exception.Message;Log "FAILED $($job.Game): $($job.Error)"
   if($baselineBin -and $baselineCue){$job.SourceUnchanged=((Hash $job.Bin) -eq $baselineBin -and (Hash $job.Cue) -eq $baselineCue)}
   # GUI state after a failure is unknown. Stop safely and mark remaining games Pending.
   Save-Report;break
  }
  $done++;Save-Report
 }
}finally{
 Write-Progress -Id 1 -Activity 'Rebuild with Rogue v1' -Completed
 if($jabuProcess -and -not $jabuProcess.HasExited){[void]$jabuProcess.CloseMainWindow()}
 Save-Report
 $verified=@($jobs|Where-Object Status -eq 'Verified').Count
 $failed=@($jobs|Where-Object Status -eq 'Failed').Count
 $pending=@($jobs|Where-Object Status -eq 'Pending').Count
 Log "FINAL: verified=$verified/$($jobs.Count), failed=$failed, pending=$pending"
 Log "Output and reports: $OutputRoot"
 Log 'Package validation is not a PS4 gameplay test.'
}
if(@($jobs|Where-Object {$_.Status -ne 'Verified' -or -not $_.SourceUnchanged}).Count){exit 1}
