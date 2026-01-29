import json
import os
from utils.logger import global_logger


class CookiePool:
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.cookie_path = os.path.join(base_dir, "config", "cookies.json")
        # 初始化Cookie文件
        if not os.path.exists(self.cookie_path):
            with open(self.cookie_path, "w", encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False, indent=2)

    def save_cookie(self, platform: str, account: str, cookie: dict):
        """保存Cookie：按平台-账号维度存储"""
        with open(self.cookie_path, "r", encoding="utf-8") as f:
            cookies = json.load(f)

        if platform not in cookies:
            cookies[platform] = {}
        cookies[platform][account] = cookie

        with open(self.cookie_path, "w", encoding="utf-8") as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        global_logger.info(f"已保存{platform}账号[{account}]的Cookie")

    def get_cookie(self, platform: str, account: str) -> dict:
        """获取指定平台+账号的Cookie"""
        with open(self.cookie_path, "r", encoding="utf-8") as f:
            cookies = json.load(f)

        return cookies.get(platform, {}).get(account, {})

    def clear_cookie(self, platform: str, account: str = None):
        """清除Cookie：支持清除指定账号或整个平台"""
        with open(self.cookie_path, "r", encoding="utf-8") as f:
            cookies = json.load(f)

        if platform in cookies:
            if account:
                if account in cookies[platform]:
                    del cookies[platform][account]
            else:
                del cookies[platform]

        with open(self.cookie_path, "w", encoding="utf-8") as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        global_logger.info(f"已清除{platform}账号[{account}]的Cookie" if account else f"已清除{platform}所有Cookie")


# 全局Cookie池实例
cookie_pool = CookiePool()