@echo off
chcp 65001 >nul
cd /d "%~dp0.."
set WID=%~1
set TMPF=%TEMP%\theoria-%WID%.txt
echo Your worker id is %WID% - use it for every board.py command.> "%TMPF%"
echo.>> "%TMPF%"
type "monitor\prompts\W-worker.md" >> "%TMPF%"
echo === Theoria worker %WID% starting ===
type "%TMPF%" | claude -p --dangerously-skip-permissions --model opus
echo.
echo === worker %WID% finished - press any key to close ===
pause >nul
