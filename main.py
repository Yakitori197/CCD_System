# -*- coding: utf-8 -*-
"""
CCD 視覺檢測與自動剔除系統

"""

import sys
from pathlib import Path

# 添加項目根目錄到 Python 路徑
sys.path.insert(0, str(Path(__file__).parent))

from gui.main_window import MainWindow
from utils.config import ConfigError
from utils.logger import get_logger


def check_dependencies():
    """檢查依賴套件"""
    missing = []
    
    try:
        import cv2
    except ImportError:
        missing.append("opencv-python")
    
    try:
        import numpy
    except ImportError:
        missing.append("numpy")
    
    try:
        from ultralytics import YOLO
    except ImportError:
        missing.append("ultralytics")
    
    if missing:
        print("錯誤: 缺少必要套件")
        print(f"請執行: pip install {' '.join(missing)}")
        return False
    
    return True


def main():
    """主程式入口"""
    print("=" * 60)
    print("CCD 視覺檢測與自動剔除系統 v1.2")
    print("=" * 60)
    print()
    
    # 檢查依賴
    if not check_dependencies():
        input("按 Enter 鍵退出...")
        return
    
    # 初始化日誌
    logger = get_logger()
    logger.info("系統啟動")
    
    try:
        # 啟動 GUI
        app = MainWindow()
        app.run()

    except ConfigError as e:
        # 設定檔錯誤：明確告知並拒絕啟動（不靜默帶預設值運行）
        logger.critical(f"設定檔錯誤，系統拒絕啟動:\n{e}")
        print()
        print("!" * 60)
        print("設定檔錯誤，請修正後重新啟動:")
        print(str(e))
        print("!" * 60)
        input("按 Enter 鍵退出...")
    except KeyboardInterrupt:
        logger.info("用戶中斷")
    except Exception as e:
        logger.critical(f"系統錯誤: {e}", exc_info=True)
        input("按 Enter 鍵退出...")
    finally:
        logger.info("系統關閉")


if __name__ == "__main__":
    main()