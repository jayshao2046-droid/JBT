# 向 Atlas 申请看板端 Token

## 申请概述

**申请人**: Roo (Claude Agent)  
**申请时间**: 2026-04-13  
**申请目的**: 统一门户系统开发 - 整合四端看板为统一网站  
**预计工作量**: 17天（约3周）  

---

## Token 申请清单

### 1. 模拟交易端 (sim-trading)
- **服务路径**: `services/sim-trading/`
- **Token 编号**: `SIMWEB-TOKEN-01`
- **授权范围**: 
  - 读取: `services/sim-trading/**/*`
  - 写入: `services/sim-trading/**/*`
  - 排除: `services/sim-trading/node_modules/**`, `services/sim-trading/.next/**`
- **授权操作**: 读取、编辑、创建、删除
- **有效期**: 30天
- **用途**: 整合模拟交易看板到统一门户，调整路由、API代理、组件结构

### 2. 回测端 (backtest)
- **服务路径**: `services/backtest/`
- **Token 编号**: `BACKWEB-TOKEN-01`
- **授权范围**: 
  - 读取: `services/backtest/**/*`
  - 写入: `services/backtest/**/*`
  - 排除: `services/backtest/node_modules/**`, `services/backtest/.next/**`
- **授权操作**: 读取、编辑、创建、删除
- **有效期**: 30天
- **用途**: 整合回测看板到统一门户，调整路由、API代理、组件结构

### 3. 数据端 (data)
- **服务路径**: `services/data/`
- **Token 编号**: `DATAWEB-TOKEN-01`
- **授权范围**: 
  - 读取: `services/data/**/*`
  - 写入: `services/data/**/*`
  - 排除: `services/data/node_modules/**`, `services/data/.next/**`
- **授权操作**: 读取、编辑、创建、删除
- **有效期**: 30天
- **用途**: 整合数据看板到统一门户，调整路由、API代理、组件结构

### 4. 决策端 (decision)
- **服务路径**: `services/decision/`
- **Token 编号**: `DECWEB-TOKEN-01`
- **授权范围**: 
  - 读取: `services/decision/**/*`
  - 写入: `services/decision/**/*`
  - 排除: `services/decision/node_modules/**`, `services/decision/.next/**`
- **授权操作**: 读取、编辑、创建、删除
- **有效期**: 30天
- **用途**: 整合决策看板到统一门户，调整路由、API代理、组件结构

### 5. 统一门户 (portal)
- **服务路径**: `services/portal/`
- **Token 编号**: `PORTAL-TOKEN-01`
- **授权范围**: 
  - 读取: `services/portal/**/*`
  - 写入: `services/portal/**/*`
  - 排除: `services/portal/node_modules/**`, `services/portal/.next/**`
- **授权操作**: 读取、编辑、创建、删除
- **有效期**: 30天
- **用途**: 开发统一门户主体，包含登录页、首页、系统设置页、四端整合

### 6. 门户设计文档
- **文档路径**: `docs/portal-design/`
- **Token 编号**: `PORTAL-DOC-TOKEN-01`
- **授权范围**: 
  - 读取: `docs/portal-design/**/*`
  - 写入: `docs/portal-design/**/*`
- **授权操作**: 读取、编辑、创建
- **有效期**: 30天
- **用途**: 更新设计文档、技术方案、工作流程文档

---

## 工作计划概览

### 阶段 1: 准备阶段（已完成）
- ✅ 创建统一门户骨架项目
- ✅ 复制四端页面到临时文件夹
- ✅ 打包为 v0 参考包（6.4MB 干净版本）
- ✅ 编写完整设计文档和技术方案

### 阶段 2: v0 设计阶段（等待中）
- ⏳ 将参考包提供给 v0
- ⏳ v0 完成登录页、首页、系统设置页设计
- ⏳ v0 统一四端底色和组件规范

### 阶段 3: 整合阶段（需要 Token）
- 🔒 将 v0 输出整合到 portal 项目
- 🔒 调整四端路由结构（加服务前缀）
- 🔒 合并 API 代理配置
- 🔒 统一组件库和样式
- 🔒 实现统一导航和认证

### 阶段 4: API 对接阶段（需要 Token）
- 🔒 对接四个后端服务 API
- 🔒 实现统一的 API 客户端
- 🔒 配置环境变量和代理

### 阶段 5: 验证和交付阶段（需要 Token）
- 🔒 验证所有功能和 KPI
- 🔒 测试四端页面集成
- 🔒 测试登录、权限、设置功能
- 🔒 性能优化和最终调试

---

## 风险控制

### 1. 代码安全
- 所有修改将通过 Git 版本控制
- 重要修改前会创建备份分支
- 遵循项目现有的代码规范和架构模式

### 2. 功能完整性
- 不会删除或破坏现有功能
- 只进行整合和增强，不做破坏性修改
- 保持四端现有 API 接口不变

### 3. 可回滚性
- 每个阶段完成后提交独立 commit
- 可随时回滚到任意阶段
- 保留原有四端项目作为备份

### 4. 测试覆盖
- 整合后进行全面功能测试
- 验证所有 KPI 和数据展示
- 确保四端功能无损迁移

---

## 预期产出

### 1. 统一门户网站
- **地址**: `http://localhost:3000`
- **功能**: 登录页 + 首页 + 系统设置页 + 四端看板
- **路由结构**:
  - `/` - 首页（总控台）
  - `/login` - 登录页
  - `/settings` - 系统设置页
  - `/sim-trading/*` - 模拟交易看板
  - `/backtest/*` - 回测看板
  - `/data/*` - 数据看板
  - `/decision/*` - 决策看板

### 2. 统一技术栈
- **前端**: Next.js 15 + React 19 + TypeScript
- **UI 库**: shadcn/ui（统一黑色底色基调）
- **图表**: recharts
- **状态管理**: React Context + SWR
- **认证**: JWT + RBAC + 会员等级

### 3. 统一后端代理
- **模拟交易**: `http://localhost:8001`
- **回测**: `http://localhost:8002`
- **数据**: `http://localhost:8003`
- **决策**: `http://localhost:8004`

### 4. 完整文档
- 统一门户系统设计方案
- 四端看板合并技术调整方案
- 看板端完整开发部署工作流程
- API 对接文档
- 部署和运维文档

---

## 申请理由

1. **用户明确需求**: 用户要求将四个独立看板合并为统一门户网站
2. **技术可行性**: 已完成技术方案设计和骨架搭建，技术路径清晰
3. **工作量合理**: 预计 17 天工作量，分 10 个阶段实施，风险可控
4. **产出价值高**: 统一门户将大幅提升用户体验和系统一致性
5. **安全可控**: 所有修改可追溯、可回滚，不影响现有功能

---

## 请求 Atlas 审批

请 Atlas 审批以上 6 个 Token 的申请，授权 Roo 进行统一门户系统的开发工作。

**申请状态**: 等待审批  
**预计开始时间**: Token 签发后立即开始  
**预计完成时间**: Token 签发后 17 个工作日内完成  

---

*本文档由 Roo 生成，用于向 Atlas 申请看板端开发 Token*
