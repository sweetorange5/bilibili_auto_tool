from abc import ABCMeta, abstractmethod
from typing import Dict, List, Optional
from utils.logger import global_logger


class BasePlatform(metaclass=ABCMeta):
    """平台适配抽象基类：所有平台必须实现以下方法"""

    def __init__(self, platform_name: str, account: str):
        self.platform_name = platform_name  # 平台名称（bilibili/douyin/kuaishou）
        self.account = account  # 当前使用的账号
        self.logger = global_logger
        self.cookie = {}  # 账号Cookie（子类初始化时加载）

    @abstractmethod
    def send_comment(self, content: str, target_url: str) -> bool:
        """发送评论/弹幕：返回是否成功"""
        pass

    @abstractmethod
    def like_content(self, target_url: str) -> (bool, str):
        """点赞：返回（是否成功，状态信息）"""
        pass

    @abstractmethod
    def check_like_limit(self) -> (bool, str):
        """检查点赞上限：返回（是否已达上限，状态信息）"""
        pass

    @abstractmethod
    def preview_comment(self, content: str) -> str:
        """预览评论样式：返回模拟的平台展示效果"""
        pass

    def load_cookie(self, cookie: Dict):
        """加载Cookie（子类可重写扩展）"""
        self.cookie = cookie
        self.logger.info(f"{self.platform_name}账号[{self.account}]已加载Cookie")

    def quit(self):
        """清理资源（如关闭selenium driver）"""
        pass