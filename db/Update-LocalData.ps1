# Run after updating ps4_games_expanded.json to refresh double-click HTML support.
$ErrorActionPreference = 'Stop'
$inputPath = Join-Path $PSScriptRoot 'ps4_games_expanded.json'
$text = [IO.File]::ReadAllText($inputPath)
$null = ConvertFrom-Json -InputObject $text
$text = $text.Replace([string][char]0x2028, '\u2028').Replace([string][char]0x2029, '\u2029')
[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'ps4-games-data.js'), 'window.PS4_GAMES_DATA = ' + $text + ';', [Text.UTF8Encoding]::new($false))
Write-Host 'Local browser data updated.'
