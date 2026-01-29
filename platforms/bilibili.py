import re
import time
import requests
import os
from platforms.base_platform import BasePlatform
from utils.ua_pool import ua_pool
from utils.logger import global_logger
from typing import Dict, Tuple, Optional
from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.microsoft import EdgeChromiumDriverManager

from utils.driver_helper import get_edge_driver, apply_stealth

class BilibiliPlatform(BasePlatform):
    def __init__(self, account: str):
        super().__init__("bilibili", account)
        # 加载Cookie
        from utils.cookie_handler import cookie_pool
        self.load_cookie(cookie_pool.get_cookie("bilibili", account))
        # B站接口配置
        self.video_comment_api = "https://api.bilibili.com/x/v2/reply/add"
        self.live_danmaku_api = "https://api.live.bilibili.com/msg/send"
        self.video_like_api = "https://api.bilibili.com/x/web-interface/archive/like"
        self.driver = None  # selenium驱动（直播间点赞备用）

    def _init_selenium_driver(self) -> Optional[webdriver.Edge]:
        """初始化selenium驱动（复用DouyinPlatform逻辑，适配B站）"""
        if self.driver:
            try:
                _ = self.driver.window_handles
                return self.driver
            except Exception:
                self.driver = None
        
        edge_options = EdgeOptions()
        edge_options.add_argument("--headless=new")  # 无头模式
        edge_options.add_argument("--disable-gpu")
        edge_options.add_argument("--disable-dev-shm-usage")
        edge_options.add_argument("--window-size=1920,1080")
        edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        edge_options.add_experimental_option("useAutomationExtension", False)
        
        # 设置持久化目录
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        user_data_dir = os.path.join(base_dir, "userdata", "bilibili", self.account)
        if not os.path.exists(user_data_dir):
            try:
                os.makedirs(user_data_dir)
            except Exception:
                pass
        edge_options.add_argument(f"--user-data-dir={user_data_dir}")
        
        driver = get_edge_driver(edge_options)
        if not driver:
            return None
            
        driver.set_page_load_timeout(30)
        
        apply_stealth(driver)
        
        # 加载Cookie到浏览器
        driver.get("https://www.bilibili.com/")
        for key, value in self.cookie.items():
            driver.add_cookie({"name": key, "value": value, "domain": ".bilibili.com"})
        driver.refresh()
        self.driver = driver
        global_logger.info(f"B站账号[{self.account}] Edge驱动初始化完成")
        return driver

    @staticmethod
    def launch_for_login(account: str) -> Optional[webdriver.Edge]:
        """启动可见的浏览器用于手动登录"""
        edge_options = EdgeOptions()
        edge_options.add_argument("--disable-gpu")
        edge_options.add_argument("--disable-dev-shm-usage")
        edge_options.add_argument("--window-size=1920,1080")
        edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        edge_options.add_experimental_option("useAutomationExtension", False)
        
        # 设置持久化目录
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        user_data_dir = os.path.join(base_dir, "userdata", "bilibili", account)
        if not os.path.exists(user_data_dir):
            try:
                os.makedirs(user_data_dir)
            except Exception:
                pass
        edge_options.add_argument(f"--user-data-dir={user_data_dir}")
        
        driver = get_edge_driver(edge_options)
        if not driver:
            return None
            
        driver.set_page_load_timeout(300)
        
        apply_stealth(driver)
        
        driver.get("https://www.bilibili.com/")
        return driver

    def send_comment(self, content: str, target_url: str) -> bool:
        """发送评论/弹幕（自动识别视频或直播）"""
        target_type, target_id = self._resolve_target(target_url)
        
        if not target_id:
            self.logger.error(f"无法解析B站URL：{target_url}")
            return False

        if target_type == "live":
            return self._send_live_danmaku(target_id, content)
        else:
            return self._send_video_comment(target_id, content)

    def _send_video_comment(self, aid: str, content: str) -> bool:
        """发送视频评论"""
        headers = {
            "User-Agent": ua_pool.get_random_ua(),
            "Cookie": "; ".join([f"{k}={v}" for k, v in self.cookie.items()]),
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "aid": aid,
            "message": content,
            "type": 1,
            "csrf": self.cookie.get("bili_jct", "")
        }
        try:
            response = requests.post(self.video_comment_api, headers=headers, data=data, timeout=10)
            result = response.json()
            if result.get("code") == 0:
                self.logger.info(f"B站账号[{self.account}]发送视频评论成功：{content}")
                return True
            else:
                self.logger.error(f"B站视频评论失败：{result.get('message')}")
                return False
        except Exception as e:
            self.logger.error(f"B站视频评论异常：{str(e)}")
            return False

    def _send_live_danmaku(self, room_id: str, content: str) -> bool:
        """发送直播弹幕"""
        headers = {
            "User-Agent": ua_pool.get_random_ua(),
            "Cookie": "; ".join([f"{k}={v}" for k, v in self.cookie.items()]),
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "roomid": room_id,
            "msg": content,
            "csrf": self.cookie.get("bili_jct", ""),
            "rnd": int(time.time()),
            "color": 16777215,
            "fontsize": 25,
            "mode": 1
        }
        try:
            response = requests.post(self.live_danmaku_api, headers=headers, data=data, timeout=10)
            result = response.json()
            if result.get("code") == 0:
                self.logger.info(f"B站账号[{self.account}]发送直播弹幕成功：{content}")
                return True
            else:
                self.logger.error(f"B站直播弹幕失败：{result.get('message')}")
                return False
        except Exception as e:
            self.logger.error(f"B站直播弹幕异常：{str(e)}")
            return False

    def _like_live_content(self, target_url: str) -> Tuple[bool, str]:
        """B站直播间点赞（selenium模拟）"""
        try:
            driver = self._init_selenium_driver()
            if not driver:
                return False, "浏览器初始化失败"
            
            # 如果当前不在目标直播间，则跳转
            if target_url not in driver.current_url:
                driver.get(target_url)
            
            # 等待点赞按钮加载
            # B站直播间点赞按钮通常在右下角，class含有 'like-btn'
            like_btn = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'like-btn') or @title='点赞' or contains(@class, 'LikeBtn')]"))
            )
            
            like_btn.click()
            time.sleep(0.5)
            
            return True, "点赞成功"
            
        except Exception as e:
            global_logger.error(f"B站直播点赞失败: {str(e)}")
            if "no such window" in str(e) or "invalid session" in str(e):
                self.driver = None
            return False, f"点赞失败: {str(e)}"

    def like_content(self, target_url: str) -> Tuple[bool, str]:
        """B站点赞（支持视频和直播）"""
        target_type, aid = self._resolve_target(target_url)
        
        if target_type == "live":
            return self._like_live_content(target_url)
        
        if not aid:
            return False, "URL解析失败"

        headers = {
            "User-Agent": ua_pool.get_random_ua(),
            "Cookie": "; ".join([f"{k}={v}" for k, v in self.cookie.items()]),
            "Referer": target_url
        }
        params = {
            "aid": aid,
            "like": 1,
            "csrf": self.cookie.get("bili_jct", "")
        }
        try:
            response = requests.post(self.video_like_api, headers=headers, params=params, timeout=10)
            result = response.json()
            if result.get("code") == 0:
                self.logger.info(f"B站账号[{self.account}]点赞成功")
                return True, "点赞成功"
            elif result.get("code") == 65006:
                return True, "已点赞过"
            else:
                return False, result.get("message", "未知错误")
        except Exception as e:
            return False, str(e)

    def check_like_limit(self) -> Tuple[bool, str]:
        return False, "未达上限"

    def preview_comment(self, content: str) -> str:
        return f"[B站] {self.account}: {content}"

    def _resolve_target(self, url: str) -> Tuple[str, Optional[str]]:
        """解析URL类型和ID"""
        # 直播
        if "live.bilibili.com" in url:
            match = re.search(r"live\.bilibili\.com/(\d+)", url)
            return "live", match.group(1) if match else None
        
        # 视频 (BV转AV)
        bv_match = re.search(r"(BV[a-zA-Z0-9]+)", url)
        if bv_match:
            bvid = bv_match.group(1)
            return "video", self._get_aid_from_bvid(bvid)
        
        # 视频 (AV号)
        av_match = re.search(r"av(\d+)", url)
        if av_match:
            return "video", av_match.group(1)
            
        return "unknown", None

    def _get_aid_from_bvid(self, bvid: str) -> Optional[str]:
        """BV号转AV号"""
        try:
            api = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
            resp = requests.get(api, headers={"User-Agent": ua_pool.get_random_ua()})
            if resp.json()['code'] == 0:
                return str(resp.json()['data']['aid'])
        except:
            pass
        return None

    def quit(self):
        """关闭selenium驱动"""
        if self.driver:
            try:
                self.driver.quit()
                global_logger.info(f"B站账号[{self.account}] selenium驱动已关闭")
            except Exception:
                pass
            finally:
                self.driver = None

    def __del__(self):
        self.quit()