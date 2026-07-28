@echo off
REM Theoria research worker - visible terminal edition
REM   monitor\worker.cmd          (auto id)
REM   monitor\worker.cmd W-alice  (named)
REM Opens its own console window. The worker serves itself from the board:
REM claim -> deliver -> claim next. Close the window to retire that worker.
setlocal
set WID=%~1
if "%WID%"=="" set WID=W-%RANDOM%
start "Theoria %WID%" "%~dp0_worker_run.cmd" %WID%
echo launched %WID% in its own window
endlocal
