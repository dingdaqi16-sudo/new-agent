# cron-job.org 方案

这是现在推荐的自动触发方式。

它的思路很简单：

1. cron-job.org 每 5 分钟发一次 HTTP 请求
2. 这个请求去调用 GitHub 的 `workflow_dispatch`
3. GitHub Actions 继续执行你现有的发送逻辑
4. 邮件从 QQ SMTP 发出，手机收通知

这样就不依赖你的 Mac 是否开机。

## 先准备什么

- 一个公开的 GitHub 仓库
- 一个 GitHub fine-grained PAT，至少给这个仓库 `Actions: Read and write` 权限
- 已经配置好的 QQ 邮箱 SMTP secret

## 先本地试一次

在项目目录执行：

```bash
cd macro-alert-mail
GITHUB_TOKEN=你的GitHubPAT ./scripts/dispatch_workflow.sh main
```

如果成功，GitHub Actions 里会多出一次 `workflow_dispatch` 运行。

## cron-job.org 里怎么填

创建一个新的 Cron Job：

- Method: `POST`
- URL:

```text
https://api.github.com/repos/dingdaqi16-sudo/new-agent/actions/workflows/remind.yml/dispatches
```

- Headers:

```text
Accept: application/vnd.github+json
Authorization: Bearer 你的GitHubPAT
X-GitHub-Api-Version: 2022-11-28
Content-Type: application/json
```

- Body:

```json
{"ref":"main"}
```

- Schedule: every `5 minutes`

## 怎么确认生效

1. 去 GitHub 仓库 `Actions`
2. 看 `macro-alert-mail` 是否出现新的 `workflow_dispatch`
3. 打开 `send-reminders`
4. 看日志里有没有 `sent=1` 或 `sent=0 skipped=1`

## 注意

- GitHub PAT 不要公开发给别人
- 如果你还在本机装了 `launchd`，要先停掉，避免重复发
- 这个方案仍然是零成本的，cron-job.org 免费计划就够用
