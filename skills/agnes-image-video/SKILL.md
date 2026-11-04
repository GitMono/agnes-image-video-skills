---
name: agnes-image-video
description: >-
  Generate and download images or videos with Agnes AI models
  (agnes-image-2.5-flash, agnes-video-2.5-flash) through the OpenAI-compatible
  API, either from text or from a reference image, on the China
  (api.agnes-ai.cn) or global (apihub.agnes-ai.com) endpoint. Use when the
  user asks to generate an image or video with Agnes, or mentions
  agnes-image / agnes-video. Do not use for editing an existing image (this
  skill has no image-to-image support) or for non-Agnes providers.
  Triggers: 生成图片、生成视频、文生图、图生视频、Agnes.
license: MIT
allowed-tools: Bash(python3:*) Bash(python:*)
metadata:
  display_name: "Agnes 图像与视频"
  display_name_en: "Agnes Image & Video"
  description_zh: "通过 Agnes AI 的 OpenAI 兼容 API 生成图片与视频，支持中国区与国际区双端点，跨平台支持 macOS / Windows / Linux 桌面端。"
  description_en: "Generate images and videos via Agnes AI's OpenAI-compatible API, with China and global endpoints, cross-platform on macOS / Windows / Linux."
---

# Agnes Image & Video

通过 Agnes AI 的 OpenAI 兼容 API 生成图片和视频。**分两个区域，密钥与端点必须同区**（跨区混用报 401 `Invalid token`）。

## 区域与密钥

| 区域 | Base URL | 密钥环境变量 | 控制台 |
|------|----------|-------------|--------|
| 中国区 `cn` | `https://api.agnes-ai.cn/v1` | `AGNES_API_KEY_CN` | platform.agnes-ai.cn |
| 国际区 `global` | `https://apihub.agnes-ai.com/v1` | `AGNES_API_KEY_GLOBAL` / `AGNES_API_KEY`（两者均支持，`_GLOBAL` 优先） | agnes-ai.com |

脚本在所有桌面平台（macOS / Windows / Linux）通用，关键是把密钥设为**启动 Python 的那个终端**可见的环境变量。

### 设置密钥（按平台选择其一）

**macOS（默认 zsh）/ Linux（bash）** — 写入 shell 配置文件后重开终端：

```bash
# macOS zsh 用 ~/.zshrc；macOS 旧版 bash 与 Linux 用 ~/.bashrc
echo 'export AGNES_API_KEY_GLOBAL="sk-..."' >> ~/.zshrc
echo 'export AGNES_API_KEY_CN="sk-..."'     >> ~/.zshrc
```

**Windows PowerShell** — 当前会话临时设置：

```powershell
$env:AGNES_API_KEY_GLOBAL="sk-..."
$env:AGNES_API_KEY_CN="sk-..."
```

永久（用户级，重开终端生效）：

```powershell
[Environment]::SetEnvironmentVariable("AGNES_API_KEY_GLOBAL", "sk-...", "User")
[Environment]::SetEnvironmentVariable("AGNES_API_KEY_CN", "sk-...", "User")
```

**Windows CMD** — 永久（用户级）：

```bat
setx AGNES_API_KEY_GLOBAL "sk-..."
setx AGNES_API_KEY_CN "sk-..."
```

> ⚠️ 环境变量必须在**启动 Python 的那个终端**里可见。用 IDE 内置终端时，需重启 IDE 或在其设置里配置环境变量。

脚本 `--region` 参数控制走哪个区：
- `auto`（默认）：检测到 `AGNES_API_KEY_CN` 优先走中国区，否则国际区。
- `cn` / `global`：强制指定。

## 快速开始

> 脚本为 Python 3，跨平台通用。运行解释器：macOS/Linux 用 `python3`，Windows 用 `py` 或 `python`。
>
> **路径基准**：下文 `<skill-dir>` 指本 SKILL.md 所在目录。执行前先由 SKILL.md 的实际路径推出 `<skill-dir>`，不要假设当前工作目录就是 skill 目录（Agent 的 cwd 通常是用户项目根目录）。

