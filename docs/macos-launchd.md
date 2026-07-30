# Mac 自动运行

这是现在的推荐方式。

它不依赖 GitHub 的定时任务，改成让你的 Mac 用 `launchd` 每 5 分钟跑一次发送脚本。
脚本还是同一套宏观提醒逻辑，只是自动触发换成了本机定时器。
你需要让这台 Mac 保持登录，并尽量别关机/长时间休眠。

## 安装

先把 QQ 邮箱 SMTP 信息准备好，然后在项目根目录执行：

```bash
cd macro-alert-mail
SMTP_HOST=smtp.qq.com \
SMTP_PORT=465 \
SMTP_USER=你的QQ邮箱 \
SMTP_PASSWORD=你的QQ邮箱授权码 \
MAIL_FROM=你的QQ邮箱 \
MAIL_TO=你的QQ邮箱 \
./scripts/install_launchd.sh
```

## 你会得到什么

- 每 5 分钟自动检查一次
- 命中提醒窗口就发邮件
- 手机收 QQ 邮件通知
- 本机状态文件放在 `~/Library/Application Support/macro-alert-mail/`

## 看日志

```bash
tail -f ~/Library/Logs/macro-alert-mail/stdout.log
tail -f ~/Library/Logs/macro-alert-mail/stderr.log
```

## 卸载

```bash
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.dingdaqi16-sudo.macro-alert-mail.plist
rm -f ~/Library/LaunchAgents/com.dingdaqi16-sudo.macro-alert-mail.plist
```
