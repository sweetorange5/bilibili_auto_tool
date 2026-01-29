import ttkbootstrap as ttk
from ttkbootstrap.constants import *


class StatusDisplay(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        # 平台名称
        self.platform = "bilibili"

        # 布局：状态信息+控制按钮
        self._setup_status()
        self._setup_buttons()

    def _setup_status(self):
        """状态信息展示"""
        status_frame = ttk.Frame(self)
        status_frame.pack(side=LEFT, fill=X, expand=YES)

        # 整体状态
        ttk.Label(status_frame, text="当前状态：", font=("Arial", 12)).grid(row=0, column=0, sticky=W, padx=5)
        self.status_var = ttk.StringVar(value="已停止")
        self.status_label = ttk.Label(
            status_frame, textvariable=self.status_var, font=("Arial", 12, "bold"),
            foreground="gray"
        )
        self.status_label.grid(row=0, column=1, sticky=W, padx=5)

        # 评论进度
        ttk.Label(status_frame, text="评论进度：", font=("Arial", 12)).grid(row=0, column=2, sticky=W, padx=20)
        self.comment_progress = ttk.Progressbar(status_frame, length=150, mode="determinate")
        self.comment_progress.grid(row=0, column=3, sticky=W, padx=5)
        self.comment_progress_var = ttk.StringVar(value="0/0")
        ttk.Label(status_frame, textvariable=self.comment_progress_var, font=("Arial", 11)).grid(row=0, column=4,
                                                                                                 padx=5)

        # 点赞进度
        ttk.Label(status_frame, text="点赞进度：", font=("Arial", 12)).grid(row=0, column=5, sticky=W, padx=20)
        self.like_progress = ttk.Progressbar(status_frame, length=150, mode="determinate")
        self.like_progress.grid(row=0, column=6, sticky=W, padx=5)
        self.like_progress_var = ttk.StringVar(value="0/0")
        ttk.Label(status_frame, textvariable=self.like_progress_var, font=("Arial", 11)).grid(row=0, column=7, padx=5)

    def _setup_buttons(self):
        """控制按钮"""
        btn_frame = ttk.Frame(self)
        btn_frame.pack(side=RIGHT, padx=20)

        self.start_btn = ttk.Button(btn_frame, text="启动", style="success.TButton", width=10)
        self.start_btn.pack(side=LEFT, padx=5)

        self.pause_btn = ttk.Button(btn_frame, text="暂停", style="warning.TButton", width=10)
        self.pause_btn.pack(side=LEFT, padx=5)

        self.stop_btn = ttk.Button(btn_frame, text="停止", style="danger.TButton", width=10)
        self.stop_btn.pack(side=LEFT, padx=5)

    def update_status(self, status: str, color: str):
        """更新整体状态"""
        self.status_var.set(status)
        self.status_label.config(foreground=color)

    def update_like_progress(self, percentage: float, text: str):
        """更新点赞进度"""
        self.like_progress_var.set(text)
        self.like_progress["value"] = percentage

    def update_comment_progress(self, percentage: float, text: str):
        """更新评论进度"""
        self.comment_progress_var.set(text)
        self.comment_progress["value"] = percentage

    def update_platform(self, platform: str):
        """更新平台名称"""
        self.platform = platform