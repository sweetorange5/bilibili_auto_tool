from typing import List, Optional, Tuple
from core.risk_control import risk_control
from utils.logger import global_logger
import time
from threading import Thread
from core.platform_manager import platform_manager

class CommentSender:
    def __init__(self, platform: str, accounts: List[str], target_url: str):
        self.platform = platform  # 目标平台
        self.accounts = accounts  # 用于发送的账号列表
        self.target_url = target_url  # 目标URL（视频/直播间）
        self.content_list = []  # 评论内容列表
        self.send_mode = "order"  # 发送模式：order（顺序）/ random（随机）
        self.interval_type = "random"  # 间隔类型：fixed（固定）/ random（随机）
        self.fixed_interval = 10  # 固定间隔（秒）
        self.random_interval = (5, 15)  # 随机间隔范围（秒）
        self.is_running = False  # 运行状态
        self.current_index = 0  # 当前发送索引（支持断点续传）
        self.platform_instances = {}  # 平台实例缓存 {account: instance}

    def load_content(self, content: Optional[str] = None, file_path: Optional[str] = None):
        """加载评论内容：支持自定义文本或导入文件"""
        if content:
            # 按行分割自定义文本，去除空行
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            self.content_list.extend(lines)
        elif file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self.content_list = [line.strip() for line in f if line.strip()]
                global_logger.info(f"已导入评论内容：{len(self.content_list)}条")
            except Exception as e:
                global_logger.error(f"导入评论文件失败：{str(e)}")

    def set_send_rule(self, send_mode: str, interval_type: str, fixed_interval: float = None,
                      random_interval: Tuple = None):
        """设置发送规则"""
        self.send_mode = send_mode
        self.interval_type = interval_type
        if fixed_interval:
            self.fixed_interval = fixed_interval
        if random_interval:
            self.random_interval = random_interval

    def _get_next_content(self) -> Optional[str]:
        """获取下一条评论内容（根据发送模式）"""
        if not self.content_list:
            return None

        if self.send_mode == "order":
            # 顺序发送：支持断点续传
            if self.current_index >= len(self.content_list):
                self.current_index = 0  # 循环发送（可配置是否循环）
            content = self.content_list[self.current_index]
            self.current_index += 1
            return content
        elif self.send_mode == "random":
            from random import choice
            return choice(self.content_list)
        return None

    def _get_send_interval(self) -> float:
        """获取发送间隔（根据间隔类型）"""
        if self.interval_type == "fixed":
            return self.fixed_interval
        elif self.interval_type == "random":
            return risk_control.get_random_interval("comment")
        return 10.0

    def _get_platform_instance(self, account: str):
        """获取或创建平台实例"""
        return platform_manager.get_instance(self.platform, account)

    def _send_single_comment(self, account: str, content: str) -> bool:
        """单个账号发送单条评论"""
        # 1. 风控阈值检测
        allow, msg = risk_control.check_threshold(self.platform, account, "comment")
        if not allow:
            global_logger.error(f"账号[{account}]发送评论被风控拦截：{msg}")
            return False

        # 2. 获取平台对象
        platform_obj = self._get_platform_instance(account)
        if not platform_obj:
            return False

        # 3. 发送评论
        success = platform_obj.send_comment(content, self.target_url)
        if success:
            # 4. 递增风控计数器
            risk_control.increment_counter(self.platform, account, "comment")
        return success

    def run(self):
        """启动发送（多线程并发）"""
        if self.is_running:
            global_logger.warning("评论发送已在运行中")
            return

        if not self.content_list:
            global_logger.error("未加载评论内容，无法启动发送")
            return

        self.is_running = True
        global_logger.info(
            f"启动评论发送：平台={self.platform}，账号数={len(self.accounts)}，内容数={len(self.content_list)}")

        # 多账号并发发送（每个账号一个线程）
        def account_send_thread(account: str):
            while self.is_running:
                content = self._get_next_content()
                if not content:
                    break

                # 发送单条评论
                self._send_single_comment(account, content)

                # 等待间隔
                time.sleep(self._get_send_interval())

        # 启动所有账号线程
        for account in self.accounts:
            Thread(target=account_send_thread, args=(account,), daemon=True).start()

    def pause(self):
        """暂停发送"""
        self.is_running = False
        global_logger.info("已暂停评论发送")

    def stop(self):
        """停止发送（重置索引）"""
        self.is_running = False
        self.current_index = 0
        # 资源清理统一由PlatformManager管理
        global_logger.info("已停止评论发送")