@echo off
echo Starting KKWIEER College Hall Reservation System...
echo.

pushd backend

:: Check if .venv exists
if not exist "..\.venv\" (
    echo Error: Virtual environment not found in root.
    echo Please create it using: python -m venv .venv
    pause
    exit /b
)

echo Activating Virtual Environment...
call ..\.venv\Scripts\activate

echo Launching Flask Server...
echo The website will be available at: http://localhost:5000
echo.

:: Run python in a way that stays open
python app.py

popd
pause
