from typing import Dict, Optional, Tuple
from utils.logger import global_logger
import time
from random import uniform


class RiskControl:
    """风控策略核心：模拟真人行为+阈值检测"""

    def __init__(self):
        # 基础风控配置（可从config读取）
        self.min_comment_interval = 5  # 最小评论间隔（秒）
        self.max_comment_interval = 15  # 最大评论间隔（秒）
        self.min_like_interval = 8  # 最小点赞间隔（秒）
        self.max_like_interval = 12  # 最大点赞间隔（秒）
        self.comment_limit_per_account = 100  # 单账号单日评论上限
        self.like_limit_per_account = 500  # 单账号单日点赞上限

        # 账号操作计数器（内存存储，重启重置）
        self.account_counter: Dict[str, Dict[str, int]] = {}

    def get_random_interval(self, action_type: str) -> float:
        """获取随机间隔（根据操作类型）"""
        if action_type == "comment":
            return uniform(self.min_comment_interval, self.max_comment_interval)
        elif action_type == "like":
            return uniform(self.min_like_interval, self.max_like_interval)
        return 10.0

    def check_threshold(self, platform: str, account: str, action_type: str) -> Tuple[bool, str]:
        """检查操作阈值：返回（是否允许操作，提示信息）"""
        key = f"{platform}_{account}"
        if key not in self.account_counter:
            self.account_counter[key] = {"comment": 0, "like": 0}

        count = self.account_counter[key][action_type]
        limit = self.comment_limit_per_account if action_type == "comment" else self.like_limit_per_account

        # 阈值预警（80%上限）
        if count >= limit * 0.8:
            msg = f"账号[{account}]{action_type}次数已达上限的80%（当前{count}/{limit}）"
            global_logger.warning(msg)
            return True, msg

        # 阈值超限
        if count >= limit:
            msg = f"账号[{account}]{action_type}次数已达上限（{count}/{limit}）"
            global_logger.error(msg)
            return False, msg

        return True, "正常"

    def increment_counter(self, platform: str, account: str, action_type: str):
        """递增操作计数器"""
        key = f"{platform}_{account}"
        if key not in self.account_counter:
            self.account_counter[key] = {"comment": 0, "like": 0}
        self.account_counter[key][action_type] += 1

    def reset_counter(self, platform: str, account: str = None):
        """重置计数器（支持单个账号或整个平台）"""
        if account:
            key = f"{platform}_{account}"
            if key in self.account_counter:
                del self.account_counter[key]
        else:
            for key in list(self.account_counter.keys()):
                if key.startswith(platform):
                    del self.account_counter[key]
        global_logger.info(
            f"已重置{platform}账号[{account}]的操作计数器" if account else f"已重置{platform}所有账号计数器")


# 全局风控实例
risk_control = RiskControl()