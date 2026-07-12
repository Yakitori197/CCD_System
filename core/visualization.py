# -*- coding: utf-8 -*-
"""
檢測結果視覺化模組（v1.2 重構自 detector.py）

負責在標註影像上疊加判定結果、模式資訊與類別清單。
樣式集中於 AnnotationStyle，不再散落寫死於判定邏輯中。
"""

from dataclasses import dataclass
from typing import List

import cv2
import numpy as np


@dataclass
class AnnotationStyle:
    """疊加樣式（BGR 色彩）"""
    font: int = cv2.FONT_HERSHEY_SIMPLEX
    result_font_scale: float = 2.0
    result_thickness: int = 4
    result_padding: int = 20
    ok_color: tuple = (0, 255, 0)
    ng_color: tuple = (0, 0, 255)
    banner_bg_color: tuple = (0, 0, 0)
    banner_alpha: float = 0.6
    info_font_scale: float = 0.6
    info_color: tuple = (255, 255, 255)
    classes_font_scale: float = 0.5
    classes_color: tuple = (200, 200, 200)
    max_classes_shown: int = 3


DEFAULT_STYLE = AnnotationStyle()


def annotate_judgment(
    image: np.ndarray,
    judgment: str,
    mode_display: str,
    detected_classes: List[str],
    style: AnnotationStyle = DEFAULT_STYLE,
) -> np.ndarray:
    """
    在影像上疊加判定結果（左上角橫幅）、模式（左下）、類別清單（左下上方）。

    會直接修改傳入影像並回傳之。
    """
    h, _w = image.shape[:2]
    color = style.ok_color if judgment == "OK" else style.ng_color

    # 判定橫幅（半透明黑底 + 大字）
    (text_w, text_h), _baseline = cv2.getTextSize(
        judgment, style.font, style.result_font_scale, style.result_thickness
    )
    pad = style.result_padding
    overlay = image.copy()
    cv2.rectangle(overlay, (10, 10), (10 + text_w + pad * 2, 10 + text_h + pad * 2),
                  style.banner_bg_color, -1)
    cv2.addWeighted(overlay, style.banner_alpha, image, 1 - style.banner_alpha, 0, image)
    cv2.putText(image, judgment, (10 + pad, 10 + text_h + pad),
                style.font, style.result_font_scale, color, style.result_thickness)

    # 模式資訊（左下角）
    cv2.putText(image, mode_display, (10, h - 15),
                style.font, style.info_font_scale, style.info_color, 2)

    # 檢測到的類別（模式資訊上方）
    if detected_classes:
        shown = detected_classes[:style.max_classes_shown]
        classes_text = f"Detected: {', '.join(shown)}"
        if len(detected_classes) > style.max_classes_shown:
            classes_text += "..."
        cv2.putText(image, classes_text, (10, h - 45),
                    style.font, style.classes_font_scale, style.classes_color, 1)

    return image
