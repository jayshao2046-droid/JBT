# Atlas ↔ Alienware 交接单

> 最后更新: 2026-04-19  
> 用途: Atlas 无法通过 SSH 在 Windows 上可靠执行后台进程/PowerShell 命令，所有需要在 Alienware 本地执行的操作通过此文档交接。

---

## 当前待办（Alienware 侧执行）

### ✅ 已完成

| # | 事项 | 状态 |
|---|------|------|
| 1 | 3个 researcher 文件已 SCP 到位 (kline_analyzer.py, config.py, scheduler.py) | ✅ |
| 2 | tushare 包已安装 | ✅ |
| 3 | .env.researcher 已追加 TUSHARE_TOKEN | ✅ |
| 4 | start_researcher.bat 已重写（含 TUSHARE_TOKEN） | ✅ |
| 5 | wmic 启动了 researcher 后台进程 (PID 55292→cmd, python 可能为 41108) | ✅ |

### ⏳ 待验证 / 执行

| # | 事项 | 优先级 | 命令 |
|---|------|--------|------|
| 1 | 确认 researcher 服务正常监听 8199 | P0 | 见下方 |
| 2 | 如果没启动成功，手动重启 | P0 | 见下方 |
| 3 | 验证 tushare 日K获取正常 | P1 | 见下方 |

---

## 操作手册

### 1. 检查 researcher 是否在运行

```cmd
:: 在 Alienware 打开 CMD
netstat -ano | findstr 8199
```

如果有 `LISTENING`，说明服务正常。

### 2. 如果没启动 / 需要重启

```cmd
:: 先杀旧进程
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *researcher*" 2>nul

:: 用 start_researcher.bat 启动
cd /d C:\Users\17621\jbt\services\data
start_researcher.bat
```

或者手动启动（等效于 bat 内容）：

```cmd
cd /d C:\Users\17621\jbt\services\data
set OLLAMA_URL=http://localhost:11434
set DATA_API_URL=http://192.168.31.76:8105
set DECISION_API_URL=http://192.168.31.142:8104
set TUSHARE_TOKEN=e6db4d86105126f1f6f09fe933fb4c8cca044e7f94c4168317262eba
python run_researcher_server.py
```

### 3. 验证 tushare 日K拉取

```cmd
cd /d C:\Users\17621\jbt\services\data
set TUSHARE_TOKEN=e6db4d86105126f1f6f09fe933fb4c8cca044e7f94c4168317262eba
python -c "import tushare as ts; pro=ts.pro_api(); df=pro.fut_daily(ts_code='RB2510.SHF', start_date='20260414', end_date='20260418'); print(df.head())"
```

如果返回了 K 线数据，说明 tushare Token 和网络均正常。

### 4. 查看 researcher 启动日志（排错用）

```cmd
:: 如果用了 wmic 启动，日志可能不在文件里
:: 如果直接运行 start_researcher.bat，日志在终端窗口
:: 也可以查 Windows 事件查看器或加文件日志：
cd /d C:\Users\17621\jbt\services\data
set OLLAMA_URL=http://localhost:11434
set DATA_API_URL=http://192.168.31.76:8105
set DECISION_API_URL=http://192.168.31.142:8104
set TUSHARE_TOKEN=e6db4d86105126f1f6f09fe933fb4c8cca044e7f94c4168317262eba
python run_researcher_server.py > researcher.log 2>&1
:: 然后另开一个 CMD 窗口：
type C:\Users\17621\jbt\services\data\researcher.log
```

---

## Atlas 侧待办（MacBook 远程可完成）

| # | 事项 | 状态 | 备注 |
|---|------|------|------|
| 1 | SCP pipeline.py 到 Studio Decision | ⏳ | SSH jaybot@192.168.31.142 |
| 2 | 重启 Studio Decision 服务 | ⏳ | Docker 容器 |
| 3 | 整体功能验证 | ⏳ | 等 Alienware 侧确认后 |

---

## 协作约定

1. **Atlas → Alienware**：Atlas 把需要在 Alienware 执行的指令写在本文档"待办"区，标注优先级。
2. **Alienware → Atlas**：用户在 Alienware 执行完毕后，把结果（成功/失败/日志）反馈给 Atlas。
3. **Atlas 不再尝试通过 SSH 在 Alienware 上执行后台进程或 PowerShell 命令**（已证实不稳定）。
4. Atlas 仍可通过 SSH 做只读检查（如 `type`、`findstr`、`tasklist`、`netstat`）。
5. 文件传输（SCP）由 Atlas 直接完成，无需交接。

---

## 路径速查

| 项目 | 路径 |
|------|------|
| 项目根 | `C:\Users\17621\jbt\` |
| researcher 源码 | `C:\Users\17621\jbt\services\data\src\researcher\` |
| 启动脚本 | `C:\Users\17621\jbt\services\data\start_researcher.bat` |
| 环境配置 | `C:\Users\17621\jbt\services\data\.env.researcher` |
| Python | 系统 Python 3.11 (`C:\Users\17621\AppData\Local\Programs\Python\Python311\`) |