```bash
# 文生图（auto 区域，默认模型 agnes-image-2.5-flash）
python3 "<skill-dir>/scripts/generate_image.py" -p "一只猫坐在书桌上，水彩风格" -o cat.png

# 文生视频（异步任务，脚本自动轮询直至完成）
python3 "<skill-dir>/scripts/generate_video.py" -p "海浪拍打礁石，慢镜头" -o waves.mp4

# 指定中国区
python3 "<skill-dir>/scripts/generate_video.py" -p "..." --region cn -o out.mp4

# 图生视频（参考图，会上传至 Agnes 服务器）
python3 "<skill-dir>/scripts/generate_video.py" -p "让图片动起来" -i ref.png --region cn -o out.mp4
```

Windows 下把 `python3` 换成 `py`，路径用双引号包裹（如 `"%USERPROFILE%\...\scripts\generate_video.py"`）。

## 核心能力

### 1. 图片生成（同步返回）

- 端点：`POST {base}/images/generations`
- 默认模型：`agnes-image-2.5-flash`（中国区有 2.1 / 2.5，国际区另有 2.0-flash）
- 支持尺寸（请求值）：`512x512`、`768x768`、`1024x1024`、`1920x1080`、`1080x1920`
  - **会归一化**：实测 `512x512` → `1024x1024`，`1920x1080` → `1312x736`。需要精确尺寸就请求 `2K` + `ratio`，再下游裁剪。
- 数量：`-n` 指定，默认 1；多张时输出名自动加 `_0`、`_1` 后缀
- 返回：`data[0].url`（CDN 公开链接，下载无需认证）
- **本 skill 只做文生图**：不支持图生图。图生图在 `extra_body.image` 传参考图 URL 或 Data URI，**不需要** `tags: ["img2img"]`（官方 2.1 文档明确说明）；本仓库未实现该分支。

### 2. 视频生成（异步任务）

- 端点：`POST {base}/videos`
- 必填字段：`model`、`prompt`、`mode`（`text` 文生 / `reference` 图生）
- 可选：`seconds`（字符串 `"4"`–`"12"`）、`size`（Flash 固定 `"720P"`，传其他值报 400）、`aspect_ratio`（默认 `16:9`）
- 提交返回 `video_id`；轮询 `GET {api_host}/agnesapi?video_id=<ID>&model_name=<模型>`（注意 `/agnesapi` 在根路径，**不含 /v1**）
- 结果：响应顶层 `url` 字段即视频地址
- **禁止传 `num_frames` / `width` / `height` / `fps`**：2.5 契约下这些字段会让请求直接 400，时长只用 `seconds`。（`8n+1`、`≤441` 的帧数约束属于旧 v2.0 契约，**不适用于 2.5**。）

### 3. 可用模型（实测）

> 用 `GET {base}/models` 实时确认。两区列表略有差异：

| 类型 | 中国区 `api.agnes-ai.cn` | 国际区 `apihub.agnes-ai.com` |
|------|------------------------|------------------------------|
| 图片 | `agnes-image-2.1-flash`、`agnes-image-2.5-flash` | 额外多一个 `agnes-image-2.0-flash` |
| 视频 | `agnes-video-2.5-flash`、`agnes-video-2.5` | 同左 |
| 文本 | `agnes-2.5-flash`、`agnes-2.5-pro`、`agnes-3.0-flash` 等 | `agnes-2.5-*`、`agnes-3.0-flash` |

> ⚠️ 中国区**没有** `agnes-image-2.0-flash`，脚本默认用 `2.5-flash` 两区通用。

## 工作流

