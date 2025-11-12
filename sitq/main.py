#!/usr/bin/env python3

"""
SitQ - 监控 + 抢购助手（本地桌面运行，需手动扫码微信登录）

说明:
- 该脚本不会尝试绕过验证码或自动完成支付；遇到需要人工处理的步骤会暂停并提示。
- 在 config.json 中配置目标页面的 URL 与 CSS/XPath 选择器。
"""

import json
import time
import logging
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    NoSuchElementException, TimeoutException, WebDriverException
)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sys
import argparse
try:
    from plyer import notification
except Exception:
    notification = None

LOG = logging.getLogger("sitq")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")


def load_config(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def notify(title: str, msg: str):
    LOG.info("通知: %s - %s", title, msg)
    if notification:
        try:
            notification.notify(title=title, message=msg, timeout=8)
        except Exception:
            pass


def start_driver(headless=False, user_data_dir=None):
    from selenium.webdriver.chrome.options import Options
    opts = Options()
    if headless:
        # 新版 chrome 无头模式标志
        opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    if user_data_dir:
        opts.add_argument(f"--user-data-dir={user_data_dir}")

    try:
        driver = webdriver.Chrome(options=opts)
    except WebDriverException as e:
        LOG.error("无法启动 Chrome WebDriver: %s", e)
        raise
    driver.set_window_size(1200, 900)
    return driver


def wait_for_login(driver, cfg, timeout=300):
    """
    等待用户扫码登录。通过配置中的 logged_in_selector 判断是否登录成功。
    """
    LOG.info("打开登录页: %s", cfg["login_url"])
    driver.get(cfg["login_url"])

    check_sel = cfg.get("logged_in_selector")
    if not check_sel:
        LOG.warning("未配置 logged_in_selector，无法自动检测登录完成，请在配置中设置")
        return False

    LOG.info("请用微信扫码登录（在浏览器中）。等待登录完成（最大 %s 秒）...", timeout)
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, check_sel))
        )
        LOG.info("检测到 %s，登录成功。", check_sel)
        notify("SitQ", "检测到已登录")
        return True
    except TimeoutException:
        LOG.error("等待登录超时 (%s 秒)。", timeout)
        return False


def check_availability(driver, cfg):
    """
    返回 True/False 表示是否满足抢购条件（例如：有票）。
    通过 availability_selector 在页面上判断。
    """
    sel = cfg.get("availability_selector")
    if not sel:
        raise RuntimeError("未配置 availability_selector")
    try:
        el = driver.find_element(By.CSS_SELECTOR, sel)
        text = el.text.strip().lower()
        LOG.debug("availability element text: %s", text)
        # 简单逻辑：若元素可见且不为空，则认为有可用项；更复杂逻辑可以在 config 中扩展
        if cfg.get("availability_positive_text"):
            return cfg.get("availability_positive_text") in text
        return len(text) > 0
    except NoSuchElementException:
        LOG.debug("availability_selector 未找到元素")
        return False


