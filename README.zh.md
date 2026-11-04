# Agnes Image & Video

<p align="center">
  <a href="https://github.com/yinjianjun1/agnes-image-video-skills/blob/main/README.md">🇺🇸 English</a> |
  <a href="https://github.com/yinjianjun1/agnes-image-video-skills/blob/main/README.zh.md">🇨🇳 简体中文</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.9%2B-yellow?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.9+">
  <img src="https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-blue?style=for-the-badge" alt="跨平台">
  <a href="https://github.com/yinjianjun1/agnes-image-video-skills/blob/main/LICENSE"><img src="https://img.shields.io/github/license/yinjianjun1/agnes-image-video-skills?style=for-the-badge&color=green" alt="License"></a>
</p>

一个通过 [Agnes AI](https://agnes-ai.com) 的 OpenAI 兼容 API 生成**图片**与**视频**的 AI 技能。支持**中国区**（`api.agnes-ai.cn`）与**国际区**（`apihub.agnes-ai.com`）两个独立区域，并可在 **macOS、Windows、Linux** 上运行。

仓库采用标准 Skills 布局：技能本体位于 `skills/`，根目录存放文档与元数据，全部为纯 Python 3 标准库实现，无第三方依赖。

## 特性

- **文生图** — 同步 `POST /v1/images/generations`，返回 CDN 链接。
- **文生视频** — 异步 `POST /v1/videos`，轮询 `/agnesapi` 直至完成。
- **图生视频** — 同一异步流程，携带参考图（`mode: reference`）。
- **双区支持** — 中国区与国际区 API 结构相同但密钥独立；**密钥与端点必须同区**。
- **跨平台** — 仅用标准库（`urllib`、`pathlib`、`os.path`），不依赖任何 shell 特性。
- **容错** — 对 5xx 与 `video_queue_full` 指数退避重试，4xx 不重试。

## 仓库结构

```
agnes-image-video/
├── skills/
│   └── agnes-image-video/
│       ├── SKILL.md            # 技能说明
│       ├── scripts/
│       │   ├── agnes_api.py    # 共用 HTTP 客户端（认证、重试、轮询）
│       │   ├── generate_image.py
│       │   └── generate_video.py
│       └── references/
│           └── api_reference.md
├── README.md
├── README.zh.md
├── LICENSE
└── skill.json
```

## 环境要求

- **Python 3.9+**
- **Agnes API 密钥** — 中国区 `AGNES_API_KEY_CN`，或国际区 `AGNES_API_KEY_GLOBAL` / `AGNES_API_KEY`（两者均支持，任设其一即可）。

## 安装

### Skills CLI（推荐）

用 [Skills CLI](https://skills.sh) 安装：

```bash
npx skills add https://github.com/yinjianjun1/agnes-image-video-skills --skill agnes-image-video
```

加 `--global` 可用户级安装。

### 手动复制

把技能目录复制到助手的 skills 目录：

```bash
# Claude Code
cp -R skills/agnes-image-video ~/.claude/skills/

# WorkBuddy / CodeBuddy（用户级）
cp -R skills/agnes-image-video ~/.workbuddy/skills/
```

Windows 下用 `xcopy` / `robocopy`，或用资源管理器把文件夹复制到 `%USERPROFILE%\.claude\skills\`。

## 配置

| 区域 | Base URL | 密钥环境变量 | 控制台 |
|------|----------|-------------|--------|
| 中国区 `cn` | `https://api.agnes-ai.cn/v1` | `AGNES_API_KEY_CN` | platform.agnes-ai.cn |
| 国际区 `global` | `https://apihub.agnes-ai.com/v1` | `AGNES_API_KEY_GLOBAL` / `AGNES_API_KEY`（两者均支持，同时设置时取 `_GLOBAL`） | agnes-ai.com |

脚本从**启动 Python 的那个终端**的环境变量读取密钥。按平台设置：

**macOS（zsh）/ Linux（bash）** — 追加到 shell 配置后重开终端：

```bash
# macOS zsh → ~/.zshrc ；macOS 旧版 bash / Linux → ~/.bashrc
echo 'export AGNES_API_KEY_GLOBAL="sk-..."' >> ~/.zshrc
echo 'export AGNES_API_KEY_CN="sk-..."'     >> ~/.zshrc
```

**Windows PowerShell**

```powershell
# 当前会话临时
$env:AGNES_API_KEY_GLOBAL="sk-..."
$env:AGNES_API_KEY_CN="sk-..."

# 永久（用户级，重开终端生效）
[Environment]::SetEnvironmentVariable("AGNES_API_KEY_GLOBAL", "sk-...", "User")
[Environment]::SetEnvironmentVariable("AGNES_API_KEY_CN", "sk-...", "User")
```

**Windows CMD**

```bat
setx AGNES_API_KEY_GLOBAL "sk-..."
setx AGNES_API_KEY_CN "sk-..."
```

> 密钥必须在启动 Python 的终端中可见。使用 IDE 内置终端时，需重启 IDE 或在其设置里配置环境变量。

## 用法

macOS/Linux 用 `python3`，Windows 用 `py` 或 `python`。**不要假设仓库根目录就是当前工作目录**——用绝对路径调用脚本，输出才会落在你想要的位置：

```bash
# 指向安装后的 skill 目录（仓库内为 ./skills/agnes-image-video）
SKILL_DIR="$HOME/.claude/skills/agnes-image-video"

# 文生图（auto 区域，默认模型 agnes-image-2.5-flash）
python3 "$SKILL_DIR/scripts/generate_image.py" \
  -p "一只猫坐在书桌上，水彩风格" -o cat.png

# 文生视频（异步任务，脚本自动轮询直至完成）
python3 "$SKILL_DIR/scripts/generate_video.py" \
  -p "海浪拍打礁石，慢镜头" -o waves.mp4

# 指定中国区
python3 "$SKILL_DIR/scripts/generate_video.py" \
  -p "..." --region cn -o out.mp4

# 图生视频（参考图，会上传至 Agnes 服务器）
python3 "$SKILL_DIR/scripts/generate_video.py" \
  -p "让图片动起来" -i ref.png --region cn -o out.mp4
```

`--region` 取 `auto`（默认）、`cn` 或 `global`。`auto` 检测到 `AGNES_API_KEY_CN` 优先走中国区，否则回退国际区。

### 命令行参数

| 脚本 | 参数 | 说明 |
|------|------|------|
| 两者 | `-p/--prompt` | 必填 |
| 两者 | `-m/--model` | 模型名 |
| 两者 | `-o/--output` | 输出文件（默认时间戳命名，写入当前目录） |
| 两者 | `--region` | `auto` / `cn` / `global` |
| 图片 | `-s/--size` | `512x512` / `768x768` / `1024x1024` / `1920x1080` / `1080x1920` |
| 图片 | `-n` | 生成数量（默认 1） |
| 视频 | `-s/--seconds` | `4`–`12`（默认 `5`） |
| 视频 | `-i/--image` | 参考图，自动切 `mode=reference` |
| 视频 | `--poll-interval` / `--timeout` | 轮询间隔（10s）/ 超时（600s）。低于约 10s 会触发 429 |

> **尺寸归一化**：请求的尺寸不保证原样输出。实测 `512x512` 实际返回 **1024x1024**，`1920x1080` 实际返回 **1312x736**。需要精确尺寸时，改用档位 `2K` 配 `ratio`，再在下游裁剪。
>
> **能力边界**：仅支持文生图、文生视频、图生视频，**不支持图生图**——图生图需在 `extra_body.image` 传参考图数组，且**不需要** `tags: ["img2img"]`，本仓库未实现。
>
> **隐私**：图生视频会把本地参考图 base64 编码后上传至 Agnes，敏感图片不要用 `-i`。
>
> **耗时**：视频轮询最长 `--timeout`（600s），叠加最多 8 次指数退避（实测约 4 分 45 秒），负载高时单次可超 12 分钟。
>
> **输出**：文件写入当前目录，同名文件**无提示直接覆盖**。

### 可用模型（实测）

| 类型 | 中国区 `api.agnes-ai.cn` | 国际区 `apihub.agnes-ai.com` |
|------|--------------------------|------------------------------|
| 图片 | `agnes-image-2.1-flash`、`agnes-image-2.5-flash` | 另有 `agnes-image-2.0-flash` |
| 视频 | `agnes-video-2.5-flash`、`agnes-video-2.5` | 同左 |

> 中国区**没有** `agnes-image-2.0-flash`；用两区通用的 `agnes-image-2.5-flash`。

## 排障

- **401 `Invalid token`** — 密钥与端点跨区，必须同区。
- **403 `insufficient_user_quota`** — 该区域（或该模型）余额为 $0，去对应控制台充值；本地重试无效。实测：同一账号下 Flash 模型仍能提交，非 Flash 模型直接 403。
- **429 `Too Many Requests`** — 轮询过快。脚本会退避后继续轮询，默认间隔 10s；持续出现就调大 `--poll-interval`。
- **503 `video_queue_full`** — 上游视频队列满。脚本指数退避重试——实测 8 次共约 **4 分 45 秒** 后放弃。换低峰时段；改用 `agnes-video-2.5`（独立队列）仅在**该模型有余额**时有效，否则同样 403。
- **图片通道更稳** — 实测两次生图各 8–9 秒成功，视频提交每次都遇队列满。视频队列满时，先用图片模型出静态素材（`/images/generations` 不走视频队列），备着做图生视频。

完整参数与错误码见 [`api_reference.md`](skills/agnes-image-video/references/api_reference.md)。

## 许可

[MIT](LICENSE) © MONO
