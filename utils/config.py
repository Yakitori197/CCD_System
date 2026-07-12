# -*- coding: utf-8 -*-
"""
配置管理模組

設計原則（v1.2 重構）：
- 設定檔壞掉要 fail-loud：JSON 解析錯誤或數值不合法時拋出 ConfigError，
  絕不靜默 fallback 到預設值（舊版曾因 config.json 含 // 註解導致
  設定永遠沒生效卻沒人發現）。
- 檔案不存在視為「首次啟動」，使用預設值並明確告知。
- 註解一律用 "_comment" 開頭的 key（合法 JSON），不要用 //。
"""

import json
from pathlib import Path
from typing import Optional
from models.data_models import SystemConfig, CameraConfig, DetectorConfig, RejectionConfig

VALID_DETECTION_MODES = ("auto", "defect", "object")
VALID_CAMERA_BACKENDS = ("opencv",)


class ConfigError(Exception):
    """設定檔錯誤（格式或數值不合法）——啟動時必須修正，不允許帶病運行"""


def _require(condition: bool, message: str):
    if not condition:
        raise ConfigError(message)


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        self.config: Optional[SystemConfig] = None

    def load(self) -> SystemConfig:
        """
        載入配置。

        - 檔案不存在 → 回傳預設配置（首次啟動屬正常情況）
        - JSON 格式錯誤 / 數值不合法 → 拋出 ConfigError（fail-loud）
        """
        if not self.config_path.exists():
            print(f"配置文件不存在，使用預設值（首次啟動？）: {self.config_path}")
            self.config = SystemConfig()
            return self.config

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigError(
                f"配置文件不是合法 JSON: {self.config_path}\n"
                f"  錯誤位置: 第 {e.lineno} 行第 {e.colno} 列: {e.msg}\n"
                f"  提示: JSON 不支援 // 註解，請改用 \"_comment\" 欄位"
            ) from e

        # 移除所有 _comment 開頭的註解欄位
        data = {k: v for k, v in data.items() if not k.startswith('_comment')}

        camera_config = CameraConfig(
            index=data.get('camera_index', 0),
            width=data.get('camera_width', 1920),
            height=data.get('camera_height', 1080),
            fps=data.get('camera_fps', 30),
            backend=data.get('camera_backend', 'opencv'),
        )

        detector_config = DetectorConfig(
            model_path=data.get('model_path', ''),
            confidence_threshold=data.get('confidence_threshold', 0.5),
            iou_threshold=data.get('iou_threshold', 0.45),
            device=data.get('device', 'cpu'),
            detection_mode=data.get('detection_mode', 'defect'),
            ng_classes=data.get('ng_classes', []),
            ok_classes=data.get('ok_classes', []),
        )

        rejection_config = RejectionConfig(
            enabled=data.get('rejection_enabled', False),
            delay_ms=data.get('rejection_delay_ms', 500),
            pulse_ms=data.get('rejection_pulse_ms', 100),
            serial_port=data.get('serial_port', 'COM3'),
            baudrate=data.get('serial_baudrate', 9600)
        )

        config = SystemConfig(
            camera=camera_config,
            detector=detector_config,
            rejection=rejection_config,
            save_ok_images=data.get('save_ok_images', False),
            save_ng_images=data.get('save_ng_images', True),
            output_dir=data.get('output_dir', './rejection_output')
        )

        self.validate(config)

        self.config = config
        print(f"配置載入成功: {self.config_path}")
        print(f"檢測模式: {detector_config.detection_mode}")
        return config

    @staticmethod
    def validate(config: SystemConfig):
        """驗證配置數值，不合法就拋 ConfigError"""
        cam, det, rej = config.camera, config.detector, config.rejection

        _require(cam.backend in VALID_CAMERA_BACKENDS,
                 f"camera_backend 必須是 {VALID_CAMERA_BACKENDS}，收到: {cam.backend!r}")
        _require(isinstance(cam.index, int) and cam.index >= 0,
                 f"camera_index 必須是 >= 0 的整數，收到: {cam.index!r}")
        _require(cam.width > 0 and cam.height > 0,
                 f"相機解析度必須為正值，收到: {cam.width}x{cam.height}")
        _require(cam.fps > 0, f"camera_fps 必須為正值，收到: {cam.fps!r}")

        _require(det.detection_mode in VALID_DETECTION_MODES,
                 f"detection_mode 必須是 {VALID_DETECTION_MODES}，收到: {det.detection_mode!r}")
        _require(0.0 < det.confidence_threshold < 1.0,
                 f"confidence_threshold 必須介於 0 與 1 之間，收到: {det.confidence_threshold!r}")
        _require(0.0 < det.iou_threshold < 1.0,
                 f"iou_threshold 必須介於 0 與 1 之間，收到: {det.iou_threshold!r}")
        _require(isinstance(det.ng_classes, list),
                 f"ng_classes 必須是列表，收到: {type(det.ng_classes).__name__}")
        _require(isinstance(det.ok_classes, list),
                 f"ok_classes 必須是列表，收到: {type(det.ok_classes).__name__}")
        overlap = set(det.ng_classes) & set(det.ok_classes)
        _require(not overlap, f"同一類別不能同時出現在 ok_classes 與 ng_classes: {sorted(overlap)}")

        _require(rej.delay_ms >= 0, f"rejection_delay_ms 不可為負，收到: {rej.delay_ms!r}")
        _require(rej.pulse_ms > 0, f"rejection_pulse_ms 必須為正值，收到: {rej.pulse_ms!r}")
        _require(rej.baudrate > 0, f"serial_baudrate 必須為正值，收到: {rej.baudrate!r}")

    def save(self, config: Optional[SystemConfig] = None):
        """儲存配置"""
        if config is None:
            config = self.config

        if config is None:
            print("無配置可儲存")
            return

        data = config.to_dict()
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"配置已儲存: {self.config_path}")

    def update(self, **kwargs):
        """更新配置"""
        if self.config is None:
            self.config = SystemConfig()

        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            elif hasattr(self.config.camera, key.replace('camera_', '')):
                setattr(self.config.camera, key.replace('camera_', ''), value)
            elif hasattr(self.config.detector, key.replace('detector_', '')):
                setattr(self.config.detector, key.replace('detector_', ''), value)
            elif hasattr(self.config.rejection, key.replace('rejection_', '')):
                setattr(self.config.rejection, key.replace('rejection_', ''), value)

        self.validate(self.config)
