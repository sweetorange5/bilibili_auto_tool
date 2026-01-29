from typing import Dict, Optional
from platforms.base_platform import BasePlatform
from platforms.bilibili import BilibiliPlatform
from threading import Lock
from utils.logger import global_logger

class PlatformInstanceManager:
    _instance = None
    _lock = Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance.instances = {}  # { "platform_account": instance }
            return cls._instance

    def get_instance(self, platform_name: str, account_name: str) -> BasePlatform:
        account_name = account_name.strip()
        key = f"{platform_name}_{account_name}"
        if key in self.instances:
            global_logger.info(f"PlatformManager: 复用实例 {key} (id={id(self.instances[key])})")
            return self.instances[key]
        
        # 创建新实例
        global_logger.info(f"PlatformManager: 创建新实例 {key}")
        instance = None
        if platform_name == "bilibili":
            instance = BilibiliPlatform(account_name)
        else:
            raise ValueError(f"Unknown platform: {platform_name}")
            
        self.instances[key] = instance
        global_logger.info(f"PlatformManager: 实例 {key} 创建完成 (id={id(instance)})")
        return instance

    def quit_all(self):
        """退出所有实例（关闭浏览器）"""
        with self._lock:
            for key, instance in list(self.instances.items()):
                try:
                    if hasattr(instance, 'quit'):
                        global_logger.info(f"PlatformManager: 关闭实例 {key}")
                        instance.quit()
                except Exception as e:
                    global_logger.error(f"PlatformManager: 关闭实例 {key} 失败: {e}")
            self.instances.clear()
            global_logger.info("PlatformManager: 所有实例已清理")

    def clear_instances(self):
        """清理所有实例（通常在停止时调用，或者保留以复用）"""
        # 兼容旧代码调用，实际执行 quit_all
        self.quit_all()

# 全局单例
platform_manager = PlatformInstanceManager()
