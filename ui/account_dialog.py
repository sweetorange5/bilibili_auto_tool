import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from core.account_manager import account_manager
from utils.cookie_handler import cookie_pool
from tkinter import messagebox

class AccountDialog(ttk.Toplevel):
    def __init__(self, parent, platform="bilibili", callback=None):
        super().__init__(parent)
        self.title("添加账号")
        self.geometry("500x400")
        self.resizable(False, False)
        self.platform = platform
        self.callback = callback
        
        self._center_window(parent)
        self._setup_ui()
        
        self.transient(parent)
        self.grab_set()

    def _center_window(self, parent):
        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (500 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (400 // 2)
        self.geometry(f"+{x}+{y}")

    def _setup_ui(self):
        container = ttk.Frame(self, padding=20)
        container.pack(fill=BOTH, expand=YES)

        # 平台显示
        ttk.Label(container, text="当前平台：", font=("Arial", 10)).grid(row=0, column=0, sticky=W, pady=5)
        ttk.Label(container, text=self.platform, font=("Arial", 10, "bold"), bootstyle="info").grid(row=0, column=1, sticky=W, pady=5)

        # 账号备注
        ttk.Label(container, text="账号备注：", font=("Arial", 10)).grid(row=1, column=0, sticky=W, pady=5)
        self.username_var = ttk.StringVar()
        ttk.Entry(container, textvariable=self.username_var, width=30).grid(row=1, column=1, sticky=W, pady=5)
        ttk.Label(container, text="（仅用于区分，非登录名）", font=("Arial", 8), bootstyle="secondary").grid(row=2, column=1, sticky=W)

        # Cookie输入
        ttk.Label(container, text="Cookie数据：", font=("Arial", 10)).grid(row=3, column=0, sticky=NW, pady=5)
        self.cookie_text = ttk.Text(container, height=10, width=40, font=("Consolas", 9))
        self.cookie_text.grid(row=3, column=1, sticky=W, pady=5)
        
        # 辅助功能区
        helper_frame = ttk.Frame(container)
        helper_frame.grid(row=4, column=1, sticky=W, pady=5)
        ttk.Button(helper_frame, text="🔗 浏览器登录获取Cookie", command=self._open_login_browser, style="info.Outline.TButton").pack(side=LEFT, padx=0)
        
        ttk.Label(container, text="使用上方按钮自动获取，登陆账号后按提示操作，添加账号时请耐心等待", font=("Arial", 8), bootstyle="secondary").grid(row=5, column=1, sticky=W)

        # 按钮区
        btn_frame = ttk.Frame(container)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=20)
        
        ttk.Button(btn_frame, text="保存账号", command=self._save_account, bootstyle="success").pack(side=LEFT, padx=10)
        ttk.Button(btn_frame, text="取消", command=self.destroy, bootstyle="secondary").pack(side=LEFT, padx=10)

    def _open_login_browser(self):
        """打开浏览器进行登录"""
        username = self.username_var.get().strip()
        if not username:
            from tkinter import messagebox
            messagebox.showwarning("提示", "请先输入账号备注（将作为配置文件名）")
            return
            
        from tkinter import messagebox
        if not messagebox.askyesno("确认", "即将打开浏览器，请在浏览器中手动登录账号。\n登录成功后，不要关闭浏览器，回到此窗口点击确认以获取Cookie。\n\n是否继续？"):
            return

        # 根据平台启动浏览器
        driver = None
        try:
            if self.platform == "bilibili":
                from platforms.bilibili import BilibiliPlatform
                driver = BilibiliPlatform.launch_for_login(username)
            else:
                return

            if not driver:
                messagebox.showerror("错误", "启动浏览器失败")
                return

            # 弹窗等待用户确认
            if messagebox.askokcancel("等待登录", "请在打开的浏览器中完成登录。\n\n登录完成后，点击【确定】自动抓取Cookie。\n点击【取消】放弃操作。"):
                # 获取Cookie
                cookies = driver.get_cookies()
                cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
                
                # 填充到文本框
                self.cookie_text.delete("1.0", "end")
                self.cookie_text.insert("1.0", cookie_str)
                messagebox.showinfo("成功", "Cookie已成功获取！")
            
            # 关闭浏览器
            driver.quit()
            
        except Exception as e:
            messagebox.showerror("错误", f"操作失败：{str(e)}")
            if driver:
                try:
                    driver.quit()
                except:
                    pass

    def _save_account(self):
        username = self.username_var.get().strip()
        cookie_str = self.cookie_text.get("1.0", "end-1c").strip()

        if not username:
            messagebox.showwarning("提示", "请输入账号备注！")
            return
        
        if not cookie_str:
            messagebox.showwarning("提示", "请输入Cookie数据！")
            return

        # 解析Cookie
        try:
            cookie_dict = self._parse_cookie(cookie_str)
        except Exception as e:
            messagebox.showerror("错误", f"Cookie格式解析失败：{str(e)}")
            return

        # 保存到文件
        try:
            # 1. 保存账号信息
            account_manager.add_account(self.platform, {"username": username})
            # 2. 保存Cookie
            cookie_pool.save_cookie(self.platform, username, cookie_dict)
            
            messagebox.showinfo("成功", f"账号 [{username}] 添加成功！")
            if self.callback:
                self.callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("错误", f"保存失败：{str(e)}")

    def _parse_cookie(self, cookie_str: str) -> dict:
        """解析Cookie字符串为字典"""
        cookie_dict = {}
        # 简单处理：按分号分割
        items = cookie_str.split(';')
        for item in items:
            if '=' in item:
                key, value = item.split('=', 1)
                cookie_dict[key.strip()] = value.strip()
        return cookie_dict
