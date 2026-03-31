@echo off
:: CHRS - Quick Git Push (double-click to run)
:: Pass an optional commit message: push.bat "my message"

cd /d "%~dp0"

if "%~1"=="" (
    for /f "tokens=1-5 delims=/ :" %%a in ("%date% %time%") do set TS=%%c-%%b-%%a %%d:%%e
    set MSG=update: %TS%
) else (
    set MSG=%~1
)

echo.
echo [*] Staging all changes...
git add -A

echo [*] Committing: %MSG%
git commit -m "%MSG%"

echo [*] Pushing to GitHub...
git push origin master

echo.
echo [OK] Done! Changes pushed to GitHub.
echo.
pause
