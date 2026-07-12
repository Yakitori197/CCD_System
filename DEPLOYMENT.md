# 🚀 CCD 系統部署指南

## 📋 部署前檢查清單

### ✅ 硬體需求

- [ ] **相機**：USB 相機或工業相機（已連接並上電）
- [ ] **電腦**：Intel i5 8代 或 AMD Ryzen 5 以上
- [ ] **記憶體**：8 GB 以上（推薦 16 GB）
- [ ] **作業系統**：Windows 10/11 (64-bit)
- [ ] **GPU**（可選）：NVIDIA GPU（用於加速）

### ✅ 軟體需求

- [ ] **Python**：3.8 - 3.11（必須勾選 "Add to PATH"）
- [ ] **相機驅動**：已安裝對應驅動程式
- [ ] **網路連接**：用於下載依賴套件

---

## 📂 完整文件清單

### 核心程式文件（13 個）

```
專案根目錄/
├── main.py                      ✓ 主程式入口
├── config.json                  ✓ 系統配置文件
├── requirements.txt             ✓ 依賴套件清單（已更新）
├── start.bat                    ✓ 啟動腳本（已更新）
├── quick_install.bat            ✓ 快速安裝腳本（新增）
├── test_camera.py               ✓ 相機測試工具（新增）
│
├── core/                        ✓ 核心模組
│   ├── __init__.py
│   ├── camera.py               ✓ 相機管理
│   ├── detector.py             ✓ YOLOv8 檢測器
│   ├── rejector.py             ✓ 剔除控制器
│   └── engine.py               ✓ 檢測引擎
│
├── models/                      ✓ 數據模型
│   ├── __init__.py
│   └── data_models.py          ✓ 數據結構定義
│
├── utils/                       ✓ 工具模組
│   ├── __init__.py
│   ├── config.py               ✓ 配置管理
│   └── logger.py               ✓ 日誌系統
│
└── gui/                         ✓ 圖形介面
    ├── __init__.py
    └── main_window.py          ✓ 主視窗（已更新含預覽）
```

### 必須創建的目錄

```
models/                          ✓ 存放 YOLOv8 模型 (.pt 文件)
logs/                            ✓ 系統日誌
rejection_output/                ✓ 檢測輸出
├── OK/                          ✓ 良品圖片
├── NG/                          ✓ 不良品圖片
└── logs/                        ✓ 檢測記錄
```

---

## 🎯 部署步驟（全新電腦）

### 方法 A：快速安裝（推薦）

```batch
# 1. 解壓所有文件到目標目錄
例如：D:\ccd_system\

# 2. 雙擊執行
quick_install.bat

# 3. 按照提示完成安裝

# 4. 測試相機
python test_camera.py

# 5. 啟動系統
start.bat
```

### 方法 B：手動安裝

```batch
# 1. 檢查 Python
python --version
# 應顯示：Python 3.8.x 或 3.9.x 或 3.10.x 或 3.11.x

# 2. 升級 pip
python -m pip install --upgrade pip

# 3. 安裝依賴
pip install -r requirements.txt

# 4. 建立目錄
mkdir logs
mkdir models
mkdir rejection_output\OK
mkdir rejection_output\NG
mkdir rejection_output\logs

# 5. 測試相機
python test_camera.py

# 6. 啟動系統
python main.py
```

---

## 🔍 部署後驗證

### 1. 檢查套件安裝

```python
# 在 Python 命令列執行：
import cv2
print("OpenCV:", cv2.__version__)

import numpy
print("NumPy:", numpy.__version__)

import ultralytics
print("Ultralytics: OK")

from PIL import Image
print("Pillow: OK")

import serial
print("PySerial: OK")
```

### 2. 測試相機

```batch
python test_camera.py
```

**預期結果：**
- 找到至少一個可用相機
- 顯示相機索引和解析度
- 彈出相機測試視窗

### 3. 測試系統啟動

```batch
start.bat
```

**預期結果：**
- 所有套件檢查通過
- GUI 視窗正常顯示
- 沒有錯誤訊息

---

## ⚠️ 常見部署問題

### 問題 1：Python 未安裝或未加入 PATH

**症狀：**
```
'python' 不是內部或外部命令
```

**解決：**
1. 下載 Python：https://www.python.org/downloads/
2. 安裝時勾選 "Add Python to PATH"
3. 重新啟動命令提示字元

---

### 問題 2：pip 安裝套件失敗

**症狀：**
```
ERROR: Could not find a version that satisfies the requirement...
```

**解決方案 A：使用國內鏡像（中國用戶）**
```batch
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

**解決方案 B：逐個安裝**
```batch
pip install opencv-python
pip install numpy
pip install ultralytics
pip install pillow
pip install pyserial
```

**解決方案 C：離線安裝**
```batch
# 在有網路的電腦下載
pip download -r requirements.txt -d packages/

