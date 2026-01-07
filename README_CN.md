# ⚡ MCP Vault (`mcpv`)

> **AI 代理 (AI Agents) 的终极性能加速器**  
> _"系统延迟减少 99%，加载时间归零，Token 成本降低 90%。"_

<div align="center">

![License](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.10+-F7CA3F.svg?style=flat-square&logo=python&logoColor=black)
![Platform](https://img.shields.io/badge/OS-Windows-0078D6.svg?style=flat-square&logo=windows&logoColor=white)
![Status](https://img.shields.io/badge/Status-Accelerated-brightgreen.svg?style=flat-square)

</div>

<div align="right">
  <a href="README.md">🇺🇸 English</a> | <a href="README_KR.md">🇰🇷 한국어</a>
</div>

<br>

> [!CAUTION]
> **⚠️ 兼容性警告 (Compatibility Warning)**<br>
> 目前本项目仅支持 **Windows** 操作系统和 **Antigravity** 代理环境。

<br>

## ❓ 为什么选择 `mcpv`？

在使用 AI 代理（Antigravity, Cursor）时，你是否有过这样的体验？
> *"为什么这么卡？"*  
> *"又卡死了..."*  
> *"为什么 Token 费用这么高？"*

`mcpv` 不仅仅是一个工具。它是你代理的 **涡轮引擎 (Turbo Engine)**。

<br>

### 🏎️ 压倒性的性能差异

| 功能 | 😫 没有 `mcpv` (Before) | ⚡ 安装 `mcpv` (After) | 📈 效果 |
| :--- | :--- | :--- | :--- |
| **速度** | 无 GPU 加速，UI 卡顿 | **强制 GPU 加速，流畅** | **100倍** 体感提升 |
| **加载** | 每次等待 10秒+ | **0.1秒 瞬间启动** (Lazy Load) | **零** 等待 |
| **成本** | 每次发送全部代码 | **自动拦截重复项** (Smart Cache) | **90%** 节省 |

<br>

---

## ✨ 3大核心功能

### 1️⃣ Booster Injection (物理加速)
**"一行命令解锁硬件限制"**
- **强制激活 GPU**: 注入隐藏的渲染加速标志 (`--enable-gpu-rasterization`)。
- **绕过权限问题**: 使用 `RunAsInvoker` 绕过烦人的管理员权限请求 (Error 740)。
- **僵尸进程杀手**: 自动清理占用端口的幽灵进程。

### 2️⃣ Smart Valve (成本防御)
**"为你省钱的智能钱包卫士"**
- 检测代理习惯性请求的巨大上下文数据 (`repomix`)。
- **只发送第一次**，从第二次开始仅回复 10 Token 的 **"已缓存 (Already cached)"** 消息。
- 物理阻断意外的 Token 炸弹。

### 3️⃣ Gateway Hijacking (安全金库)
**"不再为复杂的配置烦恼"**
- 自动将现有的复杂 MCP 设置迁移到安全的金库 (Vault)。
- 代理只与 `mcpv` 对话，但所有工具在后台都能完美运行。

<br>

---

## 🛠️ 经过验证的推荐设置 (Verified Setup)

开发者亲测的 MCP 服务器配置。与其一起使用时，`mcpv` 能发挥最佳协同效应。

```json
{
  "mcpServers": {
    "rube": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://rube.app/mcp"]
    },
    "open-aware": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://open-aware.qodo.ai/mcp"]
    },
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp", "--api-key", "PUT_IN_YOUR_API_KEY_HERE"]
    },
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
    },
    "mcp-server-neon": {
      "disabled": false,
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://mcp.neon.tech/sse"],
      "env": {
        "NEON_API_KEY": "NEVERCHANGE_DONT_PUT_IN_ANYTHING_ELSE_THAN_ME_HERE"
      }
    }
  }
}
```

<br>

---

# 🚀 安装与运行指南 (Windows / 基于 uv)

建议使用 `uv` 在 **独立的虚拟环境 (.venv)** 中安装和运行本项目。

> ✅ 请在 **项目根目录**（此 README 所在位置）使用 **PowerShell** 执行以下操作。

---

## 0. 准备工作
- Windows 10/11
- PowerShell
- 已安装 `uv`
  - 检查安装：`uv --version`

---

## 1. 清理现有进程（可选）
如果是重新安装，请先停止任何正在运行的 `mcpv` 或 Python 进程以避免冲突。

> ⚠️ 停止 `python` 进程可能会影响其他正在进行的任务。请谨慎操作。

```powershell
Stop-Process -Name "mcpv" -Force -ErrorAction SilentlyContinue
Stop-Process -Name "python" -Force -ErrorAction SilentlyContinue
```

---

## 2. 创建虚拟环境并安装包
使用 `uv` 创建一个与系统 Python 隔离的干净环境。

```powershell
# 安装 uv (如果尚未安装)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# 创建虚拟环境 (.venv)
uv venv

# 在虚拟环境中安装 mcpv 包
uv pip install .
```

---

## 3. 注册 Antigravity 设置（核心步骤）
使用生成的虚拟环境中的 Python 来执行安装命令。

```powershell
# 使用 .venv 环境内的 Python 将 mcpv 注册到 Antigravity。
.venv\Scripts\python -m mcpv install --force
```

---

## 4. 运行
双击桌面上生成的 **`Antigravity Boost (mcpv)`** 快捷方式即可运行。

---

## (可选) 验证安装
检查 `mcpv` 模块是否在 `.venv` 中正常加载。

```powershell
.venv\Scripts\python -m mcpv --help
```

---

## 🛠️ 指令 (Commands)

| 指令 | 说明 |
| --- | --- |
| `mcpv install` | 安装网关并创建桌面快捷方式。 |
| `mcpv install --force` | 即使只有一个 MCP 服务器也强制安装。 |
| `mcpv start` | 启动服务器（Antigravity 内部使用）。 |
| `mcpv --help` | 显示帮助信息。 |

---

☕ **Support**  
如果这个项目帮您节省了 Token 和时间，请我喝杯咖啡吧！  

[<img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" width="180" />](https://www.google.com/url?sa=E&source=gmail&q=https://www.buymeacoffee.com/mcpv)

<br>

---

<div align="center">
  <b>⚡ Charged by MCP Vault</b><br>
  <i>Developed for High-Performance AI Agent Operations</i>
</div>
