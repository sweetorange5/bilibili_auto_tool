import logging
import os
from datetime import datetime


class Logger:
    def __init__(self, log_name="operation.log"):
        # 创建logs目录（不存在则创建）
        if not os.path.exists("../logs"):
            os.makedirs("../logs")

        # 日志配置
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        # 日志格式：时间-模块-级别-内容
        formatter = logging.Formatter(
            "%(asctime)s - %(module)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # 文件处理器（按日期分割日志）
        log_file = os.path.join("../logs", f"{datetime.now().strftime('%Y%m%d')}_{log_name}")
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)

        # 控制台处理器（实时输出）
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def get_logger(self):
        return self.logger


# 单例模式：全局唯一日志实例
global_logger = Logger().get_logger()