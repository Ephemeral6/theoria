@echo off
REM Live dashboard server: serves monitor/ so app.html can fetch state.json.
REM Open http://localhost:8787/app.html once; the page refreshes itself.
cd /d "%~dp0"
echo Theoria dashboard: http://localhost:8787/app.html
"D:\Miniforge3\python.exe" -m http.server 8787 --bind 127.0.0.1
