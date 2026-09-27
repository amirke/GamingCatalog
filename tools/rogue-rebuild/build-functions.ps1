function Invoke-PkgCheck([string[]]$Arguments,[string]$LogPath){
 foreach($arg in $Arguments){if($arg.Contains('"')){throw 'Unexpected quote in package tool argument'}}
 $quoted=($Arguments|ForEach-Object {'"'+$_+'"'}) -join ' '
 $process=Start-Process -FilePath $pkgTool -ArgumentList $quoted -WindowStyle Hidden -PassThru -RedirectStandardOutput $LogPath -RedirectStandardError ($LogPath+'.stderr')
 # Retain the native handle before waiting; Windows PowerShell 5.1 otherwise
 # may lose ExitCode when Start-Process redirects output and the child exits.
 $nativeHandle=$process.Handle
 $start=Get-Date
 while(-not $process.WaitForExit(5000)){Log "CHECK $($Arguments[0]) | elapsed $([int]((Get-Date)-$start).TotalSeconds)s"}
 $process.WaitForExit()
 if($process.ExitCode -ne 0){throw "Package tool failed: $($Arguments[0]); see $LogPath"}
 return @(Get-Content -LiteralPath $LogPath)
}
function Validate-Pkg([string]$Path,[string]$GameId,[long]$MinDiscBytes,[string]$LogName){
 $info=@(Invoke-PkgCheck @('img_info',$Path) (Join-Path $logs ($LogName+'-info.txt')))
 if(($info -join "`n") -notmatch [regex]::Escape("Title ID: $GameId")){throw 'Package title ID does not match the loaded game'}
 $list=@(Invoke-PkgCheck @('img_file_list','--passcode',$passcode,'--oformat','long+recursive',$Path) (Join-Path $logs ($LogName+'-files.txt')))
 $discLine=@($list | Where-Object {$_ -match '^F\s+\d+\s+.*Image0/image/disc01\.iso$'})
 if($discLine.Count -ne 1 -or $discLine[0] -notmatch '^F\s+(\d+)\s'){throw 'Embedded disc missing'}
 if([long]$Matches[1] -lt $MinDiscBytes){throw 'Embedded disc is smaller than input'}
 foreach($required in @('Image0/eboot.bin','Image0/ps2-emu-compiler.self','Sc0/param.sfo')){if(-not @($list|Where-Object {$_.EndsWith($required)}).Count){throw "Package missing $required"}}
 Log 'Checking package integrity; elapsed time is reported every five seconds'
 $verify=@(Invoke-PkgCheck @('img_verify','--passcode',$passcode,'--format_check','off','--integrity_check','on','--no_progress_bar',$Path) (Join-Path $logs ($LogName+'-integrity.txt')))
 if(($verify -join "`n") -notmatch 'Check Integrity Process successfully finished'){throw 'Package integrity check failed'}
}
function Create-Package($Loaded,[string]$Folder,[string]$LogName){
 New-Item -ItemType Directory -Force -Path $Folder | Out-Null
 if(@(Get-ChildItem -LiteralPath $Folder -Filter '*.pkg').Count){throw 'Output folder already contains a PKG; refusing overwrite'}
 Click-Observed (Find-Only @(Get-JabuNodes $Loaded.Window) 'Create fPKG')
 $dialog=Wait-Window 'Browse For Folder'
 [JabuUI]::SelectFolder($dialog,$Folder)
 Click-Observed (Find-Only @(Get-JabuNodes $dialog) 'OK')
 $buildStart=Get-Date;$until=(Get-Date).AddMinutes(60);$nextLog=(Get-Date).AddSeconds(5)
 do{
  foreach($w in @(Get-JabuWindows)){
   if($w -eq $Loaded.Window -or [JabuUI]::Text($w) -eq 'Browse For Folder'){continue}
   $nodes=@(Get-JabuNodes $w);$message=$nodes.Text -join "`n"
   if($message -match 'Process Finished!'){
    $nodes | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath (Join-Path $logs ($LogName+'-completion.json'))
    Click-Observed (Find-Only $nodes 'OK')
    Start-Sleep -Milliseconds 600
    $files=@(Get-ChildItem -LiteralPath $Folder -Filter '*.pkg')
    if($files.Count -ne 1){throw 'Jabu finished but one unique PKG was not found'}
    return $files[0].FullName
   }
   Save-JabuScreenshot $w (Join-Path $logs ($LogName+'-unexpected.png'))
   $nodes | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath (Join-Path $logs ($LogName+'-unexpected.json'))
   throw "Unexpected build dialog: $message"
  }
  if(-not (Get-Process -Name PS2-FPKG -ErrorAction SilentlyContinue)){throw 'Jabu exited during creation'}
  if((Get-Date) -gt $nextLog){Log "BUILDING $LogName | elapsed $([int]((Get-Date)-$buildStart).TotalSeconds)s";$nextLog=(Get-Date).AddSeconds(5)}
  Start-Sleep -Seconds 1
 }while((Get-Date)-lt $until)
 throw 'Jabu build timeout'
}
