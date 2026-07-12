# -*- coding: utf-8 -*-
"""設定層（utils/config.py）單元測試"""

import json

import pytest

from utils.config import ConfigManager, ConfigError
from models.data_models import SystemConfig


def write(tmp_path, content: str):
    p = tmp_path / "config.json"
    p.write_text(content, encoding="utf-8")
    return str(p)


class TestLoad:

    def test_missing_file_returns_defaults(self, tmp_path):
        mgr = ConfigManager(str(tmp_path / "nope.json"))
        config = mgr.load()
        assert isinstance(config, SystemConfig)
        assert config.detector.detection_mode == "defect"

    def test_valid_config_loads(self, tmp_path):
        path = write(tmp_path, json.dumps({
            "camera_index": 1,
            "confidence_threshold": 0.7,
            "detection_mode": "object",
            "ok_classes": ["good"],
            "ng_classes": ["bad"],
        }))
        config = ConfigManager(path).load()
        assert config.camera.index == 1
        assert config.detector.confidence_threshold == 0.7
        assert config.detector.detection_mode == "object"
        assert config.detector.ok_classes == ["good"]

    def test_comment_keys_are_ignored(self, tmp_path):
        path = write(tmp_path, json.dumps({
            "_comment": "hello",
            "_comment_model": "world",
            "detection_mode": "defect",
        }))
        config = ConfigManager(path).load()
        assert config.detector.detection_mode == "defect"

    def test_invalid_json_raises_not_silently_defaults(self, tmp_path):
        """v1.1 的 bug：// 註解導致 JSON 解析失敗卻靜默用預設值。v1.2 必須拋錯。"""
        path = write(tmp_path, '{\n  "camera_index": 0,  // comment\n}')
        with pytest.raises(ConfigError) as exc:
            ConfigManager(path).load()
        assert "JSON" in str(exc.value)


class TestValidation:

    @pytest.mark.parametrize("overrides", [
        {"detection_mode": "banana"},
        {"confidence_threshold": 0.0},
        {"confidence_threshold": 1.5},
        {"iou_threshold": -0.1},
        {"camera_index": -1},
        {"camera_width": 0},
        {"camera_backend": "quantum"},
        {"rejection_delay_ms": -5},
        {"serial_baudrate": 0},
        {"ok_classes": ["X"], "ng_classes": ["X"]},
    ])
    def test_invalid_values_raise(self, tmp_path, overrides):
        path = write(tmp_path, json.dumps(overrides))
        with pytest.raises(ConfigError):
            ConfigManager(path).load()


class TestRoundTrip:

    def test_save_then_load_preserves_values(self, tmp_path):
        path = str(tmp_path / "config.json")
        mgr = ConfigManager(path)
        config = SystemConfig()
        config.detector.detection_mode = "object"
        config.detector.confidence_threshold = 0.66
        config.detector.ok_classes = ["good"]
        config.camera.index = 2
        mgr.save(config)

        loaded = ConfigManager(path).load()
        assert loaded.detector.detection_mode == "object"
        assert loaded.detector.confidence_threshold == 0.66
        assert loaded.detector.ok_classes == ["good"]
        assert loaded.camera.index == 2
