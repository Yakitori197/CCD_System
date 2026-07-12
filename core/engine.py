# -*- coding: utf-8 -*-
"""
檢測引擎模組
"""

import cv2
import time
import json
import queue
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict

from models.data_models import (
    SystemConfig, ProductRecord, Statistics
)
from core.camera import CameraManager
from core.detector import YOLODetector
from core.rejector import RejectionController
from utils.logger import get_logger


class InspectionEngine:
    """檢測與剔除引擎"""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.logger = get_logger()
        
        # 核心組件
        self.camera: Optional[CameraManager] = None
        self.detector: Optional[YOLODetector] = None
        self.rejector: Optional[RejectionController] = None
        
        # 狀態管理
        self.is_running = False
        self.product_counter = 0
        
        # 數據存儲
        self.records: List[ProductRecord] = []
        self.statistics = Statistics()
        
        # 延遲隊列
        self.delay_queue = queue.PriorityQueue()
        self.rejection_thread: Optional[threading.Thread] = None

        # 連續檢測（v1.2）：推理在 worker thread 執行，
        # 結果經 result_queue 交給 GUI 輪詢，不阻塞 UI 主執行緒
        self.result_queue: "queue.Queue[ProductRecord]" = queue.Queue()
        self.inspection_thread: Optional[threading.Thread] = None
        
        # 輸出目錄
        self.output_dir = Path(config.output_dir)
        self._setup_directories()
    
    def _setup_directories(self):
        """建立輸出目錄"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "OK").mkdir(exist_ok=True)
        (self.output_dir / "NG").mkdir(exist_ok=True)
        (self.output_dir / "logs").mkdir(exist_ok=True)
        self.logger.debug(f"輸出目錄已建立: {self.output_dir}")
    
    def initialize(self) -> bool:
        """初始化系統"""
        self.logger.info("開始初始化系統...")
        
        try:
            # 初始化相機
            self.camera = CameraManager(self.config.camera)
            if not self.camera.open():
                raise RuntimeError("相機初始化失敗")
            
            # 啟用自動重連
            self.camera.enable_auto_reconnect()
            
            # 載入檢測模型
            self.detector = YOLODetector(self.config.detector)
            if not self.detector.load_model():
                raise RuntimeError("模型載入失敗")
            
            # 初始化剔除控制器
            if self.config.rejection.enabled:
                self.rejector = RejectionController(self.config.rejection)
                if not self.rejector.connect():
                    self.logger.warning("剔除控制器初始化失敗，但繼續運行")
            
            self.logger.info("系統初始化完成")
            return True
            
        except Exception as e:
            self.logger.error(f"初始化失敗: {e}", exc_info=True)
            return False
    
    def process_single(self) -> Optional[ProductRecord]:
        """處理單個產品"""
        if not self.camera or not self.detector:
            self.logger.error("系統未初始化")
            return None
        
        start_time = time.time()
        
        try:
            # 取像
            ret, frame = self.camera.read()
            if not ret or frame is None:
                self.logger.warning("取像失敗")
                return None
            
            # 檢測
            judgment, confidence, defect_classes, annotated = self.detector.detect(frame)
            
            processing_time = (time.time() - start_time) * 1000
            
            # 建立記錄
            self.product_counter += 1
            record = ProductRecord(
                product_id=self.product_counter,
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
                judgment=judgment,
                confidence=confidence,
                defect_classes=defect_classes,
                processing_time=processing_time
            )
            
            # 儲存圖像
            if (judgment == "OK" and self.config.save_ok_images) or \
               (judgment == "NG" and self.config.save_ng_images):
                filename = f"{record.product_id:06d}_{judgment}_{datetime.now().strftime('%H%M%S')}.jpg"
                save_path = self.output_dir / judgment / filename
                cv2.imwrite(str(save_path), annotated)
                record.image_path = str(save_path)
                self.logger.debug(f"圖像已儲存: {save_path}")
            
            # 更新統計
            if judgment == "OK":
                self.statistics.increment_ok()
            elif judgment == "NG":
                self.statistics.increment_ng()
                
                # 加入剔除隊列
                if self.config.rejection.enabled and self.rejector:
                    reject_time = time.time() + (self.config.rejection.delay_ms / 1000.0)
                    self.delay_queue.put((reject_time, record))
            
            # 保存記錄
            self.records.append(record)
            
            return record
            
        except Exception as e:
            self.logger.error(f"處理產品失敗: {e}", exc_info=True)
            return None
    
    def _rejection_worker(self):
        """剔除工作線程"""
        self.logger.info("剔除工作線程已啟動")
        
        while self.is_running:
            try:
                if not self.delay_queue.empty():
                    reject_time, record = self.delay_queue.get(timeout=0.1)
                    
                    # 等待到達剔除時間
                    wait_time = reject_time - time.time()
                    if wait_time > 0:
                        time.sleep(wait_time)
                    
                    # 執行剔除
                    if self.rejector and self.rejector.trigger(delay_ms=0):
                        record.rejection_sent = True
                        self.statistics.increment_rejection()
                        self.logger.info(f"產品 #{record.product_id:06d} 已剔除")
                    else:
                        self.logger.error(f"產品 #{record.product_id:06d} 剔除失敗")
                else:
                    time.sleep(0.01)
                    
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"剔除工作線程錯誤: {e}", exc_info=True)
        
        self.logger.info("剔除工作線程已停止")
    
    def _inspection_worker(self):
        """連續檢測工作線程：推理不佔用 GUI 主執行緒"""
        self.logger.info("檢測工作線程已啟動")

        while self.is_running:
            record = self.process_single()
            if record:
                self.result_queue.put(record)
            else:
                # 取像/推理失敗時稍作等待，避免空轉
                time.sleep(0.05)

        self.logger.info("檢測工作線程已停止")

    def start_continuous(self):
        """開始連續檢測"""
        if self.is_running:
            self.logger.warning("系統已在運行中")
            return

        self.is_running = True
        self.logger.info("開始連續檢測")

        # 啟動檢測工作線程
        self.inspection_thread = threading.Thread(
            target=self._inspection_worker,
            daemon=True
        )
        self.inspection_thread.start()

        # 啟動剔除工作線程
        if self.config.rejection.enabled and self.rejector:
            self.rejection_thread = threading.Thread(
                target=self._rejection_worker,
                daemon=True
            )
            self.rejection_thread.start()
    
    def stop(self):
        """停止檢測"""
        self.logger.info("停止檢測...")
        self.is_running = False

        # 等待檢測線程結束
        if self.inspection_thread and self.inspection_thread.is_alive():
            self.inspection_thread.join(timeout=2)

        # 等待剔除線程結束
        if self.rejection_thread and self.rejection_thread.is_alive():
            self.rejection_thread.join(timeout=2)
        
        # 保存記錄
        self.save_records()
        
        self.logger.info("檢測已停止")
    
    def shutdown(self):
        """關閉系統"""
        self.logger.info("關閉系統...")
        
        self.stop()
        
        if self.camera:
            self.camera.close()
        
        if self.rejector:
            self.rejector.disconnect()
        
        self.logger.info("系統已關閉")
    
    def save_records(self):
        """儲存檢測記錄"""
        if not self.records:
            self.logger.info("無記錄需要儲存")
            return
        
        try:
            log_file = self.output_dir / "logs" / f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            data = {
                "timestamp": datetime.now().isoformat(),
                "statistics": self.statistics.to_dict(),
                "records": [r.to_dict() for r in self.records]
            }
            
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"記錄已儲存: {log_file}")
            
        except Exception as e:
            self.logger.error(f"儲存記錄失敗: {e}", exc_info=True)
    
    def get_statistics(self) -> Dict:
        """獲取統計數據"""
        return self.statistics.to_dict()
    
    def reset_statistics(self):
        """重置統計"""
        self.statistics.reset()
        self.records.clear()
        self.product_counter = 0
        self.logger.info("統計已重置")