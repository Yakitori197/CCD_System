# -*- coding: utf-8 -*-
"""
快速檢查模型信息
"""

from ultralytics import YOLO
from pathlib import Path

def check_model(model_path):
    """檢查模型信息"""
    print("\n" + "=" * 60)
    print(f" 檢查模型: {Path(model_path).name}")
    print("=" * 60)
    
    try:
        # 載入模型
        model = YOLO(model_path)
        
        print(f"\n✓ 模型載入成功")
        print(f"\n類別信息:")
        print(f"  類別數量: {len(model.names)}")
        print(f"  類別列表:")
        
        for idx, name in model.names.items():
            print(f"    {idx}: {name}")
        
        print(f"\n建議配置:")
        
        # 簡單判斷
        class_names = list(model.names.values())
        
        # 檢查是否有缺陷關鍵字
        defect_keywords = [
            'defect', 'scratch', 'crack', 'stain', 'damage', 
            'broken', 'ng', 'bad', 'fault', 'error',
            '瑕疵', '缺陷', '劃痕', '裂紋', '污點', '破損', '不良'
        ]
        
        has_defect = False
        defect_classes = []
        
        for cls_name in class_names:
            cls_lower = str(cls_name).lower()
            for keyword in defect_keywords:
                if keyword in cls_lower:
                    has_defect = True
                    defect_classes.append(cls_name)
                    break
        
        print()
        if has_defect:
            print("  🔴 這是缺陷檢測模型")
            print(f"  🔴 檢測到缺陷類別: {defect_classes}")
            print()
            print('  建議配置 config.json:')
            print('  {')
            print(f'    "model_path": "{model_path}",')
            print('    "detection_mode": "defect"')
            print('  }')
            print()
            print("  判定邏輯:")
            print("    檢測到瑕疵 → NG ❌")
            print("    沒檢測到 → OK ✅")
        else:
            print("  🔵 可能是物體檢測模型")
            print()
            print('  建議配置 config.json:')
            print('  {')
            print(f'    "model_path": "{model_path}",')
            print('    "detection_mode": "object"')
            print('  }')
            print()
            print("  判定邏輯:")
            print("    檢測到產品 → OK ✅")
            print("    沒檢測到 → NG ❌")
        
        print()
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        model_path = sys.argv[1]
    else:
        print("\n請輸入模型路徑:")
        model_path = input("模型路徑: ").strip()
        
        if not model_path:
            model_path = "./models/YiDa.pt"
    
    if not Path(model_path).exists():
        print(f"\n❌ 文件不存在: {model_path}")
    else:
        check_model(model_path)
    
    print("\n按 Enter 鍵退出...")
    input()