# 複製 packages/ 資料夾到目標電腦
pip install --no-index --find-links=packages/ -r requirements.txt
```

---

### 問題 3：相機無法開啟

**症狀：**
```
無法開啟相機 0
```

**診斷步驟：**

1. **檢查相機連接**
   ```batch
   # Windows 裝置管理員
   devmgmt.msc
   
   # 查看「影像裝置」或「相機」
   ```

2. **測試不同索引**
   ```batch
   python test_camera.py
   # 會自動測試索引 0-5
   ```

3. **修改配置**
   ```json
   // config.json
   {
     "camera_index": 1,  // 改成測試工具找到的索引
     ...
   }
   ```

4. **檢查占用**
   ```batch
   # 關閉所有可能占用相機的程式
   # - Skype
   # - Teams
   # - Zoom
   # - 瀏覽器
   ```

---

### 問題 4：GUI 無法顯示相機畫面

**症狀：**
- GUI 啟動正常
- 但預覽區域是黑色或顯示「未開啟相機」

**檢查清單：**

1. **確認 Pillow 已安裝**
   ```batch
   pip install pillow --upgrade
   ```

2. **確認 GUI 代碼已更新**
   ```python
   # gui/main_window.py 應包含：
   from PIL import Image, ImageTk
   ```

3. **檢查相機索引**
   ```batch
   python test_camera.py
   ```

4. **查看日誌**
   ```
   logs/ccd_YYYYMMDD.log
   ```

---

### 問題 5：模型載入失敗

**症狀：**
```
模型載入失敗: [Errno 2] No such file or directory
```

**解決：**

1. **確認模型文件存在**
   ```
   models/
   └── best_model.pt  ← 您的 YOLOv8 模型
   ```

2. **確認模型格式正確**
   - 必須是 YOLOv8 訓練的 .pt 文件
   - 不能是 YOLOv5 或其他版本

3. **測試模型**
   ```python
   from ultralytics import YOLO
   model = YOLO("models/best_model.pt")
   print(model.names)  # 應顯示類別名稱
   ```

---

## 📊 部署檢查表

完成以下所有項目後，系統即可投入使用：

### 安裝階段
- [ ] Python 3.8-3.11 已安裝並加入 PATH
- [ ] 所有依賴套件安裝成功
- [ ] 目錄結構完整
- [ ] 配置文件已準備

### 測試階段
- [ ] 相機測試通過（test_camera.py）
- [ ] 找到正確的相機索引
- [ ] 系統啟動無錯誤
- [ ] GUI 顯示正常

### 功能階段
- [ ] YOLOv8 模型已準備
- [ ] 模型載入成功
- [ ] 相機畫面顯示正常
- [ ] 單次檢測功能正常
- [ ] 連續檢測功能正常
- [ ] 統計數據更新正常

### 可選功能
- [ ] 剔除裝置連接（如需要）
- [ ] 序列埠測試通過
- [ ] 剔除功能測試正常

---

## 🎓 培訓建議

為操作人員準備以下培訓內容：

### 基礎操作（15 分鐘）
1. 啟動系統：雙擊 start.bat
2. 載入模型：點擊「載入模型」選擇 .pt 文件
3. 開啟相機：點擊「開啟相機」
4. 開始檢測：點擊「開始連續檢測」
5. 停止檢測：點擊「停止檢測」

### 參數調整（10 分鐘）
1. 置信度閾值：滑桿調整 0.1-0.9
2. 剔除延遲：根據產線速度設定（毫秒）
3. 啟用/停用剔除：勾選框切換

### 異常處理（10 分鐘）
1. 相機斷線：系統會自動重連
2. 檢測速度慢：降低解析度或使用 GPU
3. 誤檢率高：提高置信度閾值
4. 漏檢率高：降低置信度閾值

### 數據查看（5 分鐘）
1. 即時統計：右側面板實時顯示
2. 檢測記錄：rejection_output/logs/
3. 圖片存檔：rejection_output/OK 或 NG/
4. 系統日誌：logs/

---

## 📞 技術支援

如遇到無法解決的問題：

1. **查看日誌**
   ```
   logs/ccd_YYYYMMDD.log
   ```

2. **收集信息**
   - Python 版本
   - 作業系統版本
   - 錯誤訊息完整內容
   - 相機型號

3. **聯繫技術支援**
   - 提供上述信息
   - 附上日誌文件
   - 描述操作步驟

---

## 📝 版本記錄

### v1.0 (2025-10-02)
- ✅ 模組化架構重構
- ✅ 新增相機即時預覽功能
- ✅ 新增自動重連機制
- ✅ 完善的日誌系統
- ✅ 快速安裝腳本
- ✅ 相機測試工具


---