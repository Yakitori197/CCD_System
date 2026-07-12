# -*- coding: utf-8 -*-
"""
判定邏輯模組（v1.2 重構自 detector.py）

把「檢測到什麼類別 → OK/NG」的決策從推理與繪圖中抽離：
- ClassSemantics：類別語意（哪些類別代表 OK、哪些代表 NG）。
  優先使用設定檔顯式宣告（ok_classes / ng_classes），
  未宣告時 fallback 到類別名稱關鍵字自動識別。
- JudgmentPolicy 家族：三種判定策略，純函式、無 I/O、無重依賴，
  可直接單元測試。

本模組刻意不 import cv2 / numpy / ultralytics。
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

# 類別名稱關鍵字（fallback 自動識別用）
OK_KEYWORDS = ('ok', 'good', 'pass', 'normal', '良品', '合格')
NG_KEYWORDS = ('ng', 'bad', 'fail', 'defect', 'abnormal', '不良', '缺陷')


@dataclass
class Judgment:
    """判定結果"""
    result: str          # "OK" / "NG"
    reason: str          # 人可讀的判定原因（進日誌）


@dataclass
class ClassSemantics:
    """模型類別的 OK/NG 語意"""
    ok_classes: List[str] = field(default_factory=list)
    ng_classes: List[str] = field(default_factory=list)
    source: str = "none"  # "explicit"（設定檔宣告）/ "keyword"（關鍵字識別）/ "none"

    @property
    def is_classification(self) -> bool:
        """同時具備 OK 與 NG 類別語意 → 視為分類模型"""
        return bool(self.ok_classes) and bool(self.ng_classes)

    @classmethod
    def resolve(
        cls,
        class_names: Dict[int, str],
        explicit_ok: Optional[List[str]] = None,
        explicit_ng: Optional[List[str]] = None,
    ) -> 'ClassSemantics':
        """
        解析類別語意。

        優先順序：
        1. 設定檔顯式宣告（explicit_ok / explicit_ng 同時非空）→ 直接採用
        2. 類別名稱關鍵字自動識別（舊版行為，保留為 fallback）
        """
        if explicit_ok and explicit_ng:
            return cls(ok_classes=list(explicit_ok), ng_classes=list(explicit_ng),
                       source="explicit")

        ok_found: List[str] = []
        ng_found: List[str] = []
        for name in (class_names or {}).values():
            lower = str(name).lower()
            if any(k in lower for k in NG_KEYWORDS):
                ng_found.append(str(name))
            elif any(k in lower for k in OK_KEYWORDS):
                ok_found.append(str(name))

        if ok_found and ng_found:
            return cls(ok_classes=ok_found, ng_classes=ng_found, source="keyword")
        return cls(source="none")


class JudgmentPolicy:
    """判定策略基底"""

    mode_name = "base"

    def judge(self, detected_classes: List[str]) -> Judgment:
        raise NotImplementedError

    def describe(self) -> str:
        """判定邏輯的說明文字（顯示於 GUI 與日誌）"""
        raise NotImplementedError


class ClassificationPolicy(JudgmentPolicy):
    """分類模型：NG 類別 → NG；OK 類別 → OK；什麼都沒檢測到 → NG（異常/缺失）"""

    mode_name = "classification"

    def __init__(self, semantics: ClassSemantics):
        if not semantics.is_classification:
            raise ValueError("ClassificationPolicy 需要同時具備 OK 與 NG 類別語意")
        self.semantics = semantics

    def judge(self, detected_classes: List[str]) -> Judgment:
        if not detected_classes:
            return Judgment("NG", "未檢測到任何類別（異常/缺失產品）")
        for cls_name in detected_classes:
            if cls_name in self.semantics.ng_classes:
                return Judgment("NG", f"檢測到 NG 類別: {cls_name}")
        for cls_name in detected_classes:
            if cls_name in self.semantics.ok_classes:
                return Judgment("OK", f"檢測到 OK 類別: {cls_name}")
        # 檢測到的類別不在已知語意內 → 保守判 NG
        return Judgment("NG", f"檢測到未宣告語意的類別: {detected_classes}")

    def describe(self) -> str:
        return (f"分類模型（語意來源: {self.semantics.source}）: "
                f"{self.semantics.ng_classes} → NG；{self.semantics.ok_classes} → OK；"
                f"未檢測到 → NG")


class DefectPolicy(JudgmentPolicy):
    """缺陷檢測：檢測到（指定）缺陷 → NG；沒檢測到 → OK"""

    mode_name = "defect"

    def __init__(self, ng_classes: Optional[List[str]] = None):
        self.ng_classes = list(ng_classes or [])

    def judge(self, detected_classes: List[str]) -> Judgment:
        if not detected_classes:
            return Judgment("OK", "未檢測到缺陷")
        if self.ng_classes:
            for cls_name in detected_classes:
                if cls_name in self.ng_classes:
                    return Judgment("NG", f"檢測到 NG 類別: {cls_name}")
            return Judgment("OK", f"檢測到的類別不在 NG 清單: {detected_classes}")
        return Judgment("NG", f"檢測到缺陷: {detected_classes}")

    def describe(self) -> str:
        if self.ng_classes:
            return f"缺陷檢測: 檢測到 {self.ng_classes} → NG；其他/未檢測到 → OK"
        return "缺陷檢測: 檢測到任何目標 → NG；未檢測到 → OK"


class ObjectPolicy(JudgmentPolicy):
    """物體檢測：檢測到產品 → OK；沒檢測到 → NG"""

    mode_name = "object"

    def judge(self, detected_classes: List[str]) -> Judgment:
        if detected_classes:
            return Judgment("OK", f"檢測到產品: {detected_classes}")
        return Judgment("NG", "未檢測到產品")

    def describe(self) -> str:
        return "物體檢測: 檢測到產品 → OK；未檢測到 → NG"


def build_policy(
    mode: str,
    semantics: ClassSemantics,
    config_ng_classes: Optional[List[str]] = None,
) -> JudgmentPolicy:
    """
    依模式建立判定策略。

    mode 為 "auto" 時：具 OK/NG 語意 → ClassificationPolicy，否則 DefectPolicy。
    """
    if mode == "auto":
        if semantics.is_classification:
            return ClassificationPolicy(semantics)
        return DefectPolicy(config_ng_classes)
    if mode == "defect":
        if semantics.is_classification:
            return ClassificationPolicy(semantics)
        return DefectPolicy(config_ng_classes)
    if mode == "object":
        return ObjectPolicy()
    raise ValueError(f"未知的檢測模式: {mode!r}")
