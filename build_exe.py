"""
RogueByte GeoForensics Intelligence - Automated PyInstaller Builder
==================================================================
Builds a standalone executable (EXE) or distribution folder using PyInstaller.
Usage:
    python build_exe.py
"""

import sys
import os
import subprocess
import shutil

# Ensure working directory is the script's directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def build():
    print("=" * 70)
    print("  ROGUEBYTE GEOFORENSICS INTELLIGENCE - BUILD STANDALONE EXE")
    print("=" * 70)

    print(f"[*] Python Runtime: {sys.version.split()[0]} ({sys.platform})")
    print(f"[*] Working Directory: {os.getcwd()}")

    # Check PyInstaller
    try:
        import PyInstaller
        print(f"[+] PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        print("[!] PyInstaller غير مثبت. جاري التثبيت...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller", "PySide6", "reportlab"])

    # Clean prior build artifacts
    for d in ["build", "dist"]:
        if os.path.exists(d):
            print(f"[*] تنظيف المجلد السابق: {d}/")
            try:
                shutil.rmtree(d, ignore_errors=True)
            except Exception:
                pass

    # Direct clean command without UPX to prevent Antivirus false positives
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "main.py",
        "--name=RogueByteGeoForensics",
        "--onefile",
        "--windowed",
        "--noconfirm",
        "--clean",
        "--noupx",
        "--hidden-import=PySide6",
        "--hidden-import=PySide6.QtCore",
        "--hidden-import=PySide6.QtWidgets",
        "--hidden-import=PySide6.QtGui",
        "--hidden-import=sqlite3",
        "--hidden-import=hashlib",
        "--hidden-import=json",
    ]

    print(f"\n[*] جاري بدء عملية البناء والتجميع:\n    {' '.join(cmd)}\n")
    ret = subprocess.call(cmd)

    dist_dir = os.path.abspath("dist")
    found_files = []
    if os.path.exists(dist_dir):
        for root, dirs, files in os.walk(dist_dir):
            for file in files:
                found_files.append(os.path.join(root, file))

    if ret == 0 and found_files:
        print("\n" + "=" * 70)
        print("  نجح تجميع التطبيق بنجاح! SUCCESSFUL BUILD")
        print("=" * 70)
        print(f"[+] المجلد الناتج: {dist_dir}")
        for fpath in found_files:
            size_mb = os.path.getsize(fpath) / (1024 * 1024)
            print(f"    -> {os.path.basename(fpath)} ({size_mb:.2f} MB)")
        print("\nيمكنك الآن تشغيل الملف التنفيذي مباشرة على Windows.")
    else:
        print("\n" + "=" * 70)
        if not found_files:
            print("[!] تنبيه هام: مجلد dist فارغ!")
            print("السبب الأكثر شيوعاً في Windows:")
            print("قام مضاد الفيروسات (Windows Defender) بحجز أو حذف ملف EXE فور إنشائه (False Positive).")
            print("الحل: افتح 'أمن Windows' -> 'الحماية من الفيروسات' -> 'سجل الحماية' واسمح بالملف.")
            print("\nأو جرب بناء نمط المجلد المستقر (Folder mode):")
            print("pyinstaller --noconfirm --onedir --windowed --name RogueByteGeoForensics main.py")
        else:
            print(f"[!] حدث خطأ أثناء التجميع برمز خروج: {ret}")
        print("=" * 70)


if __name__ == "__main__":
    build()
