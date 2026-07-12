@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ========================================
:: CCD 系統 - 啟動腳本
:: ========================================

title CCD System Starting...

echo.
echo ================================================
echo      CCD 視覺檢測與自動剔除系統
echo ================================================
echo.

:: ========================================
:: 1. 檢查 Python
:: ========================================
echo [1/4] 檢查 Python...

python --version >nul 2>&1
if errorlevel 1 (
    echo [錯誤] 未安裝 Python
    echo.
    echo 請下載安裝 Python 3.8-3.11:
    echo https://www.python.org/downloads/
    echo.
    echo 安裝時務必勾選 "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

python --version
echo Python 檢查通過
echo.

:: ========================================
:: 2. 檢查必要套件
:: ========================================
echo [2/4] 檢查必要套件...

set MISSING=0

python -c "import cv2" >nul 2>&1
if errorlevel 1 (
    echo [缺失] opencv-python
    set MISSING=1
) else (
    echo [OK] opencv-python
)

python -c "import numpy" >nul 2>&1
if errorlevel 1 (
    echo [缺失] numpy
    set MISSING=1
) else (
    echo [OK] numpy
)

python -c "import ultralytics" >nul 2>&1
if errorlevel 1 (
    echo [缺失] ultralytics
    set MISSING=1
) else (
    echo [OK] ultralytics
)

python -c "import PIL" >nul 2>&1
if errorlevel 1 (
    echo [缺失] pillow - 重要!
    set MISSING=1
) else (
    echo [OK] pillow
)

python -c "import serial" >nul 2>&1
if errorlevel 1 (
    echo [缺失] pyserial
    set MISSING=1
) else (
    echo [OK] pyserial
)

echo.

:: ========================================
:: 3. 安裝缺失套件
:: ========================================
if %MISSING%==1 (
    echo [3/4] 安裝缺失套件...
    echo.
    echo 正在安裝，請稍候（可能需要 3-5 分鐘）...
    echo.
    
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    
    if errorlevel 1 (
        echo.
        echo [錯誤] 安裝失敗
        echo.
        echo 請手動執行:
        echo pip install opencv-python numpy ultralytics pillow pyserial
        echo.
        pause
        exit /b 1
    )
    
    echo.
    echo 套件安裝完成
    echo.
) else (
    echo [3/4] 所有套件已安裝
    echo.
)

:: ========================================
:: 4. 檢查目錄
:: ========================================
echo [4/4] 檢查目錄結構...

if not exist "main.py" (
    echo [錯誤] 找不到 main.py
    pause
    exit /b 1
)

if not exist "core\" mkdir core
if not exist "models\" mkdir models
if not exist "utils\" mkdir utils
if not exist "gui\" mkdir gui
if not exist "logs\" mkdir logs

echo 目錄結構正常
echo.

:: ========================================
:: 啟動程式
:: ========================================
echo ================================================
echo  正在啟動程式...
echo ================================================
echo.

python main.py

if errorlevel 1 (
    echo.
    echo ================================================
    echo  程式執行失敗
    echo ================================================
    echo.
    echo 常見問題:
    echo 1. 相機問題 - 執行 test_camera.py
    echo 2. 模型問題 - 檢查 models 目錄
    echo 3. 查看日誌 - 檢查 logs 目錄
    echo.
    pause
    exit /b 1
)

echo.
echo ================================================
echo  程式已正常退出
echo ================================================
echo.
pause