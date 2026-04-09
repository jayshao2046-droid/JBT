# Atlas 数据端迁移续工作提示词

把下面这段直接交给新的 Atlas 窗口：

你现在继续接管 JBT 项目的总项目经理工作，这一轮只处理“把 Mini 上已经稳定运行的 legacy 数据采集 / 调度 / 通知体系迁移到 JBT data Docker 体系”的治理、派发与续窗执行准备。JBT 当前是唯一项目管理来源；`J_BotQuant` 在本任务中只承担现网 inventory 的只读参考，不再承担 prompt / plan / context 来源。请严格按以下顺序读取并继续，不要跳过：

1. `ATLAS_PROMPT.md`
2. `docs/plans/ATLAS_MASTER_PLAN.md`
3. `PROJECT_CONTEXT.md`
4. `WORKFLOW.md`
5. `docs/prompts/总项目经理调度提示词.md`
6. `docs/prompts/公共项目提示词.md`
7. `docs/prompts/agents/总项目经理提示词.md`
8. `services/data/README.md`
9. `services/data/.env.example`
10. `services/data/src/main.py`
11. `services/data/tests/test_main.py`
12. `docs/handoffs/Atlas-全员协同执行提示词.md`
13. 只读检查 Mini 现网数据侧（需要命令时先向 Jay.S 展示命令并等确认）：
   - `~/J_BotQuant/collectors/`
   - `~/J_BotQuant/scripts/`
   - `crontab -l`
   - 如存在，再读 `~/J_BotQuant/scripts/system/`、`~/J_BotQuant/scripts/systemd/`、当前 Docker 容器状态

读取后先汇报以下事实，不要跳过：

1. JBT 已是唯一项目管理来源；`J_BotQuant` 在本任务里只承担现网 inventory 的只读参考，不再作为开工 prompt / plan / progress 来源。
2. JBT `services/data/` 当前只是最小供数 API，不等于已完成数据端迁移。
3. Mini 现网数据采集已经基本完整，但真实生产运行仍大量依赖 legacy system 级脚本、cron 与运维脚本，而不是纯 Docker 编排。
4. 这次用户要求的不是“补一个 data API”，而是把 **system 级采集 / 调度 / 健康检查 / 通知** 整体迁入 JBT Docker 体系。
5. 本次迁移的最高约束是：**24 小时连续执行，不允许停采，不允许因为迁移导致罢工。**
6. 飞书 / 邮件通道可以沿用，但 Mini 上已有旧 `send_feishu_*` / `send_email_*` 与其他旧消息推送实现；迁移前必须先盘点消息来源，避免新旧链路同时推送造成重复告警。
7. 当前 `TASK-0018-B` active token 只覆盖 `services/data/src/main.py` 与 `services/data/tests/test_main.py` 两文件，不足以承接这次完整迁移；**默认不得借该 token 越权开工。**

你在新窗口中的第一轮工作重点：

1. 先让项目架构师判定：这次“Mini 数据端 system 级迁移到 JBT Docker”是否必须新建独立 data 主任务；在没有预审结论前，默认不要并入 `TASK-0018-B`。
2. 先做 inventory，把 Mini 现网能力至少拆成 6 类：
   - 采集器本体（collectors）
   - 调度器 / cron / session 启停脚本
   - 健康检查 / 心跳 / 自愈
   - 备份 / 同步 / NAS / 清理
   - 通知 / 飞书 / 邮件 / 日报
   - 过渡期必须保留的 legacy 兼容壳
3. 先输出一份“迁移职责矩阵”，明确哪些逻辑应进入 `services/data/**`，哪些应作为部署层容器编排，哪些只应临时留在 `integrations/legacy-botquant/**`。
4. 先冻结迁移策略：**不得一次性停旧 cron 再切新 Docker**；必须采用 `inventory -> shadow run -> 分链切换 -> 观察 -> 全量切换 -> 回滚预案`。
5. 先冻结通知治理口径：飞书与邮件保留，但要统一到 JBT 标准模板；旧 push 脚本先盘点、分组、去重，禁止迁移期双发。
6. 若需要终端命令、远程探测、Docker 检查、git 操作、远端同步或现网服务验证，先把命令逐条汇报给 Jay.S，等待确认后再执行。

新窗口中的交付物顺序必须是：

1. 任务归属 / 是否新建独立任务的结论
2. Mini 数据端现网 inventory 清单
3. system 级脚本到 Docker 化的职责映射矩阵
4. 24h 无中断迁移方案与回滚方案
5. 通知去重与统一模板迁移方案
6. 需要项目架构师建档的 task / review / lock / handoff 列表
7. 只有在上述治理动作完成后，才允许进入具体代码派发

输出要求：

- 始终先汇报当前阻塞、当前派发、下一检查点。
- 必须明确提醒：这是数据端运行方式迁移，不是单纯 API 开发；默认先走项目架构师预审，不允许 Atlas 直接下场改 data 业务代码。
- 所有新动作优先落治理文件，不得先写 `services/data/**` 后补账本。
- 不要把“可以沿用飞书 / 邮件通道”误解成“继续保留旧消息脚本原样运行”；迁移前必须先完成消息源盘点与去重。
- 不要把“Mini 现有采集已完整”误解成“可以立刻停掉 legacy system 级脚本”；只有在 Docker 新链路经过 shadow run 和观察验证后，才允许逐链切换。