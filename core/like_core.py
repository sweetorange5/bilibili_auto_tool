from typing import List, Tuple, Dict
from core.risk_control import risk_control
from utils.logger import global_logger
import time
from random import uniform
from threading import Thread
from core.platform_manager import platform_manager


class LikeCore:
    def __init__(self, platform: str, accounts: List[str], target_url: str):
        self.platform = platform
        self.accounts = accounts
        self.target_url = target_url
        self.interval_type = "random"  # 间隔类型：fixed/random
        self.fixed_interval = 10  # 固定间隔（秒）
        self.random_interval = (8, 12)  # 随机间隔范围（秒）
        self.like_limit = 99999  # 单账号点赞上限
        self.is_running = False  # 运行状态
        self.account_like_count = {acc: 0 for acc in accounts}  # 账号点赞计数器
        self.platform_instances = {}  # 平台实例缓存

    @property
    def current_likes(self) -> int:
        """获取当前总点赞数"""
        return sum(self.account_like_count.values())

    def set_like_rule(self, interval_type: str, fixed_interval: float = None, random_interval: tuple = None,
                      like_limit: int = None):
        """设置点赞规则"""
        self.interval_type = interval_type
        if fixed_interval:
            self.fixed_interval = fixed_interval
        if random_interval:
            self.random_interval = random_interval
        if like_limit:
            self.like_limit = like_limit

    def _get_like_interval(self) -> float:
        """获取点赞间隔"""
        if self.interval_type == "fixed":
            return self.fixed_interval
        elif self.interval_type == "random":
            # 使用用户设置的随机范围
            return uniform(self.random_interval[0], self.random_interval[1])
        return 10.0

    def _get_platform_instance(self, account: str):
        """获取或创建平台实例"""
        return platform_manager.get_instance(self.platform, account)

    def _like_single_account(self, account: str) -> Tuple[bool, str]:
        """单个账号执行点赞"""
        # 1. 检查本地点赞上限
        if self.account_like_count[account] >= self.like_limit:
            return False, "已达自定义点赞上限"

        # 2. 风控阈值检测
        allow, msg = risk_control.check_threshold(self.platform, account, "like")
        if not allow:
            return False, msg

        # 3. 获取平台对象
        platform_obj = self._get_platform_instance(account)
        if not platform_obj:
            return False, "平台初始化失败"

        # 4. 检查平台点赞上限
        limit_reached, limit_msg = platform_obj.check_like_limit()
        if limit_reached:
            return False, limit_msg

        # 5. 执行点赞
        success, like_msg = platform_obj.like_content(self.target_url)
        if success:
            self.account_like_count[account] += 1
            risk_control.increment_counter(self.platform, account, "like")
            return True, "点赞成功"
        return False, like_msg

    def run(self):
        """启动点赞（多线程并发）"""
        if self.is_running:
            global_logger.warning("点赞功能已在运行中")
            return

        self.is_running = True
        global_logger.info(
            f"启动点赞功能：平台={self.platform}，账号数={len(self.accounts)}，上限={self.like_limit}次/账号")

        # 多账号并发点赞
        def account_like_thread(account: str):
            while self.is_running:
                # 检查是否已达本地上限
                if self.account_like_count[account] >= self.like_limit:
                    global_logger.info(f"账号[{account}]已达点赞上限（{self.like_limit}次），停止点赞")
                    break

                # 执行点赞
                success, msg = self._like_single_account(account)
                global_logger.info(f"账号[{account}]点赞结果：{msg}")

                # 点赞失败且触发风控，停止该账号
                if "上限" in msg or "频繁" in msg:
                    global_logger.warning(f"账号[{account}]触发风控，停止点赞")
                    break

                # 等待间隔
                time.sleep(self._get_like_interval())

        # 启动所有账号线程
        for account in self.accounts:
            Thread(target=account_like_thread, args=(account,), daemon=True).start()

    def pause(self):
        """暂停点赞"""
        self.is_running = False
        global_logger.info("已暂停点赞功能")

    def stop(self):
        """停止点赞（重置计数器并清理资源）"""
        self.is_running = False
        self.account_like_count = {acc: 0 for acc in self.accounts}
        # 不再在此处清理实例，由PlatformManager统一管理或保持常驻
        global_logger.info("已停止点赞功能")

    def get_like_status(self) -> Dict[str, Tuple[int, int]]:
        """获取点赞状态：{账号: (已点赞次数, 上限次数)}"""
        return {acc: (self.account_like_count[acc], self.like_limit) for acc in self.accounts}