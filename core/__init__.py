# -*- coding: utf-8 -*-
"""
Core package

刻意不在此 re-export 子模組：camera/detector/engine 依賴 cv2、ultralytics
等重套件，急切載入會讓純邏輯模組（decision）無法在輕量環境下測試。
請直接 import 需要的子模組，例如：

    from core.engine import InspectionEngine
    from core.decision import build_policy
"""
