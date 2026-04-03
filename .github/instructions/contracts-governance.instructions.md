---
applyTo: "shared/contracts/**"
description: "Use when: 定义或修改跨服务 API 契约、字段模型、请求响应结构时，强制先契约后实现"
---

# Contracts Governance

当你修改 `shared/contracts/**` 时，必须遵守：

1. 契约变更优先于实现变更。
2. 字段命名必须稳定、可复用、避免绑定某个服务的内部实现。
3. 模拟交易和实盘交易可以复用契约，但不能混用账本目录。
4. 一切跨服务调用以契约为唯一边界，不允许用临时字段硬连。
5. 修改 `shared/contracts/**` 前必须先完成 Architect 预审并获得 Jay.S 对指定文件的 Token。
6. 契约修改完成后，必须由 Architect 终审后再锁回。
