# Governance Tools

本目录存放 JBT 的治理工具。

当前已提供：

- `jbt_lockctl.py`：文件级 Token 锁控器

## 锁控器用途

用于把 `WORKFLOW.md` 里的“文件白名单 + Agent 绑定 + 过期时间 + 锁回”流程变成可执行命令。

## 运行方式

```bash
python governance/jbt_lockctl.py bootstrap
python governance/jbt_lockctl.py issue --task TASK-0001 --agent 模拟交易 --files services/sim-trading/src/app.py
python governance/jbt_lockctl.py validate --token <TOKEN> --task TASK-0001 --agent 模拟交易 --files services/sim-trading/src/app.py
python governance/jbt_lockctl.py lockback --token <TOKEN> --result approved --review-id REVIEW-TASK-0001
```

## 本地状态目录

锁控器会把本地状态写到：

- `.jbt/lockctl/config.json`
- `.jbt/lockctl/tokens.json`
- `.jbt/lockctl/events.jsonl`

这些文件已经被 `.gitignore` 忽略，不会进入 Git。

## 安全说明

1. 当前版本适用于本地开发治理，不是远程零信任密钥系统。
2. 当前版本将签名密钥保存于本地 `.jbt` 状态目录。
3. 若后续需要更强安全性，下一步可以迁移到 macOS Keychain 或独立签发服务。
