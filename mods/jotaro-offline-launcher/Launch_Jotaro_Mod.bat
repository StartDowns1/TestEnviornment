@echo off
setlocal
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "%~dp0modctl.ps1" launch
set "RESULT=%ERRORLEVEL%"
echo.
if not "%RESULT%"=="0" echo Mod launcher stopped with code %RESULT%.
pause
exit /b %RESULT%

