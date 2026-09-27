. (Join-Path $PSScriptRoot 'native-ui.ps1')
function Wait-Window([string]$Title,[int]$Seconds=30){
 $until=(Get-Date).AddSeconds($Seconds)
 do{$found=@(Get-JabuWindows | Where-Object {[JabuUI]::Text($_) -like $Title});if($found.Count -eq 1){return $found[0]};Start-Sleep -Milliseconds 300}while((Get-Date)-lt $until)
 throw "Window not found uniquely: $Title"
}
function Click-Observed($Node){
 if(-not $Node.Enabled -or -not $Node.Visible){throw 'Control not enabled and visible'}
 [void][JabuUI]::PostMessage([IntPtr]$Node.Handle,0xF5,[IntPtr]::Zero,[IntPtr]::Zero)
}
function Find-Only($Nodes,[string]$Text){
 $a=@($Nodes|Where-Object {$_.Text -eq $Text -and $_.Visible});if($a.Count -ne 1){throw "Expected exactly one control: $Text, found $($a.Count)"};return $a[0]
}
function Row-Control($Nodes,[string]$Label,[string]$Class,[string]$Text='*'){
 $labelNode=Find-Only $Nodes $Label
 $a=@($Nodes|Where-Object {$_.Parent -eq $labelNode.Parent -and $_.Class -match $Class -and $_.Text -like $Text -and $_.Visible -and $_.Enabled -and $_.X -gt $labelNode.X -and [Math]::Abs(($_.Y+$_.Height/2)-($labelNode.Y+$labelNode.Height/2)) -lt 8})
 if($a.Count -ne 1){throw "Expected one observed row control for $Label, found $($a.Count)"};return $a[0]
}
function Open-DiscCopy([string]$Path){
 foreach($w in @(Get-JabuWindows)){if([JabuUI]::Text($w) -eq 'Welcome to PS2-FPKG v0.7-Beta'){Click-Observed (Find-Only @(Get-JabuNodes $w) 'OK')}}
 $main=Wait-Window 'PS2-FPKG v0.7-Beta - Convert PS2 games to PS4 fPKGs!'
 $nodes=@(Get-JabuNodes $main);Click-Observed (Row-Control $nodes 'Disc1:' 'BUTTON' 'Select')
 $open=Wait-Window 'Select a disc image...';$nodes=@(Get-JabuNodes $open)
 $edit=@($nodes|Where-Object {$_.Class -eq 'Edit' -and $_.Id -eq 1148 -and $_.Visible})
 if($edit.Count -ne 1){throw 'Observed file-name field changed'}
 [void][JabuUI]::SendMessage([IntPtr]$edit[0].Handle,12,[IntPtr]::Zero,$Path)
 Click-Observed (Find-Only $nodes '&Open')
 $until=(Get-Date).AddSeconds(90);$limg=$false;$unexpected=@{}
 do{
  foreach($w in @(Get-JabuWindows)){
   if($w -eq $main -or [JabuUI]::Text($w) -eq 'Select a disc image...'){continue};$nodes=@(Get-JabuNodes $w)
   if(($nodes.Text -join "`n") -match 'A LIMG segment will be added to the end of this .bin file'){
    Save-JabuScreenshot $w (Join-Path $logs 'last-limg.png');Click-Observed (Find-Only $nodes '&Yes');$limg=$true
   }else{
    # The Windows file dialog can briefly expose a shell notification while closing.
    # Never click it; stop only if the same unexpected window remains present.
    $key=$w.ToInt64().ToString()
    if(-not $unexpected.ContainsKey($key)){$unexpected[$key]=Get-Date}
    if(((Get-Date)-$unexpected[$key]).TotalSeconds -gt 4){throw "Unexpected load dialog: $($nodes.Text -join ' | ')"}
   }
  }
  # Jabu may stop answering WM_GETTEXT briefly while it appends LIMG.
  # Keep waiting within the existing deadline until all observed labels return.
  if(-not [JabuUI]::IsWindowEnabled($main)){Start-Sleep -Milliseconds 400;continue}
  $nodes=@(Get-JabuNodes $main)
  $labelsReady=$true
  foreach($label in @('Disc1:','NP Title:','Title:')){
   if(@($nodes|Where-Object {$_.Text -eq $label -and $_.Visible}).Count -ne 1){$labelsReady=$false}
  }
  if(-not $labelsReady){Start-Sleep -Milliseconds 400;continue}
  $disc=Row-Control $nodes 'Disc1:' '\.EDIT\.'
  if($disc.Text -eq $Path -and [JabuUI]::IsWindowEnabled($main)){
   $np=Row-Control $nodes 'NP Title:' '\.EDIT\.';$title=Row-Control $nodes 'Title:' '\.EDIT\.'
   if($np.Text -notmatch '^[A-Z]{4}[0-9]{5}$' -or $np.Text -eq 'CRST00001'){throw 'Game ID not detected'}
   return [pscustomobject]@{Window=$main;Id=$np.Text;Title=$title.Text;Limg=$limg;Disc=$disc.Text}
  }
  Start-Sleep -Milliseconds 400
 }while((Get-Date)-lt $until)
 throw 'Disc load timeout'
}
