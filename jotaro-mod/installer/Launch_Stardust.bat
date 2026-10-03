@echo off
setlocal
rem Stardust Storm: install a mod payload (if not installed yet) and start Storm 4 OFFLINE.
rem Uninstall later with: Stardust.bat -Action uninstall
cd /d "%~dp0.."

set "STATE=%~dp0state\stardust-state.json"
set "GAME="
if not exist "%STATE%" if not exist "out\phase5\install-state.json" (
  set /p "GAME=Storm 4 folder (contains NSUNS4.exe): "
)

set "PAYLOAD=out\payload\ladder\L0"
set "SET=L0"
echo Payload to run with [Enter = %PAYLOAD%]
set /p "PAYLOAD=Payload folder: "
for %%I in ("%PAYLOAD%") do set "SET=%%~nxI"

if defined GAME (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0stardust.ps1" -Action launch -GameRoot "%GAME%" -Payload "%PAYLOAD%" -Set "%SET%"
) else (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0stardust.ps1" -Action launch -Payload "%PAYLOAD%" -Set "%SET%"
)
pause
