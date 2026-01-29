from fake_useragent import UserAgent
from random import choice


class UAPool:
    def __init__(self):
        # 预定义常用UA（避免fake-useragent联网失败）
        self.ua_list = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0"
        ]

    def get_random_ua(self):
        """获取随机UA（优先用预定义列表，失败则用fake-useragent）"""
        try:
            return UserAgent().random
        except:
            return choice(self.ua_list)


# 全局UA池实例
ua_pool = UAPool()