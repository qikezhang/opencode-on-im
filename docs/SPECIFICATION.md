# OpenCode Cloudify 产品规格文档

> **版本**: v1.0  
> **日期**: 2026-01-13  
> **状态**: MVP 规格定稿  
> **时间线**: 6 周

---

## 目录

1. [产品概述](#1-产品概述)
2. [产品架构](#2-产品架构)
3. [功能规格](#3-功能规格)
4. [技术规格](#4-技术规格)
5. [用户体验流程](#5-用户体验流程)
6. [数据模型](#6-数据模型)
7. [API 设计](#7-api-设计)
8. [安全设计](#8-安全设计)
9. [部署架构](#9-部署架构)
10. [开发计划](#10-开发计划)
11. [风险与缓解](#11-风险与缓解)

---

## 1. 产品概述

### 1.1 产品定位

**OpenCode Cloudify** 是一个开箱即用的云端 AI 编程助手解决方案，将 OpenCode 封装为 Docker 镜像，集成 IM Bot、Web 终端和网络代理，让用户通过手机随时随地管理 AI 编程任务。

### 1.2 产品形态

```
┌─────────────────────────────────────────────────────────────────┐
│                     双产品漏斗架构                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   opencode-on-im (独立 PyPI 包)                                 │
│   ├── 定位: 轻量级 OpenCode IM 插件                              │
│   ├── 功能: Telegram/钉钉 Bot，纯 Python                        │
│   ├── 安装: pip install opencode-on-im                          │
│   ├── 用户: 极客、自建环境者                                     │
│   └── 转化: README 引导至 Cloudify                              │
│                         │                                        │
│                         ▼                                        │
│   opencode-cloudify (主产品)                                     │
│   ├── 定位: 云端 AI 员工完整解决方案                              │
│   ├── 功能: OpenCode + IM Bot + Web Terminal + 代理              │
│   ├── 安装: docker run / Deploy to DigitalOcean                 │
│   ├── 用户: 主流开发者                                           │
│   └── 变现: 联盟佣金 (VPS + 代理 IP)                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 商业模式

**带路党模式 (The Sherpa Model)**

| 收入管道 | 来源 | 预估佣金 |
|----------|------|----------|
| 算力管道 | DigitalOcean / Vultr VPS 推荐 | $25-100/用户 |
| 网络管道 | IPRoyal / Smartproxy 静态住宅代理 | $3-10/月/用户 |

**核心原则**:
- 代码 100% 开源 (MIT)
- 不卖软件，不加强制广告
- 卖 "环境"、"稳定性"、"省心"

### 1.4 目标用户

| 用户类型 | 特征 | 转化路径 |
|----------|------|----------|
| **A类: API 土豪** | 用官方 API Key，求稳 | VPS 佣金 |
| **B类: 会员白嫖党** | ChatGPT Plus/Gemini Advanced 用户 | VPS + 代理 IP 佣金 |
| **C类: 极客党** | 动手能力强，不愿付费 | 口碑传播 |

---

## 2. 产品架构

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           OpenCode Cloudify                                 │
│                         (Docker Container)                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        s6-overlay (进程管理)                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│           │                    │                    │                       │
│           ▼                    ▼                    ▼                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│  │   OpenCode      │  │  opencode-on-im │  │     ttyd        │            │
│  │   (Core)        │  │   (IM Bot)      │  │  (Web Terminal) │            │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘            │
│           │                    │                    │                       │
│           └────────────────────┼────────────────────┘                       │
│                                │                                            │
│                    ┌───────────▼───────────┐                               │
│                    │   Unified Message     │                               │
│                    │      Protocol         │                               │
│                    └───────────┬───────────┘                               │
│                                │                                            │
│           ┌────────────────────┼────────────────────┐                       │
│           ▼                    ▼                    ▼                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│  │    Session      │  │   Notification  │  │    Instance     │            │
│  │    Manager      │  │     Router      │  │    Registry     │            │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘            │
│                                │                                            │
│                    ┌───────────▼───────────┐                               │
│                    │   /data (Volume)      │                               │
│                    │   持久化存储           │                               │
│                    └───────────────────────┘                               │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  外部连接                                                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐                         │
│  │ Telegram │  │  钉钉    │  │ Residential Proxy │                         │
│  │   API    │  │   API    │  │   (可选)          │                         │
│  └──────────┘  └──────────┘  └──────────────────┘                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 模块职责

| 模块 | 职责 | 技术选型 |
|------|------|----------|
| **OpenCode Core** | AI 编程核心引擎 | 官方安装 |
| **opencode-on-im** | IM 消息处理、会话管理 | Python + aiogram + 钉钉 SDK |
| **ttyd** | Web 终端，备用操作入口 | ttyd (可切换 code-server) |
| **Session Manager** | 多实例会话状态管理 | 本地 JSON/SQLite |
| **Notification Router** | 消息分发、多用户广播 | asyncio |
| **Instance Registry** | 实例注册、二维码生成 | 本地存储 |
| **s6-overlay** | 进程管理、健康检查 | s6-overlay v3 |

---

## 3. 功能规格

### 3.1 MVP 功能清单

| 功能 | 优先级 | 状态 | 描述 |
|------|--------|------|------|
| Telegram 适配器 | P0 | MVP | 接收/发送消息，支持 Markdown + 图片 |
| 钉钉适配器 | P0 | MVP | 企业内部应用，消息卡片 |
| 二维码绑定 | P0 | MVP | 实例生成二维码，用户扫码绑定 |
| 多实例管理 | P0 | MVP | 一用户绑定多实例，命名+切换 |
| 多用户协作 | P0 | MVP | 多用户绑定同一实例，在线状态提示 |
| CLI 输出同步 | P0 | MVP | 接管 OpenCode 输出，推送到 IM |
| 长内容转图片 | P0 | MVP | 超过阈值自动转图片发送 |
| 移动端 Web CLI | P0 | MVP | ttyd 提供 Web 终端访问 |
| 踢人/重生二维码 | P0 | MVP | Owner 可重置绑定 |
| 代理配置 | P0 | MVP | 支持配置住宅代理 |
| 联盟链接嵌入 | P0 | MVP | README、启动向导、文档 |
| 升级检查 | P0 | MVP | 启动时检查新版本+推广内容 |

### 3.2 V1.0+ 功能（暂不实现）

| 功能 | 原因 |
|------|------|
| 权限审批按钮 | 复杂度高，MVP 后评估 |
| 内网穿透引导 | 用户自行解决，文档支持 |
| 语音转文字 | 依赖 OpenCode 多模态能力 |
| Matrix 适配器 | 用户量小，后续扩展 |
| Slack 适配器 | 企业市场，后续扩展 |

### 3.3 功能详细规格

#### 3.3.1 二维码绑定系统

**二维码内容结构**:
```json
{
  "instance_id": "uuid-v4",
  "instance_name": "my-project",
  "connect_secret": "hmac-sha256-signature",
  "local_endpoint": "127.0.0.1:4096",
  "created_at": 1736755200,
  "version": 1
}
```

**编码方式**: `base64url(JSON)`

**生命周期**:
- 永不自动过期
- 用户可手动作废并重新生成
- 重新生成后，旧二维码立即失效
- 所有已绑定用户被踢出，需重新扫码

**绑定流程**:
```
1. 用户扫描二维码
2. Bot 解析二维码内容
3. 验证 connect_secret 签名
4. 记录 (user_id, instance_id) 绑定关系
5. 发送欢迎消息 + 实例状态
```

#### 3.3.2 多实例管理

**实例命名规则**:
- 默认名称: 基于 OpenCode session 自动生成
- 格式: `{project-name}` 或 `{project-name}-{n}`
- 用户可修改，不可与已有名称冲突
- 冲突时自动追加 `-1`, `-2`, ...

**切换机制**:
```
/switch <instance-name>   # 切换当前活跃实例
/list                     # 列出所有绑定实例
/status                   # 查看当前实例状态
/unbind <instance-name>   # 解绑实例
```

#### 3.3.3 多用户协作

**协作模型**: 软提醒 (Soft Warning)

- 所有绑定用户权限相同
- 任何操作后，消息末尾显示在线用户列表
- 不锁定、不阻止并发操作
- 冲突由用户自行负责

**消息格式示例**:
```
[my-project] AI 回复:
这是代码修改建议...

---
📡 在线用户: @alice, @bob
```

**踢人机制**:
```
/reset-qr              # 重新生成二维码，踢出所有用户
/kick <username>       # 踢出指定用户 (V1.0+)
```

#### 3.3.4 消息输出处理

**输出分类与处理**:

| 输出类型 | 处理方式 | 示例 |
|----------|----------|------|
| 对话文本 | 完整发送 | AI 回复 |
| 短代码块 (≤10行) | Markdown 展开 | `print("hello")` |
| 长代码块 (>10行) | 转图片 | 大段代码 |
| Diff | 转图片 | +/- 行变更 |
| 工具调用日志 | 折叠/摘要 | "Reading 3 files..." |
| 错误堆栈 | 转图片 | Traceback |
| 进度指示 | 状态消息 | "Working..." |

**Telegram 处理**:
- Markdown V2 格式
- 超长内容分多条消息
- 代码/Diff 转 PNG 图片 (等宽字体渲染)

**钉钉处理**:
- 消息卡片格式
- 所有代码块转图片 (钉钉 Markdown 能力弱)
- 关键内容 + "查看详情" 链接

**消息积压处理**:
- 用户离线期间，最多保留最新 20 条消息
- 上线后推送: "您错过了 N 条消息" + 最新 20 条

#### 3.3.5 Web Terminal

**默认配置**: ttyd

**切换命令**:
```
/web-terminal ttyd          # 切换到 ttyd (轻量)
/web-terminal code-server   # 切换到 code-server (完整 IDE)
```

**访问方式**:
- IM Bot 发送卡片链接
- 用户点击在手机/电脑浏览器打开
- 需用户自行配置网络可达性

#### 3.3.6 代理配置

**配置方式**:

1. **环境变量**:
```bash
RESIDENTIAL_PROXY_URL=http://user:pass@ip:port
```

2. **启动向导**: 首次启动交互式询问

3. **配置文件** (`/data/config.yaml`):
```yaml
proxy:
  enabled: true
  url: "http://user:pass@ip:port"
  type: "residential"  # residential | datacenter
```

4. **IM 命令**:
```
/proxy set http://user:pass@ip:port
/proxy status
/proxy disable
```

---

## 4. 技术规格

### 4.1 技术栈

| 层级 | 选型 | 版本 | 理由 |
|------|------|------|------|
| **语言** | Python | 3.11+ | 用户熟悉，生态丰富 |
| **异步框架** | asyncio | 原生 | 标准库，无额外依赖 |
| **Telegram** | aiogram | 3.x | 最现代的异步 Telegram 库 |
| **钉钉** | dingtalk-sdk | 官方 | 官方支持，稳定 |
| **包管理** | Poetry | 1.7+ | 现代依赖管理 |
| **Web Terminal** | ttyd | latest | 轻量，移动端友好 |
| **进程管理** | s6-overlay | v3 | Docker 原生，现代 |
| **图片渲染** | Pillow + Pygments | latest | 代码高亮转图片 |
| **二维码** | qrcode | latest | 标准库 |
| **配置** | pydantic-settings | 2.x | 类型安全配置 |
| **持久化** | JSON + SQLite | - | 轻量，无外部依赖 |

### 4.2 目录结构

```
opencode-cloudify/
├── README.md                      # 主 README，含 Deploy 按钮
├── LICENSE                        # MIT
├── pyproject.toml                 # Poetry 配置
├── docker/
│   ├── Dockerfile                 # 主镜像构建
│   ├── Dockerfile.slim            # 精简版 (无 code-server)
│   ├── docker-compose.yml         # 本地开发
│   ├── docker-compose.prod.yml    # 生产部署
│   └── s6-overlay/
│       ├── s6-rc.d/
│       │   ├── opencode/
│       │   ├── opencode-on-im/
│       │   └── ttyd/
│       └── cont-init.d/
│           └── 00-init.sh
├── src/
│   └── opencode_on_im/            # 核心包 (发布到 PyPI)
│       ├── __init__.py
│       ├── __main__.py            # CLI 入口
│       ├── core/
│       │   ├── config.py          # 配置管理
│       │   ├── session.py         # 会话管理
│       │   ├── instance.py        # 实例注册
│       │   └── notification.py    # 通知路由
│       ├── adapters/
│       │   ├── base.py            # 适配器抽象
│       │   ├── telegram/
│       │   │   ├── __init__.py
│       │   │   ├── bot.py
│       │   │   ├── handlers.py
│       │   │   └── formatters.py
│       │   └── dingtalk/
│       │       ├── __init__.py
│       │       ├── bot.py
│       │       ├── handlers.py
│       │       └── formatters.py
│       ├── renderers/
│       │   ├── image.py           # 代码转图片
│       │   └── markdown.py        # Markdown 处理
│       ├── opencode/
│       │   ├── client.py          # OpenCode SDK 封装
│       │   ├── events.py          # 事件订阅
│       │   └── plugin.py          # 插件集成
│       └── utils/
│           ├── qrcode.py          # 二维码生成
│           ├── crypto.py          # 签名验证
│           └── storage.py         # 持久化
├── scripts/
│   ├── entrypoint.sh              # Docker 入口
│   ├── install-opencode.sh        # OpenCode 安装
│   └── setup-proxy.sh             # 代理配置
├── docs/
│   ├── SETUP_GUIDE.md             # 安装指南
│   ├── CONFIGURATION.md           # 配置参考
│   ├── PROXY_BEST_PRACTICE.md     # 代理最佳实践 (含联盟链接)
│   ├── DEPLOY_DIGITALOCEAN.md     # DO 部署教程 (含联盟链接)
│   ├── TELEGRAM_SETUP.md          # Telegram Bot 创建
│   ├── DINGTALK_SETUP.md          # 钉钉应用创建
│   └── TROUBLESHOOTING.md         # 常见问题
├── tests/
│   ├── conftest.py
│   ├── test_adapters/
│   ├── test_core/
│   └── test_renderers/
└── .github/
    ├── workflows/
    │   ├── ci.yml                 # 测试 + Lint
    │   ├── release.yml            # PyPI + Docker Hub 发布
    │   └── docker-build.yml       # 镜像构建
    └── ISSUE_TEMPLATE/
```

### 4.3 依赖清单

```toml
[tool.poetry.dependencies]
python = "^3.11"
aiogram = "^3.4"
dingtalk-sdk = "^2.0"
pydantic = "^2.6"
pydantic-settings = "^2.2"
aiohttp = "^3.9"
aiofiles = "^23.2"
pillow = "^10.2"
pygments = "^2.17"
qrcode = "^7.4"
aiosqlite = "^0.19"
structlog = "^24.1"
tenacity = "^8.2"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0"
pytest-asyncio = "^0.23"
pytest-cov = "^4.1"
ruff = "^0.2"
mypy = "^1.8"
```

### 4.4 Docker 镜像规格

**目标体积**: < 800MB (精简版)

| 组件 | 体积 | 包含 |
|------|------|------|
| 基础镜像 (python:3.11-slim) | ~150MB | Python 运行时 |
| Node.js (OpenCode 依赖) | ~100MB | Node 20 LTS |
| OpenCode CLI | ~50MB | 核心程序 |
| opencode-on-im | ~20MB | Python 包 |
| ttyd | ~5MB | Web 终端 |
| s6-overlay | ~10MB | 进程管理 |
| 系统依赖 | ~100MB | 字体、图形库 |
| **总计 (slim)** | **~450MB** | |
| code-server (可选) | +400MB | 完整 VS Code |
| **总计 (full)** | **~850MB** | |

**镜像 Tag**:
- `latest` / `slim`: 精简版，默认 ttyd
- `full`: 包含 code-server
- `x.y.z`: 版本号

---

## 5. 用户体验流程

### 5.1 首次安装流程

```
┌─────────────────────────────────────────────────────────────────┐
│                     首次安装用户旅程                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 发现 (GitHub/Reddit/HN)                                     │
│     │                                                           │
│     ▼                                                           │
│  2. 点击 [Deploy to DigitalOcean] 按钮 ────────► 联盟链接       │
│     │                                                           │
│     ▼                                                           │
│  3. 创建 Droplet，自动拉取 Docker 镜像                          │
│     │                                                           │
│     ▼                                                           │
│  4. 首次启动向导                                                │
│     ├── 输入 Telegram Bot Token                                │
│     ├── (可选) 输入钉钉配置                                     │
│     └── (可选) 配置代理 URL ────────────────────► 联盟链接      │
│     │                                                           │
│     ▼                                                           │
│  5. 终端显示二维码                                              │
│     │                                                           │
│     ▼                                                           │
│  6. 手机扫码，绑定 Telegram Bot                                 │
│     │                                                           │
│     ▼                                                           │
│  7. 收到欢迎消息，开始使用                                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 日常使用流程

```
┌─────────────────────────────────────────────────────────────────┐
│                       日常使用流程                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  用户在手机 Telegram                                            │
│     │                                                           │
│     ├── 发送文字指令 ──────► OpenCode 执行 ──────► 结果推送     │
│     │                                                           │
│     ├── 发送语音消息 ──────► 直传 OpenCode (需多模态支持)        │
│     │                                                           │
│     ├── 收到长代码 ────────► 自动转图片显示                      │
│     │                                                           │
│     ├── 点击卡片链接 ──────► 打开 Web Terminal (ttyd)            │
│     │                                                           │
│     ├── /switch project-2 ─► 切换到另一个实例                   │
│     │                                                           │
│     └── /status ───────────► 查看实例状态 + 在线用户            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 5.3 IM Bot 命令列表

| 命令 | 描述 | 示例 |
|------|------|------|
| `/start` | 开始使用，显示帮助 | `/start` |
| `/help` | 显示命令帮助 | `/help` |
| `/status` | 当前实例状态 + 在线用户 | `/status` |
| `/list` | 列出所有绑定实例 | `/list` |
| `/switch <name>` | 切换活跃实例 | `/switch my-project` |
| `/rename <new>` | 重命名当前实例 | `/rename api-server` |
| `/unbind <name>` | 解绑实例 | `/unbind old-project` |
| `/reset-qr` | 重新生成二维码，踢出所有用户 | `/reset-qr` |
| `/web` | 获取 Web Terminal 链接 | `/web` |
| `/web-terminal <type>` | 切换终端类型 | `/web-terminal code-server` |
| `/proxy set <url>` | 设置代理 | `/proxy set http://...` |
| `/proxy status` | 查看代理状态 | `/proxy status` |
| `/proxy disable` | 禁用代理 | `/proxy disable` |
| `/sessions` | 列出 OpenCode 会话 | `/sessions` |
| `/cancel` | 取消当前任务 | `/cancel` |

---

## 6. 数据模型

### 6.1 持久化存储结构

**存储位置**: `/data/`

```
/data/
├── config.yaml              # 用户配置
├── instances.json           # 实例注册信息
├── bindings.db              # SQLite: 用户绑定关系
└── cache/
    └── rendered/            # 图片缓存
```

### 6.2 数据模型定义

```python
# config.yaml
class Config(BaseSettings):
    telegram_token: str | None = None
    dingtalk_app_key: str | None = None
    dingtalk_app_secret: str | None = None
    dingtalk_agent_id: str | None = None
    
    proxy_enabled: bool = False
    proxy_url: str | None = None
    
    web_terminal: Literal["ttyd", "code-server"] = "ttyd"
    web_terminal_port: int = 7681
    
    message_image_threshold: int = 10  # 行数
    max_offline_messages: int = 20
    
    opencode_port: int = 4096

# instances.json
class Instance(BaseModel):
    id: str                    # UUID
    name: str                  # 用户可读名称
    opencode_session_id: str   # OpenCode session ID
    connect_secret: str        # HMAC 签名密钥
    created_at: datetime
    qr_version: int = 1        # 二维码版本，重置时+1

# bindings.db (SQLite)
# Table: bindings
# | id | platform | user_id | instance_id | bound_at | last_active |
# | 1  | telegram | 123456  | uuid-xxx    | ...      | ...         |

# Table: offline_messages  
# | id | instance_id | user_id | content | created_at |
```

---

## 7. API 设计

### 7.1 适配器抽象接口

```python
from abc import ABC, abstractmethod
from typing import AsyncIterator

class BaseAdapter(ABC):
    """IM 平台适配器基类"""
    
    @abstractmethod
    async def start(self) -> None:
        """启动 Bot"""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """停止 Bot"""
        pass
    
    @abstractmethod
    async def send_text(
        self, 
        user_id: str, 
        text: str,
        parse_mode: str | None = None
    ) -> None:
        """发送文本消息"""
        pass
    
    @abstractmethod
    async def send_image(
        self, 
        user_id: str, 
        image: bytes,
        caption: str | None = None
    ) -> None:
        """发送图片消息"""
        pass
    
    @abstractmethod
    async def send_card(
        self,
        user_id: str,
        title: str,
        content: str,
        buttons: list[dict]
    ) -> None:
        """发送卡片消息"""
        pass
    
    @abstractmethod
    def on_message(self) -> AsyncIterator[IncomingMessage]:
        """接收消息流"""
        pass
```

### 7.2 OpenCode 集成接口

```python
class OpenCodeClient:
    """OpenCode SDK 封装"""
    
    async def create_session(self, title: str) -> Session:
        """创建新会话"""
        pass
    
    async def send_message(
        self, 
        session_id: str, 
        content: str,
        attachments: list[bytes] | None = None  # 语音等
    ) -> None:
        """发送消息到会话"""
        pass
    
    async def subscribe_events(
        self, 
        session_id: str
    ) -> AsyncIterator[Event]:
        """订阅会话事件流"""
        pass
    
    async def cancel_task(self, session_id: str) -> None:
        """取消当前任务"""
        pass
    
    async def get_session_status(self, session_id: str) -> SessionStatus:
        """获取会话状态"""
        pass
```

### 7.3 升级检查 API

**端点**: `GET https://api.opencode-cloudify.dev/v1/check-update`

**请求**:
```json
{
  "version": "1.0.0",
  "platform": "docker",
  "instance_id": "anonymous-hash"
}
```

**响应**:
```json
{
  "latest_version": "1.1.0",
  "update_available": true,
  "release_notes_url": "https://github.com/.../releases/tag/v1.1.0",
  "promotion": {
    "enabled": true,
    "message": "🎉 DigitalOcean 本月活动: 新用户 $200 免费额度",
    "link": "https://m.do.co/c/xxx",
    "expires_at": "2026-02-01"
  }
}
```

---

## 8. 安全设计

### 8.1 威胁模型

| 威胁 | 风险等级 | 缓解措施 |
|------|----------|----------|
| 二维码泄露 | 高 | 支持重置、签名验证 |
| IM Token 泄露 | 高 | 环境变量/配置文件，不存日志 |
| 中间人攻击 | 中 | HTTPS 强制，代理加密 |
| 未授权访问 | 中 | 仅服务已绑定用户 |
| DoS 攻击 | 低 | 速率限制 |

### 8.2 安全措施

**二维码签名**:
```python
import hmac
import hashlib

def generate_connect_secret(instance_id: str, secret_key: str) -> str:
    return hmac.new(
        secret_key.encode(),
        instance_id.encode(),
        hashlib.sha256
    ).hexdigest()[:32]
```

**绑定验证**:
```python
async def verify_binding(qr_data: dict, secret_key: str) -> bool:
    expected = generate_connect_secret(qr_data["instance_id"], secret_key)
    return hmac.compare_digest(expected, qr_data["connect_secret"])
```

**数据隔离**:
- 所有数据本地存储，不上传
- 升级检查 API 仅传输版本号和匿名 hash
- 无遥测、无追踪

---

## 9. 部署架构

### 9.1 推荐部署方式

**目标平台**: DigitalOcean Droplet (联盟首选)

**最低配置**:
- 1 vCPU
- 1 GB RAM
- 25 GB SSD
- Ubuntu 22.04

**一键部署脚本**:
```bash
curl -fsSL https://get.opencode-cloudify.dev | bash
```

**Docker Compose 部署**:
```yaml
version: '3.8'

services:
  cloudify:
    image: opencode-cloudify/cloudify:latest
    container_name: opencode-cloudify
    restart: unless-stopped
    ports:
      - "7681:7681"  # Web Terminal
    volumes:
      - cloudify-data:/data
    environment:
      - TELEGRAM_TOKEN=${TELEGRAM_TOKEN}
      - DINGTALK_APP_KEY=${DINGTALK_APP_KEY}
      - DINGTALK_APP_SECRET=${DINGTALK_APP_SECRET}
      - RESIDENTIAL_PROXY_URL=${RESIDENTIAL_PROXY_URL:-}
    
volumes:
  cloudify-data:
```

### 9.2 网络配置

**用户自行负责**:
- 公网 IP 或内网穿透 (Tailscale/Cloudflare Tunnel)
- 防火墙开放端口 7681 (Web Terminal)
- HTTPS 反向代理 (可选，推荐)

**文档引导**:
- 提供 Tailscale 安装教程
- 提供 Cloudflare Tunnel 配置示例
- 提供 Nginx 反代配置

---

## 10. 开发计划

### 10.1 6 周 MVP 里程碑

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           6 周开发计划                                       │
├──────────┬──────────────────────────────────────────────────────────────────┤
│ Week 1   │ 项目初始化 + 核心框架                                             │
│          │ ├── 项目结构、Poetry、CI/CD                                      │
│          │ ├── 配置管理 (pydantic-settings)                                 │
│          │ ├── 持久化层 (JSON + SQLite)                                     │
│          │ └── 适配器抽象接口                                               │
├──────────┼──────────────────────────────────────────────────────────────────┤
│ Week 2   │ Telegram 适配器                                                   │
│          │ ├── aiogram 集成                                                 │
│          │ ├── 消息收发                                                     │
│          │ ├── 命令处理器                                                   │
│          │ └── Markdown + 图片发送                                          │
├──────────┼──────────────────────────────────────────────────────────────────┤
│ Week 3   │ OpenCode 集成 + 二维码系统                                        │
│          │ ├── OpenCode SDK 封装                                            │
│          │ ├── 事件订阅 + 输出转发                                          │
│          │ ├── 二维码生成 + 绑定验证                                        │
│          │ └── 多实例管理                                                   │
├──────────┼──────────────────────────────────────────────────────────────────┤
│ Week 4   │ 钉钉适配器 + 图片渲染                                             │
│          │ ├── 钉钉 SDK 集成                                                │
│          │ ├── 消息卡片格式                                                 │
│          │ ├── 代码转图片 (Pillow + Pygments)                               │
│          │ └── 长内容自动转图片                                             │
├──────────┼──────────────────────────────────────────────────────────────────┤
│ Week 5   │ Docker 镜像 + Web Terminal                                        │
│          │ ├── Dockerfile 编写                                              │
│          │ ├── s6-overlay 配置                                              │
│          │ ├── ttyd 集成                                                    │
│          │ ├── 代理配置支持                                                 │
│          │ └── 首次启动向导                                                 │
├──────────┼──────────────────────────────────────────────────────────────────┤
│ Week 6   │ 文档 + 测试 + 发布                                                │
│          │ ├── 完整文档 (含联盟链接)                                        │
│          │ ├── 单元测试 + 集成测试                                          │
│          │ ├── PyPI 发布 (opencode-on-im)                                   │
│          │ ├── Docker Hub 发布                                              │
│          │ └── GitHub Release + 推广素材                                    │
└──────────┴──────────────────────────────────────────────────────────────────┘
```

### 10.2 任务分解 (GitHub Issues)

**Week 1: 项目初始化** (5 issues)
1. `[INFRA]` 项目结构初始化 + Poetry 配置
2. `[INFRA]` GitHub Actions CI/CD 配置
3. `[CORE]` 配置管理模块 (pydantic-settings)
4. `[CORE]` 持久化层实现 (storage.py)
5. `[CORE]` 适配器抽象接口定义

**Week 2: Telegram 适配器** (5 issues)
6. `[ADAPTER]` aiogram Bot 基础框架
7. `[ADAPTER]` Telegram 消息处理器
8. `[ADAPTER]` Telegram 命令路由
9. `[ADAPTER]` Markdown 格式化器
10. `[ADAPTER]` 图片发送支持

**Week 3: OpenCode 集成** (5 issues)
11. `[CORE]` OpenCode SDK 客户端封装
12. `[CORE]` 事件订阅 + 输出转发
13. `[CORE]` 二维码生成 + 签名
14. `[CORE]` 绑定验证 + 用户管理
15. `[CORE]` 多实例会话管理

**Week 4: 钉钉 + 渲染** (5 issues)
16. `[ADAPTER]` 钉钉 SDK 集成
17. `[ADAPTER]` 钉钉消息卡片格式
18. `[RENDER]` 代码高亮渲染器 (Pygments)
19. `[RENDER]` 代码转图片 (Pillow)
20. `[CORE]` 长内容自动转图片逻辑

**Week 5: Docker + Web** (5 issues)
21. `[DOCKER]` Dockerfile 编写
22. `[DOCKER]` s6-overlay 进程管理配置
23. `[DOCKER]` ttyd 集成 + 切换支持
24. `[CORE]` 代理配置模块
25. `[UX]` 首次启动交互向导

**Week 6: 发布** (5 issues)
26. `[DOCS]` README + 安装指南
27. `[DOCS]` 代理最佳实践 (含联盟链接)
28. `[DOCS]` DigitalOcean 部署教程
29. `[TEST]` 单元测试 + 集成测试
30. `[RELEASE]` PyPI + Docker Hub 发布

---

## 11. 风险与缓解

### 11.1 技术风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| OpenCode API 变更 | 中 | 高 | 锁定 SDK 版本，监控上游 |
| IM 平台封禁/限制 | 低 | 高 | 多平台支持，长轮询模式 |
| 镜像体积过大 | 中 | 中 | 多阶段构建，slim 版本 |
| 钉钉审核不过 | 中 | 中 | 企业内部应用，绕过审核 |

### 11.2 商业风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 联盟佣金取消 | 低 | 高 | 多平台联盟，分散风险 |
| 被 Fork 分流 | 中 | 中 | 主动分拆策略，控制叙事 |
| 用户采用缓慢 | 中 | 中 | 内容营销，社区运营 |
| 官方下场竞争 | 低 | 高 | 差异化定位 (BYOC + 性价比) |

### 11.3 运营风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 维护倦怠 | 高 | 高 | 模块化设计，吸引贡献者 |
| 用户支持压力 | 中 | 中 | 完善文档，FAQ，社区互助 |
| 安全漏洞 | 低 | 高 | 代码审计，依赖更新 |

---

## 附录

### A. 联盟链接嵌入点清单

| 位置 | 类型 | 链接目标 |
|------|------|----------|
| README.md 首页 | Deploy 大按钮 | DigitalOcean |
| README.md 底部 | 推荐代理服务 | IPRoyal |
| 首次启动向导 | 代理配置提示 | IPRoyal |
| PROXY_BEST_PRACTICE.md | 详细教程 | IPRoyal |
| DEPLOY_DIGITALOCEAN.md | 完整教程 | DigitalOcean |
| Docker Hub 描述 | 部署链接 | DigitalOcean |
| 升级检查 API 响应 | 推广消息 | 动态内容 |
| Bot 欢迎消息 | 可选提示 | 根据配置 |
| IP 被封报错 | 解决方案推荐 | IPRoyal |

### B. 术语表

| 术语 | 定义 |
|------|------|
| Cloudify | OpenCode Cloudify 项目简称 |
| 实例 | 一个运行中的 OpenCode 进程 |
| 绑定 | IM 用户与实例的关联关系 |
| 适配器 | IM 平台接入模块 |
| 会话 | OpenCode 中的一个对话上下文 |

### C. 参考资料

- [OpenCode 官方仓库](https://github.com/anomalyco/opencode)
- [aiogram 文档](https://docs.aiogram.dev/)
- [钉钉开发文档](https://open.dingtalk.com/)
- [s6-overlay](https://github.com/just-containers/s6-overlay)
- [ttyd](https://github.com/tsl0922/ttyd)

---

*文档生成时间: 2026-01-13*  
*版本: v1.0*  
*作者: Sisyphus AI Agent*
