# Qwen Audit Collaboration

【签名】Atlas
【时间】2026-04-11
【设备】MacBook

## 1. 用途

1. 本目录是 Atlas 与 Roo/Qwen 的固定协同投递区。
2. Atlas 只通过本目录下的任务单向 Qwen 派发项目级只读审查任务。
3. Qwen 必须把最终审查结果和整改方案写回本目录指定文件，Atlas 再直接读取这些文件复核。
4. Atlas 看不到 Roo/Qwen 聊天框里的自然语言往返；只有写入仓库文件的内容，Atlas 才能稳定读取并复核。

## 2. 文件角色

1. `ATLAS_TO_QWEN_AUDIT.md`
   Atlas 写；Qwen 读。用于下发当前轮次审查要求。
2. `QWEN_AUDIT_REPORT.md`
   Qwen 写；Atlas 读。用于提交问题清单、风险结论和证据。
3. `QWEN_AUDIT_PLAN.md`
   Qwen 写；Atlas 读。用于提交整改方案、拆批建议和执行顺序。

## 3. 工作规则

1. 当前目录只承接项目级只读审查，不构成任何代码写授权。
2. Qwen 在本轮默认只读；若审查结论认为必须改代码，也只能先写方案，不能直接落写业务文件。
3. Qwen 不得在本目录中发明正式 `TASK-XXXX` 编号；如需拆批，只能写成“建议批次”或“建议阶段”。
4. 若 Qwen 发现某个建议路径在仓库中不存在，必须明确标注“猜测路径”或“未确认存在”，不得直接当成白名单建议。
5. 若用户要发起下一轮审查，优先覆盖更新 `ATLAS_TO_QWEN_AUDIT.md`，再让 Qwen 覆盖更新两份回执文件。

## 4. 直接给 Roo/Qwen 的最短启动口令

请读取 `docs/handoffs/qwen-audit-collab/ATLAS_TO_QWEN_AUDIT.md`，按其中要求完成只读审查，并把结果写回 `QWEN_AUDIT_REPORT.md` 与 `QWEN_AUDIT_PLAN.md`。不要修改任何业务代码。