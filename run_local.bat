@echo off
chcp 65001 > nul
echo ======================================================================
echo   RogueByte GeoForensics Intelligence - تشغيل التطبيق المكتبي محلياً
echo ======================================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [خطأ] Python غير مثبت أو غير مضاف لمتغيرات البيئة PATH!
    pause
    exit /b 1
)

if not exist venv (
    echo [*] إنشاء بيئة عمل افتراضية جديدة (venv)...
    python -m venv venv
)

echo [*] تفعيل البيئة وتثبيت الاعتماديات...
call venv\Scripts\activate.bat
python -m pip install -r requirements.txt

echo.
echo [*] تشغيل واجهة التحقيق الجنائي PySide6...
python main.py

pause
