# -*- coding: utf-8 -*-
"""
數據模型定義
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict
from datetime import datetime


@dataclass
class ProductRecord:
    """產品檢測記錄"""
    product_id: int
    timestamp: str
    judgment: str  # "OK" / "NG"
    confidence: float
    defect_classes: List[str]
    processing_time: float  # ms
    image_path: Optional[str] = None
    rejection_sent: bool = False
    
    def to_dict(self) -> Dict:
        """轉換為字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ProductRecord':
        """從字典建立"""
        return cls(**data)


@dataclass
class Statistics:
    """統計數據"""
    total_count: int = 0
    ok_count: int = 0
    ng_count: int = 0
    rejection_count: int = 0
    
    @property
    def yield_rate(self) -> float:
        """良率（%）"""
        if self.total_count == 0:
            return 0.0
        return (self.ok_count / self.total_count) * 100
    
    def increment_ok(self):
        """增加良品計數"""
        self.total_count += 1
        self.ok_count += 1
    
    def increment_ng(self):
        """增加不良品計數"""
        self.total_count += 1
        self.ng_count += 1
    
    def increment_rejection(self):
        """增加剔除計數"""
        self.rejection_count += 1
    
    def to_dict(self) -> Dict:
        """轉換為字典"""
        return {
            "total": self.total_count,
            "ok": self.ok_count,
            "ng": self.ng_count,
            "rejection": self.rejection_count,
            "yield_rate": f"{self.yield_rate:.2f}%"
        }
    
    def reset(self):
        """重置統計"""
        self.total_count = 0
        self.ok_count = 0
        self.ng_count = 0
        self.rejection_count = 0


@dataclass
class CameraConfig:
    """相機配置"""
    index: int = 0
    width: int = 1920
    height: int = 1080
    fps: int = 30
    auto_exposure: bool = True
    exposure_value: int = -6

    # 相機後端："opencv"（USB/UVC）。
    # 工業相機（GenICam / Basler pylon / Hikvision）可實作 CameraSource
    # 介面後在 core/camera.py 的 create_camera_source() 註冊新後端。
    backend: str = "opencv"


@dataclass
class DetectorConfig:
    """檢測器配置"""
    model_path: str = ""
    confidence_threshold: float = 0.5
    iou_threshold: float = 0.45
    device: str = "cpu"  # "cpu" or "cuda"
    
    # 檢測模式：
    # "defect": 缺陷檢測模式 - 檢測到=NG，沒檢測到=OK
    # "object": 物體檢測模式 - 檢測到=OK，沒檢測到=NG
    detection_mode: str = "defect"
    
    # NG 類別列表（可選）
    # 當 detection_mode="defect" 且此列表非空時，
    # 只有檢測到列表中的類別才判定為 NG
    ng_classes: List[str] = field(default_factory=list)

    # OK 類別列表（可選）
    # 分類模型建議在此顯式宣告 OK/NG 類別語意，
    # 未宣告時才 fallback 到類別名稱關鍵字自動識別（見 core/decision.py）
    ok_classes: List[str] = field(default_factory=list)


@dataclass
class RejectionConfig:
    """剔除配置"""
    enabled: bool = False
    delay_ms: int = 500
    pulse_ms: int = 100
    serial_port: str = "COM3"
    baudrate: int = 9600


@dataclass
class SystemConfig:
    """系統配置"""
    camera: CameraConfig = field(default_factory=CameraConfig)
    detector: DetectorConfig = field(default_factory=DetectorConfig)
    rejection: RejectionConfig = field(default_factory=RejectionConfig)
    
    save_ok_images: bool = False
    save_ng_images: bool = True
    output_dir: str = "./rejection_output"
    
    def to_dict(self) -> Dict:
        """轉換為字典"""
        return {
            "camera_index": self.camera.index,
            "camera_width": self.camera.width,
            "camera_height": self.camera.height,
            "camera_backend": self.camera.backend,
            "model_path": self.detector.model_path,
            "confidence_threshold": self.detector.confidence_threshold,
            "iou_threshold": self.detector.iou_threshold,
            "device": self.detector.device,
            "detection_mode": self.detector.detection_mode,
            "ng_classes": self.detector.ng_classes,
            "ok_classes": self.detector.ok_classes,
            "rejection_enabled": self.rejection.enabled,
            "rejection_delay_ms": self.rejection.delay_ms,
            "rejection_pulse_ms": self.rejection.pulse_ms,
            "serial_port": self.rejection.serial_port,
            "serial_baudrate": self.rejection.baudrate,
            "save_ok_images": self.save_ok_images,
            "save_ng_images": self.save_ng_images,
            "output_dir": self.output_dir
        }