def perform_booking_flow(driver, cfg):
    """
    执行到填写表单并提交的流程。所有的选择器在 config 中定义。
    返回 True 如果提交成功（到达提交后页面或弹窗），否则 False。
    """
    # 导航到 booking_url（或在当前页面直接操作）
    booking_url = cfg.get("booking_url")
    if booking_url:
        LOG.info("导航到下单页面: %s", booking_url)
        driver.get(booking_url)
        time.sleep(cfg.get("after_nav_delay", 1.0))

    # 填写字段
    fields = cfg.get("fill_fields", {})
    for sel, value in fields.items():
        try:
            el = driver.find_element(By.CSS_SELECTOR, sel)
            el.clear()
            el.send_keys(value)
            LOG.info("填入字段 %s -> %s", sel, value)
        except NoSuchElementException:
            LOG.warning("未找到字段 %s，跳过", sel)

    # 可选：点击确认/下一步按钮
    click_sel = cfg.get("pre_submit_click")
    if click_sel:
        try:
            btn = driver.find_element(By.CSS_SELECTOR, click_sel)
            btn.click()
            LOG.info("点击 %s", click_sel)
            time.sleep(cfg.get("after_click_delay", 0.5))
        except NoSuchElementException:
            LOG.warning("未找到按钮 %s，跳过点击", click_sel)

    # 在提交前检查是否出现验证码或需要人工交互（通过 selector）
    human_check_sel = cfg.get("human_intervention_selector")
    if human_check_sel:
        try:
            el = driver.find_element(By.CSS_SELECTOR, human_check_sel)
            if el.is_displayed():
                LOG.warning("检测到需要人工干预的元素 %s，暂停并通知用户", human_check_sel)
                notify("SitQ - 需要人工干预", f"检测到 {human_check_sel}，请手动完成")
                return False
        except NoSuchElementException:
            pass

    # 点击提交按钮
    submit_sel = cfg.get("submit_selector")
    if submit_sel:
        try:
            submit_btn = driver.find_element(By.CSS_SELECTOR, submit_sel)
            submit_btn.click()
            LOG.info("已点击提交 %s", submit_sel)
            time.sleep(cfg.get("after_submit_delay", 2.0))
            notify("SitQ", "已尝试提交，请检查是否成功")
            return True
        except NoSuchElementException:
            LOG.error("未找到提交按钮 %s，无法提交", submit_sel)
            return False
    else:
        LOG.error("未配置 submit_selector，无法执行提交")
        return False


def main(argv):
    parser = argparse.ArgumentParser(description="SitQ - 监控与自动填写助手")
    parser.add_argument("--config", "-c", default="config.json", help="配置文件路径（JSON）")
    parser.add_argument("--headless", action="store_true", help="无头模式运行（仅测试用）")
    parser.add_argument("--user-data-dir", default=None, help="Chrome user-data-dir（可缓存登录）")
    args = parser.parse_args(argv)

    cfg_path = Path(args.config)
    if not cfg_path.exists():
        LOG.error("配置文件不存在: %s", cfg_path)
        sys.exit(2)

    cfg = load_config(cfg_path)

    driver = start_driver(headless=args.headless, user_data_dir=args.user_data_dir)

    try:
        # 登录流程（扫码）
        if not wait_for_login(driver, cfg, timeout=cfg.get("login_timeout", 300)):
            LOG.error("登录失败或超时，退出")
            driver.quit()
            return

        # 进入监控循环
        monitor_url = cfg.get("monitor_url")
        if not monitor_url:
            LOG.error("未配置 monitor_url，退出")
            driver.quit()
            return

        LOG.info("进入监控页面: %s", monitor_url)
        driver.get(monitor_url)
        poll_interval = cfg.get("poll_interval_seconds", 2)
        max_attempts = cfg.get("max_attempts", 0)  # 0 表示无限
        attempts = 0

        while True:
            attempts += 1
            LOG.info("第 %s 次检测...", attempts)
            try:
                driver.refresh()
            except Exception:
                LOG.warning("刷新页面遇到异常，尝试重新加载")
                driver.get(monitor_url)
            time.sleep(cfg.get("after_refresh_delay", 0.5))

            available = check_availability(driver, cfg)
            LOG.info("可用状态: %s", available)
            if available:
                notify("SitQ", "检测到目标可用，开始自动抢购流程")
                ok = perform_booking_flow(driver, cfg)
                if ok:
                    LOG.info("已执行抢购流程（提交尝试完成），程序将停止或根据配置决定继续")
                    if cfg.get("stop_after_success", True):
                        break
                else:
                    LOG.info("流程未完成（可能需要人工干预）。程序继续监控或退出按配置。")
                    if cfg.get("stop_on_intervention", True):
                        break

            if max_attempts and attempts >= max_attempts:
                LOG.info("达到最大检测次数，退出")
                break

            time.sleep(poll_interval)

    finally:
        LOG.info("退出，关闭浏览器")
        driver.quit()


if __name__ == "__main__":
    main(sys.argv[1:])
