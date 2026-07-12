# -*- coding: utf-8 -*-
"""
相機管理模組（v1.2 重構）

抽象出 CameraSource 介面，讓工業相機（GenICam/Harvester、Basler pylon、
Hikvision MVS…）可以在不動 CameraManager 與引擎的情況下接入：

    1. 繼承 CameraSource 實作 open/close/read/is_available/get_properties
    2. 在 create_camera_source() 註冊新的 backend 名稱
    3. config.json 設 "camera_backend": "<你的backend>"

CameraManager 對外介面與 v1.1 相容。
"""

import time
import threading
from abc import ABC, abstractmethod
from typing import Optional, Tuple

import cv2
import numpy as np

from models.data_models import CameraConfig
from utils.logger import get_logger


# ---------------------------------------------------------------------- #
# 相機來源介面
# ---------------------------------------------------------------------- #

class CameraSource(ABC):
    """相機來源抽象介面"""

    def __init__(self, config: CameraConfig):
        self.config = config

    @abstractmethod
    def open(self) -> bool:
        """開啟相機，回傳是否成功"""

    @abstractmethod
    def close(self):
        """釋放相機資源"""

    @abstractmethod
    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """讀取一幀 BGR 影像"""

    @abstractmethod
    def is_available(self) -> bool:
        """相機目前是否可用"""

    def get_properties(self) -> dict:
        """相機屬性（可選實作）"""
        return {}


class OpenCVCameraSource(CameraSource):
    """USB / UVC 相機（cv2.VideoCapture）"""

    def __init__(self, config: CameraConfig):
        super().__init__(config)
        self.capture: Optional[cv2.VideoCapture] = None
        self.logger = get_logger()

    def open(self) -> bool:
        self.capture = cv2.VideoCapture(self.config.index)
        if not self.capture.isOpened():
            self.logger.error(f"無法開啟相機 {self.config.index}")
            return False

        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.height)
        self.capture.set(cv2.CAP_PROP_FPS, self.config.fps)

        if self.config.auto_exposure:
            self.capture.set(cv2.CAP_PROP_AUTO_EXPOSURE, 3)   # auto
        else:
            self.capture.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)   # manual
            self.capture.set(cv2.CAP_PROP_EXPOSURE, self.config.exposure_value)

        actual_w = self.capture.get(cv2.CAP_PROP_FRAME_WIDTH)
        actual_h = self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self.logger.info(f"相機已開啟: {actual_w:.0f}x{actual_h:.0f} @ {self.config.fps}fps")
        return True

    def close(self):
        if self.capture:
            self.capture.release()
            self.capture = None

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        if not self.capture:
            return False, None
        ret, frame = self.capture.read()
        if ret and frame is not None:
            return True, frame
        return False, None

    def is_available(self) -> bool:
        return self.capture is not None and self.capture.isOpened()

    def get_properties(self) -> dict:
        if not self.is_available():
            return {}
        return {
            'width': self.capture.get(cv2.CAP_PROP_FRAME_WIDTH),
            'height': self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT),
            'fps': self.capture.get(cv2.CAP_PROP_FPS),
            'exposure': self.capture.get(cv2.CAP_PROP_EXPOSURE),
            'brightness': self.capture.get(cv2.CAP_PROP_BRIGHTNESS),
            'contrast': self.capture.get(cv2.CAP_PROP_CONTRAST),
        }


def create_camera_source(config: CameraConfig) -> CameraSource:
    """
    相機後端工廠。

    新增工業相機後端時在此註冊，例如：
        "pylon": BaslerPylonSource,
        "harvester": GenICamHarvesterSource,
    """
    backends = {
        "opencv": OpenCVCameraSource,
    }
    if config.backend not in backends:
        raise ValueError(
            f"未知的相機後端: {config.backend!r}，可用: {sorted(backends)}"
        )
    return backends[config.backend](config)


# ---------------------------------------------------------------------- #
# 相機管理器（快取最後一幀 + 自動重連）
# ---------------------------------------------------------------------- #

class CameraManager:
    """相機管理器：包裝 CameraSource，提供執行緒安全的最後一幀與自動重連"""

    def __init__(self, config: CameraConfig):
        self.config = config
        self.source: CameraSource = create_camera_source(config)
        self.is_opened = False
        self.last_frame: Optional[np.ndarray] = None
        self.frame_lock = threading.Lock()
        self.reconnect_enabled = False
        self.reconnect_thread: Optional[threading.Thread] = None
        self.logger = get_logger()

    def open(self) -> bool:
        """開啟相機"""
        try:
            self.is_opened = self.source.open()
            return self.is_opened
        except Exception as e:
            self.logger.error(f"開啟相機失敗: {e}", exc_info=True)
            return False

    def close(self):
        """關閉相機"""
        self.reconnect_enabled = False
        try:
            self.source.close()
            self.is_opened = False
            self.logger.info("相機已關閉")
        except Exception as e:
            self.logger.error(f"關閉相機失敗: {e}")

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """讀取一幀圖像"""
        if not self.is_opened:
            return False, None

        try:
            ret, frame = self.source.read()
            if ret and frame is not None:
                with self.frame_lock:
                    self.last_frame = frame.copy()
                return True, frame
            self.logger.warning("讀取幀失敗")
            return False, None
        except Exception as e:
            self.logger.error(f"讀取幀異常: {e}")
            return False, None

    def get_last_frame(self) -> Optional[np.ndarray]:
        """獲取最後一幀（線程安全）"""
        with self.frame_lock:
            if self.last_frame is not None:
                return self.last_frame.copy()
        return None

    def is_available(self) -> bool:
        """檢查相機是否可用"""
        return self.is_opened and self.source.is_available()

    def enable_auto_reconnect(self):
        """啟用自動重連"""
        if self.reconnect_enabled:
            return
        self.reconnect_enabled = True
        self.reconnect_thread = threading.Thread(target=self._reconnect_worker, daemon=True)
        self.reconnect_thread.start()
        self.logger.info("自動重連已啟用")

    def _reconnect_worker(self):
        """自動重連工作線程"""
        while self.reconnect_enabled:
            time.sleep(2)
            if not self.is_available():
                self.logger.warning("相機斷線，嘗試重連...")
                try:
                    self.source.close()
                except Exception:
                    pass
                time.sleep(1)
                if self.open():
                    self.logger.info("相機重連成功")
                else:
                    self.logger.error("相機重連失敗，2秒後重試")

    def get_properties(self) -> dict:
        """獲取相機屬性"""
        if not self.is_available():
            return {}
        return self.source.get_properties()
