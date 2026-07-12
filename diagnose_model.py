# -*- coding: utf-8 -*-
"""
模型診斷工具 - 完整分析模型類別和判定邏輯
使用方法：
  單一模型診斷：python diagnose_model.py models/YourModel.pt
  比較兩個模型：python diagnose_model.py models/YourModel_A.pt models/YourModel_B.pt
"""

from ultralytics import YOLO
from pathlib import Path
import sys


def diagnose_model(model_path):
    """完整診斷模型"""
    print("\n" + "=" * 80)
    print(f" 模型診斷工具 - {Path(model_path).name}")
    print("=" * 80)
    
    try:
        # 載入模型
        print(f"\n載入模型中...")
        model = YOLO(model_path)
        class_names = model.names
        
        print(f"✓ 模型載入成功")
        print(f"\n📊 基本信息:")
        print(f"  類別數量: {len(class_names)}")
        print(f"  模型路徑: {model_path}")
        
        # 顯示所有類別
        print(f"\n📋 完整類別列表:")
        for idx, name in class_names.items():
            print(f"  [{idx:2d}] {name}")
        
        # 分析類別類型
        print(f"\n🔍 類別分析:")
        
        # 轉換為小寫列表
        class_list = [str(name).lower() for name in class_names.values()]
        
        # OK 相關關鍵字
        ok_keywords = ['ok', 'good', 'pass', 'normal', '良品', '合格', 'qualified']
        # NG 相關關鍵字
        ng_keywords = ['ng', 'bad', 'fail', 'defect', 'abnormal', '不良', '缺陷', 'reject']
        # 缺陷關鍵字
        defect_keywords = [
            'scratch', 'crack', 'stain', 'damage', 'broken',
            'dent', 'chip', 'pit', 'mark', 'rust', 'corrosion',
            'tear', 'hole', 'burr', 'flaw', 'blemish',
            '劃痕', '裂紋', '污點', '破損', '凹痕', '缺口', '毛邊'
        ]
        # COCO 通用物體
        coco_keywords = [
            'person', 'bicycle', 'car', 'motorcycle', 'airplane',
            'bus', 'train', 'truck', 'boat', 'traffic', 'fire',
            'stop', 'parking', 'bench', 'bird', 'cat', 'dog',
            'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra',
            'giraffe', 'backpack', 'umbrella', 'handbag', 'tie',
            'suitcase', 'frisbee', 'skis', 'snowboard', 'sports',
            'kite', 'baseball', 'basketball', 'skateboard', 'surfboard',
            'tennis', 'bottle', 'wine', 'cup', 'fork', 'knife',
            'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange',
            'broccoli', 'carrot', 'hot', 'pizza', 'donut', 'cake',
            'chair', 'couch', 'potted', 'bed', 'dining', 'toilet',
            'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell',
            'microwave', 'oven', 'toaster', 'sink', 'refrigerator',
            'book', 'clock', 'vase', 'scissors', 'teddy', 'hair',
            'toothbrush'
        ]
        
        ok_classes = []
        ng_classes = []
        defect_classes = []
        coco_classes = []
        
        for cls_name in class_names.values():
            cls_lower = str(cls_name).lower()
            
            # 檢查 OK 類別
            for keyword in ok_keywords:
                if keyword in cls_lower or cls_lower == keyword:
                    ok_classes.append(cls_name)
                    break
            
            # 檢查 NG 類別
            for keyword in ng_keywords:
                if keyword in cls_lower or cls_lower == keyword:
                    ng_classes.append(cls_name)
                    break
            
            # 檢查缺陷類別
            for keyword in defect_keywords:
                if keyword in cls_lower:
                    defect_classes.append(cls_name)
                    break
            
            # 檢查 COCO 類別
            if cls_lower in coco_keywords:
                coco_classes.append(cls_name)
        
        # 顯示分類結果
        if ok_classes:
            print(f"  ✅ OK 類別: {ok_classes}")
        if ng_classes:
            print(f"  ❌ NG 類別: {ng_classes}")
        if defect_classes:
            print(f"  🔴 缺陷類別: {defect_classes}")
        if coco_classes:
            print(f"  🌍 COCO 通用類別: {coco_classes[:5]}" + 
                  ("..." if len(coco_classes) > 5 else ""))
        
        if not (ok_classes or ng_classes or defect_classes or coco_classes):
            print(f"  ℹ️  未識別到特定類型（可能是自訓練模型）")
        
        # 判定模型類型
        print(f"\n🎯 模型類型判定:")
        
        is_classification = bool(ok_classes and ng_classes)
        is_defect = bool(defect_classes) and not is_classification
        is_coco = len(coco_classes) >= 10
        
        if is_classification:
            print(f"  ✓ 類型: 【分類模型】Classification Model")
            print(f"  ✓ 特徵: 同時包含 OK 和 NG 類別")
            print(f"\n💡 判定邏輯:")
            print(f"  ┌─────────────────────────────────────────┐")
            print(f"  │  檢測到 {ng_classes} → NG（不良品）")
            print(f"  │  檢測到 {ok_classes} → OK（良品）")
            print(f"  │  沒檢測到任何類別 → NG（異常/缺失）")
            print(f"  └─────────────────────────────────────────┘")
            print(f"\n⚙️  建議配置:")
            print(f'  {{')
            print(f'    "model_path": "{model_path}",')
            print(f'    "detection_mode": "auto",')
            print(f'    "confidence_threshold": 0.5,')
            print(f'    "ng_classes": []  // 分類模型不需要這個')
            print(f'  }}')
            print(f"\n✅ 系統會自動識別為分類模型")
        
        elif is_defect:
            print(f"  ✓ 類型: 【缺陷檢測模型】Defect Detection")
            print(f"  ✓ 特徵: 包含缺陷類別 {defect_classes}")
            print(f"\n💡 判定邏輯:")
            print(f"  ┌─────────────────────────────────────────┐")
            print(f"  │  檢測到缺陷 → NG（不良品）")
            print(f"  │  沒檢測到缺陷 → OK（良品）")
            print(f"  └─────────────────────────────────────────┘")
            print(f"\n⚙️  建議配置:")
            print(f'  {{')
            print(f'    "model_path": "{model_path}",')
            print(f'    "detection_mode": "defect",')
            print(f'    "confidence_threshold": 0.5,')
            print(f'    "ng_classes": {defect_classes}')
            print(f'  }}')
        
        elif is_coco:
            print(f"  ✓ 類型: 【通用物體檢測】Object Detection (COCO)")
            print(f"  ✓ 特徵: COCO 80 類或類似（{len(coco_classes)} 個通用類別）")
            print(f"\n💡 判定邏輯:")
            print(f"  ┌─────────────────────────────────────────┐")
            print(f"  │  檢測到物體 → OK（產品存在）")
            print(f"  │  沒檢測到物體 → NG（產品缺失）")
            print(f"  └─────────────────────────────────────────┘")
            print(f"\n⚙️  建議配置:")
            print(f'  {{')
            print(f'    "model_path": "{model_path}",')
            print(f'    "detection_mode": "object",')
            print(f'    "confidence_threshold": 0.5,')
            print(f'    "ng_classes": []')
            print(f'  }}')
        
        else:
            print(f"  ⚠️  類型: 【自訓練模型】Custom Trained Model")
            print(f"  ⚠️  無法自動判定類型")
            print(f"\n💡 建議:")
            print(f"  • 如果訓練的是缺陷: 使用 'defect' 模式")
            print(f"  • 如果訓練的是產品: 使用 'object' 模式")
            print(f"  • 不確定時: 使用 'auto' 模式讓系統分析")
            print(f"\n⚙️  建議配置:")
            print(f'  {{')
            print(f'    "model_path": "{model_path}",')
            print(f'    "detection_mode": "auto",  // 或 "defect" / "object"')
            print(f'    "confidence_threshold": 0.5')
            print(f'  }}')
        
        # 測試推理
        print(f"\n🧪 測試推理:")
        print(f"  正在測試模型...")
        test_image_size = (640, 640, 3)
        import numpy as np
        test_image = np.random.randint(0, 255, test_image_size, dtype=np.uint8)
        
        try:
            results = model(test_image, verbose=False)
            print(f"  ✅ 推理成功 - 模型工作正常")
        except Exception as e:
            print(f"  ❌ 推理失敗: {e}")
        
        print("\n" + "=" * 80)
        
        # 返回判定結果
        return {
            'is_classification': is_classification,
            'is_defect': is_defect,
            'is_coco': is_coco,
            'ok_classes': ok_classes,
            'ng_classes': ng_classes,
            'defect_classes': defect_classes,
            'coco_classes': coco_classes
        }
        
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        return None


