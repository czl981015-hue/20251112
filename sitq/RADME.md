```markdown
# SitQ - 监控 + 抢购助手 (Selenium 模板)

说明
- 本项目是一个通用模板：打开目标网站，等待微信扫码登录（需手机扫码），登录后进入监控页面轮询状态，检测到可用时自动尝试填写并提交表单。
- 仅用于在你有合法授权的情况下自动化你的流程。禁止用于绕过 CAPTCHA、反刷或自动支付等受限操作。

快速开始
1. 安装依赖：
   pip install -r requirements.txt

2. 安装 Chrome 浏览器与 chromedriver，或使用 webdriver-manager（可在代码中扩展自动安装）。
   推荐将 chromedriver 放在 PATH 中，或使用 --user-data-dir 参数保持登录会话。

3. 复制并编辑配置文件：
   cp sitq/config.example.json sitq/config.json
   按目标站点调整 login_url、monitor_url、选择器与填充值。

4. 运行：
   python sitq/main.py -c sitq/config.json

   常用参数：
   --headless      无头模式（仅用于测试）
   --user-data-dir 指定 Chrome 的用户数据目录以缓存登录

注意
- 如果页面要求验证码或手机支付，脚本将在检测到相应元素时停止并通知你人工完成。
- 建议先手动进入目标群聊并确认选择器后再让脚本全自动轮询与填写。
```
