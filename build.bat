@echo off
echo Deleting existing spec file...
if exist ThotIndex.spec del ThotIndex.spec

echo Activating venv...
call venv\Scripts\activate

echo Building...
.\venv\Scripts\python.exe -O -m PyInstaller -F -y -c --clean --windowed --name "ThotIndex" --paths . src/main.py --paths venv/Library/bin

echo Build complete.
pause
