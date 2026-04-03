---
applyTo: "services/**"
description: "Use when: 开发 JBT 任一服务目录时，强制保持服务隔离、禁止跨服务 import 和跨目录读写"
---

# Service Isolation

当你修改 `services/**` 下的任意文件时，必须遵守：

1. 只能修改当前服务目录中的业务代码。
2. 不得直接 import 其他服务的 `src` 模块。
3. 不得直接读取其他服务的账本、日志或配置目录。
4. 共享模型进入 `shared/contracts`，共享无状态工具进入 `shared/python-common`。
5. 如需旧系统兼容，只能通过 `integrations/legacy-botquant` 适配。
6. 未经过任务登记、Architect 预审和 Jay.S Token 解锁，不得修改任何锁定文件。
7. 修改完成后必须返回 Architect 终审，不得自行宣布完成。
