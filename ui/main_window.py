import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ui.setting_panel import SettingPanel
from ui.status_display import StatusDisplay
from ui.guide import NewUserGuide
from core.comment_send import CommentSender
from core.like_core import LikeCore
from core.account_manager import account_manager
import webbrowser
from tkinter import messagebox

class MainWindow(ttk.Window):
    def __init__(self):
        super().__init__(title="全自动氛围神器", size=(1400, 900), themename="litera")

        # # 尝试最大化窗口（Windows系统）
        # try:
        #     self.state("zoomed")
        # except:
        #     pass

        # 初始化核心组件
        self.platform = "bilibili"  # 默认平台
        self.accounts = []  # 已选择的账号
        self.comment_sender = None  # 评论发送实例
        self.like_core = None  # 点赞实例
        
        # 定时器相关
        self.comment_timer_id = None
        self.start_time = None
        self.comment_duration_seconds = 0
        self.like_duration_seconds = 0
        self.update_ui_timer = None

        # 新手引导（首次启动）
        self._check_first_start()

        # 布局管理
        self._setup_layout()

        # 绑定事件
        self._bind_events()

        # 绑定窗口关闭事件
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _check_first_start(self):
        """检查是否首次启动（显示新手引导）"""
        from config.config_handler import ConfigHandler
        config = ConfigHandler()
        if config.get("first_start", True):
            NewUserGuide(self)
            config.set("first_start", False)

    def _setup_layout(self):
        """布局设置：顶部选择区、中间配置区、底部状态区"""
        # 1. 顶部选择区（平台+账号）
        top_frame = ttk.Frame(self, padding=10)
        top_frame.pack(fill=X, side=TOP)

        # 平台选择
        ttk.Label(top_frame, text="目标平台：", font=("Arial", 12)).pack(side=LEFT, padx=5)
        self.platform_var = ttk.StringVar(value="bilibili")
        platform_options = ttk.Combobox(
            top_frame, textvariable=self.platform_var, values=["bilibili"],
            state="readonly", width=15, font=("Arial", 11)
        )
        platform_options.pack(side=LEFT, padx=5)
        platform_options.bind("<<ComboboxSelected>>", self._on_platform_change)

        # 账号选择（下拉框+刷新按钮）
        ttk.Label(top_frame, text="选择账号：", font=("Arial", 12)).pack(side=LEFT, padx=5)
        self.account_var = ttk.StringVar()
        self.account_combobox = ttk.Combobox(
            top_frame, textvariable=self.account_var, state="readonly", width=20, font=("Arial", 11)
        )
        self.account_combobox.pack(side=LEFT, padx=5)

        refresh_btn = ttk.Button(top_frame, text="刷新账号", command=self._load_accounts, style="primary.TButton")
        refresh_btn.pack(side=LEFT, padx=5)

        # 添加账号按钮
        add_btn = ttk.Button(top_frame, text="添加账号", command=self._open_add_account_dialog, style="success.TButton")
        add_btn.pack(side=LEFT, padx=5)

        # 删除账号按钮
        del_btn = ttk.Button(top_frame, text="删除账号", command=self._delete_current_account, style="danger.TButton")
        del_btn.pack(side=LEFT, padx=5)

        # 2. 底部状态区（进度+控制按钮）- 先pack以保证不被遮挡
        self.status_display = StatusDisplay(self)
        self.status_display.pack(fill=X, side=BOTTOM, padx=10, pady=10)

        # 3. 中间配置区（评论配置+点赞配置）- 占据剩余空间
        self.setting_panel = SettingPanel(self)
        self.setting_panel.pack(fill=BOTH, expand=YES, padx=10, pady=5)

        # 初始加载账号
        self._load_accounts()

    def _load_accounts(self):
        """加载指定平台的账号到下拉框"""
        self.accounts = account_manager.get_accounts(self.platform)
        account_names = [acc["username"] for acc in self.accounts]
        self.account_combobox["values"] = account_names
        
        # Load last account if exists and valid
        from config.config_handler import ConfigHandler
        last_account = ConfigHandler().get("last_account", "")
        
        if last_account and last_account in account_names:
            self.account_var.set(last_account)
        elif account_names:
            self.account_var.set(account_names[0])
        else:
            self.account_var.set("当前无账号")

    def _on_platform_change(self, event):
        """平台切换事件：重新加载账号"""
        self.platform = self.platform_var.get()
        self._load_accounts()
        self.status_display.update_platform(self.platform)
        # 保存选择的平台
        from config.config_handler import ConfigHandler
        ConfigHandler().set("last_platform", self.platform)

    def _on_account_change(self, event):
        """账号切换事件"""
        # 保存选择的账号
        from config.config_handler import ConfigHandler
        ConfigHandler().set("last_account", self.account_var.get())

    def _delete_current_account(self):
        """删除当前选中的账号"""
        current_account = self.account_var.get()
        if not current_account or current_account == "当前无账号":
            messagebox.showwarning("提示", "请先选择要删除的账号！")
            return
            
        if not messagebox.askyesno("确认删除", f"确定要删除账号 [{current_account}] 吗？\n删除后无法恢复，且会清理相关的登录缓存数据。"):
            return
            
        try:
            # 1. 从配置文件删除
            account_manager.delete_account(self.platform, current_account)
            
            # 2. 清理用户数据目录 (userdata)
            import shutil
            import os
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            userdata_dir = os.path.join(base_dir, "userdata", self.platform, current_account)
            if os.path.exists(userdata_dir):
                try:
                    shutil.rmtree(userdata_dir)
                except Exception as e:
                    print(f"清理用户数据失败: {e}")
            
            # 3. 刷新列表
            messagebox.showinfo("成功", f"账号 [{current_account}] 已删除。")
            self._load_accounts()
            
        except Exception as e:
            messagebox.showerror("错误", f"删除失败：{str(e)}")

    def _open_add_account_dialog(self):
        """打开添加账号对话框"""
        from ui.account_dialog import AccountDialog
        AccountDialog(self, platform=self.platform, callback=self._load_accounts)

    def _bind_events(self):
        """绑定控制按钮事件"""
        # 启动按钮：同时启动评论+点赞（可单独控制）
        self.status_display.start_btn.config(command=self._start_all)
        # 暂停按钮
        self.status_display.pause_btn.config(command=self._pause_all)
        # 停止按钮
        self.status_display.stop_btn.config(command=self._stop_all)

    def _init_core_instances(self):
        """初始化核心功能实例"""
        settings = self.setting_panel.get_settings()

        # 确定账号列表
        # 强制单账号模式（已移除 run_all_accounts）
        selected_accounts = [self.account_var.get()]

        target_url = settings["url"]

        # 初始化评论发送实例
        self.comment_sender = CommentSender(self.platform, selected_accounts, target_url)
        # 加载评论内容（自定义文本+导入文件）
        custom_content = settings["comment_content"]
        if custom_content:
            self.comment_sender.load_content(content=custom_content)
        import_file = settings["import_file"]
        if import_file:
            self.comment_sender.load_content(file_path=import_file)
        # 设置发送规则
        send_mode = settings["send_mode"]
        interval_type = settings["interval_type"]
        fixed_interval = float(settings["fixed_interval"] or 10)
        random_interval = (
            float(settings["random_interval_min"] or 5),
            float(settings["random_interval_max"] or 15)
        )
        self.comment_sender.set_send_rule(send_mode, interval_type, fixed_interval, random_interval)

        # 初始化点赞实例
        self.like_core = LikeCore(self.platform, selected_accounts, target_url)
        # 设置点赞规则
        like_interval_type = settings["like_interval_type"]
        like_fixed_interval = float(settings["like_fixed_interval"] or 10)
        like_random_interval = (
            float(settings["like_random_min"] or 8),
            float(settings["like_random_max"] or 12)
        )
        like_limit = int(settings["like_limit"] or 100)
        self.like_core.set_like_rule(like_interval_type, like_fixed_interval, like_random_interval, like_limit)

    def _start_all(self):
        """启动所有功能"""
        # 0. 账号校验
        if not self.account_var.get() or self.account_var.get() == "当前无账号":
             messagebox.showwarning("提示", "请先添加并选择账号！")
             return

        # 1. 基础校验
        settings = self.setting_panel.get_settings()
        target_url = settings["url"]
        
        if not target_url:
            messagebox.showwarning("提示", "请输入目标URL！")
            return

        # 简单校验URL与平台是否匹配
        if self.platform == "bilibili" and "bilibili" not in target_url:
            if not messagebox.askyesno("确认", "当前选择平台为B站，但URL似乎不是B站链接。\n是否继续？"):
                return

        # 2. 初始化核心
        is_new_start = False
        if not self.comment_sender or not self.like_core:
            self._init_core_instances()
            is_new_start = True
            # 重置计时器
            self.start_time = None
            try:
                self.comment_duration_seconds = int(settings.get("comment_duration", "60")) * 60
            except ValueError:
                self.comment_duration_seconds = 3600
                
            try:
                self.like_duration_seconds = int(settings.get("like_duration", "60")) * 60
            except ValueError:
                self.like_duration_seconds = 3600

        # 打开网页（如果是新启动且勾选了选项）
        if is_new_start and settings.get("open_url", False):
            try:
                webbrowser.open(target_url)
            except Exception as e:
                print(f"打开网页失败: {e}")

        # 3. 启动功能
        import time
        if is_new_start or not self.start_time:
             self.start_time = time.time()

        # 启动评论发送
        if settings["comment_enabled"]:
            self.comment_sender.run()
        # 启动点赞
        if settings["like_enabled"]:
            self.like_core.run()

        self.status_display.update_status("运行中", "green")
        
        # 启动UI更新循环
        self._start_ui_update_loop()

    def _pause_all(self):
        """暂停所有功能"""
        if self.comment_sender:
            self.comment_sender.pause()
        if self.like_core:
            self.like_core.pause()
        
        # 暂停时不需要停止计时器变量，但停止UI更新
        if self.update_ui_timer:
            self.after_cancel(self.update_ui_timer)
            self.update_ui_timer = None
            
        self.status_display.update_status("暂停中", "yellow")

    def _stop_all(self):
        """停止所有功能"""
        if self.comment_sender:
            self.comment_sender.stop()
            self.comment_sender = None
        if self.like_core:
            self.like_core.stop()
            self.like_core = None
            
        # 清理所有浏览器实例
        try:
            from core.platform_manager import platform_manager
            platform_manager.quit_all()
        except Exception as e:
            print(f"停止清理失败: {e}")

        # 停止UI更新
        if self.update_ui_timer:
            self.after_cancel(self.update_ui_timer)
            self.update_ui_timer = None
        self.start_time = None
        
        self.status_display.update_status("已停止", "gray")

    def _on_closing(self):
        """窗口关闭处理：确保清理所有资源"""
        if messagebox.askokcancel("退出", "确定要退出程序吗？\n所有正在运行的任务将被终止。"):
            try:
                # 1. 停止业务逻辑
                self._stop_all()
                
                # 2. 强制清理所有浏览器实例
                from core.platform_manager import platform_manager
                platform_manager.quit_all()
                
                # 3. 销毁窗口
                self.destroy()
                
                # 4. 强制退出进程（防止残留）
                import sys
                import os
                sys.exit(0)
            except Exception as e:
                print(f"退出清理异常: {e}")
                # 强制自杀
                import os
                os._exit(1)

    def _start_ui_update_loop(self):
        """启动UI更新循环（进度条、倒计时等）"""
        if not self.start_time:
            return

        import time
        current_time = time.time()
        elapsed = current_time - self.start_time
        
        # 1. 检查评论运行时间 (作为主计时器)
        time_up = False
        if self.comment_duration_seconds > 0:
            if elapsed >= self.comment_duration_seconds:
                time_up = True
                if self.comment_sender and self.comment_sender.is_running:
                    self.comment_sender.stop()
                    self.status_display.update_comment_progress(100, "已达到设定时长，停止评论")
                if self.like_core and self.like_core.is_running:
                    self.like_core.stop()
                    self.status_display.update_like_progress(100, "已达到设定时长，停止点赞")
            else:
                # 更新评论进度条（基于时间）
                progress_percent = (elapsed / self.comment_duration_seconds) * 100
                remaining = self.comment_duration_seconds - elapsed
                time_str = f"剩余时间: {int(remaining // 60)}分{int(remaining % 60)}秒"
                
                if self.comment_sender and self.comment_sender.is_running:
                    self.status_display.update_comment_progress(progress_percent, time_str)
                elif not self.comment_sender:
                     self.status_display.update_comment_progress(0, "未启动")

                # 更新点赞状态（如果正在运行）
                if self.like_core and self.like_core.is_running:
                     current_likes = getattr(self.like_core, 'current_likes', 0)
                     account_count = len(getattr(self.like_core, 'accounts', []))
                     settings = self.setting_panel.get_settings()
                     single_limit = int(settings.get("like_limit", 100))
                     total_target = single_limit * account_count if account_count > 0 else single_limit
                     
                     if total_target > 0:
                         like_percent = min((current_likes / total_target) * 100, 100)
                         self.status_display.update_like_progress(like_percent, f"{current_likes}/{total_target} {time_str}")
                     else:
                         self.status_display.update_like_progress(0, f"{current_likes}/∞ {time_str}")

        else:
             # 无限模式
             if self.comment_sender and self.comment_sender.is_running:
                self.status_display.update_comment_progress(0, "无限模式运行中")
             
             if self.like_core and self.like_core.is_running:
                 current_likes = getattr(self.like_core, 'current_likes', 0)
                 self.status_display.update_like_progress(0, f"{current_likes}/∞")

        # 3. 检查是否全部停止
        comment_running = self.comment_sender and self.comment_sender.is_running
        like_running = self.like_core and self.like_core.is_running
        
        if not comment_running and not like_running:
            self._stop_all()
            messagebox.showinfo("完成", "所有任务已结束。")
            return

        # 循环调用
        self.update_ui_timer = self.after(1000, self._start_ui_update_loop)