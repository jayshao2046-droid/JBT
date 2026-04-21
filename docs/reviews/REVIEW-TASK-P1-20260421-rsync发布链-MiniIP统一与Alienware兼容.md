# REVIEW-TASK-P1-20260421-rsync发布链-MiniIP统一与Alienware兼容

【状态】通过
【日期】2026-04-21
【审核】Atlas

## 预审结论

通过，允许按最小范围收口当前 rsync 发布链。

## 冻结结论

1. 本批只处理现役治理脚本，不触及任何服务业务代码。
2. Mini 地址统一仅限“当前会真实被执行的发布链入口”，不清洗历史审计材料。
3. Alienware 必须单独走 Windows 分支，不能继续复用 Unix 的 docker / nohup 模型。
4. 发布链扩容到 `sim-trading`、`researcher` 属于同一治理脚本内的兼容补齐，不视为跨服务代码改造。

## 白名单

1. governance/scripts/jbt_rsync_deploy.sh
2. governance/scripts/jbt_rsync_rollback.sh

## 验收要求

1. bash 语法检查通过。
2. dry-run 离线预演通过。
3. Mini 76 与 Alienware Windows 分支逻辑清晰可审计。

## 复核结果

通过。

### 复核证据

1. `bash -n governance/scripts/jbt_rsync_deploy.sh` 通过。
2. `bash -n governance/scripts/jbt_rsync_rollback.sh` 通过。
3. `jbt_rsync_deploy.sh --service data --dry-run` 输出目标为 `jaybot@192.168.31.76:~/JBT/services/data/`。
4. `jbt_rsync_deploy.sh --service sim-trading --dry-run` 输出目标为 `17621@192.168.31.223:C:/Users/17621/jbt/services/sim-trading/`。
5. `jbt_rsync_deploy.sh --service researcher --dry-run` 输出目标为 `17621@192.168.31.223:C:/Users/17621/jbt/services/data/`。
6. 只读远端验证通过：Alienware 上 `C:/Users/17621/jbt/services/data` 与 `C:/Users/17621/jbt/services/sim-trading` 均可通过 `powershell -EncodedCommand` 正常访问。

### 复核结论

1. 现役发布链入口的 Mini 旧地址已收口。
2. Windows 分支不再复用 Unix 引号层和重启模型。
3. 历史审计文档中的旧 IP 未批量替换，保留历史事实。