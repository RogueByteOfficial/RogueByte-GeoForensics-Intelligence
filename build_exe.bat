@echo off
cd /d "%~dp0"
chcp 65001 > nul
echo ======================================================================
echo   RogueByte GeoForensics Intelligence - بناء ملف EXE لنظام Windows
echo ======================================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [خطأ] لم يتم العثور على Python في مسار النظام PATH!
    echo يرجى تثبيت Python 3.10 أو أحدث وتفعيل خيار "Add Python to PATH".
    pause
    exit /b 1
)

echo [*] التحقق من الحزم وتثبيتها...
python -m pip install -r requirements.txt

echo.
echo [*] بدء تجميع التطبيق باستخدام PyInstaller...
python build_exe.py

echo.
pause
