import os
import shutil
import time
import threading
import psutil
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options as EdgeOptions
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium_stealth import stealth
from utils.logger import global_logger
from typing import Optional

# 全局锁，防止多线程同时启动驱动导致端口冲突或资源竞争
driver_lock = threading.Lock()

def kill_zombie_processes(user_data_dir: str):
    """
    清理占用指定 user_data_dir 的僵尸 msedge 进程
    """
    if not user_data_dir:
        return
        
    user_data_dir = os.path.abspath(user_data_dir).lower()
    killed_count = 0
    
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                # 检查进程名
                if proc.info['name'] and 'msedge' in proc.info['name'].lower():
                    # 检查命令行参数
                    cmdline = proc.info['cmdline']
                    if cmdline:
                        for arg in cmdline:
                            if arg.startswith('--user-data-dir=') and user_data_dir in os.path.abspath(arg.split('=', 1)[1]).lower():
                                global_logger.info(f"发现僵尸进程 PID={proc.info['pid']}, 正在清理...")
                                proc.kill()
                                killed_count += 1
                                break
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
    except Exception as e:
        global_logger.warning(f"清理僵尸进程时出错: {e}")
        
    if killed_count > 0:
        time.sleep(1) # 等待释放

def get_edge_driver(options: EdgeOptions) -> Optional[webdriver.Edge]:
    """
    获取Edge浏览器驱动，采用多级降级策略：
    1. 检查项目根目录下的 msedgedriver.exe
    2. 尝试使用 webdriver_manager 自动下载
    3. 尝试使用系统环境变量中的驱动
    """
    with driver_lock:
        time.sleep(1) # 增加间隔，减轻系统瞬间压力
        
        # 尝试清理 User Data Dir 中的锁文件和僵尸进程
        try:
            for arg in options.arguments:
                if arg.startswith("--user-data-dir="):
                    user_data_dir = arg.split("=", 1)[1]
                    
                    # 1. 杀掉占用该目录的僵尸进程
                    kill_zombie_processes(user_data_dir)
                    
                    # 2. 清理锁文件
                    lock_file = os.path.join(user_data_dir, "SingletonLock")
                    if os.path.exists(lock_file):
                        try:
                            os.remove(lock_file)
                            global_logger.info(f"清理僵尸锁文件: {lock_file}")
                        except Exception as e:
                            global_logger.warning(f"清理锁文件失败: {e}")
                    break
        except Exception as e:
             global_logger.warning(f"预清理环境失败: {e}")

        # 动态获取可用端口，解决多账号冲突和DevToolsActivePort报错
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # 使用 127.0.0.1 避免 ipv6 解析问题
            sock.bind(('127.0.0.1', 0))
            free_port = sock.getsockname()[1]
            sock.close()
            options.add_argument(f"--remote-debugging-port={free_port}")
            global_logger.info(f"分配动态调试端口: {free_port}")
        except Exception as e:
            global_logger.warning(f"获取动态端口失败，使用默认端口9222: {e}")
            options.add_argument("--remote-debugging-port=9222")

        # 1. 检查本地是否存在驱动
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    local_driver_path = os.path.join(project_root, "msedgedriver.exe")
    
    # 通用稳定性参数（应用于所有启动方式）
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--remote-allow-origins=*")
    # 补充关键参数，防止显卡报错和内存共享问题
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")

    if os.path.exists(local_driver_path):
        try:
            global_logger.info(f"使用本地驱动: {local_driver_path}")
            service = Service(executable_path=local_driver_path)
            return webdriver.Edge(service=service, options=options)
        except Exception as e:
            global_logger.warning(f"本地驱动启动失败: {e}")

    # 2. 尝试 webdriver_manager 自动下载
    try:
        global_logger.info("尝试自动下载/更新 Edge驱动...")
        # 设置下载源为淘宝镜像（如果支持）或者默认
        # 注意：EdgeChromiumDriverManager 默认使用微软官方源，国内可能不稳定
        driver_path = EdgeChromiumDriverManager().install()
        service = Service(executable_path=driver_path)
        return webdriver.Edge(service=service, options=options)
    except Exception as e:
        global_logger.warning(f"自动下载驱动失败: {e}")

    # 3. 尝试直接启动（依赖系统PATH或Selenium Manager）
    try:
        global_logger.info("尝试使用系统默认驱动配置...")
        return webdriver.Edge(options=options)
    except Exception as e:
        global_logger.error(f"系统默认驱动启动失败: {e}")
    
    global_logger.error("所有驱动加载方式均失败。")
    global_logger.error("请手动下载 msedgedriver.exe 并放置在项目根目录。")
    global_logger.error("下载地址: https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/")
    global_logger.error("注意：请下载与您当前Edge浏览器版本匹配的驱动。")
    return None

def apply_stealth(driver: webdriver.Edge):
    """
    应用selenium-stealth隐藏浏览器特征
    注意：selenium-stealth默认检查driver是否为Chrome，此处需要临时修改class绕过检查
    """
    try:
        # 保存原始class
        original_class = driver.__class__
        # 欺骗selenium-stealth
        driver.__class__ = webdriver.Chrome
        
        stealth(driver,
                languages=["zh-CN", "zh"],
                vendor="Microsoft Corporation",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True)
                
    except Exception as e:
        global_logger.warning(f"应用stealth失败: {e}")
    finally:
        # 恢复原始class
        driver.__class__ = original_class
