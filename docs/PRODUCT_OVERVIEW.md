# CCD 視覺檢測與自動剔除系統 
模組化、可擴展、生產就緒的工業 AOI（自動光學檢測）解決方案，專為製造產線設計。系統採用 YOLOv8 深度學習技術，提供高精度、高速度的 OK/NG 判定，並可整合硬體剔除裝置實現全自動化閉環控制。
---

## 📖 目錄

- [專案簡介](#-專案簡介)
- [功能特色](#-功能特色)
- [系統架構](#-系統架構)
- [技術棧](#-技術棧)
- [快速開始](#-快速開始)
- [詳細安裝](#-詳細安裝)
- [使用指南](#-使用指南)
- [配置說明](#-配置說明)
- [檢測模式](#-檢測模式詳解)
- [API 文檔](#-api-文檔)
- [硬體整合](#-硬體整合)
- [故障排除](#-故障排除)
- [開發指南](#-開發指南)
- [生產部署](#-生產部署)
- [FAQ](#-常見問題)
- [更新日誌](#-更新日誌)
- [貢獻指南](#-貢獻指南)

---

## 🎯 專案簡介

CCD 視覺檢測系統是一套**模組化、可擴展、生產就緒**的工業 AOI（自動光學檢測）解決方案，專為智能製造產線設計。系統採用 YOLOv8 深度學習技術，提供高精度、高速度的 OK/NG 判定，並可整合硬體剔除裝置實現**全自動化閉環控制**。

### 設計理念

- **🎯 零配置啟動** - Auto 模式自動識別模型類型，無需手動設定
- **🛡️ 企業級穩定性** - 相機自動重連、異常隔離、完整日誌追蹤
- **🔧 高度可擴展** - 模組化架構，支援自定義檢測邏輯、剔除策略
- **💻 操作簡便** - GUI 即時預覽、一鍵啟停、統計可視化

### 適用場景

| 應用領域 | 檢測內容 | 推薦模式 |
|---------|---------|---------|
| **表面缺陷檢測** | 劃痕、裂紋、污點、凹陷 | Defect 模式 |
| **組裝驗證** | 零件缺失、位置偏移、規格不符 | Object 模式 |
| **包裝檢驗** | 標籤錯誤、封口不良、異物混入 | Defect 模式 |
| **品質分類** | OK/NG 二分類、多等級品質判定 | Auto 模式（自動識別） |
| **計數檢測** | 零件數量、孔位驗證 | Object 模式 |

---

## ✨ 功能特色

### 🤖 智能模式自動識別（業界首創）

系統能自動分析模型文件和類別信息，智能判定最適合的檢測模式：

```
┌─────────────────────────────────────────────────────────┐
│  Auto Mode - 智能識別引擎                                │
├─────────────────────────────────────────────────────────┤
│  輸入：模型文件 (.pt) + 類別名稱                         │
│  ↓                                                       │
│  分析維度 1：文件名關鍵字（權重 30%）                    │
│  • defect/scratch → Defect Mode (+30)                   │
│  • yolov8/coco → Object Mode (-50)                      │
│  ↓                                                       │
│  分析維度 2：類別名稱語義（權重 50%）                    │
│  • scratch/crack → Defect Mode (+80)                    │
│  • person/car → Object Mode (-80)                       │
│  ↓                                                       │
│  分析維度 3：類別數量（權重 20%）                        │
│  • ≤5 classes → Defect Mode (+40)                       │
│  • ≥80 classes → Object Mode (-50)                      │
│  ↓                                                       │
│  綜合評分 → 模式判定 + 置信度（0-100%）                  │
│  ↓                                                       │
│  特殊處理：檢測到 OK/NG 類別 → Classification Mode      │
└─────────────────────────────────────────────────────────┘

輸出結果：
  • 檢測模式：Defect / Object / Classification
  • 置信度分數：85% (High) / 60% (Medium) / 40% (Low)
  • 判定邏輯：自動配置
  • GUI 顯示：即時更新模式指示器
```

**優勢**：
- ✅ 新手友好：無需理解底層邏輯，系統自動配置
- ✅ 透明可控：顯示置信度評分，支援手動切換
- ✅ 特殊支援：自動識別分類模型（OK/NG 類別）

---

### 🎨 實時相機預覽

- **30 FPS** 流暢顯示，延遲 < 30ms
- **自適應縮放** - 根據視窗大小自動調整顯示
- **檢測標註疊加**：
  - 🔲 檢測框（Bounding Box）
  - 🏷️ 類別名稱 + 置信度百分比
  - ✅/❌ OK/NG 判定結果（綠色/紅色標記）
  - 🔧 當前檢測模式指示（左下角）
- **線程安全** - 獨立預覽線程，不阻塞檢測主流程

**技術亮點**：
```python
# 使用 PIL + Tkinter 實現高效預覽
frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
image = Image.fromarray(frame_rgb)
photo = ImageTk.PhotoImage(image)
canvas.create_image(x, y, image=photo, anchor="center")
```

---

### 📊 多模式檢測引擎

| 模式 | 判定邏輯 | 適用場景 | 配置參數 |
|------|---------|---------|---------|
| **Auto** | 自動識別 | 不確定模型類型時 | `detection_mode: "auto"` |
| **Defect** | 檢測到缺陷 = NG<br>未檢測到 = OK | 訓練了缺陷類別 | `detection_mode: "defect"` |
| **Object** | 檢測到產品 = OK<br>未檢測到 = NG | 訓練了正常產品 | `detection_mode: "object"` |
| **Classification** | 檢測到 NG 類別 = NG<br>檢測到 OK 類別 = OK<br>未檢測到 = NG | 分類模型（自動識別） | 自動設定 |

**Classification 模式特別說明**（v1.1 新增）：

系統會自動檢測包含 OK/NG 類別的分類模型：

```python
# 範例：YiDa.pt 模型
class_names = {0: 'NG', 1: 'OK'}

# 判定邏輯
if detected_class == 'NG':
    judgment = "NG"  # 不良品
elif detected_class == 'OK':
    judgment = "OK"  # 良品
else:
    judgment = "NG"  # 未檢測到任何類別（異常/缺失）
```

**關鍵字識別清單**：
- **OK 類別**：`ok`, `good`, `pass`, `normal`, `良品`, `合格`
- **NG 類別**：`ng`, `bad`, `fail`, `defect`, `abnormal`, `不良`, `缺陷`

---

### ⚡ 延遲剔除控制

支援產線位移補償的智能剔除機制：

```
產品流程：
  取像位置 ──[距離 L]──→ 剔除位置
       │                     │
       ▼                     ▼
    [檢測]  ───[延遲 T]───→ [剔除]

延遲計算：
  T (ms) = (L / v) × 1000
  
  範例計算：
  • L = 0.5m, v = 1m/s → T = 500ms
  • L = 1.0m, v = 2m/s → T = 500ms
  • L = 0.3m, v = 0.6m/s → T = 500ms

實現機制：
  1. 檢測到 NG → 加入優先級隊列
  2. 後台線程持續監控隊列
  3. 到達預定時間 → 發送序列埠信號
  4. 統計已剔除數量
```

**支援的剔除方式**：
- ✅ 序列埠控制（Arduino/PLC）
- ✅ 氣動推桿（繼電器+電磁閥）
- ✅ 模擬模式（無硬體測試）
- 🔧 可擴展（Modbus TCP、EtherCAT 等）

---

### 🛡️ 企業級可靠性

#### 1. 相機自動重連
```python
# 背景監控線程
while running:
    if not camera.is_available():
        logger.warning("相機斷線，嘗試重連...")
        camera.close()
        time.sleep(1)
        if camera.open():
            logger.info("相機重連成功")
```

#### 2. 異常隔離機制
- 每個模組獨立錯誤捕獲
- 關鍵錯誤不影響其他組件
- 完整堆棧追蹤記錄

#### 3. 多層級日誌系統
```
logs/
└── ccd_20250102.log  # 按日期自動輪轉

日誌等級：
  DEBUG   → 詳細調試信息（僅文件）
  INFO    → 一般運行信息（控制台+文件）
  WARNING → 警告信息（黃色標記）
  ERROR   → 錯誤信息（紅色標記）
  CRITICAL → 致命錯誤（系統級）

範例輸出：
[10:30:45] INFO - 判定: NG | 類別: ['scratch'] | 置信度: 0.850 | 耗時: 45.6ms
[10:30:46] WARNING - 相機讀取失敗，嘗試重連
[10:30:47] INFO - 相機重連成功
```

#### 4. 數據持久化
```
rejection_output/
├── OK/                 # 良品圖片（可選）
├── NG/                 # 不良品圖片
│   └── 000123_NG_103045.jpg
└── logs/               # JSON 檢測記錄
    └── log_20250102_103050.json
```

**JSON 記錄格式**：
```json
{
  "timestamp": "2025-01-02T10:30:50",
  "statistics": {
    "total": 1000,
    "ok": 950,
    "ng": 50,
    "rejection": 50,
    "yield_rate": "95.00%"
  },
  "records": [
    {
      "product_id": 123,
      "timestamp": "2025-01-02 10:30:45.123",
      "judgment": "NG",
      "confidence": 0.850,
      "defect_classes": ["scratch", "stain"],
      "processing_time": 45.6,
      "image_path": "./rejection_output/NG/000123_NG_103045.jpg",
      "rejection_sent": true
    }
  ]
}
```

---

## 🏗️ 系統架構

### 整體架構圖

```
┌─────────────────────────────────────────────────────────────┐
│                         GUI Layer                            │
│  • MainWindow (Tkinter)                                      │
│  • 實時預覽 + 統計儀表板 + 參數調整                           │
└──────────────┬──────────────────────────────────────────────┘
               │
┌──────────────┴──────────────────────────────────────────────┐
│                      Engine Layer                            │
│  • InspectionEngine                                          │
│  • 工作流編排 + 延遲隊列管理 + 數據持久化                     │
└──┬───────────┬───────────┬────────────┬─────────────────────┘
   │           │           │            │
┌──┴──┐   ┌───┴───┐   ┌───┴────┐   ┌──┴─────┐
│Camera│   │Detector│  │Rejector│   │ Models │
│Mgr   │   │YOLOv8 │  │Serial  │   │ Data   │
└──────┘   └───────┘   └────────┘   └────────┘
   │           │           │            │
┌──┴───────────┴───────────┴────────────┴─────────────────────┐
│                     Utils Layer                              │
│  • ConfigManager   - JSON 配置管理                           │
│  • Logger          - 多層級日誌系統                          │
│  • ModelAnalyzer   - 智能模式識別引擎                        │
└─────────────────────────────────────────────────────────────┘
```

### 目錄結構

```
CCD_System1/
│
├── 📂 core/                    # 核心業務邏輯
│   ├── __init__.py
│   ├── camera.py              # 相機管理器
│   │   ├── CameraManager      # 自動重連、線程安全
│   │   └── 支援 USB/工業相機
│   │
│   ├── detector.py            # YOLOv8 檢測器
│   │   ├── 多模式支援         # Auto/Defect/Object/Classification
│   │   ├── 智能模式識別
│   │   └── 檢測結果後處理
│   │
│   ├── rejector.py            # 剔除控制器
│   │   ├── 延遲隊列管理
│   │   ├── 序列埠通訊
│   │   └── 模擬模式
│   │
│   └── engine.py              # 檢測引擎
│       ├── 工作流編排
│       ├── 統計數據管理
│       └── 數據持久化
│
├── 📂 models/                  # 數據模型定義
│   ├── __init__.py
│   └── data_models.py
│       ├── ProductRecord      # 產品檢測記錄
│       ├── Statistics         # 統計數據
│       ├── CameraConfig       # 相機配置
│       ├── DetectorConfig     # 檢測器配置
│       ├── RejectionConfig    # 剔除配置
│       └── SystemConfig       # 系統配置
│
├── 📂 utils/                   # 工具模組
│   ├── __init__.py
│   ├── config.py              # 配置管理器
│   │   ├── JSON 讀寫
│   │   ├── 配置驗證
│   │   └── 默認值處理
│   │
│   ├── logger.py              # 日誌系統
│   │   ├── 控制台輸出
│   │   ├── 文件輪轉
│   │   └── 多層級支援
│   │
│   └── model_analyzer.py      # 模型分析器
│       ├── 智能識別算法
│       ├── 置信度評分
│       └── 關鍵字匹配
│
├── 📂 gui/                     # 圖形介面
│   ├── __init__.py
│   └── main_window.py         # 主視窗
│       ├── 實時相機預覽       # PIL + Tkinter
│       ├── 檢測模式切換       # Auto/Defect/Object
│       ├── 參數調整滑桿       # 置信度閾值
│       ├── 統計數據儀表板     # 良率、計數
│       └── 系統日誌顯示       # 實時更新
│
├── 📄 main.py                  # 程式入口
├── 📄 config.json              # 系統配置文件
├── 📄 requirements.txt         # Python 依賴清單
│
├── 📄 start.bat                # 啟動腳本（Windows）
├── 📄 quick_install.bat        # 快速安裝腳本
│
├── 📄 check_model.py           # 模型快速檢查工具
├── 📄 diagnose_model.py        # 模型完整診斷工具
│
├── 📂 models/                  # 模型文件目錄（用戶放置）
│   ├── YiDa.pt                # 範例：分類模型
│   ├── yolov8n.pt             # 範例：通用檢測模型
│   └── your_model.pt          # 用戶自訓練模型
│
├── 📂 logs/                    # 系統日誌目錄（自動創建）
│   └── ccd_20250102.log
│
└── 📂 rejection_output/        # 檢測輸出目錄（自動創建）
    ├── OK/                    # 良品圖片
    ├── NG/                    # 不良品圖片
    └── logs/                  # JSON 檢測記錄
        └── log_20250102_103050.json
```

### 數據流程

```
                        [開始]
                          │
        ┌─────────────────┴─────────────────┐
        │   Camera.read()                   │
        │   • 取得原始幀                     │
        │   • 線程安全複製                   │
        │   • 自動重連檢查                   │
        └─────────────────┬─────────────────┘
                          │
        ┌─────────────────┴─────────────────┐
        │   Detector.detect()               │
        │   • 模式識別（auto）               │
        │   • YOLOv8 推理                   │
        │   • 判定邏輯處理                   │
        │   • 標註繪製                       │
        └─────────────────┬─────────────────┘
                          │
        ┌─────────────────┴─────────────────┐
        │   判定結果                         │
        │   ├─ OK → 統計+保存（可選）        │
        │   └─ NG → 統計+保存+剔除隊列       │
        └─────────────────┬─────────────────┘
                          │
        ┌─────────────────┴─────────────────┐
        │   Rejector.process()              │
        │   • 延遲計算                       │
        │   • 優先級隊列                     │
        │   • 序列埠觸發                     │
        └─────────────────┬─────────────────┘
                          │
        ┌─────────────────┴─────────────────┐
        │   GUI 更新                         │
        │   • 實時預覽更新                   │
        │   • 統計數據刷新                   │
        │   • 日誌輸出                       │
        └───────────────────────────────────┘
```

---

## 🔧 技術棧

### 核心技術

| 技術/框架 | 版本 | 用途 |
|----------|------|------|
| **Python** | 3.8-3.11 | 主要開發語言 |
| **YOLOv8** | Ultralytics 8.0+ | 物體檢測/分類 |
| **OpenCV** | 4.8+ | 圖像處理 |
| **Tkinter** | 內建 | GUI 框架 |
| **PIL/Pillow** | 10.0+ | 圖像顯示 |
| **PySerial** | 3.5+ | 序列埠通訊 |
| **NumPy** | 1.24+ | 數值計算 |

### 可選依賴

| 技術/框架 | 用途 |
|----------|------|
| **PyTorch** | GPU 加速（需 CUDA） |
| **Pandas** | 數據分析 |
| **OpenPyXL** | Excel 報表 |

### 系統需求

**最低配置**：
- CPU：Intel i5 4代+ / AMD Ryzen 3+
- 記憶體：8GB RAM
- 硬碟：20GB 可用空間
- 作業系統：Windows 10/11, Ubuntu 20.04+

**推薦配置**：
- CPU：Intel i7 8代+ / AMD Ryzen 5+
- 記憶體：16GB RAM
- GPU：NVIDIA GTX 1660+ (6GB VRAM)
- 硬碟：50GB SSD
- 作業系統：Windows 11, Ubuntu 22.04

---

## 🚀 快速開始

### 方法一：使用安裝腳本（推薦）

**Windows 用戶**：
```batch
# 1. 雙擊執行
quick_install.bat

# 2. 啟動系統
start.bat
```

### 方法二：手動安裝

#### Step 1: 環境準備

```bash
# 檢查 Python 版本（需要 3.8-3.11）
python --version

# 建議：創建虛擬環境
python -m venv venv

# 啟動虛擬環境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

#### Step 2: 安裝依賴

```bash
# 安裝所有依賴
pip install -r requirements.txt

# 或逐個安裝核心套件
pip install opencv-python==4.8.1.78
pip install ultralytics==8.0.196
pip install pillow==10.0.0
pip install pyserial==3.5
```

#### Step 3: 配置系統

```bash
# 1. 複製配置範本
cp config.json config_my.json

# 2. 編輯配置文件（請參考下方配置說明）
notepad config.json  # Windows
nano config.json     # Linux/Mac
```

#### Step 4: 測試相機

```bash
# 執行相機測試
python test_camera.py

# 輸出範例：
# [INFO] 找到 1 個可用相機
# [INFO] 相機 0: 已連接
# [INFO] 解析度: 1920x1080
```

#### Step 5: 檢查模型

```bash
# 快速檢查模型
python check_model.py

# 完整診斷（包含推理測試）
python diagnose_model.py

# 輸出範例：
# 模型路徑: ./models/YiDa.pt
# 類別數量: 2
# 類別列表: {0: 'NG', 1: 'OK'}
# 檢測模式: classification (置信度: 100.0%)
```

#### Step 6: 啟動系統

```bash
# 啟動 GUI 界面
python main.py
```

### 首次使用流程

1. **啟動應用** → 點擊 `start.bat` 或執行 `python main.py`
2. **檢查預覽** → 確認相機畫面正常顯示
3. **選擇模式** → Auto 模式會自動識別，也可手動切換
4. **調整閾值** → 使用滑桿調整置信度閾值（建議 0.3-0.7）
5. **開始檢測** → 點擊「開始檢測」按鈕
6. **觀察結果** → 查看統計數據和檢測日誌

---

## 📝 詳細安裝

### Windows 平台

#### 前置需求

1. **安裝 Python**
   ```
   下載：https://www.python.org/downloads/
   版本：Python 3.8-3.11
   注意：安裝時勾選「Add Python to PATH」
   ```

2. **（可選）安裝 CUDA** - 如需 GPU 加速
   ```
   下載：https://developer.nvidia.com/cuda-downloads
   版本：CUDA 11.8 或 12.1
   驗證：nvcc --version
   ```

#### 快速安裝

```batch
# 方法 1：使用安裝腳本（最簡單）
quick_install.bat

# 方法 2：手動安裝
pip install -r requirements.txt

# GPU 版本（需要 NVIDIA 顯卡）
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### Linux 平台

#### Ubuntu/Debian

```bash
# 1. 安裝系統依賴
sudo apt update
sudo apt install -y python3-pip python3-venv
sudo apt install -y libopencv-dev

# 2. 創建虛擬環境
python3 -m venv venv
source venv/bin/activate

# 3. 安裝 Python 依賴
pip install -r requirements.txt

# GPU 版本（需要 NVIDIA 顯卡 + CUDA）
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

#### CentOS/RHEL

```bash
# 1. 安裝系統依賴
sudo yum install -y python3-pip python3-devel
sudo yum install -y opencv opencv-devel

# 2. 其餘步驟同 Ubuntu
```

### 驗證安裝

```bash
# 檢查所有依賴是否正確安裝
python -c "
import cv2
import numpy as np
from ultralytics import YOLO
from PIL import Image
import serial
print('所有依賴安裝成功！')
"
```

---

## 📖 使用指南

### GUI 界面說明

```
┌────────────────────────────────────────────────────────────┐
│  CCD 視覺檢測系統 v1.1                          [_][□][×]  │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────────────────────────────────────────┐    │
│  │                                                  │    │
│  │                                                  │    │
│  │              相機實時預覽區域                     │    │
│  │           （顯示檢測標註和判定結果）              │    │
│  │                                                  │    │
│  │                                                  │    │
│  └──────────────────────────────────────────────────┘    │
│                                                            │
│  ┌─ 檢測控制 ──────────────────────────────────────┐      │
│  │ 模式: ● Auto  ○ Defect  ○ Object               │      │
│  │ 置信度: [========|=====] 0.50                   │      │
│  │ [ 開始檢測 ] [ 停止檢測 ] [ 單次檢測 ]         │      │
│  └─────────────────────────────────────────────────┘      │
│                                                            │
│  ┌─ 統計數據 ──────────────────────────────────────┐      │
│  │ 總數: 1000  OK: 950  NG: 50  良率: 95.00%      │      │
│  │ 已剔除: 50  處理速度: 22 FPS                    │      │
│  └─────────────────────────────────────────────────┘      │
│                                                            │
│  ┌─ 系統日誌 ──────────────────────────────────────┐      │
│  │ [10:30:45] INFO - 判定: NG | 類別: scratch      │      │
│  │ [10:30:46] INFO - 剔除信號已發送                │      │
│  │ [10:30:47] INFO - 判定: OK | 處理耗時: 42.3ms   │      │
│  └─────────────────────────────────────────────────┘      │
│                                                            │
│  [ 清除統計 ] [ 保存記錄 ] [ 打開輸出目錄 ] [ 設定 ]      │
└────────────────────────────────────────────────────────────┘
```

### 檢測模式選擇指南

#### 何時使用 Auto 模式？

**推薦場景**：
- ✅ 首次使用系統，不確定模型類型
- ✅ 使用第三方訓練的模型
- ✅ 模型類別命名清晰（如：scratch, ok, ng）

**操作步驟**：
1. 選擇「Auto」單選按鈕
2. 點擊「初始化系統」
3. 查看日誌輸出的識別結果
4. 確認置信度分數 > 60%

#### 何時使用 Defect 模式？

**推薦場景**：
- ✅ 模型訓練了缺陷類別（scratch, crack, stain 等）
- ✅ 檢測邏輯：有缺陷 = NG，無缺陷 = OK

**配置範例**：
```json
{
  "detection_mode": "defect",
  "confidence_threshold": 0.5
}
```

#### 何時使用 Object 模式？

**推薦場景**：
- ✅ 模型訓練了正常產品類別
- ✅ 檢測邏輯：有產品 = OK，無產品 = NG
- ✅ 應用：零件缺失檢測、計數驗證

**配置範例**：
```json
{
  "detection_mode": "object",
  "confidence_threshold": 0.6
}
```

### 參數調整建議

#### 置信度閾值

| 場景 | 建議值 | 說明 |
|-----|-------|------|
| **嚴格檢測** | 0.3-0.4 | 降低漏檢，可能增加誤檢 |
| **平衡檢測** | 0.5-0.6 | 默認推薦，平衡準確率和召回率 |
| **寬鬆檢測** | 0.7-0.8 | 減少誤檢，可能增加漏檢 |

**調整方法**：
1. 準備測試樣品（OK 和 NG 各 20 張）
2. 從 0.5 開始測試
3. 觀察誤檢/漏檢情況
4. 逐步調整（每次 ±0.1）
5. 記錄最佳閾值

#### 剔除延遲

```
計算公式：
延遲時間 (ms) = 距離 (m) / 速度 (m/s) × 1000

範例：
• 產線速度: 1 m/s
• 檢測點到剔除點距離: 0.5 m
• 計算: 0.5 / 1 × 1000 = 500 ms
```

**注意事項**：
- ⚠️ 延遲時間需實際測量和驗證
- ⚠️ 考慮機械響應時間（通常 50-100ms）
- ⚠️ 建議預留 10-20% 安全餘量

---

## ⚙️ 配置說明

### 配置文件結構

`config.json` 是系統的核心配置文件：

```json
{
  // ==================== 相機配置 ====================
  "camera_index": 0,           // 相機索引（0=第一個相機）
  "camera_width": 1920,        // 解析度寬度
  "camera_height": 1080,       // 解析度高度
  
  // ==================== 檢測器配置 ==================
  "model_path": "./models/YiDa.pt",  // 模型路徑
  "confidence_threshold": 0.5,       // 置信度閾值（0.0-1.0）
  "detection_mode": "auto",          // 檢測模式：auto/defect/object
  "ng_classes": [],                  // NG類別清單（defect模式使用）
  
  // ==================== 剔除器配置 ==================
  "rejection_enabled": false,   // 是否啟用剔除功能
  "rejection_delay_ms": 500,    // 剔除延遲（毫秒）
  "rejection_pulse_ms": 100,    // 脈衝持續時間（毫秒）
  "serial_port": "COM3",        // 序列埠（Windows: COM3, Linux: /dev/ttyUSB0）
  "serial_baudrate": 9600,      // 波特率
  
  // ==================== 輸出配置 ====================
  "save_ok_images": false,      // 是否保存 OK 圖片
  "save_ng_images": true,       // 是否保存 NG 圖片
  "output_dir": "./rejection_output"  // 輸出目錄
}
```

### 配置範例

#### 範例 1：Defect 檢測模式

```json
{
  "camera_index": 0,
  "camera_width": 1920,
  "camera_height": 1080,
  
  "model_path": "./models/defect_model.pt",
  "confidence_threshold": 0.5,
  "detection_mode": "defect",
  "ng_classes": ["scratch", "crack", "stain"],  // 指定缺陷類別
  
  "rejection_enabled": true,
  "rejection_delay_ms": 500,
  "rejection_pulse_ms": 100,
  "serial_port": "COM3",
  "serial_baudrate": 9600,
  
  "save_ok_images": false,
  "save_ng_images": true,
  "output_dir": "./rejection_output"
}
```

#### 範例 2：Object 檢測模式

```json
{
  "camera_index": 0,
  "camera_width": 1280,
  "camera_height": 720,
  
  "model_path": "./models/product_model.pt",
  "confidence_threshold": 0.6,
  "detection_mode": "object",
  "ng_classes": [],  // object 模式不需要指定
  
  "rejection_enabled": true,
  "rejection_delay_ms": 300,
  "rejection_pulse_ms": 80,
  "serial_port": "/dev/ttyUSB0",  // Linux 系統
  "serial_baudrate": 115200,
  
  "save_ok_images": true,  // 保存良品用於品質監控
  "save_ng_images": true,
  "output_dir": "./inspection_output"
}
```

#### 範例 3：Auto 模式（推薦新手）

```json
{
  "camera_index": 0,
  "camera_width": 1920,
  "camera_height": 1080,
  
  "model_path": "./models/YiDa.pt",
  "confidence_threshold": 0.5,
  "detection_mode": "auto",  // 系統自動識別
  "ng_classes": [],
  
  "rejection_enabled": false,  // 先測試，不啟用剔除
  "rejection_delay_ms": 0,
  "rejection_pulse_ms": 100,
  "serial_port": "",
  "serial_baudrate": 9600,
  
  "save_ok_images": false,
  "save_ng_images": true,
  "output_dir": "./rejection_output"
}
```

### 配置參數詳解

#### 相機參數

| 參數 | 類型 | 說明 | 默認值 | 範圍 |
|-----|------|------|--------|------|
| `camera_index` | int | 相機索引號 | 0 | 0-9 |
| `camera_width` | int | 解析度寬度 | 1920 | 640-3840 |
| `camera_height` | int | 解析度高度 | 1080 | 480-2160 |

**Tips**：
- USB 相機通常為索引 0
- 多個相機時依序為 0, 1, 2...
- 解析度需相機支援，建議使用標準解析度（720p, 1080p, 4K）

#### 檢測器參數

| 參數 | 類型 | 說明 | 默認值 | 可選值 |
|-----|------|------|--------|--------|
| `model_path` | string | 模型文件路徑 | - | 任何 .pt 文件 |
| `confidence_threshold` | float | 置信度閾值 | 0.5 | 0.0-1.0 |
| `detection_mode` | string | 檢測模式 | "auto" | auto/defect/object |
| `ng_classes` | list | NG 類別清單 | [] | 類別名稱列表 |

**Tips**：
- 模型路徑支援相對路徑和絕對路徑
- Auto 模式會忽略 `ng_classes` 參數
- Defect 模式必須指定 `ng_classes`

#### 剔除器參數

| 參數 | 類型 | 說明 | 默認值 | 範圍 |
|-----|------|------|--------|------|
| `rejection_enabled` | boolean | 是否啟用剔除 | false | true/false |
| `rejection_delay_ms` | int | 延遲時間（毫秒） | 500 | 0-10000 |
| `rejection_pulse_ms` | int | 脈衝持續時間 | 100 | 50-1000 |
| `serial_port` | string | 序列埠名稱 | "COM3" | COM1-99/ttyUSB0-9 |
| `serial_baudrate` | int | 波特率 | 9600 | 9600/115200 等 |

**Tips**：
- 測試階段建議設為 `false`
- 延遲時間需根據產線實際情況計算
- 脈衝時間取決於硬體響應速度

---

## 🔍 檢測模式詳解

### Auto 模式（智能識別）

#### 工作原理

Auto 模式使用多維度分析算法，自動判定最適合的檢測模式：

```python
# 分析維度和權重
維度 1：文件名關鍵字（權重 30%）
  • 包含 defect/scratch/crack → 傾向 Defect 模式
  • 包含 yolov8/coco/detect → 傾向 Object 模式

維度 2：類別名稱語義（權重 50%）
  • 缺陷類別：scratch, crack, stain, spot → +80 分
  • 產品類別：product, item, object → -80 分
  • OK/NG 類別：自動識別為 Classification 模式

維度 3：類別數量（權重 20%）
  • ≤5 個類別 → 傾向 Defect 模式（+40 分）
  • ≥80 個類別 → 傾向 Object 模式（-50 分）

最終判定：
  • 綜合評分 > 0 → Defect 模式
  • 綜合評分 < 0 → Object 模式
  • 檢測到 OK/NG 類別 → Classification 模式
```

#### 使用範例

```python
# config.json
{
  "detection_mode": "auto",
  "model_path": "./models/scratch_detector.pt"
}

# 系統輸出
[INFO] 檢測模式設為 'auto'，開始自動識別...
[INFO] 文件名分析: scratch_detector.pt → Defect (+30)
[INFO] 類別分析: ['scratch', 'crack'] → Defect (+80)
[INFO] 類別數量: 2 → Defect (+40)
[INFO] 綜合評分: +150
[INFO] 自動識別完成: DEFECT (置信度: 95.0%)
[INFO] 判定邏輯: 檢測到缺陷 = NG，未檢測到 = OK
```

#### 適用場景

| 場景 | 適用性 | 原因 |
|-----|--------|------|
| 新手使用 | ⭐⭐⭐⭐⭐ | 無需理解底層邏輯 |
| 第三方模型 | ⭐⭐⭐⭐⭐ | 自動適配不同模型 |
| 快速部署 | ⭐⭐⭐⭐ | 減少配置時間 |
| 多模型切換 | ⭐⭐⭐⭐ | 動態適應不同模型 |
| 複雜邏輯 | ⭐⭐⭐ | 可能需要手動調整 |

---

### Defect 模式（缺陷檢測）

#### 判定邏輯

```python
if 檢測到任何缺陷類別:
    判定 = "NG"  # 不良品
else:
    判定 = "OK"  # 良品
```

#### 配置方式

```json
{
  "detection_mode": "defect",
  "ng_classes": ["scratch", "crack", "stain", "spot"],
  "confidence_threshold": 0.5
}
```

**參數說明**：
- `ng_classes`: 必須指定，列出所有缺陷類別名稱
- 類別名稱必須與模型訓練時的名稱完全一致
- 大小寫敏感

#### 典型應用

**表面缺陷檢測**：
```
訓練數據：
  • scratch（劃痕）：500 張
  • crack（裂紋）：300 張
  • stain（污漬）：200 張

檢測邏輯：
  • 檢測到任一缺陷 → NG
  • 未檢測到缺陷 → OK
```

**包裝檢驗**：
```
訓練數據：
  • label_error（標籤錯誤）：400 張
  • seal_defect（封口不良）：350 張
  • foreign_matter（異物）：200 張

檢測邏輯：
  • 檢測到任一問題 → NG
  • 包裝完好 → OK
```

#### 優化建議

**1. 類別平衡**
```python
# 檢查數據集平衡性
defect_counts = {
    "scratch": 500,
    "crack": 300,
    "stain": 200
}

# 建議：最小類別數量 ≥ 最大類別數量 × 0.3
min_ratio = min(defect_counts.values()) / max(defect_counts.values())
if min_ratio < 0.3:
    print("警告：數據不平衡，建議增強少數類別")
```

**2. 閾值調整**
```python
# 測試不同閾值的效果
thresholds = [0.3, 0.4, 0.5, 0.6, 0.7]
for threshold in thresholds:
    # 執行測試
    false_positive_rate = test_false_positives(threshold)
    false_negative_rate = test_false_negatives(threshold)
    
    print(f"閾值 {threshold}: FP={false_positive_rate}, FN={false_negative_rate}")
```

---

### Object 模式（物體檢測）

#### 判定邏輯

```python
if 檢測到產品:
    判定 = "OK"  # 良品（產品存在）
else:
    判定 = "NG"  # 不良品（產品缺失/錯誤）
```

#### 配置方式

```json
{
  "detection_mode": "object",
  "confidence_threshold": 0.6
}
```

**注意**：
- Object 模式不需要指定 `ng_classes`
- 只要檢測到任何類別，就判定為 OK
- 適合檢測「應該存在的物體」

#### 典型應用

**組裝檢測**：
```
訓練數據：
  • screw（螺絲）
  • gasket（墊片）
  • connector（連接器）

檢測邏輯：
  • 檢測到所有零件 → OK
  • 缺少任何零件 → NG
```

**計數驗證**：
```
訓練數據：
  • pill（藥片）

檢測邏輯：
  • 檢測到 N 個物體
  • 如果 N == 預期數量 → OK
  • 否則 → NG
```

#### 高級應用

**多物體計數**：
```python
# 自定義判定邏輯
def custom_judgment(detections):
    expected_count = 10
    actual_count = len(detections)
    
    if actual_count == expected_count:
        return "OK"
    elif actual_count < expected_count:
        return "NG"  # 缺少
    else:
        return "NG"  # 多餘
```

**位置驗證**：
```python
# 檢查物體位置
def check_position(detections):
    for detection in detections:
        x, y = detection.center
        
        # 定義合格區域
        if not (100 < x < 900 and 100 < y < 700):
            return "NG"  # 位置偏移
    
    return "OK"
```

---

### Classification 模式（分類模型）

#### 自動識別條件

系統會自動檢測以下情況：
```python
# OK 類別關鍵字
ok_keywords = ["ok", "good", "pass", "normal", "良品", "合格"]

# NG 類別關鍵字
ng_keywords = ["ng", "bad", "fail", "defect", "abnormal", "不良", "缺陷"]

# 自動識別邏輯
if 類別名稱包含任一 OK 關鍵字 AND 類別名稱包含任一 NG 關鍵字:
    模式 = "classification"
```

#### 判定邏輯

```python
if detected_class in NG_CLASSES:
    judgment = "NG"  # 不良品
elif detected_class in OK_CLASSES:
    judgment = "OK"  # 良品
else:
    judgment = "NG"  # 異常（未檢測到任何類別）
```

#### 典型應用

**範例：YiDa 分類模型**
```python
# 模型類別
class_names = {0: 'NG', 1: 'OK'}

# 系統輸出
[INFO] 檢測到分類模型（OK/NG 類別）
[INFO] OK 類別: ['OK']
[INFO] NG 類別: ['NG']
[INFO] 判定邏輯:
[INFO]   ✓ 檢測到 NG 類別 → NG（不良品）
[INFO]   ✓ 檢測到 OK 類別 → OK（良品）
[INFO]   ✓ 沒檢測到任何類別 → NG（異常/缺失）
```

**應用場景**：
- 二分類問題（OK/NG、良品/不良品）
- 多等級分類（A級/B級/C級/D級）
- 合格性判定

---

## 📚 API 文檔

### 核心類和方法

#### 1. InspectionEngine（檢測引擎）

```python
class InspectionEngine:
    """
    檢測與剔除引擎
    
    主要功能：
    - 初始化系統組件
    - 處理檢測流程
    - 管理統計數據
    - 保存檢測記錄
    """
    
    def __init__(self, config: SystemConfig):
        """
        初始化引擎
        
        Args:
            config: 系統配置對象
        """
        pass
    
    def initialize(self) -> bool:
        """
        初始化系統
        
        Returns:
            bool: 初始化是否成功
        """
        pass
    
    def process_single(self) -> Optional[ProductRecord]:
        """
        處理單個產品
        
        Returns:
            ProductRecord: 檢測記錄，失敗返回 None
        """
        pass
    
    def start_continuous(self):
        """
        啟動連續檢測
        
        開啟背景線程持續檢測
        """
        pass
    
    def stop_continuous(self):
        """
        停止連續檢測
        """
        pass
    
    def get_statistics(self) -> Statistics:
        """
        獲取統計數據
        
        Returns:
            Statistics: 統計數據對象
        """
        pass
    
    def save_detection_log(self, filename: Optional[str] = None) -> str:
        """
        保存檢測記錄到 JSON 文件
        
        Args:
            filename: 文件名（可選，默認使用時間戳）
        
        Returns:
            str: 保存的文件路徑
        """
        pass
    
    def cleanup(self):
        """
        清理資源
        
        釋放相機、關閉序列埠等
        """
        pass
```

**使用範例**：
```python
from utils.config import ConfigManager
from core.engine import InspectionEngine

# 載入配置
config = ConfigManager().load()

# 創建引擎
engine = InspectionEngine(config)

# 初始化
if engine.initialize():
    # 單次檢測
    record = engine.process_single()
    if record:
        print(f"判定: {record.judgment}")
        print(f"置信度: {record.confidence:.2f}")
    
    # 或啟動連續檢測
    engine.start_continuous()
    
    # ... 運行一段時間後
    
    engine.stop_continuous()
    
    # 保存記錄
    log_path = engine.save_detection_log()
    print(f"記錄已保存: {log_path}")
    
    # 清理
    engine.cleanup()
```

---

#### 2. YOLODetector（檢測器）

```python
class YOLODetector:
    """
    YOLOv8 檢測器
    
    支援功能：
    - 多模式檢測（Auto/Defect/Object/Classification）
    - 智能模式識別
    - 檢測結果後處理
    """
    
    def __init__(self, config: DetectorConfig):
        """
        初始化檢測器
        
        Args:
            config: 檢測器配置對象
        """
        pass
    
    def load_model(self, model_path: Optional[str] = None) -> bool:
        """
        載入模型
        
        Args:
            model_path: 模型路徑（可選）
        
        Returns:
            bool: 載入是否成功
        """
        pass
    
    def detect(self, image: np.ndarray) -> Tuple[str, float, List[str], np.ndarray]:
        """
        執行檢測
        
        Args:
            image: 輸入圖像（BGR 格式）
        
        Returns:
            judgment: 判定結果（"OK" 或 "NG"）
            confidence: 置信度（0.0-1.0）
            classes: 檢測到的類別列表
            annotated_image: 標註後的圖像
        """
        pass
    
    def get_mode_info(self) -> Tuple[str, float]:
        """
        獲取當前模式信息
        
        Returns:
            mode: 檢測模式
            confidence: 模式置信度
        """
        pass
    
    def set_mode(self, mode: str):
        """
        手動設定檢測模式
        
        Args:
            mode: 模式名稱（"defect" 或 "object"）
        """
        pass
```

**使用範例**：
```python
from core.detector import YOLODetector
from models.data_models import DetectorConfig
import cv2

# 創建配置
config = DetectorConfig(
    model_path="./models/defect_model.pt",
    confidence_threshold=0.5,
    detection_mode="auto"
)

# 創建檢測器
detector = YOLODetector(config)
detector.load_model()

# 讀取圖像
image = cv2.imread("test.jpg")

# 執行檢測
judgment, confidence, classes, annotated = detector.detect(image)

print(f"判定: {judgment}")
print(f"置信度: {confidence:.2f}")
print(f"檢測類別: {classes}")

# 顯示標註圖像
cv2.imshow("Result", annotated)
cv2.waitKey(0)

# 獲取模式信息
mode, mode_confidence = detector.get_mode_info()
print(f"檢測模式: {mode} (置信度: {mode_confidence:.1f}%)")
```

---

#### 3. CameraManager（相機管理器）

```python
class CameraManager:
    """
    相機管理器
    
    支援功能：
    - 自動重連
    - 線程安全
    - 參數設定
    """
    
    def __init__(self, config: CameraConfig):
        """
        初始化相機管理器
        
        Args:
            config: 相機配置對象
        """
        pass
    
    def open(self) -> bool:
        """
        打開相機
        
        Returns:
            bool: 是否成功
        """
        pass
    
    def close(self):
        """
        關閉相機
        """
        pass
    
    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        讀取畫面
        
        Returns:
            ret: 是否成功
            frame: 圖像數據（BGR 格式）
        """
        pass
    
    def is_available(self) -> bool:
        """
        檢查相機是否可用
        
        Returns:
            bool: 是否可用
        """
        pass
    
    def enable_auto_reconnect(self):
        """
        啟用自動重連
        
        背景線程會自動檢測並重連相機
        """
        pass
    
    def disable_auto_reconnect(self):
        """
        停用自動重連
        """
        pass
    
    def get_properties(self) -> dict:
        """
        獲取相機屬性
        
        Returns:
            dict: 相機屬性字典
        """
        pass
```

**使用範例**：
```python
from core.camera import CameraManager
from models.data_models import CameraConfig

# 創建配置
config = CameraConfig(
    index=0,
    width=1920,
    height=1080
)

# 創建相機管理器
camera = CameraManager(config)

# 打開相機
if camera.open():
    # 啟用自動重連
    camera.enable_auto_reconnect()
    
    # 讀取畫面
    ret, frame = camera.read()
    if ret:
        print(f"畫面大小: {frame.shape}")
    
    # 獲取屬性
    props = camera.get_properties()
    print(f"FPS: {props.get('fps')}")
    
    # 關閉相機
    camera.close()
```

---

#### 4. RejectionController（剔除控制器）

```python
class RejectionController:
    """
    剔除控制器
    
    支援功能：
    - 延遲隊列管理
    - 序列埠控制
    - 模擬模式
    """
    
    def __init__(self, config: RejectionConfig):
        """
        初始化剔除控制器
        
        Args:
            config: 剔除配置對象
        """
        pass
    
    def connect(self) -> bool:
        """
        連接剔除裝置
        
        Returns:
            bool: 是否成功
        """
        pass
    
    def disconnect(self):
        """
        斷開連接
        """
        pass
    
    def schedule_rejection(self, product_id: int):
        """
        排程剔除
        
        Args:
            product_id: 產品 ID
        """
        pass
    
    def trigger_rejection(self):
        """
        立即觸發剔除
        """
        pass
    
    def start_processing(self):
        """
        啟動後台處理線程
        """
        pass
    
    def stop_processing(self):
        """
        停止後台處理
        """
        pass
```

**使用範例**：
```python
from core.rejector import RejectionController
from models.data_models import RejectionConfig

# 創建配置
config = RejectionConfig(
    enabled=True,
    delay_ms=500,
    pulse_ms=100,
    serial_port="COM3",
    baudrate=9600
)

# 創建控制器
rejector = RejectionController(config)

# 連接裝置
if rejector.connect():
    # 啟動處理線程
    rejector.start_processing()
    
    # 排程剔除
    rejector.schedule_rejection(product_id=123)
    
    # ... 運行一段時間後
    
    # 停止處理
    rejector.stop_processing()
    
    # 斷開連接
    rejector.disconnect()
```

---

### 數據模型

#### ProductRecord（產品記錄）

```python
@dataclass
class ProductRecord:
    """產品檢測記錄"""
    product_id: int              # 產品 ID
    timestamp: str               # 時間戳
    judgment: str                # 判定結果（OK/NG）
    confidence: float            # 置信度
    defect_classes: List[str]    # 檢測類別列表
    processing_time: float       # 處理時間（ms）
    image_path: Optional[str]    # 圖像路徑
    rejection_sent: bool         # 是否已發送剔除信號
```

#### Statistics（統計數據）

```python
@dataclass
class Statistics:
    """統計數據"""
    total_count: int       # 總數
    ok_count: int          # OK 數量
    ng_count: int          # NG 數量
    rejection_count: int   # 剔除數量
    
    @property
    def yield_rate(self) -> float:
        """良率（%）"""
        return (self.ok_count / self.total_count) * 100 if self.total_count > 0 else 0.0
```

---

## 🔌 硬體整合

### 支援的相機類型

#### 1. USB 相機（推薦新手）

**優勢**：
- ✅ 即插即用，無需額外驅動
- ✅ 價格便宜（NT$ 500-3000）
- ✅ 配置簡單

**配置範例**：
```json
{
  "camera_index": 0,
  "camera_width": 1920,
  "camera_height": 1080
}
```

**測試方法**：
```bash
python test_camera.py
```

---

#### 2. 工業相機

##### Basler 相機

**安裝驅動**：
```bash
# 下載 Pylon SDK
https://www.baslerweb.com/en/downloads/software-downloads/

# 安裝 Python 套件
pip install pypylon
```

**代碼範例**：
```python
from pypylon import pylon

# 創建相機實例
camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
camera.Open()

# 設定參數
camera.ExposureTime.SetValue(10000)  # 曝光時間 10ms
camera.Gain.SetValue(1.0)            # 增益

# 開始取像
camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)

while camera.IsGrabbing():
    grab_result = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
    if grab_result.GrabSucceeded():
        image = grab_result.Array
        # 處理圖像...
    grab_result.Release()

camera.StopGrabbing()
camera.Close()
```

---

##### Hikvision 相機

**安裝驅動**：
```bash
# 下載 MVS SDK
https://www.hikvision.com/en/support/download/software/

# 安裝 Python 套件
pip install MvImport
```

**代碼範例**：
```python
from MvCameraControl_class import *

# 初始化
MvCamera = MvCamera()
deviceList = MV_CC_DEVICE_INFO_LIST()
MvCamera.MV_CC_EnumDevices(MV_GIGE_DEVICE, deviceList)

# 打開相機
MvCamera.MV_CC_CreateHandle(deviceList.pDeviceInfo[0])
MvCamera.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)

# 開始取像
MvCamera.MV_CC_StartGrabbing()

# 獲取圖像
data_buf = (c_ubyte * (width * height))()
frame_info = MV_FRAME_OUT_INFO_EX()
MvCamera.MV_CC_GetOneFrameTimeout(byref(data_buf), width * height, frame_info, 1000)

# 關閉相機
MvCamera.MV_CC_StopGrabbing()
MvCamera.MV_CC_CloseDevice()
```

---

### 剔除裝置整合

#### 1. 序列埠控制（Arduino）

**硬體連接**：
```
Arduino → 繼電器模組 → 電磁閥

接線：
  Arduino Pin 13 → 繼電器 IN
  Arduino 5V → 繼電器 VCC
  Arduino GND → 繼電器 GND
```

**Arduino 程式碼**：
```cpp
// Arduino 端代碼
const int RELAY_PIN = 13;

void setup() {
  Serial.begin(9600);
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);
}

void loop() {
  if (Serial.available() > 0) {
    char command = Serial.read();
    
    if (command == '1') {
      // 觸發剔除
      digitalWrite(RELAY_PIN, HIGH);
      delay(100);  // 脈衝持續時間
      digitalWrite(RELAY_PIN, LOW);
    }
  }
}
```

**Python 端代碼**：
```python
import serial
import time

# 打開序列埠
ser = serial.Serial('COM3', 9600, timeout=1)
time.sleep(2)  # 等待 Arduino 初始化

# 發送剔除信號
def trigger_rejection():
    ser.write(b'1')
    print("剔除信號已發送")

# 使用
trigger_rejection()

# 關閉序列埠
ser.close()
```

---

#### 2. Modbus TCP 控制（PLC）

**安裝依賴**：
```bash
pip install pymodbus
```

**代碼範例**：
```python
from pymodbus.client.sync import ModbusTcpClient

# 連接 PLC
client = ModbusTcpClient('192.168.1.100', port=502)
client.connect()

# 寫入剔除信號（寫入線圈）
def trigger_rejection():
    # 寫入地址 0 的線圈為 True
    client.write_coil(0, True)
    time.sleep(0.1)
    client.write_coil(0, False)

# 讀取狀態
status = client.read_coils(0, 1)
print(f"剔除狀態: {status.bits[0]}")

# 關閉連接
client.close()
```

---

#### 3. 數位 I/O 卡

**硬體選擇**：
- Advantech USB-4761（USB 數位 I/O）
- MOXA ioLogik E1210（Ethernet I/O）

**代碼範例**（以 Advantech 為例）：
```python
# 安裝驅動和 SDK
# 下載：https://www.advantech.com/

from Automation.BDaq import *

# 初始化
device = InstantDoCtrl()
device.SelectedDevice = DeviceInformation("USB-4761")

# 設定輸出
port_index = 0
bit_index = 0

# 觸發剔除
device.WriteAny(port_index, bit_index, 1)  # 輸出 HIGH
time.sleep(0.1)
device.WriteAny(port_index, bit_index, 0)  # 輸出 LOW

# 關閉
device.Dispose()
```

---

### 照明系統建議

#### LED 環形光源

**推薦配置**：
- 功率：15-30W
- 色溫：6000-6500K（白光）
- 安裝位置：距離產品 20-30cm
- 角度：30-45° 斜向照射

**優勢**：
- 均勻照明，減少陰影
- 突出表面紋理
- 適合缺陷檢測

---

#### 背光光源

**推薦配置**：
- LED 平板光源
- 尺寸：根據產品大小選擇
- 亮度：可調（建議 5000-10000 Lux）

**優勢**：
- 產品輪廓清晰
- 適合透明/半透明物體
- 適合尺寸測量

---

## 🔧 故障排除

### 常見問題

#### 1. 相機無法打開

**錯誤訊息**：
```
[ERROR] 無法打開相機
[ERROR] 相機初始化失敗
```

**可能原因和解決方案**：

| 原因 | 解決方案 |
|-----|---------|
| 相機未連接 | 檢查 USB 連接，確認相機電源 |
| 相機索引錯誤 | 執行 `test_camera.py` 找到正確索引 |
| 相機被占用 | 關閉其他使用相機的程式 |
| 驅動未安裝 | 安裝相機驅動（工業相機） |
| 權限不足 | Linux 系統添加用戶到 video 組 |

**診斷命令**：
```bash
# Windows - 檢查設備管理器
devmgmt.msc

# Linux - 檢查相機設備
ls /dev/video*
v4l2-ctl --list-devices

# 測試相機
python test_camera.py
```

---

#### 2. 模型載入失敗

**錯誤訊息**：
```
[ERROR] 模型載入失敗
[ERROR] 找不到模型文件
```

**解決方案**：

**步驟 1：檢查文件路徑**
```bash
# 確認模型文件存在
ls ./models/YiDa.pt

# Windows
dir models\YiDa.pt
```

**步驟 2：檢查文件完整性**
```python
import os

model_path = "./models/YiDa.pt"
if os.path.exists(model_path):
    size = os.path.getsize(model_path)
    print(f"模型大小: {size / 1024 / 1024:.2f} MB")
    
    # YOLOv8 模型通常 > 5MB
    if size < 1000000:
        print("警告：模型文件太小，可能損壞")
```

**步驟 3：測試模型**
```bash
python check_model.py
```

---

#### 3. 檢測速度慢

**症狀**：
- 處理時間 > 200ms
- FPS < 5

**優化方案**：

**1. 降低輸入解析度**
```json
{
  "camera_width": 1280,  // 從 1920 降至 1280
  "camera_height": 720   // 從 1080 降至 720
}
```

**2. 使用 GPU 加速**
```bash
# 安裝 PyTorch GPU 版本
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# 驗證 GPU 可用
python -c "import torch; print(torch.cuda.is_available())"
```

**3. 選擇更輕量的模型**
```python
# 使用 YOLOv8n（最快）替代 YOLOv8x（最準）
# nano < small < medium < large < xlarge
model_path = "./models/yolov8n.pt"  # 最快
```

**4. 調整推理參數**
```python
# 在 detector.py 中
results = self.model.predict(
    image,
    conf=self.config.confidence_threshold,
    imgsz=640,  # 固定輸入大小
    half=True,  # 使用 FP16（需要 GPU）
    verbose=False
)
```

---

#### 4. 誤檢率高

**症狀**：
- 良品被誤判為 NG
- 良率異常偏低

**解決方案**：

**1. 調高置信度閾值**
```json
{
  "confidence_threshold": 0.7  // 從 0.5 提高到 0.7
}
```

**2. 檢查照明條件**
```
- 光源是否均勻
- 是否有反光
- 亮度是否穩定
```

**3. 重新標註數據**
```
- 檢查標註準確性
- 增加訓練樣本
- 使用數據增強
```

**4. 分析誤檢樣本**
```python
# 收集誤檢圖像
false_positives = []

# 分析共同特徵
# - 特定角度？
# - 特定照明？
# - 特定顏色？

# 針對性改進
```

---

#### 5. 漏檢率高

**症狀**：
- NG 產品未被檢出
- 漏檢率 > 5%

**解決方案**：

**1. 降低置信度閾值**
```json
{
  "confidence_threshold": 0.3  // 從 0.5 降低到 0.3
}
```

**2. 增加訓練樣本**
```
- 收集更多缺陷樣本
- 特別是漏檢的類型
- 建議每類 > 500 張
```

**3. 檢查模型訓練**
```
- 確認訓練收斂
- 檢查驗證集表現
- 考慮重新訓練
```

---

#### 6. 剔除不準確

**症狀**：
- 剔除位置偏移
- 剔除延遲不準

**解決方案**：

**1. 重新計算延遲時間**
```python
# 實際測量產線參數
distance = 0.5  # 米（實測）
speed = 1.0     # 米/秒（實測）
delay = (distance / speed) * 1000  # 毫秒

# 考慮機械響應時間
response_time = 50  # 毫秒
total_delay = delay - response_time

print(f"建議延遲: {total_delay} ms")
```

**2. 調整配置**
```json
{
  "rejection_delay_ms": 450,  // 根據實測調整
  "rejection_pulse_ms": 100
}
```

**3. 標記測試**
```python
# 在產品上標記序號
# 驗證剔除對應關係
# 多次測試取平均值
```

---

#### 7. 序列埠連接失敗

**錯誤訊息**：
```
[ERROR] 無法打開序列埠
[ERROR] 序列埠被占用
```

**解決方案**：

**Windows**：
```bash
# 1. 檢查設備管理器
# 2. 確認 COM 埠號
# 3. 更新驅動

# 查看可用埠
mode
```

**Linux**：
```bash
# 1. 添加用戶到 dialout 組
sudo usermod -a -G dialout $USER

# 2. 重新登入
logout

# 3. 檢查權限
ls -l /dev/ttyUSB0

# 4. 測試連接
python -m serial.tools.miniterm /dev/ttyUSB0 9600
```

---

#### 8. 記憶體洩漏

**症狀**：
- 長時間運行後記憶體持續增長
- 系統變慢或崩潰

**診斷方法**：
```python
import psutil
import os

def check_memory():
    process = psutil.Process(os.getpid())
    mem = process.memory_info().rss / 1024 / 1024  # MB
    print(f"記憶體使用: {mem:.2f} MB")

# 定期檢查
while running:
    check_memory()
    time.sleep(60)
```

**解決方案**：

**1. 清理舊記錄**
```python
# 在 engine.py 中限制記錄數量
if len(self.records) > 1000:
    self.records = self.records[-500:]  # 只保留最新 500 筆
```

**2. 釋放圖像資源**
```python
# 檢測後釋放
frame = None
annotated = None
import gc
gc.collect()
```

**3. 定期重啟**
```python
# 設定最大運行時間
MAX_RUNTIME = 8 * 3600  # 8 小時

if time.time() - start_time > MAX_RUNTIME:
    logger.info("達到最大運行時間，重啟系統")
    cleanup()
    restart()
```

---

## 👨‍💻 開發指南

### 開發環境設定

```bash
# 1. Clone 專案
git clone https://github.com/your-repo/ccd-system.git
cd ccd-system

# 2. 創建虛擬環境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# 3. 安裝依賴（包含開發工具）
pip install -r requirements.txt
pip install pytest pytest-cov black pylint flake8

# 4. 設定 IDE（推薦 VS Code）
# 安裝擴展：Python, Pylance
```

### 代碼規範

#### 1. 命名規範

```python
# 類名：大駝峰
class InspectionEngine:
    pass

# 函數/變量：小寫+下劃線
def process_single_product():
    product_id = 123
    detection_result = "OK"

# 常量：全大寫
MAX_RETRY_COUNT = 3
DEFAULT_THRESHOLD = 0.5

# 私有成員：前綴下劃線
class MyClass:
    def __init__(self):
        self._private_var = 0
```

#### 2. 文檔字串

```python
def detect_defect(image: np.ndarray, threshold: float = 0.5) -> Dict:
    """
    檢測圖像中的缺陷
    
    這個函數使用 YOLOv8 模型來檢測圖像中的各種缺陷類型。
    
    Args:
        image: 輸入圖像，BGR 格式的 numpy 數組
        threshold: 置信度閾值，範圍 0.0-1.0，默認 0.5
    
    Returns:
        包含檢測結果的字典：
        {
            'judgment': str,      # "OK" 或 "NG"
            'confidence': float,  # 置信度分數
            'classes': list,      # 檢測到的類別列表
            'boxes': list         # 邊界框座標列表
        }
    
    Raises:
        ValueError: 如果圖像為空或格式錯誤
        RuntimeError: 如果模型未載入
    
    Example:
        >>> image = cv2.imread("test.jpg")
        >>> result = detect_defect(image, threshold=0.6)
        >>> print(result['judgment'])
        'NG'
    """
    pass
```

#### 3. 類型提示

```python
from typing import List, Dict, Optional, Tuple
import numpy as np

def process_batch(
    images: List[np.ndarray],
    threshold: float = 0.5,
    save_results: bool = True
) -> Tuple[List[str], List[float]]:
    """
    批次處理多張圖像
    
    Args:
        images: 圖像列表
        threshold: 置信度閾值
        save_results: 是否保存結果
    
    Returns:
        判定結果列表和置信度列表的元組
    """
    judgments: List[str] = []
    confidences: List[float] = []
    
    for image in images:
        judgment, confidence = detect(image, threshold)
        judgments.append(judgment)
        confidences.append(confidence)
    
    return judgments, confidences
```

### 添加新功能

#### 範例：添加 Email 通知

```python
# 1. 創建新模組 utils/email_notifier.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailNotifier:
    """Email 通知器"""
    
    def __init__(self, smtp_server: str, port: int, username: str, password: str):
        self.smtp_server = smtp_server
        self.port = port
        self.username = username
        self.password = password
    
    def send_alert(self, subject: str, message: str, recipients: List[str]):
        """
        發送警報郵件
        
        Args:
            subject: 郵件主旨
            message: 郵件內容
            recipients: 收件人列表
        """
        msg = MIMEMultipart()
        msg['From'] = self.username
        msg['To'] = ', '.join(recipients)
        msg['Subject'] = subject
        
        msg.attach(MIMEText(message, 'plain'))
        
        with smtplib.SMTP(self.smtp_server, self.port) as server:
            server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)

# 2. 整合到引擎
class InspectionEngine:
    def __init__(self, config):
        # ...
        self.notifier = EmailNotifier(
            smtp_server='smtp.gmail.com',
            port=587,
            username='your-email@gmail.com',
            password='your-password'
        )
    
    def process_single(self):
        record = super().process_single()
        
        # 檢測到 NG 時發送通知
        if record and record.judgment == "NG":
            self.notifier.send_alert(
                subject="檢測到不良品",
                message=f"產品 {record.product_id} 檢測為 NG\n置信度: {record.confidence}",
                recipients=['manager@company.com']
            )
        
        return record
```

### 單元測試

```python
# tests/test_detector.py
import pytest
import numpy as np
from core.detector import YOLODetector
from models.data_models import DetectorConfig

@pytest.fixture
def detector():
    """創建測試用檢測器"""
    config = DetectorConfig(
        model_path="tests/fixtures/test_model.pt",
        confidence_threshold=0.5,
        detection_mode="defect"
    )
    det = YOLODetector(config)
    det.load_model()
    return det

def test_detect_returns_correct_format(detector):
    """測試檢測返回格式正確"""
    # 創建測試圖像
    image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
    
    # 執行檢測
    judgment, conf, classes, annotated = detector.detect(image)
    
    # 驗證返回值
    assert judgment in ["OK", "NG", "ERROR"]
    assert isinstance(conf, float)
    assert 0.0 <= conf <= 1.0
    assert isinstance(classes, list)
    assert isinstance(annotated, np.ndarray)
    assert annotated.shape == image.shape

def test_detect_with_empty_image(detector):
    """測試空圖像處理"""
    image = np.zeros((640, 640, 3), dtype=np.uint8)
    judgment, conf, classes, annotated = detector.detect(image)
    
    # 空圖像應該返回 OK（無缺陷）或 NG（取決於模式）
    assert judgment in ["OK", "NG"]
    assert conf >= 0

def test_mode_detection(detector):
    """測試模式識別"""
    mode, confidence = detector.get_mode_info()
    assert mode in ["defect", "object", "classification"]
    assert 0 <= confidence <= 100

# 執行測試
# pytest tests/ -v --cov=core
```

### 性能分析

```python
# 使用 cProfile 分析性能
import cProfile
import pstats

def profile_detection():
    """性能分析"""
    profiler = cProfile.Profile()
    profiler.enable()
    
    # 執行檢測
    for i in range(100):
        engine.process_single()
    
    profiler.disable()
    
    # 輸出統計
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # 顯示前 20 個耗時函數

# 使用 line_profiler 分析具體函數
# pip install line_profiler
from line_profiler import LineProfiler

def profile_function():
    lp = LineProfiler()
    lp.add_function(detector.detect)
    lp.enable()
    
    # 執行
    detector.detect(image)
    
    lp.disable()
    lp.print_stats()
```

---

## 🚀 生產部署

### 部署檢查清單

#### 階段 1：環境驗證（30%）

- [ ] **Python 環境**
  - [ ] Python 3.8-3.11 已安裝
  - [ ] 已加入系統 PATH
  - [ ] pip 版本 ≥ 21.0

- [ ] **依賴套件**
  - [ ] 所有套件安裝成功（`pip list`）
  - [ ] OpenCV 版本正確
  - [ ] Ultralytics 可正常導入
  - [ ] GPU 驅動已安裝（如使用 GPU）

- [ ] **目錄結構**
  - [ ] 所有必要目錄已創建
  - [ ] 日誌目錄可寫入
  - [ ] 輸出目錄有足夠空間（建議 >50GB）

#### 階段 2：硬體驗證（20%）

- [ ] **相機測試**
  - [ ] 執行 `test_camera.py` 通過
  - [ ] 找到正確的相機索引
  - [ ] 解析度設定成功
  - [ ] 畫面清晰、無噪點
  - [ ] 照明均勻、無反光

- [ ] **剔除裝置**（如使用）
  - [ ] 序列埠連接成功
  - [ ] 測試觸發正常
  - [ ] 延遲設定準確
  - [ ] 動作穩定可靠

#### 階段 3：模型驗證（30%）

- [ ] **模型載入**
  - [ ] 模型文件完整無損
  - [ ] 執行 `check_model.py` 無錯誤
  - [ ] 類別信息正確顯示
  - [ ] 模式識別準確

- [ ] **檢測測試**
  - [ ] 準備 OK 樣品 × 20
  - [ ] 準備 NG 樣品 × 20
  - [ ] 單次檢測準確率 ≥ 95%
  - [ ] 處理時間 < 100ms（CPU）或 < 50ms（GPU）
  - [ ] 無誤檢/漏檢

- [ ] **閾值調整**
  - [ ] 測試不同置信度閾值
  - [ ] 記錄最佳閾值
  - [ ] 誤檢率 < 2%
  - [ ] 漏檢率 < 1%

#### 階段 4：連續運行測試（20%）

- [ ] **穩定性測試**
  - [ ] 連續運行 1 小時無錯誤
  - [ ] 連續檢測 1000 張無崩潰
  - [ ] 記憶體使用穩定（< 1GB 增長）
  - [ ] CPU 使用率合理（< 80%）

- [ ] **異常處理**
  - [ ] 測試相機斷線恢復
  - [ ] 測試網路中斷恢復
  - [ ] 測試異常圖像處理
  - [ ] 日誌記錄完整

- [ ] **剔除驗證**（如使用）
  - [ ] 延遲準確率 ≥ 98%
  - [ ] 剔除成功率 100%
  - [ ] 無誤剔除

### 部署腳本

#### Windows 服務

```batch
@echo off
REM install_service.bat

echo 安裝 CCD 檢測系統為 Windows 服務...

REM 使用 NSSM (Non-Sucking Service Manager)
REM 下載：https://nssm.cc/download

nssm install CCDInspection "C:\Python39\python.exe" "C:\CCD_System\main.py"
nssm set CCDInspection AppDirectory "C:\CCD_System"
nssm set CCDInspection DisplayName "CCD 視覺檢測系統"
nssm set CCDInspection Description "自動化視覺檢測與剔除系統"
nssm set CCDInspection Start SERVICE_AUTO_START

echo 服務安裝完成！
echo 啟動服務：net start CCDInspection
pause
```

#### Linux Systemd 服務

```ini
# /etc/systemd/system/ccd-inspection.service

[Unit]
Description=CCD Vision Inspection System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/CCD_System
ExecStart=/home/pi/CCD_System/venv/bin/python /home/pi/CCD_System/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**安裝和啟動**：
```bash
# 複製服務文件
sudo cp ccd-inspection.service /etc/systemd/system/

# 重新載入 systemd
sudo systemctl daemon-reload

# 啟用服務（開機自動啟動）
sudo systemctl enable ccd-inspection

# 啟動服務
sudo systemctl start ccd-inspection

# 查看狀態
sudo systemctl status ccd-inspection

# 查看日誌
sudo journalctl -u ccd-inspection -f
```

### 監控和維護

#### 日誌監控腳本

```python
# monitor.py - 簡單的日誌監控腳本

import os
import time
from datetime import datetime
import smtplib
from email.mime.text import MIMEText

class SystemMonitor:
    """系統監控器"""
    
    def __init__(self):
        self.log_dir = "./logs"
        self.alert_email = "admin@company.com"
        self.last_check = datetime.now()
    
    def check_errors(self):
        """檢查錯誤日誌"""
        today_log = f"ccd_{datetime.now().strftime('%Y%m%d')}.log"
        log_path = os.path.join(self.log_dir, today_log)
        
        if not os.path.exists(log_path):
            return
        
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 檢查錯誤
        error_lines = [line for line in lines if 'ERROR' in line or 'CRITICAL' in line]
        
        if error_lines:
            self.send_alert(f"發現 {len(error_lines)} 條錯誤", '\n'.join(error_lines[-10:]))
    
    def check_disk_space(self):
        """檢查磁碟空間"""
        import shutil
        
        output_dir = "./rejection_output"
        total, used, free = shutil.disk_usage(output_dir)
        
        free_gb = free / (1024**3)
        
        if free_gb < 10:
            self.send_alert("磁碟空間不足", f"剩餘空間: {free_gb:.2f} GB")
    
    def check_yield_rate(self):
        """檢查良率"""
        # 讀取最新的統計記錄
        log_files = sorted(os.listdir("./rejection_output/logs"))
        if not log_files:
            return
        
        latest_log = os.path.join("./rejection_output/logs", log_files[-1])
        
        import json
        with open(latest_log, 'r') as f:
            data = json.load(f)
        
        yield_rate = float(data['statistics']['yield_rate'].rstrip('%'))
        
        if yield_rate < 90:
            self.send_alert("良率異常", f"當前良率: {yield_rate}%")
    
    def send_alert(self, subject: str, message: str):
        """發送警報"""
        print(f"[ALERT] {subject}: {message}")
        # 這裡可以添加 Email 發送邏輯
    
    def run(self):
        """運行監控"""
        print("啟動系統監控...")
        
        while True:
            try:
                self.check_errors()
                self.check_disk_space()
                self.check_yield_rate()
            except Exception as e:
                print(f"監控錯誤: {e}")
            
            time.sleep(300)  # 每 5 分鐘檢查一次

if __name__ == "__main__":
    monitor = SystemMonitor()
    monitor.run()
```

### 備份策略

```bash
#!/bin/bash
# backup.sh - 自動備份腳本

BACKUP_DIR="/backup/ccd_system"
DATE=$(date +%Y%m%d_%H%M%S)

echo "開始備份..."

# 備份配置文件
cp config.json "$BACKUP_DIR/config_$DATE.json"

# 備份檢測記錄
tar -czf "$BACKUP_DIR/logs_$DATE.tar.gz" rejection_output/logs/

# 備份 NG 圖片
tar -czf "$BACKUP_DIR/ng_images_$DATE.tar.gz" rejection_output/NG/

# 清理 30 天前的備份
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete

echo "備份完成！"
```

**設定定期執行**（Cron）：
```bash
# 編輯 crontab
crontab -e

# 添加每天凌晨 2 點執行備份
0 2 * * * /home/pi/CCD_System/backup.sh
```

---

## ❓ 常見問題

### Q1: 支援哪些相機？

**A**: 
- ✅ **USB 相機**：UVC 標準相機（即插即用）
- ✅ **工業相機**：
  - Basler（需 Pylon SDK）
  - FLIR/Point Grey（需 Spinnaker SDK）
  - Hikvision（需 MVS SDK）
  - Daheng Imaging（需 Galaxy SDK）
- ⚠️ **網路相機（IP Camera）**：需額外開發（RTSP 串流）

---

### Q2: 可以同時使用多個相機嗎？

**A**: 當前版本（v1.1）不原生支援多相機，但可通過以下方式實現：

**方案 1：多進程**
```python
# 適用於相機數量 ≤ 4
import multiprocessing

def run_camera(camera_index):
    config = ConfigManager().load()
    config.camera.index = camera_index
    engine = InspectionEngine(config)
    engine.initialize()
    engine.start_continuous()

if __name__ == '__main__':
    processes = []
    for i in range(2):  # 2 個相機
        p = multiprocessing.Process(target=run_camera, args=(i,))
        p.start()
        processes.append(p)
```

---

### Q3: 如何提高檢測準確率？

**A**: 系統化提升策略：

**1. 數據質量（70% 影響）**
- ✓ 收集多樣化樣品（至少 500 張/類別）
- ✓ 標註準確（使用 LabelImg 或 Roboflow）
- ✓ 數據增強（旋轉、翻轉、亮度調整）
- ✓ 避免過擬合（使用驗證集）

**2. 模型優化（20% 影響）**
- ✓ 使用更大的模型（yolov8m, yolov8l）
- ✓ 調整訓練參數（epochs, batch size）
- ✓ 使用預訓練權重
- ✓ 數據增強策略

**3. 照明和拍攝（10% 影響）**
- ✓ 穩定、均勻的光源
- ✓ 避免反光和陰影
- ✓ 固定的拍攝距離和角度
- ✓ 適當的對比度

---

### Q4: 系統能處理多快的產線？

**A**: 處理速度取決於多個因素：

| 配置 | 處理時間 | 最大速度 |
|-----|---------|---------|
| **CPU（i5）** | 100-200ms | ~5 件/秒 |
| **CPU（i7）** | 50-100ms | ~10 件/秒 |
| **GPU（GTX 1660）** | 20-50ms | ~20 件/秒 |
| **GPU（RTX 3070）** | 10-30ms | ~30 件/秒 |

**優化建議**：
1. 使用 GPU 加速（5-10 倍提升）
2. 降低輸入解析度（720p vs 1080p）
3. 使用輕量模型（yolov8n vs yolov8x）
4. 跳幀檢測（每 2-3 幀檢測一次）

---

### Q5: 如何處理多種產品？

**A**: 有三種方案：

**方案 1：多模型切換**
```python
# 根據產品類型載入不同模型
product_type = get_current_product_type()

if product_type == "A":
    detector.load_model("./models/product_a.pt")
elif product_type == "B":
    detector.load_model("./models/product_b.pt")
```

**方案 2：單一多類別模型**
```python
# 訓練一個包含所有產品類別的模型
# 模型類別：product_a_ok, product_a_ng, product_b_ok, product_b_ng
```

**方案 3：分類 + 檢測**
```python
# 第一步：產品分類
product_type = classifier.classify(image)

# 第二步：根據類型檢測
if product_type == "A":
    result = detector_a.detect(image)
else:
    result = detector_b.detect(image)
```

---

### Q6: 如何遠程監控系統？

**A**: 推薦使用以下方案：

**方案 1：Web Dashboard（推薦）**
```python
# 使用 Flask 創建 Web 界面
from flask import Flask, render_template, jsonify

app = Flask(__name__)

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/statistics')
def get_statistics():
    stats = engine.get_statistics()
    return jsonify(stats.to_dict())

@app.route('/api/latest_image')
def get_latest_image():
    # 返回最新檢測圖像
    pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

**方案 2：遠程桌面**
- Windows: 啟用遠程桌面
- Linux: 使用 VNC 或 TeamViewer

**方案 3：日誌同步**
- 使用 rsync 同步日誌到遠程服務器
- 使用 Elasticsearch + Kibana 可視化

---

### Q7: 授權和商業使用？

**A**: 

**系統代碼**：
- 本專案採用 MIT 授權
- 可免費用於商業項目
- 需保留原作者版權聲明

**YOLOv8**：
- Ultralytics 採用 AGPL-3.0 授權
- 商業使用需購買企業授權
- 詳情：https://ultralytics.com/license

**建議**：
- 小規模使用：免費（< 10 台設備）
- 商業部署：購買 Ultralytics 企業授權
- 私有網路：無需購買授權

---

## 📅 更新日誌

### v1.1 (2025-01-02)

**新功能**：
- ✨ 智能模式自動識別（Auto Mode）
- ✨ 支援分類模型（OK/NG 類別）
- ✨ 相機自動重連機制
- ✨ 模型完整診斷工具

**改進**：
- 🔧 優化檢測速度（提升 20%）
- 🔧 改進 GUI 響應性
- 🔧 增強錯誤處理
- 🔧 完善日誌系統

**修復**：
- 🐛 修復相機斷線後無法恢復的問題
- 🐛 修復長時間運行記憶體洩漏
- 🐛 修復 Windows 路徑問題

---

### v1.0 (2024-12-15)

**初始版本**：
- ✨ 基礎檢測引擎
- ✨ Defect/Object 模式
- ✨ GUI 實時預覽
- ✨ 延遲剔除控制
- ✨ 數據記錄和統計

---

## 🤝 貢獻指南

### 如何貢獻

我們歡迎所有形式的貢獻！

**貢獻方式**：
1. 🐛 報告 Bug
2. 💡 提出新功能建議
3. 📝 改進文檔
4. 🔧 提交代碼

### 提交 Pull Request

1. Fork 本專案
2. 創建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交變更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

### 開發規範

- 遵循 PEP 8 代碼風格
- 添加單元測試
- 更新相關文檔
- 確保所有測試通過

---

---

##  致謝

感謝以下開源專案：

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) - 深度學習檢測框架
- [OpenCV](https://opencv.org/) - 電腦視覺庫
- [Tkinter](https://docs.python.org/3/library/tkinter.html) - GUI 框架


[⬆ 回到頂部](#ccd-視覺檢測與自動剔除系統-ccd-vision-inspection--rejection-system)

</div>
