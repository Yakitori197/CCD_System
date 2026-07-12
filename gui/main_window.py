# -*- coding: utf-8 -*-
"""
GUI 主視窗 - 支援分類模型顯示
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from typing import Optional
import threading
import queue
import cv2
from PIL import Image, ImageTk
import numpy as np

from models.data_models import SystemConfig, ProductRecord
from core.engine import InspectionEngine
from utils.config import ConfigManager
from utils.logger import get_logger


class MainWindow:
    """主視窗"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("CCD 視覺檢測與自動剔除系統 v1.2")
        self.root.geometry("1400x900")
        
        # 初始化
        self.logger = get_logger()
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load()
        
        self.engine: Optional[InspectionEngine] = None
        self.is_running = False
        self.update_timer = None
        
        # 預覽相關
        self.preview_image = None
        self.preview_update_flag = True
        
        # 建立 UI
        self.setup_ui()
        
        self.logger.info("GUI 初始化完成")
    
    def setup_ui(self):
        """建立使用者介面"""
        # 頂部控制列
        self._create_control_bar()
        
        # 主內容區
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 左側：即時預覽
        self._create_preview_panel(main_frame)
        
        # 右側：控制與統計
        self._create_info_panel(main_frame)
        
        # 底部狀態列
        self._create_status_bar()
    
    def _create_control_bar(self):
        """建立控制列"""
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(top_frame, text="載入模型", command=self.load_model).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="開啟相機", command=self.open_camera).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="單次檢測", command=self.single_detect).pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(top_frame, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        self.start_btn = ttk.Button(top_frame, text="開始連續檢測", command=self.start_continuous)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(top_frame, text="停止檢測", command=self.stop_continuous, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(top_frame, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        self.rejection_var = tk.BooleanVar(value=self.config.rejection.enabled)
        ttk.Checkbutton(
            top_frame,
            text="啟用剔除功能",
            variable=self.rejection_var,
            command=self.toggle_rejection
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(top_frame, text="重置統計", command=self.reset_stats).pack(side=tk.LEFT, padx=5)
    
    def _create_preview_panel(self, parent):
        """建立預覽面板"""
        left_frame = ttk.LabelFrame(parent, text="即時預覽")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # 創建 Canvas 用於顯示圖像
        self.preview_canvas = tk.Canvas(left_frame, bg='black')
        self.preview_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 在 Canvas 上顯示提示文字
        self.preview_text_id = self.preview_canvas.create_text(
            400, 300,
            text="未開啟相機\n\n請點擊「開啟相機」按鈕",
            fill="white",
            font=("Arial", 16),
            justify="center"
        )
    
    def _create_info_panel(self, parent):
        """建立資訊面板"""
        right_frame = ttk.Frame(parent)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        
        # ==================== 檢測模式控制 ====================
        mode_frame = ttk.LabelFrame(right_frame, text="🔄 檢測模式")
        mode_frame.pack(fill=tk.X, pady=5)
        
        # 當前模式顯示
        current_mode_frame = ttk.Frame(mode_frame)
        current_mode_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(current_mode_frame, text="當前模式:", font=("Arial", 9, "bold")).pack(side=tk.LEFT)
        self.mode_display_label = ttk.Label(
            current_mode_frame, 
            text="未載入", 
            font=("Arial", 9),
            foreground="gray"
        )
        self.mode_display_label.pack(side=tk.LEFT, padx=5)
        
        # 置信度顯示
        self.confidence_label = ttk.Label(
            current_mode_frame,
            text="",
            font=("Arial", 8),
            foreground="blue"
        )
        self.confidence_label.pack(side=tk.LEFT)
        
        # 模式說明
        self.mode_desc_label = ttk.Label(
            mode_frame,
            text="",
            font=("Arial", 8),
            foreground="gray",
            wraplength=280
        )
        self.mode_desc_label.pack(padx=10, pady=(0, 5))
        
        # 手動切換按鈕
        switch_frame = ttk.Frame(mode_frame)
        switch_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(switch_frame, text="手動切換:").pack(side=tk.LEFT)
        
        self.mode_var = tk.StringVar(value="auto")
        
        self.auto_radio = ttk.Radiobutton(
            switch_frame,
            text="Auto",
            variable=self.mode_var,
            value="auto",
            command=self.switch_mode
        )
        self.auto_radio.pack(side=tk.LEFT, padx=5)
        
        self.defect_radio = ttk.Radiobutton(
            switch_frame,
            text="Defect",
            variable=self.mode_var,
            value="defect",
            command=self.switch_mode
        )
        self.defect_radio.pack(side=tk.LEFT, padx=5)
        
        self.object_radio = ttk.Radiobutton(
            switch_frame,
            text="Object",
            variable=self.mode_var,
            value="object",
            command=self.switch_mode
        )
        self.object_radio.pack(side=tk.LEFT, padx=5)
        
        # 初始設定為禁用（模型載入後啟用）
        self.auto_radio.config(state=tk.DISABLED)
        self.defect_radio.config(state=tk.DISABLED)
        self.object_radio.config(state=tk.DISABLED)
        
        # 模式說明按鈕
        help_btn = ttk.Button(
            mode_frame,
            text="❓ 模式說明",
            command=self.show_mode_help,
            width=15
        )
        help_btn.pack(pady=5)
        
        # ==================== 檢測參數 ====================
        param_frame = ttk.LabelFrame(right_frame, text="檢測參數")
        param_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(param_frame, text="置信度閾值:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.conf_var = tk.DoubleVar(value=self.config.detector.confidence_threshold)
        conf_scale = ttk.Scale(
            param_frame,
            from_=0.1,
            to=0.9,
            variable=self.conf_var,
            orient=tk.HORIZONTAL,
            length=200
        )
        conf_scale.grid(row=0, column=1, padx=5, pady=5)
        self.conf_label = ttk.Label(param_frame, text=f"{self.conf_var.get():.2f}")
        self.conf_label.grid(row=0, column=2, padx=5)
        self.conf_var.trace('w', self.update_conf_label)
        
        ttk.Label(param_frame, text="剔除延遲(ms):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.delay_var = tk.IntVar(value=self.config.rejection.delay_ms)
        ttk.Spinbox(
            param_frame,
            from_=0,
            to=5000,
            textvariable=self.delay_var,
            width=10
        ).grid(row=1, column=1, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # ==================== 統計資訊 ====================
        stats_frame = ttk.LabelFrame(right_frame, text="生產統計")
        stats_frame.pack(fill=tk.X, pady=5)
        
        self.total_label = ttk.Label(stats_frame, text="總檢數: 0", font=("Arial", 10))
        self.total_label.pack(anchor=tk.W, padx=10, pady=2)
        
        self.ok_label = ttk.Label(stats_frame, text="良品數: 0", font=("Arial", 10), foreground="green")
        self.ok_label.pack(anchor=tk.W, padx=10, pady=2)
        
        self.ng_label = ttk.Label(stats_frame, text="不良品: 0", font=("Arial", 10), foreground="red")
        self.ng_label.pack(anchor=tk.W, padx=10, pady=2)
        
        self.reject_label = ttk.Label(stats_frame, text="已剔除: 0", font=("Arial", 10), foreground="orange")
        self.reject_label.pack(anchor=tk.W, padx=10, pady=2)
        
        self.yield_label = ttk.Label(stats_frame, text="良率: 0.00%", font=("Arial", 12, "bold"))
        self.yield_label.pack(anchor=tk.W, padx=10, pady=5)
        
        # ==================== 最新檢測結果 ====================
        result_frame = ttk.LabelFrame(right_frame, text="最新檢測")
        result_frame.pack(fill=tk.X, pady=5)
        
        self.result_text = tk.Text(result_frame, height=6, width=35)
        self.result_text.pack(padx=5, pady=5)
        
        # ==================== 系統日誌 ====================
        log_frame = ttk.LabelFrame(right_frame, text="系統日誌")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = tk.Text(log_frame, height=8, width=35)
        log_scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.config(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=5)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5, padx=(0, 5))
    
    def _create_status_bar(self):
        """建立狀態列"""
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.status_label = ttk.Label(status_frame, text="系統就緒", foreground="blue")
        self.status_label.pack(side=tk.LEFT)
        
        self.model_label = ttk.Label(status_frame, text="未載入模型", foreground="gray")
        self.model_label.pack(side=tk.RIGHT)
    
    # ==================== 預覽更新 ====================
    
    def update_preview(self):
        """更新相機預覽"""
        if not self.engine or not self.engine.camera:
            return
        
        try:
            frame = self.engine.camera.get_last_frame()
            
            if frame is not None:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                canvas_width = self.preview_canvas.winfo_width()
                canvas_height = self.preview_canvas.winfo_height()
                
                if canvas_width > 1 and canvas_height > 1:
                    h, w = frame_rgb.shape[:2]
                    scale = min(canvas_width / w, canvas_height / h)
                    new_w = int(w * scale)
                    new_h = int(h * scale)
                    
                    frame_resized = cv2.resize(frame_rgb, (new_w, new_h))
                    
                    image = Image.fromarray(frame_resized)
                    photo = ImageTk.PhotoImage(image)
                    
                    self.preview_canvas.delete("all")
                    self.preview_canvas.create_image(
                        canvas_width // 2,
                        canvas_height // 2,
                        image=photo,
                        anchor="center"
                    )
                    
                    self.preview_image = photo
        
        except Exception as e:
            self.logger.error(f"更新預覽失敗: {e}")
        
        finally:
            if self.preview_update_flag:
                self.root.after(30, self.update_preview)
    
    # ==================== 模式切換 ====================
    
    def switch_mode(self):
        """切換檢測模式"""
        if not self.engine or not self.engine.detector:
            messagebox.showwarning("警告", "請先載入模型")
            return
        
        new_mode = self.mode_var.get()
        old_mode = self.engine.detector.config.detection_mode
        
        if new_mode == old_mode:
            return
        
        # 確認切換
        mode_names = {
            "auto": "自動識別",
            "defect": "缺陷檢測（檢測到=NG）",
            "object": "物體檢測（檢測到=OK）"
        }
        
        if messagebox.askyesno(
            "確認切換模式",
            f"確定要切換到 {mode_names[new_mode]} 模式嗎？\n\n"
            f"當前模式: {mode_names.get(old_mode, old_mode)}"
        ):
            # 更新配置
            self.engine.detector.config.detection_mode = new_mode
            self.config.detector.detection_mode = new_mode
            
            # 重新載入模型以觸發分析
            self.logger.info(f"切換檢測模式: {old_mode} → {new_mode}")
            self.engine.detector.load_model()
            
            # 更新顯示
            self.update_mode_display()
            
            self.log(f"模式已切換: {mode_names[new_mode]}")
        else:
            # 取消切換，恢復原值
            self.mode_var.set(old_mode)
    
    def update_mode_display(self):
        """更新模式顯示 - 支援分類模型"""
        if not self.engine or not self.engine.detector:
            return
        
        try:
            mode_info = self.engine.detector.get_mode_info()
            
            actual_mode = mode_info['actual_mode']
            confidence = mode_info['confidence']
            is_auto = mode_info['is_auto']
            is_classification = mode_info.get('is_classification', False)
            
            # 更新主顯示
            if is_classification:
                # 分類模型特殊顯示
                mode_text = "CLASSIFICATION"
                mode_color = "purple"
            else:
                mode_text = actual_mode.upper() if actual_mode else "未知"
                mode_color = "green" if actual_mode == "defect" else "blue"
            
            self.mode_display_label.config(
                text=mode_text,
                foreground=mode_color
            )
            
            # 更新置信度
            if is_classification:
                # 分類模型不顯示置信度（永遠是100%）
                self.confidence_label.config(text="")
            elif is_auto and confidence > 0:
                conf_text = f"(置信度: {confidence:.0f}%)"
                conf_color = "green" if confidence > 70 else "orange" if confidence > 50 else "red"
                self.confidence_label.config(
                    text=conf_text,
                    foreground=conf_color
                )
            else:
                self.confidence_label.config(text="")
            
            # 更新說明
            if is_classification:
                ok_classes = mode_info.get('ok_classes', [])
                ng_classes = mode_info.get('ng_classes', [])
                desc = f"檢測到 {ng_classes} = NG，檢測到 {ok_classes} = OK，沒檢測到 = NG"
            elif actual_mode == "defect":
                desc = "檢測到 = NG（缺陷），沒檢測到 = OK（良品）"
            elif actual_mode == "object":
                desc = "檢測到 = OK（產品），沒檢測到 = NG（異常）"
            else:
                desc = ""
            
            self.mode_desc_label.config(text=desc)
            
            # 同步單選按鈕
            configured_mode = mode_info['configured_mode']
            self.mode_var.set(configured_mode)
            
        except Exception as e:
            self.logger.error(f"更新模式顯示失敗: {e}")
    
    def show_mode_help(self):
        """顯示模式說明"""
        help_text = """
檢測模式說明

【Auto - 自動識別】
系統自動分析模型類型並設定判定邏輯。
• 分析文件名關鍵字
• 分析訓練的類別名稱
• 分析類別數量
推薦用於不確定模型類型時。

【Defect - 缺陷檢測】
適用於訓練了產品缺陷的模型。
• 檢測到缺陷 → NG（不良品）
• 沒檢測到 → OK（良品）
例如：劃痕、裂紋、污點檢測。

【Object - 物體檢測】
適用於訓練了正常產品的模型。
• 檢測到產品 → OK（良品）
• 沒檢測到 → NG（異常）
例如：完整產品、組裝件檢測。

【Classification - 分類模型】（自動識別）
系統自動識別包含 OK/NG 類別的模型。
• 檢測到 NG 類別 → NG（不良品）
• 檢測到 OK 類別 → OK（良品）
• 沒檢測到 → NG（異常/缺失）
例如：YiDa.pt 模型（類別 0:NG, 1:OK）

提示：
• 首次使用建議選擇 Auto
• 如果自動識別不準確，手動切換
• 切換後需重新檢測驗證
        """
        
        messagebox.showinfo("檢測模式說明", help_text)
    
    # ==================== 事件處理 ====================
    
    def update_conf_label(self, *args):
        """更新置信度標籤"""
        self.conf_label.config(text=f"{self.conf_var.get():.2f}")
    
    def load_model(self):
        """載入模型"""
        model_path = filedialog.askopenfilename(
            title="選擇 YOLO 模型",
            initialdir="./models",
            filetypes=[("PyTorch Model", "*.pt"), ("All Files", "*.*")]
        )
        
        if not model_path:
            return
        
        self.config.detector.model_path = model_path
        self.model_label.config(text=f"模型: {Path(model_path).name}", foreground="green")
        self.log(f"已選擇模型: {Path(model_path).name}")
    
    def open_camera(self):
        """開啟相機"""
        if not self.config.detector.model_path:
            messagebox.showwarning("警告", "請先載入模型")
            return
        
        if self.engine:
            messagebox.showinfo("提示", "系統已初始化")
            return
        
        # 更新配置
        self.config.detector.confidence_threshold = self.conf_var.get()
        self.config.rejection.enabled = self.rejection_var.get()
        self.config.rejection.delay_ms = self.delay_var.get()
        
        # 初始化引擎
        self.engine = InspectionEngine(self.config)
        
        self.status_label.config(text="初始化中...", foreground="orange")
        self.root.update()
        
        # 在後台線程初始化
        def init_thread():
            if self.engine.initialize():
                self.root.after(0, self._on_init_success)
            else:
                self.root.after(0, self._on_init_failure)
        
        threading.Thread(target=init_thread, daemon=True).start()
    
    def _on_init_success(self):
        """初始化成功回調"""
        self.status_label.config(text="相機已開啟", foreground="green")
        self.log("系統初始化完成")
        
        # 清除提示文字
        self.preview_canvas.delete(self.preview_text_id)
        
        # 啟用模式切換按鈕
        self.auto_radio.config(state=tk.NORMAL)
        self.defect_radio.config(state=tk.NORMAL)
        self.object_radio.config(state=tk.NORMAL)
        
        # 更新模式顯示
        self.update_mode_display()
        
        # 開始預覽更新
        self.preview_update_flag = True
        self.update_preview()
        
        messagebox.showinfo("成功", "相機已開啟，可以開始檢測")
    
    def _on_init_failure(self):
        """初始化失敗回調"""
        self.status_label.config(text="初始化失敗", foreground="red")
        self.log("系統初始化失敗")
        messagebox.showerror("錯誤", "初始化失敗，請檢查日誌")
        self.engine = None
    
    def single_detect(self):
        """單次檢測（推理在背景執行緒，不凍結 UI）"""
        if not self.engine:
            messagebox.showwarning("警告", "請先開啟相機")
            return

        def worker():
            record = self.engine.process_single()
            if record:
                self.root.after(0, lambda: (
                    self.update_result_display(record),
                    self.update_statistics()
                ))

        threading.Thread(target=worker, daemon=True).start()
    
    def start_continuous(self):
        """開始連續檢測"""
        if not self.engine:
            messagebox.showwarning("警告", "請先開啟相機")
            return
        
        self.is_running = True
        self.engine.start_continuous()
        
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="連續檢測中...", foreground="orange")
        
        # 禁用模式切換
        self.auto_radio.config(state=tk.DISABLED)
        self.defect_radio.config(state=tk.DISABLED)
        self.object_radio.config(state=tk.DISABLED)
        
        self.log("開始連續檢測")
        self.poll_results()

    def poll_results(self):
        """
        輪詢檢測結果（v1.2）：
        推理由引擎的 worker thread 執行，這裡只從 result_queue 取結果更新 UI，
        主執行緒不再被推理阻塞。
        """
        if not self.is_running:
            return

        try:
            while True:
                record = self.engine.result_queue.get_nowait()
                self.update_result_display(record)
                self.update_statistics()
        except queue.Empty:
            pass  # 本輪沒有新結果

        self.update_timer = self.root.after(100, self.poll_results)
    
    def stop_continuous(self):
        """停止連續檢測"""
        self.is_running = False
        
        if self.update_timer:
            self.root.after_cancel(self.update_timer)
        
        if self.engine:
            self.engine.stop()
        
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="檢測已停止", foreground="blue")
        
        # 重新啟用模式切換
        self.auto_radio.config(state=tk.NORMAL)
        self.defect_radio.config(state=tk.NORMAL)
        self.object_radio.config(state=tk.NORMAL)
        
        self.log("停止連續檢測")
    
    def toggle_rejection(self):
        """切換剔除功能"""
        enabled = self.rejection_var.get()
        self.config.rejection.enabled = enabled
        
        if self.engine:
            self.engine.config.rejection.enabled = enabled
        
        self.log(f"剔除功能: {'啟用' if enabled else '停用'}")
    
    def reset_stats(self):
        """重置統計"""
        if self.is_running:
            messagebox.showwarning("警告", "請先停止檢測")
            return
        
        if messagebox.askyesno("確認", "確定要重置統計數據嗎？"):
            if self.engine:
                self.engine.reset_statistics()
            
            self.update_statistics()
            self.log("統計已重置")
    
    def update_result_display(self, record: ProductRecord):
        """更新檢測結果顯示"""
        result_text = f"""產品 ID: #{record.product_id:06d}
時間: {record.timestamp}
判定: {record.judgment}
置信度: {record.confidence:.3f}
處理時間: {record.processing_time:.1f} ms
"""
        
        if record.defect_classes:
            result_text += f"檢測類別: {', '.join(record.defect_classes)}\n"
        
        if record.rejection_sent:
            result_text += "剔除狀態: 已發送\n"
        
        self.result_text.delete('1.0', tk.END)
        self.result_text.insert('1.0', result_text)
        
        self.log(
            f"#{record.product_id:06d} | {record.judgment} | "
            f"{record.confidence:.2f} | {record.processing_time:.0f}ms"
        )
    
    def update_statistics(self):
        """更新統計數據"""
        if not self.engine:
            return
        
        stats = self.engine.get_statistics()
        
        self.total_label.config(text=f"總檢數: {stats['total']}")
        self.ok_label.config(text=f"良品數: {stats['ok']}")
        self.ng_label.config(text=f"不良品: {stats['ng']}")
        self.reject_label.config(text=f"已剔除: {stats['rejection']}")
        self.yield_label.config(text=f"良率: {stats['yield_rate']}")
    
    def log(self, message: str):
        """記錄日誌"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        
        # 限制日誌行數
        lines = int(self.log_text.index('end-1c').split('.')[0])
        if lines > 1000:
            self.log_text.delete('1.0', '500.0')
    
    def on_closing(self):
        """關閉視窗"""
        if self.is_running:
            if not messagebox.askyesno("確認", "檢測正在運行，確定要關閉嗎？"):
                return
            self.stop_continuous()
        
        # 停止預覽更新
        self.preview_update_flag = False
        
        if self.engine:
            self.engine.shutdown()
        
        self.logger.info("GUI 關閉")
        self.root.destroy()
    
    def run(self):
        """運行 GUI"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()