```
用户描述需求
  ↓
在终端配置密钥（见「区域与密钥」） → 执行脚本（auto 自动路由区域）
  ↓
图片：POST /images/generations → 返回 URL → 无认证下载
视频：POST /videos → 拿到 video_id → GET /agnesapi 轮询 → 顶层 url 下载
  ↓
用 present_files 展示结果文件
```

## 资源

- `scripts/agnes_api.py` — 共用 HTTP 客户端，封装区域解析、认证、重试、轮询、下载
  - `resolve_region(cli)` 按 `--region` 解析端点+密钥；`auto` 有 CN 密钥优先中国区
  - 下载：CDN 公开链接，**统一不携带 Authorization 头**（密钥只发往 API 端点）
- `scripts/generate_image.py` — 图片生成 CLI（支持 `--region`）
- `scripts/generate_video.py` — 视频生成 CLI（含异步轮询，支持 `--region`）
- `references/api_reference.md` — 完整 API 参数与验证记录

## 命令行参数

| 脚本 | 参数 | 说明 |
|------|------|------|
| 两者 | `-p/--prompt` | 必填，描述提示词 |
| 两者 | `-m/--model` | 模型名，默认图片 `agnes-image-2.5-flash` / 视频 `agnes-video-2.5-flash` |
| 两者 | `-o/--output` | 输出文件；缺省为时间戳命名，写入**当前工作目录** |
| 两者 | `--region` | `auto`（默认）/ `cn` / `global` |
| 图片 | `-s/--size` | `512x512` / `768x768` / `1024x1024` / `1920x1080` / `1080x1920`，默认 `1024x1024` |
| 图片 | `-n` | 生成数量，默认 1 |
| 视频 | `-s/--seconds` | 时长，`4`–`12` 的整数字符串，默认 `5` |
| 视频 | `-i/--image` | 参考图路径，指定后自动切 `mode=reference` |
| 视频 | `--poll-interval` / `--timeout` | 轮询间隔（默认 10s）/ 超时（默认 600s）。间隔太小会触发 429 |

## 注意事项

- **密钥与端点必须同区**：CN 密钥打到国际区 `apihub.agnes-ai.com` 会 401 `Invalid token`；反之亦然。CN 密钥只对中国区 `api.agnes-ai.cn` 有效。
- **配额不足**：报 403 `insufficient_user_quota`（余额 $0）时，本地重试无效，需去对应控制台充值后重跑。国际区与中国区配额**相互独立**。
- **视频队列满**：报 503 `video_queue_full` 是上游队列容量限制（非本地问题）。脚本内置指数退避，实测 8 次共约 **4 分 45 秒** 后放弃。持续满时换**低峰时段**；改用非 Flash 模型 `agnes-video-2.5`（独立队列）只在**该模型有余额**时有效，额度为 0 会直接 403 `insufficient_user_quota`。
- **429 限流**：轮询间隔过小会被限流（默认 10s 已避开；2s 实测必现）。脚本遇到 429 会退避后继续轮询，不会中断任务。
- **图片通道通常更稳**：视频队列满时，可先用图片模型出静态素材（`/images/generations` 不走视频队列），备着做图生视频。
- 下载 URL 是 CDN 公开链接（国际区 `platform-outputs.agnes-ai.space`、中国区 `cos-platform-outputs.agnes-ai.cn`），**无需带 Bearer 认证**；脚本对下载链接不发送任何密钥。
- 视频 `size` 对 Flash 模型固定 `"720P"`，传其他值直接 400。
- 未指定 `-o` 时用时间戳命名（`agnes_img_*.png` / `agnes_vid_*.mp4`），写入当前工作目录；同名文件会被直接覆盖，需要保留时请自行指定新路径。
- **隐私**：图生视频会把本地参考图 base64 编码后上传至 Agnes 服务器；敏感图片不要用 `-i`。
- **耗时**：视频最长等 `--timeout`（默认 600s），叠加最多 8 次指数退避（实测约 4 分 45 秒），单次最坏可超 12 分钟。执行前告诉用户这是异步任务，不要中途判定卡死。
