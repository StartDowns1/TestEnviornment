@echo off
rem Stardust Storm installer wrapper. Example:
rem   Stardust.bat -Action install -Payload ..\out\payload\ladder\L0 -Set L0 -DryRun
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0stardust.ps1" %*
pause
