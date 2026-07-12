# -*- coding: utf-8 -*-
"""
YOLOv8 檢測器模組（v1.2 重構）

職責拆分：
- 本模組：模型載入、推理（inference）
- core/decision.py：OK/NG 判定策略（可獨立測試）
- core/visualization.py：結果疊加繪圖

對外介面與 v1.1 相容：load_model() / detect() / get_mode_info() /
update_threshold() / is_loaded()。
"""

import time
from typing import Tuple, List, Optional

import cv2
import numpy as np

from models.data_models import DetectorConfig
from core.decision import ClassSemantics, JudgmentPolicy, build_policy
from core.visualization import annotate_judgment
from utils.logger import get_logger
from utils.model_analyzer import ModelAnalyzer

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False


class YOLODetector:
    """YOLOv8 檢測器"""

    def __init__(self, config: DetectorConfig):
        if not YOLO_AVAILABLE:
            raise ImportError("請安裝 ultralytics: pip install ultralytics")

        self.config = config
        self.model: Optional["YOLO"] = None
        self.class_names: dict = {}
        self.logger = get_logger()
        self.analyzer = ModelAnalyzer()

        self.semantics = ClassSemantics()
        self.policy: Optional[JudgmentPolicy] = None
        self.actual_mode: Optional[str] = None
        self.mode_confidence: float = 0.0

    # ------------------------------------------------------------------ #
    # 模型載入
    # ------------------------------------------------------------------ #

    def load_model(self, model_path: Optional[str] = None) -> bool:
        """載入模型並建立判定策略"""
        if model_path:
            self.config.model_path = model_path

        try:
            self.logger.info(f"載入模型: {self.config.model_path}")
            self.model = YOLO(self.config.model_path)
            self.class_names = self.model.names
            self.logger.info(f"模型載入成功，類別數量: {len(self.class_names)}")
            self.logger.info(f"類別列表: {self.class_names}")

            # 解析類別語意（設定檔顯式宣告優先，關鍵字識別為 fallback）
            self.semantics = ClassSemantics.resolve(
                self.class_names,
                explicit_ok=self.config.ok_classes,
                explicit_ng=self.config.ng_classes if self.config.ok_classes else None,
            )

            # 決定實際模式
            if self.config.detection_mode == "auto":
                if self.semantics.is_classification:
                    self.actual_mode = "classification"
                    self.mode_confidence = 100.0
                else:
                    detected_mode, confidence, _analysis = self.analyzer.analyze(
                        self.config.model_path, self.class_names
                    )
                    self.actual_mode = detected_mode
                    self.mode_confidence = confidence
                    self.logger.info(
                        f"自動識別完成: {detected_mode.upper()} (置信度: {confidence:.1f}%)"
                    )
            else:
                self.actual_mode = self.config.detection_mode
                self.mode_confidence = 100.0
                self.logger.info(f"使用手動指定模式: {self.actual_mode.upper()}")

            # 建立判定策略
            self.policy = build_policy(
                self.config.detection_mode,
                self.semantics,
                self.config.ng_classes,
            )
            if self.policy.mode_name == "classification":
                self.actual_mode = "classification"
            self.logger.info(f"判定邏輯: {self.policy.describe()}")

            return True

        except Exception as e:
            self.logger.error(f"載入模型失敗: {e}", exc_info=True)
            return False

    # ------------------------------------------------------------------ #
    # 推理 + 判定 + 繪圖
    # ------------------------------------------------------------------ #

    def detect(self, image: np.ndarray) -> Tuple[str, float, List[str], np.ndarray]:
        """
        執行檢測。

        Returns:
            judgment: "OK" / "NG" / "ERROR"
            max_confidence: 最高置信度
            detected_classes: 檢測到的類別列表
            annotated_image: 標註後的圖像
        """
        if self.model is None:
            raise RuntimeError("模型尚未載入")
        if self.policy is None:
            raise RuntimeError("判定策略未建立（請先 load_model）")

        start_time = time.time()

        try:
            # --- 推理 ---
            results = self.model(
                image,
                conf=self.config.confidence_threshold,
                iou=self.config.iou_threshold,
                device=self.config.device,
                verbose=False
            )[0]

            detected_classes: List[str] = []
            max_confidence = 0.0
            for box in results.boxes:
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                detected_classes.append(self.class_names.get(cls_id, f"class_{cls_id}"))
                max_confidence = max(max_confidence, conf)

            # --- 判定 ---
            judgment = self.policy.judge(detected_classes)

            # --- 繪圖 ---
            annotated = results.plot()
            annotated = cv2.cvtColor(annotated, cv2.COLOR_RGB2BGR)
            annotated = annotate_judgment(
                annotated,
                judgment.result,
                self._mode_display(),
                detected_classes,
            )

            inference_time = (time.time() - start_time) * 1000
            log = self.logger.info if judgment.result == "NG" else self.logger.debug
            log(
                f"判定: {judgment.result} | 原因: {judgment.reason} | "
                f"置信度: {max_confidence:.3f} | 耗時: {inference_time:.1f}ms"
            )

            return judgment.result, max_confidence, detected_classes, annotated

        except Exception as e:
            self.logger.error(f"檢測失敗: {e}", exc_info=True)
            return "ERROR", 0.0, [], image

    def _mode_display(self) -> str:
        """疊加於影像左下角的模式文字"""
        if self.actual_mode == "classification":
            return "Mode: Classification"
        display = f"Mode: {self.actual_mode}"
        if self.config.detection_mode == "auto":
            display += f" (Auto: {self.mode_confidence:.0f}%)"
        return display

    # ------------------------------------------------------------------ #
    # 查詢與更新
    # ------------------------------------------------------------------ #

    def get_mode_info(self) -> dict:
        """獲取當前模式信息"""
        return {
            "configured_mode": self.config.detection_mode,
            "actual_mode": self.actual_mode,
            "confidence": self.mode_confidence,
            "is_auto": self.config.detection_mode == "auto",
            "is_classification": self.actual_mode == "classification",
            "ok_classes": self.semantics.ok_classes,
            "ng_classes": self.semantics.ng_classes,
            "semantics_source": self.semantics.source,
        }

    def update_threshold(self, threshold: float):
        """更新置信度閾值"""
        self.config.confidence_threshold = threshold
        self.logger.info(f"置信度閾值已更新: {threshold:.2f}")

    def is_loaded(self) -> bool:
        """檢查模型是否已載入"""
        return self.model is not None
