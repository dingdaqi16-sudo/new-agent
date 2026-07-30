# 宏观提醒邮件版

一个零成本的个人宏观提醒工具。

它会抓取官方日历，给你发两次邮件提醒：

- 事件前一天，北京时间 12:00
- 事件发生前 90 分钟

支持的事件：

- FOMC
- CPI
- 非农
- PCE

如果官方页面明确没有下一次发布，或者日期变更，后续提醒就不会发。

说明：BLS 的 CPI 和非农在代码里走的是官方日历的文本镜像，原因是它的直连页面会拦脚本请求；Fed 和 BEA 仍然直连官方页。

## 为什么这样做

- 0 成本
- 不用做 iPhone App
- 不用买服务器
- iPhone 只要能收邮件就行

## 目录

- `macro_alert/`：核心代码
- `tests/`：单元测试
- `docs/iphone-setup.md`：iPhone 收通知教程
- `.github/workflows/remind.yml`：GitHub Actions 定时任务

## 本地预览

```bash
cd macro-alert-mail
python3 -m macro_alert.cli preview
```

## 本地测试邮件

```bash
cd macro-alert-mail
python3 -m macro_alert.cli send --dry-run
```

## 正式发送

把下面这些配置成环境变量或 GitHub Secrets：

- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_PASSWORD`
- `MAIL_FROM`
- `MAIL_TO`

QQ 邮箱要先开 `SMTP` 并使用授权码，不要直接填登录密码。

## GitHub Actions

把这个项目放到一个公开仓库里，GitHub Actions 的标准 GitHub-hosted runner 对公开仓库是免费的。

每 5 分钟跑一次，提醒窗口是 90 分钟。状态文件会自动更新并提交，避免重复提醒。

## iPhone 收件

看 `docs/iphone-setup.md`。
