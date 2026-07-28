@echo off
REM Dashboard auto-refresh: pure python, no sessions spawned, safe to run often.
cd /d "%~dp0.."
"D:\Miniforge3\python.exe" monitor\scan.py >> monitor\refresh.log 2>&1
