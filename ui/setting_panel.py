import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinterdnd2 import DND_FILES, TkinterDnD
import os
from tkinter.filedialog import askopenfilename


class SettingPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.config_handler = None  # Will be set later or imported

        # Variables with default values
        self.url_var = ttk.StringVar()
        self.import_file_path_var = ttk.StringVar()
        self.send_mode_var = ttk.StringVar(value="order")
        self.interval_type_var = ttk.StringVar(value="random")
        self.fixed_interval_var = ttk.StringVar(value="10")
        self.random_min_var = ttk.StringVar(value="5")
        self.random_max_var = ttk.StringVar(value="15")
        self.comment_switch_var = ttk.IntVar(value=1)
        self.comment_duration_var = ttk.StringVar(value="60")  # 默认运行60分钟
        self.open_url_var = ttk.BooleanVar(value=False)

        self.like_interval_type_var = ttk.StringVar(value="random")
        self.like_fixed_interval_var = ttk.StringVar(value="10")
        self.like_random_min_var = ttk.StringVar(value="8")
        self.like_random_max_var = ttk.StringVar(value="12")
        self.like_limit_var = ttk.StringVar(value="100")
        self.like_switch_var = ttk.IntVar(value=1)
        self.like_duration_var = ttk.StringVar(value="60")  # 默认点赞运行60分钟
        
        # Load config immediately
        self._load_saved_settings()

        # 布局：左侧评论配置，右侧点赞配置
        self._setup_comment_setting()
        self._setup_like_setting()
        
        # Bind events for auto-save
        self._bind_save_events()

    def _load_saved_settings(self):
        """加载保存的配置"""
        from config.config_handler import ConfigHandler
        self.config_handler = ConfigHandler()
        settings = self.config_handler.get("ui_settings", {})
        
        if settings:
            self.url_var.set(settings.get("url", ""))
            self.import_file_path_var.set(settings.get("import_file", ""))
            self.send_mode_var.set(settings.get("send_mode", "order"))
            self.interval_type_var.set(settings.get("interval_type", "random"))
            self.fixed_interval_var.set(settings.get("fixed_interval", "10"))
            self.random_min_var.set(settings.get("random_interval_min", "5"))
            self.random_max_var.set(settings.get("random_interval_max", "15"))
            self.comment_switch_var.set(1 if settings.get("comment_enabled", True) else 0)
            self.comment_duration_var.set(settings.get("comment_duration", "60"))
            self.open_url_var.set(settings.get("open_url", False))
            
            self.like_interval_type_var.set(settings.get("like_interval_type", "random"))
            self.like_fixed_interval_var.set(settings.get("like_fixed_interval", "10"))
            self.like_random_min_var.set(settings.get("like_random_min", "8"))
            self.like_random_max_var.set(settings.get("like_random_max", "12"))
            self.like_limit_var.set(settings.get("like_limit", "100"))
            self.like_switch_var.set(1 if settings.get("like_enabled", True) else 0)
            self.like_duration_var.set(settings.get("like_duration", "60"))

    def _bind_save_events(self):
        """绑定变量修改事件以自动保存"""
        vars_to_trace = [
            self.url_var, self.import_file_path_var, self.send_mode_var,
      self.interval_type_var, self.fixed_interval_var, self.random_min_var,
            self.random_max_var, self.comment_switch_var, self.comment_duration_var,
            self.open_url_var,
            self.like_interval_type_var, self.like_fixed_interval_var,
            self.like_random_min_var, self.like_random_max_var, self.like_limit_var,
            self.like_switch_var, self.like_duration_var
        ]
        for var in vars_to_trace:
            var.trace_add("write", self._auto_save_settings)
            
        # Text widget needs special handling, bound in _setup_comment_setting

    def _auto_save_settings(self, *args):
        """自动保存配置"""
        if self.config_handler:
            settings = self.get_settings()
            self.config_handler.set("ui_settings", settings)


    def _setup_comment_setting(self):
        """评论配置区域"""
        comment_frame = ttk.LabelFrame(self, text="评论/弹幕配置", padding=10)
        comment_frame.pack(side=LEFT, fill=BOTH, expand=YES, padx=5, pady=5)

        # 目标URL输入
        ttk.Label(comment_frame, text="目标URL：", font=("Arial", 11)).grid(row=0, column=0, sticky=W, pady=3)
        
        # URL输入框和复选框的容器
        url_container = ttk.Frame(comment_frame)
        url_container.grid(row=0, column=1, columnspan=2, sticky=EW, pady=3)
        
        self.url_entry = ttk.Entry(url_container, textvariable=self.url_var, font=("Arial", 10))
        self.url_entry.pack(side=LEFT, fill=X, expand=YES, padx=(5, 5))
        
        # 是否打开网页 Checkbutton
        ttk.Checkbutton(url_container, text="同时打开网页", variable=self.open_url_var).pack(side=LEFT, padx=5)

        # 评论内容输入
        ttk.Label(comment_frame, text="自定义评论：", font=("Arial", 11)).grid(row=1, column=0, sticky=W, pady=3)
        self.comment_text = ttk.Text(comment_frame, width=40, height=5, font=("Arial", 10))
        self.comment_text.grid(row=1, column=1, columnspan=2, pady=3, padx=5)
        # Load saved comment text
        if self.config_handler:
            saved_content = self.config_handler.get("ui_settings", {}).get("comment_content", "")
            if saved_content:
                self.comment_text.insert("1.0", saved_content)
        # Bind focus out to save text
        self.comment_text.bind("<FocusOut>", self._auto_save_settings)
        
        # 清空按钮 (New Feature)
        ttk.Button(comment_frame, text="清空", command=self._clear_comment_text, style="warning.Outline.TButton", width=4).grid(row=1, column=3, sticky=W, padx=2)

        # 导入文件
        ttk.Label(comment_frame, text="导入评论文件：", font=("Arial", 11)).grid(row=2, column=0, sticky=W, pady=3)
        self.file_entry = ttk.Entry(comment_frame, textvariable=self.import_file_path_var, width=30, font=("Arial", 10))
        self.file_entry.grid(row=2, column=1, pady=3, padx=5)
        ttk.Button(comment_frame, text="选择文件", command=self._select_file, style="secondary.TButton").grid(row=2,
                                                                                                              column=2,
                                                                                                              pady=3,
                                                                                                              padx=5)

        # 发送模式（顺序/随机）
        ttk.Label(comment_frame, text="发送模式：", font=("Arial", 11)).grid(row=3, column=0, sticky=W, pady=3)
        self.order_radio = ttk.Radiobutton(comment_frame, text="顺序发送", variable=self.send_mode_var, value="order")
        self.order_radio.grid(row=3, column=1, sticky=W, pady=3)
        self.random_radio = ttk.Radiobutton(comment_frame, text="随机发送", variable=self.send_mode_var, value="random")
        self.random_radio.grid(row=3, column=2, sticky=W, pady=3)

        # 间隔配置
        ttk.Label(comment_frame, text="发送间隔：", font=("Arial", 11)).grid(row=4, column=0, sticky=W, pady=3)
        self.fixed_radio = ttk.Radiobutton(comment_frame, text="固定间隔", variable=self.interval_type_var, value="fixed")
        self.fixed_radio.grid(row=4, column=1, sticky=W, pady=3)
        self.fixed_interval_entry = ttk.Entry(comment_frame, textvariable=self.fixed_interval_var, width=10, font=("Arial", 10))
        self.fixed_interval_entry.grid(row=4, column=1, padx=(80, 0), pady=3)
        ttk.Label(comment_frame, text="秒/条").grid(row=4, column=1, padx=(150, 0), pady=3)

        self.random_radio_interval = ttk.Radiobutton(comment_frame, text="随机间隔", variable=self.interval_type_var, value="random")
        self.random_radio_interval.grid(row=4, column=2, sticky=W, pady=3)
        self.random_min_entry = ttk.Entry(comment_frame, textvariable=self.random_min_var, width=8, font=("Arial", 10))
        self.random_min_entry.grid(row=4, column=2, padx=(80, 0), pady=3)
        ttk.Label(comment_frame, text="-").grid(row=4, column=2, padx=(130, 0), pady=3)
        self.random_max_entry = ttk.Entry(comment_frame, textvariable=self.random_max_var, width=8, font=("Arial", 10))
        self.random_max_entry.grid(row=4, column=2, padx=(150, 0), pady=3)

        # 评论功能开关
        self.comment_switch = ttk.Checkbutton(comment_frame, text="启用评论发送", variable=self.comment_switch_var, onvalue=1, offvalue=0, bootstyle="success")
        self.comment_switch.grid(row=5, column=1, pady=5, sticky=W)
        
        # 运行时间配置
        time_frame = ttk.Frame(comment_frame)
        time_frame.grid(row=5, column=2, sticky=W)
        ttk.Label(time_frame, text="运行时长：").pack(side=LEFT)
        ttk.Entry(time_frame, textvariable=self.comment_duration_var, width=5).pack(side=LEFT, padx=2)
        ttk.Label(time_frame, text="分钟 (共用)").pack(side=LEFT)

    def _setup_like_setting(self):
        """点赞配置区域"""
        like_frame = ttk.LabelFrame(self, text="点赞配置", padding=10)
        like_frame.pack(side=RIGHT, fill=BOTH, expand=YES, padx=5, pady=5)

        # 点赞间隔配置
        ttk.Label(like_frame, text="点赞间隔：", font=("Arial", 11)).grid(row=0, column=0, sticky=W, pady=3)
        self.like_fixed_radio = ttk.Radiobutton(like_frame, text="固定间隔", variable=self.like_interval_type_var, value="fixed")
        self.like_fixed_radio.grid(row=0, column=1, sticky=W, pady=3)
        self.like_fixed_entry = ttk.Entry(like_frame, textvariable=self.like_fixed_interval_var, width=10, font=("Arial", 10))
        self.like_fixed_entry.grid(row=0, column=1, padx=(80, 0), pady=3)
        ttk.Label(like_frame, text="秒/次").grid(row=0, column=1, padx=(150, 0), pady=3)

        self.like_random_radio = ttk.Radiobutton(like_frame, text="随机间隔", variable=self.like_interval_type_var, value="random")
        self.like_random_radio.grid(row=0, column=2, sticky=W, pady=3)
        self.like_random_min_entry = ttk.Entry(like_frame, textvariable=self.like_random_min_var, width=8, font=("Arial", 10))
        self.like_random_min_entry.grid(row=0, column=2, padx=(80, 0), pady=3)
        ttk.Label(like_frame, text="-").grid(row=0, column=2, padx=(130, 0), pady=3)
        self.like_random_max_entry = ttk.Entry(like_frame, textvariable=self.like_random_max_var, width=8, font=("Arial", 10))
        self.like_random_max_entry.grid(row=0, column=2, padx=(150, 0), pady=3)

        # 点赞上限配置
        ttk.Label(like_frame, text="期望点赞数量：", font=("Arial", 11)).grid(row=1, column=0, sticky=W, pady=3)
        self.like_limit_entry = ttk.Entry(like_frame, textvariable=self.like_limit_var, width=10, font=("Arial", 10))
        self.like_limit_entry.grid(row=1, column=1, pady=3, padx=5)
        ttk.Label(like_frame, text="次").grid(row=1, column=2, pady=3, padx=5)

        # 点赞功能开关
        self.like_switch = ttk.Checkbutton(like_frame, text="启用自动点赞", variable=self.like_switch_var, onvalue=1, offvalue=0, bootstyle="success")
        self.like_switch.grid(row=2, column=1, pady=5, sticky=W)


    def _clear_comment_text(self):
        """清空评论内容"""
        self.comment_text.delete("1.0", "end")
        self._auto_save_settings()

    def _select_file(self):
        """选择导入文件（txt/Excel/Word）"""
        file_types = [
            ("文本文件", "*.txt"),
            ("Excel文件", "*.xlsx;*.xls"),
            ("Word文件", "*.docx;*.doc"),
            ("所有文件", "*.*")
        ]
        file_path = askopenfilename(title="选择评论文件", filetypes=file_types)
        if file_path:
            self.import_file_path_var.set(file_path)

    def get_settings(self):
        """获取所有配置"""
        settings = {
            "url": self.url_var.get().strip(),
            "import_file": self.import_file_path_var.get().strip(),
            "send_mode": self.send_mode_var.get(),
            "interval_type": self.interval_type_var.get(),
            "fixed_interval": self.fixed_interval_var.get(),
            "random_interval_min": self.random_min_var.get(),
            "random_interval_max": self.random_max_var.get(),
            "comment_enabled": self.comment_switch_var.get() == 1,
            "comment_duration": self.comment_duration_var.get(),
            "comment_content": self.comment_text.get("1.0", "end-1c"),
            "open_url": self.open_url_var.get(),
            
            "like_interval_type": self.like_interval_type_var.get(),
            "like_fixed_interval": self.like_fixed_interval_var.get(),
            "like_random_min": self.like_random_min_var.get(),
            "like_random_max": self.like_random_max_var.get(),
            "like_limit": self.like_limit_var.get(),
            "like_enabled": self.like_switch_var.get() == 1,
            # 点赞不再有独立时长，使用评论时长作为全局时长
            "like_duration": self.comment_duration_var.get()
        }
        return settings
