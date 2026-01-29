import ttkbootstrap as ttk
from ttkbootstrap.constants import *

class NewUserGuide(ttk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("新手引导")
        self.geometry("600x400")
        self.resizable(False, False)
        
        # 居中显示
        self._center_window(parent)
        
        self._setup_ui()
        
        # 模态
        self.transient(parent)
        self.grab_set()
        self.wait_window()

    def _center_window(self, parent):
        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (600 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (400 // 2)
        self.geometry(f"+{x}+{y}")

    def _setup_ui(self):
        container = ttk.Frame(self, padding=20)
        container.pack(fill=BOTH, expand=YES)
        
        # 标题
        ttk.Label(
            container, 
            text="欢迎使用全自动氛围神器", 
            font=("Arial", 18, "bold"),
            bootstyle="primary"
        ).pack(pady=(0, 20))
        
        # 说明内容
        info_text = (
            "本工具支持多平台自动互动。\n\n"
            "1. 在顶部选择目标平台（B站/抖音/快手）。\n"
            "2. 导入账号并检查状态。\n"
            "3. 设置互动参数（点赞/评论）。\n"
            "4. 点击开始运行。\n\n"
            "注意：请遵守各平台规范，合理使用。"
        )
        
        ttk.Label(
            container,
            text=info_text,
            font=("Arial", 11),
            justify=LEFT,
            wraplength=550
        ).pack(fill=X, expand=YES)
        
        # 按钮
        ttk.Button(
            container,
            text="开始使用",
            command=self.destroy,
            bootstyle="success-outline",
            width=20
        ).pack(pady=20)
