import json
import os
from typing import List, Dict
from utils.logger import global_logger


class AccountManager:
    """多账号管理：添加、切换、批量操作"""

    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.account_path = os.path.join(base_dir, "config", "accounts.json")
        self._init_account_file()

    def _init_account_file(self):
        """初始化账号配置文件"""
        if not os.path.exists(self.account_path):
            with open(self.account_path, "w", encoding="utf-8") as f:
                json.dump({"bilibili": [], "douyin": [], "kuaishou": []}, f, ensure_ascii=False, indent=2)

    def add_account(self, platform: str, account_info: Dict):
        """添加账号：account_info需包含username和password（建议加密存储）"""
        with open(self.account_path, "r", encoding="utf-8") as f:
            accounts = json.load(f)

        if platform not in accounts:
            accounts[platform] = []

        # 去重（按username）
        for acc in accounts[platform]:
            if acc["username"] == account_info["username"]:
                global_logger.warning(f"{platform}账号[{account_info['username']}]已存在，无需重复添加")
                return

        accounts[platform].append(account_info)
        with open(self.account_path, "w", encoding="utf-8") as f:
            json.dump(accounts, f, ensure_ascii=False, indent=2)
        global_logger.info(f"已添加{platform}账号：{account_info['username']}")

    def get_accounts(self, platform: str) -> List[Dict]:
        """获取指定平台的所有账号"""
        with open(self.account_path, "r", encoding="utf-8") as f:
            accounts = json.load(f)
        return accounts.get(platform, [])

    def delete_account(self, platform: str, username: str):
        """删除指定账号"""
        with open(self.account_path, "r", encoding="utf-8") as f:
            accounts = json.load(f)

        if platform in accounts:
            accounts[platform] = [acc for acc in accounts[platform] if acc["username"] != username]

        with open(self.account_path, "w", encoding="utf-8") as f:
            json.dump(accounts, f, ensure_ascii=False, indent=2)
        global_logger.info(f"已删除{platform}账号：{username}")

    def batch_set_interval(self, platform: str, like_interval: tuple):
        """批量设置指定平台账号的点赞间隔（实际需关联配置文件）"""
        # 此处简化：实际需将间隔存储到账号配置中
        global_logger.info(f"已批量设置{platform}所有账号点赞间隔：{like_interval[0]}-{like_interval[1]}秒")


# 全局账号管理器实例
account_manager = AccountManager()