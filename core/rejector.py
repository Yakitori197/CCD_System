# -*- coding: utf-8 -*-
"""
剔除控制器模組
"""

import time
import threading
from typing import Optional
from models.data_models import RejectionConfig
from utils.logger import get_logger

try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False


class RejectionController:
    """剔除裝置控制器"""
    
    def __init__(self, config: RejectionConfig):
        self.config = config
        self.serial_conn: Optional[serial.Serial] = None
        self.is_connected = False
        self.simulation_mode = False
        self.trigger_lock = threading.Lock()
        
        self.logger = get_logger()
    
    def connect(self) -> bool:
        """連接序列埠"""
        if not self.config.enabled:
            self.logger.info("剔除功能未啟用")
            return True
        
        if not SERIAL_AVAILABLE:
            self.logger.warning("pyserial 未安裝，使用模擬模式")
            self.simulation_mode = True
            self.is_connected = True
            return True
        
        try:
            self.serial_conn = serial.Serial(
                port=self.config.serial_port,
                baudrate=self.config.baudrate,
                timeout=1
            )
            
            self.is_connected = True
            self.simulation_mode = False
            self.logger.info(f"剔除裝置已連接: {self.config.serial_port} @ {self.config.baudrate}")
            
            return True
            
        except Exception as e:
            self.logger.warning(f"剔除裝置連接失敗: {e}")
            self.logger.info("切換至模擬模式")
            self.simulation_mode = True
            self.is_connected = True
            return True
    
    def disconnect(self):
        """斷開連接"""
        if self.serial_conn:
            try:
                self.serial_conn.close()
                self.logger.info("剔除裝置已斷開")
            except Exception as e:
                self.logger.error(f"斷開連接失敗: {e}")
        
        self.is_connected = False
        self.simulation_mode = False
    
    def trigger(self, delay_ms: Optional[int] = None, pulse_ms: Optional[int] = None) -> bool:
        """
        觸發剔除動作
        
        Args:
            delay_ms: 延遲時間（毫秒），None 使用配置值
            pulse_ms: 脈衝持續時間（毫秒），None 使用配置值
        
        Returns:
            是否成功觸發
        """
        if not self.is_connected:
            self.logger.warning("剔除裝置未連接")
            return False
        
        delay = delay_ms if delay_ms is not None else self.config.delay_ms
        pulse = pulse_ms if pulse_ms is not None else self.config.pulse_ms
        
        # 延遲等待
        if delay > 0:
            time.sleep(delay / 1000.0)
        
        with self.trigger_lock:
            try:
                if self.simulation_mode:
                    self.logger.info(f"[模擬] 剔除信號觸發 (脈衝: {pulse}ms)")
                    time.sleep(pulse / 1000.0)
                    return True
                else:
                    # 發送觸發信號
                    self.serial_conn.write(b'R')
                    time.sleep(pulse / 1000.0)
                    # 發送停止信號
                    self.serial_conn.write(b'S')
                    
                    self.logger.info(f"剔除信號已發送 (脈衝: {pulse}ms)")
                    return True
                    
            except Exception as e:
                self.logger.error(f"發送剔除信號失敗: {e}")
                return False
    
    def trigger_async(self, delay_ms: Optional[int] = None, pulse_ms: Optional[int] = None):
        """異步觸發（不阻塞）"""
        thread = threading.Thread(
            target=self.trigger,
            args=(delay_ms, pulse_ms),
            daemon=True
        )
        thread.start()
    
    def test(self) -> bool:
        """測試剔除功能"""
        self.logger.info("執行剔除測試...")
        return self.trigger(delay_ms=0, pulse_ms=100)