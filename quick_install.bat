@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ========================================
:: CCD 系統 - 快速安裝腳本
:: 適用於首次使用
:: ========================================

title CCD 系統 - 快速安裝

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║     CCD 系統快裝工具                                        ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo 此腳本將自動完成以下操作：
echo   1. 檢查 Python 環境
echo   2. 升級 pip 到最新版
echo   3. 安裝所有依賴套件
echo   4. 建立必要的目錄結構
echo   5. 測試相機連接
echo.
echo 預計耗時：5-10 分鐘
echo.

choice /C YN /M "是否繼續安裝"
if errorlevel 2 exit /b 0

:: ========================================
:: 1. 檢查 Python
:: ========================================
echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo [1/5] 檢查 Python 環境
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ❌ 未檢測到 Python
    echo.
    echo 請先安裝 Python 3.8-3.11：
    echo https://www.python.org/downloads/
    echo.
    echo 安裝時務必勾選：Add Python to PATH
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✓ 已安裝 Python %PYTHON_VERSION%

:: ========================================
:: 2. 升級 pip
:: ========================================
echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo [2/5] 升級 pip
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo 正在升級 pip...
python -m pip install --upgrade pip

if %errorlevel% neq 0 (
    echo ⚠ pip 升級失敗，但繼續安裝
) else (
    echo ✓ pip 已升級到最新版本
)

:: ========================================
:: 3. 安裝依賴套件
:: ========================================
echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo [3/5] 安裝依賴套件
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
echo 這可能需要 5-10 分鐘，請耐心等待...
echo.

:: 檢查 requirements.txt
if not exist "requirements.txt" (
    echo ❌ 找不到 requirements.txt
    echo.
    echo 請確保以下文件在同一目錄：
    echo   - quick_install.bat
    echo   - requirements.txt
    echo.
    pause
    exit /b 1
)

:: 顯示將要安裝的套件
echo 將安裝以下套件：
type requirements.txt | findstr /v /r "^#" | findstr /v /r "^$"
echo.

:: 開始安裝
echo 開始安裝...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo ❌ 套件安裝失敗
    echo.
    echo 可能的原因：
    echo   - 網路連接問題
    echo   - 防火牆阻擋
    echo   - pip 來源無法訪問
    echo.
    echo 解決方案：
    echo.
    echo 方案 1：使用國內鏡像（推薦中國用戶）
    echo   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    echo.
    echo 方案 2：逐個安裝套件
    echo   pip install opencv-python numpy ultralytics pillow pyserial
    echo.
    pause
    exit /b 1
)

echo.
echo ✓ 所有依賴套件安裝完成

:: ========================================
:: 4. 建立目錄結構
:: ========================================
echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo [4/5] 建立目錄結構
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

:: 建立主要目錄
if not exist "core" mkdir core && echo ✓ core\
if not exist "models" mkdir models && echo ✓ models\
if not exist "utils" mkdir utils && echo ✓ utils\
if not exist "gui" mkdir gui && echo ✓ gui\
if not exist "logs" mkdir logs && echo ✓ logs\
if not exist "rejection_output" mkdir rejection_output && echo ✓ rejection_output\

:: 建立子目錄
if not exist "rejection_output\OK" mkdir rejection_output\OK
if not exist "rejection_output\NG" mkdir rejection_output\NG
if not exist "rejection_output\logs" mkdir rejection_output\logs

echo.
echo ✓ 目錄結構建立完成

:: ========================================
:: 5. 驗證安裝
:: ========================================
echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo [5/5] 驗證安裝
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo.
echo 檢查關鍵套件...

set ALL_OK=1

python -c "import cv2; print('✓ OpenCV:', cv2.__version__)" 2>nul
if %errorlevel% neq 0 (
    echo ✗ OpenCV 安裝失敗
    set ALL_OK=0
)

python -c "import numpy; print('✓ NumPy:', numpy.__version__)" 2>nul
if %errorlevel% neq 0 (
    echo ✗ NumPy 安裝失敗
    set ALL_OK=0
)

python -c "import ultralytics; print('✓ Ultralytics (YOLOv8)')" 2>nul
if %errorlevel% neq 0 (
    echo ✗ Ultralytics 安裝失敗
    set ALL_OK=0
)

python -c "import PIL; print('✓ Pillow (GUI):', PIL.__version__)" 2>nul
if %errorlevel% neq 0 (
    echo ✗ Pillow 安裝失敗（GUI 將無法顯示）
    set ALL_OK=0
)

python -c "import serial; print('✓ PySerial (序列通訊)')" 2>nul
if %errorlevel% neq 0 (
    echo ✗ PySerial 安裝失敗
    set ALL_OK=0
)

echo.

if %ALL_OK%==0 (
    echo ╔════════════════════════════════════════════════════════════╗
    echo ║  ⚠ 安裝未完全成功                                         ║
    echo ╚════════════════════════════════════════════════════════════╝
    echo.
    echo 部分套件安裝失敗，但您仍可以嘗試運行程式
    echo.
) else (
    echo ╔════════════════════════════════════════════════════════════╗
    echo ║  ✓ 安裝完成！                                              ║
    echo ╚════════════════════════════════════════════════════════════╝
)

:: ========================================
:: 後續步驟提示
:: ========================================
echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo 下一步操作：
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
echo 1. 測試相機連接（推薦）
echo    執行：python test_camera.py
echo.
echo 2. 準備 YOLOv8 模型
echo    將 .pt 模型文件放到 models\ 目錄
echo.
echo 3. 配置系統（可選）
echo    編輯 config.json 調整參數
echo.
echo 4. 啟動系統
echo    執行：start.bat
echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

:: 詢問是否立即測試相機
echo.
choice /C YN /M "是否立即測試相機"
if errorlevel 2 goto :skip_test

if exist "test_camera.py" (
    echo.
    echo 正在啟動相機測試...
    python test_camera.py
) else (
    echo.
    echo ⚠ 找不到 test_camera.py
    echo 請手動創建此測試腳本
)

:skip_test
echo.
echo 安裝完成！
pause