# CCD_System — CCD 視覺檢測與自動剔除系統

以 **YOLOv8** 為核心的產線 AOI（自動光學檢測）系統：相機取像 → 模型推理 → OK/NG 判定 → 序列埠觸發硬體剔除，附 Tkinter 操作介面與生產統計。

> v1.2 — 模組化重構版（判定/推理/繪圖分層、推理移出 UI 執行緒、設定 fail-loud、單元測試）

## 功能特色

- **三種檢測模式**：缺陷檢測（檢測到=NG）、物體檢測（檢測到=OK）、分類模型（OK/NG 類別直判），支援 `auto` 自動識別模型類型
- **判定策略分層**：OK/NG 決策邏輯獨立於 `core/decision.py`，純函式、可單元測試；類別語意優先採用設定檔顯式宣告，關鍵字識別為 fallback
- **非阻塞 GUI**：推理在背景工作執行緒執行，結果經 queue 交給 UI 輪詢，主執行緒不卡頓
- **硬體剔除整合**：NG 品經延遲佇列準時觸發序列埠剔除訊號（延遲/脈寬可調）
- **相機抽象層**：`CameraSource` 介面 + 後端工廠，USB/UVC 之外的工業相機（GenICam、Basler pylon、Hikvision）可無痛接入
- **Fail-loud 設定**：設定檔格式或數值錯誤直接報錯拒絕啟動，絕不靜默帶預設值運行
- **自動重連**：相機斷線自動偵測重連；檢測紀錄與統計自動存檔（JSON + 標註影像）

## 快速開始

```bash
pip install -r requirements.txt
python main.py
```

操作流程：`載入模型` → `開啟相機` → `單次檢測` 或 `開始連續檢測`。

## 專案結構

```
CCD_System/
├── main.py                 # 入口
├── config.json             # 主設定檔（config_defect / config_yolov8 為情境範本）
├── core/
│   ├── engine.py           # 檢測引擎：取像→推理→判定→剔除 的流程編排與工作執行緒
│   ├── detector.py         # YOLOv8 模型載入與推理
│   ├── decision.py         # OK/NG 判定策略（Classification / Defect / Object）
│   ├── visualization.py    # 結果疊加繪圖
│   ├── camera.py           # CameraSource 介面 + OpenCV 實作 + 自動重連
│   └── rejector.py         # 序列埠剔除控制
├── gui/main_window.py      # Tkinter 操作介面
├── models/                 # 模型目錄（附 yolov8n.pt 供測試；換上自己的模型即可）
├── utils/                  # 設定管理（fail-loud 驗證）、日誌、模型分析
├── tests/                  # pytest 單元測試（判定邏輯、設定層）
└── docs/PRODUCT_OVERVIEW.md  # 完整產品介紹文件
```

## 設定檔重點

```jsonc
{
  "model_path": "./models/yolov8n.pt",
  "detection_mode": "auto",        // auto / defect / object
  "confidence_threshold": 0.5,
  "ok_classes": [],                // 分類模型建議顯式宣告類別語意
  "ng_classes": [],
  "camera_backend": "opencv",      // 工業相機後端可於 core/camera.py 擴充
  "rejection_enabled": false,      // 硬體剔除開關
  "serial_port": "COM3"
}
```

> 注意：JSON 不支援 `//` 註解，設定檔內請使用 `"_comment"` 欄位；格式錯誤系統會明確報錯。

## 判定邏輯

| 模式 | 檢測到 | 未檢測到 |
|---|---|---|
| **Classification**（含 OK/NG 類別的模型） | NG 類別 → NG；OK 類別 → OK | NG（異常/缺失） |
| **Defect**（訓練缺陷的模型） | NG（可用 `ng_classes` 白名單縮小範圍） | OK |
| **Object**（訓練正常產品的模型） | OK | NG |

## 測試

```bash
pip install pytest
python -m pytest tests/ -q
```

## 授權與模型

repo 內附的 `yolov8n.pt` 為 Ultralytics 官方預訓練模型。實際產線部署時請替換為自己訓練的模型（客製模型不隨 repo 發佈）。