def compare_models(model_path_1, model_path_2):
    """比較兩個模型"""
    print("\n" + "=" * 80)
    print(" 🔄 模型比較工具")
    print("=" * 80)
    
    print(f"\n📌 分析模型 1: {Path(model_path_1).name}")
    result1 = diagnose_model(model_path_1)
    
    print(f"\n📌 分析模型 2: {Path(model_path_2).name}")
    result2 = diagnose_model(model_path_2)
    
    if result1 and result2:
        print("\n" + "=" * 80)
        print(" 📊 差異總結")
        print("=" * 80)
        
        print(f"\n【模型 1】{Path(model_path_1).name}")
        if result1['is_classification']:
            print(f"  類型: 分類模型 (Classification)")
            print(f"  OK 類別: {result1['ok_classes']}")
            print(f"  NG 類別: {result1['ng_classes']}")
            print(f"  判定: 根據檢測到的 OK/NG 類別直接判定")
        elif result1['is_defect']:
            print(f"  類型: 缺陷檢測 (Defect Detection)")
            print(f"  缺陷類別: {result1['defect_classes']}")
            print(f"  判定: 檢測到缺陷 = NG，沒檢測到 = OK")
        elif result1['is_coco']:
            print(f"  類型: COCO 通用物體檢測")
            print(f"  類別數: {len(result1['coco_classes'])}")
            print(f"  判定: 檢測到物體 = OK，沒檢測到 = NG")
        else:
            print(f"  類型: 自訓練模型（未明確分類）")
        
        print(f"\n【模型 2】{Path(model_path_2).name}")
        if result2['is_classification']:
            print(f"  類型: 分類模型 (Classification)")
            print(f"  OK 類別: {result2['ok_classes']}")
            print(f"  NG 類別: {result2['ng_classes']}")
            print(f"  判定: 根據檢測到的 OK/NG 類別直接判定")
        elif result2['is_defect']:
            print(f"  類型: 缺陷檢測 (Defect Detection)")
            print(f"  缺陷類別: {result2['defect_classes']}")
            print(f"  判定: 檢測到缺陷 = NG，沒檢測到 = OK")
        elif result2['is_coco']:
            print(f"  類型: COCO 通用物體檢測")
            print(f"  類別數: {len(result2['coco_classes'])}")
            print(f"  判定: 檢測到物體 = OK，沒檢測到 = NG")
        else:
            print(f"  類型: 自訓練模型（未明確分類）")
        
        # 關鍵差異
        print(f"\n【關鍵差異】")
        if result1['is_classification'] != result2['is_classification']:
            print(f"  ⚠️  注意: 兩個模型類型不同，判定邏輯完全不同！")
        
        print("\n" + "=" * 80)


