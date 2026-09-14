@echo off
title Build Standalone Executable - PyInstaller
color 0b

echo ======================================================================
echo    GESTURE-BASED PRESENTATION CONTROL - STANDALONE EXE BUILDER
echo ======================================================================
echo.

cd /d "%~dp0"

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    set PYTHON_CMD=py
) else (
    set PYTHON_CMD=python
)

echo [INFO] Installing PyInstaller and dependencies if needed...
%PYTHON_CMD% -m pip install pyinstaller -r requirements.txt

echo.
echo [INFO] Compiling Standalone Executable with PyInstaller...
echo This may take 1-2 minutes to package OpenCV, MediaPipe, and Tkinter...
echo.

%PYTHON_CMD% -m PyInstaller ^
    --noconfirm ^
    --onedir ^
    --windowed ^
    --name "GesturePresentationController" ^
    --collect-all mediapipe ^
    --collect-all cv2 ^
    --collect-all PIL ^
    --add-data "docs;docs" ^
    --distpath "./dist" ^
    --workpath "./build" ^
    src/main.py

if %errorlevel% equ 0 (
    echo.
    color 0a
    echo ======================================================================
    echo [SUCCESS] Executable built successfully!
    echo Location: dist\GesturePresentationController\GesturePresentationController.exe
    echo ======================================================================
    echo.
) else (
    echo.
    color 0c
    echo [ERROR] Build failed! Check the output above.
)

pause
