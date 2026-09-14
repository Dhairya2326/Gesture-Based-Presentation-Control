@echo off
title Gesture-Based Presentation Control - Launcher
color 0b

echo ======================================================================
echo    GESTURE-BASED PRESENTATION CONTROL USING COMPUTER VISION
echo    Milestone: Week 6 (Real-Time Gesture Recognition Engine)
echo ======================================================================
echo.

:: Navigate to the directory of this batch script
cd /d "%~dp0"

:: Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    py --version >nul 2>&1
    if %errorlevel% neq 0 (
        color 0c
        echo [ERROR] Python is not found in PATH!
        echo Please install Python 3.11+ from https://www.python.org/downloads/
        echo Make sure to check "Add Python to PATH" during installation.
        echo.
        pause
        exit /b 1
    ) else (
        set PYTHON_CMD=py
    )
) else (
    set PYTHON_CMD=python
)

echo [OK] Using Python: 
%PYTHON_CMD% --version
echo.

:: Verify dependencies (OpenCV, MediaPipe, Pillow)
echo [INFO] Checking Python dependencies...
%PYTHON_CMD% -c "import cv2, mediapipe, PIL" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing required dependencies from requirements.txt...
    %PYTHON_CMD% -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        color 0c
        echo [ERROR] Failed to install requirements. Please check your internet connection.
        pause
        exit /b 1
    )
)

echo [OK] All dependencies verified.
echo.
echo ======================================================================
echo    Launching Graphical User Interface (GUI)...
echo    Press Ctrl+C in this console or close the window to exit.
echo ======================================================================
echo.

:: Run Application
%PYTHON_CMD% -m src.main %*

if %errorlevel% neq 0 (
    echo.
    color 0c
    echo [INFO] Application exited with code %errorlevel%.
    pause
)