def main():
    """主函數"""
    print("\n" + "=" * 80)
    print(" 🔬 YOLOv8 模型診斷工具")
    print(" 版本: 1.0")
    print(" 功能: 自動分析模型類型並給出配置建議")
    print("=" * 80)
    
    if len(sys.argv) == 2:
        # 單一模型診斷
        model_path = sys.argv[1]
        
        if not Path(model_path).exists():
            print(f"\n❌ 錯誤: 文件不存在 - {model_path}")
            print(f"\n請檢查文件路徑是否正確")
        else:
            diagnose_model(model_path)
    
    elif len(sys.argv) == 3:
        # 比較兩個模型
        model_path_1 = sys.argv[1]
        model_path_2 = sys.argv[2]
        
        if not Path(model_path_1).exists():
            print(f"\n❌ 錯誤: 模型 1 不存在 - {model_path_1}")
        elif not Path(model_path_2).exists():
            print(f"\n❌ 錯誤: 模型 2 不存在 - {model_path_2}")
        else:
            compare_models(model_path_1, model_path_2)
    
    else:
        # 顯示使用說明
        print("\n📖 使用方法:")
        print("\n  1. 診斷單一模型:")
        print("     python diagnose_model.py <模型路徑>")
        print("\n     範例:")
        print("     python diagnose_model.py models/YiDa.pt")
        print("     python diagnose_model.py models/yolov8n.pt")
        print("\n  2. 比較兩個模型:")
        print("     python diagnose_model.py <模型1路徑> <模型2路徑>")
        print("\n     範例:")
        print("     python diagnose_model.py models/yolov8n.pt models/YiDa.pt")
        print("\n" + "=" * 80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  用戶中斷")
    except Exception as e:
        print(f"\n❌ 程式錯誤: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n按 Enter 鍵退出...")
        input()