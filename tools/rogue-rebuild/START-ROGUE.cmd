@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Rebuild-Rogue.ps1" -SourceRoot "%~dp0." %*
set "result=%ERRORLEVEL%"
echo.
echo Finished with exit code %result%. See progress.log and report.csv in the output folder.
pause
exit /b %result%
