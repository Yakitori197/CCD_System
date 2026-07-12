# -*- coding: utf-8 -*-
"""
模型分析器 - 自動識別模型類型
"""

import re
from pathlib import Path
from typing import Dict, Tuple, List
from utils.logger import get_logger


class ModelAnalyzer:
    """模型類型分析器"""
    
    # 缺陷相關關鍵字（越多越可能是缺陷檢測模型）
    DEFECT_KEYWORDS = [
        'defect', 'scratch', 'crack', 'stain', 'damage', 'broken',
        'flaw', 'blemish', 'dent', 'chip', 'pit', 'mark',
        'rust', 'corrosion', 'tear', 'hole', 'burr',
        'ng', 'bad', 'fault', 'error', 'abnormal',
        # 中文關鍵字
        '瑕疵', '缺陷', '劃痕', '裂紋', '污點', '破損', '不良'
    ]
    
    # 通用物體關鍵字（COCO 等數據集的常見類別）
    COMMON_OBJECTS = [
        'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train',
        'truck', 'boat', 'traffic', 'fire', 'stop', 'parking', 'bench',
        'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear',
        'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie',
        'suitcase', 'frisbee', 'skis', 'snowboard', 'sports', 'kite',
        'baseball', 'basketball', 'skateboard', 'surfboard', 'tennis',
        'bottle', 'wine', 'cup', 'fork', 'knife', 'spoon', 'bowl',
        'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot',
        'hot', 'pizza', 'donut', 'cake', 'chair', 'couch', 'potted',
        'bed', 'dining', 'toilet', 'tv', 'laptop', 'mouse', 'remote',
        'keyboard', 'cell', 'microwave', 'oven', 'toaster', 'sink',
        'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy',
        'hair', 'toothbrush'
    ]
    
    def __init__(self):
        self.logger = get_logger()
    
    def analyze(self, model_path: str, class_names: Dict) -> Tuple[str, float, Dict]:
        """
        分析模型類型
        
        Args:
            model_path: 模型文件路徑
            class_names: 模型的類別名稱字典 {0: 'class1', 1: 'class2', ...}
        
        Returns:
            detection_mode: "defect" 或 "object"
            confidence: 置信度分數 (0-100)
            analysis: 詳細分析結果
        """
        self.logger.info("=" * 60)
        self.logger.info("開始分析模型類型...")
        self.logger.info("=" * 60)
        
        analysis = {
            'filename_score': 0,
            'classname_score': 0,
            'class_count_score': 0,
            'total_score': 0,
            'reasons': []
        }
        
        # 1. 文件名分析
        filename_result = self._analyze_filename(model_path)
        analysis['filename_score'] = filename_result['score']
        analysis['reasons'].extend(filename_result['reasons'])
        
        # 2. 類別名稱分析
        classname_result = self._analyze_class_names(class_names)
        analysis['classname_score'] = classname_result['score']
        analysis['reasons'].extend(classname_result['reasons'])
        
        # 3. 類別數量分析
        class_count_result = self._analyze_class_count(class_names)
        analysis['class_count_score'] = class_count_result['score']
        analysis['reasons'].extend(class_count_result['reasons'])
        
        # 4. 綜合判定
        total_score = (
            analysis['filename_score'] * 0.3 +
            analysis['classname_score'] * 0.5 +
            analysis['class_count_score'] * 0.2
        )
        analysis['total_score'] = total_score
        
        # 判定模式
        if total_score > 0:
            detection_mode = "defect"
            confidence = min(abs(total_score), 100)
        else:
            detection_mode = "object"
            confidence = min(abs(total_score), 100)
        
        # 輸出分析結果
        self._log_analysis_results(detection_mode, confidence, analysis)
        
        return detection_mode, confidence, analysis
    
    def _analyze_filename(self, model_path: str) -> Dict:
        """分析文件名"""
        filename = Path(model_path).stem.lower()
        
        reasons = []
        score = 0
        
        # 檢查缺陷關鍵字
        defect_found = []
        for keyword in self.DEFECT_KEYWORDS:
            if keyword in filename:
                defect_found.append(keyword)
                score += 30
        
        if defect_found:
            reasons.append(f"文件名包含缺陷關鍵字: {', '.join(defect_found)}")
        
        # 檢查通用模型標誌
        if re.search(r'yolov[0-9]', filename):
            reasons.append("文件名為標準 YOLOv8 預訓練模型")
            score -= 50
        elif 'coco' in filename:
            reasons.append("文件名包含 COCO 標誌（通用數據集）")
            score -= 40
        
        # 檢查特定關鍵字
        if 'custom' in filename or 'train' in filename:
            reasons.append("文件名包含 'custom' 或 'train'（自訓練模型）")
            score += 20
        
        return {
            'score': score,
            'reasons': reasons
        }
    
    def _analyze_class_names(self, class_names: Dict) -> Dict:
        """分析類別名稱"""
        if not class_names:
            return {'score': 0, 'reasons': ["無類別信息"]}
        
        reasons = []
        score = 0
        
        # 轉換為列表
        classes = [str(name).lower() for name in class_names.values()]
        
        # 統計缺陷類別
        defect_classes = []
        for cls in classes:
            for keyword in self.DEFECT_KEYWORDS:
                if keyword in cls:
                    defect_classes.append(cls)
                    break
        
        defect_ratio = len(defect_classes) / len(classes) if classes else 0
        
        if defect_ratio > 0.5:
            reasons.append(f"缺陷類別佔比: {defect_ratio*100:.1f}% ({len(defect_classes)}/{len(classes)})")
            score += 80
        elif defect_ratio > 0:
            reasons.append(f"包含部分缺陷類別: {len(defect_classes)}/{len(classes)}")
            score += 40
        
        # 統計通用物體類別
        common_classes = []
        for cls in classes:
            if cls in self.COMMON_OBJECTS:
                common_classes.append(cls)
        
        common_ratio = len(common_classes) / len(classes) if classes else 0
        
        if common_ratio > 0.5:
            reasons.append(f"通用物體類別佔比: {common_ratio*100:.1f}% ({len(common_classes)}/{len(classes)})")
            score -= 80
        elif common_ratio > 0:
            reasons.append(f"包含部分通用物體: {len(common_classes)}/{len(classes)}")
            score -= 40
        
        # 特殊判斷：如果類別名稱都很簡單（如 'class_0', 'class_1'）
        generic_pattern = re.compile(r'^(class|obj|item|type)_?\d+$')
        generic_count = sum(1 for cls in classes if generic_pattern.match(cls))
        
        if generic_count == len(classes):
            reasons.append("類別名稱為通用格式（未重命名），無法判斷")
            score = 0
        
        return {
            'score': score,
            'reasons': reasons
        }
    
    def _analyze_class_count(self, class_names: Dict) -> Dict:
        """分析類別數量"""
        class_count = len(class_names)
        
        reasons = []
        score = 0
        
        if class_count == 0:
            reasons.append("無類別信息")
            return {'score': 0, 'reasons': reasons}
        
        reasons.append(f"類別數量: {class_count}")
        
        # 判斷邏輯
        if class_count <= 5:
            reasons.append("類別數量少（≤5），可能是專用缺陷檢測模型")
            score += 40
        elif class_count <= 15:
            reasons.append("類別數量中等（6-15），可能是自訓練模型")
            score += 20
        elif class_count >= 80:
            reasons.append("類別數量多（≥80），可能是 COCO 等通用數據集")
            score -= 50
        elif class_count >= 50:
            reasons.append("類別數量較多（50-79），可能是通用物體檢測")
            score -= 30
        
        return {
            'score': score,
            'reasons': reasons
        }
    
    def _log_analysis_results(self, mode: str, confidence: float, analysis: Dict):
        """輸出分析結果到日誌"""
        self.logger.info("")
        self.logger.info("分析結果:")
        self.logger.info("-" * 60)
        
        for reason in analysis['reasons']:
            self.logger.info(f"  • {reason}")
        
        self.logger.info("")
        self.logger.info("評分詳情:")
        self.logger.info(f"  • 文件名評分: {analysis['filename_score']:+.1f}")
        self.logger.info(f"  • 類別名評分: {analysis['classname_score']:+.1f}")
        self.logger.info(f"  • 類別數評分: {analysis['class_count_score']:+.1f}")
        self.logger.info(f"  • 綜合評分: {analysis['total_score']:+.1f}")
        
        self.logger.info("")
        self.logger.info("最終判定:")
        self.logger.info(f"  模型類型: {mode.upper()}")
        self.logger.info(f"  置信度: {confidence:.1f}%")
        
        if mode == "defect":
            self.logger.info(f"  判定邏輯: 檢測到 = NG（缺陷），沒檢測到 = OK（良品）")
        else:
            self.logger.info(f"  判定邏輯: 檢測到 = OK（產品），沒檢測到 = NG（異常）")
        
        self.logger.info("=" * 60)
        self.logger.info("")
    
    @staticmethod
    def get_mode_description(mode: str) -> str:
        """獲取模式描述"""
        descriptions = {
            "defect": "缺陷檢測模式：檢測到 = NG，沒檢測到 = OK",
            "object": "物體檢測模式：檢測到 = OK，沒檢測到 = NG"
        }
        return descriptions.get(mode, "未知模式")