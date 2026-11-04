# Agnes Image & Video

<p align="center">
  <a href="https://github.com/yinjianjun1/agnes-image-video-skills/blob/main/README.md">🇺🇸 English</a> |
  <a href="https://github.com/yinjianjun1/agnes-image-video-skills/blob/main/README.zh.md">🇨🇳 简体中文</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.9%2B-yellow?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.9+">
  <img src="https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-blue?style=for-the-badge" alt="Cross-platform">
  <a href="https://github.com/yinjianjun1/agnes-image-video-skills/blob/main/LICENSE"><img src="https://img.shields.io/github/license/yinjianjun1/agnes-image-video-skills?style=for-the-badge&color=green" alt="License"></a>
</p>

An AI skill that generates **images** and **videos** through the [Agnes AI](https://agnes-ai.com) OpenAI-compatible API. It supports two independent regions — **China** (`api.agnes-ai.cn`) and **global** (`apihub.agnes-ai.com`) — and runs on **macOS, Windows and Linux**.

This follows the standard Skills layout: the skill lives under `skills/`, the repo root holds the docs and metadata, and everything is plain Python 3 with no third-party dependencies.

## Features

- **Text-to-image** — synchronous `POST /v1/images/generations`, returns CDN URLs.
- **Text-to-video** — asynchronous `POST /v1/videos`, polls `/agnesapi` until completion.
- **Image-to-video** — same async flow with a reference image (`mode: reference`).
- **Dual region** — China and global endpoints share an API shape but need their own key. The key and the endpoint **must belong to the same region**.
- **Cross-platform** — stdlib only (`urllib`, `pathlib`, `os.path`); no shell-specific assumptions.
- **Resilient** — exponential backoff for 5xx and `video_queue_full`, no retry on 4xx.

## Repository Structure

```
agnes-image-video/
├── skills/
│   └── agnes-image-video/
│       ├── SKILL.md            # skill instructions
│       ├── scripts/
│       │   ├── agnes_api.py    # shared HTTP client (auth, retry, polling)
│       │   ├── generate_image.py
│       │   └── generate_video.py
│       └── references/
│           └── api_reference.md
├── README.md
├── README.zh.md
├── LICENSE
└── skill.json
```

## Requirements

- **Python 3.9+**
- An **Agnes API key** — China region (`AGNES_API_KEY_CN`) or global region (`AGNES_API_KEY_GLOBAL` / `AGNES_API_KEY`; both are supported, set either one).

## Installation

### Skills CLI (recommended)

Install with the [Skills CLI](https://skills.sh):

```bash
npx skills add https://github.com/yinjianjun1/agnes-image-video-skills --skill agnes-image-video
```

Add `--global` for a user-level install.

### Manual copy

Copy the skill folder into your assistant's skills directory:

```bash
# Claude Code
cp -R skills/agnes-image-video ~/.claude/skills/

# WorkBuddy / CodeBuddy (user-level)
cp -R skills/agnes-image-video ~/.workbuddy/skills/
```

On Windows, use `xcopy` / `robocopy`, or copy the folder with Explorer into `%USERPROFILE%\.claude\skills\`.

## Configuration

| Region | Base URL | Key environment variable | Console |
|--------|----------|--------------------------|---------|
| China `cn` | `https://api.agnes-ai.cn/v1` | `AGNES_API_KEY_CN` | platform.agnes-ai.cn |
| Global `global` | `https://apihub.agnes-ai.com/v1` | `AGNES_API_KEY_GLOBAL` / `AGNES_API_KEY` (both supported; `_GLOBAL` wins if both are set) | agnes-ai.com |

The scripts read keys from the **environment of the terminal that launches Python**. Set them per platform:

**macOS (zsh) / Linux (bash)** — append to your shell profile, then reopen the terminal:

```bash
# macOS zsh → ~/.zshrc ; macOS legacy bash / Linux → ~/.bashrc
echo 'export AGNES_API_KEY_GLOBAL="sk-..."' >> ~/.zshrc
echo 'export AGNES_API_KEY_CN="sk-..."'     >> ~/.zshrc
```

**Windows PowerShell**

```powershell
# current session
$env:AGNES_API_KEY_GLOBAL="sk-..."
$env:AGNES_API_KEY_CN="sk-..."

# permanent (user scope, reopen terminal)
[Environment]::SetEnvironmentVariable("AGNES_API_KEY_GLOBAL", "sk-...", "User")
[Environment]::SetEnvironmentVariable("AGNES_API_KEY_CN", "sk-...", "User")
```

**Windows CMD**

```bat
setx AGNES_API_KEY_GLOBAL "sk-..."
setx AGNES_API_KEY_CN "sk-..."
```

> Keys must be visible to the shell that starts Python. If you use an IDE terminal, restart the IDE or configure environment variables in its settings.

## Usage

Run the scripts with `python3` on macOS/Linux, or `py` / `python` on Windows. **Do not assume the repo root is your working directory** — call the scripts by absolute path so output lands where you want it:

```bash
# Point this at the installed skill folder (repo: ./skills/agnes-image-video)
SKILL_DIR="$HOME/.claude/skills/agnes-image-video"

# Text-to-image (auto region, default model agnes-image-2.5-flash)
python3 "$SKILL_DIR/scripts/generate_image.py" \
  -p "a cat sitting on a desk, watercolor style" -o cat.png

# Text-to-video (async task; the script polls until done)
python3 "$SKILL_DIR/scripts/generate_video.py" \
  -p "waves crashing on rocks, slow motion" -o waves.mp4

# Force the China region
python3 "$SKILL_DIR/scripts/generate_video.py" \
  -p "..." --region cn -o out.mp4

# Image-to-video with a reference image (the image is uploaded to Agnes)
python3 "$SKILL_DIR/scripts/generate_video.py" \
  -p "make the image move" -i ref.png --region cn -o out.mp4
```

`--region` accepts `auto` (default), `cn`, or `global`. `auto` prefers the China region when `AGNES_API_KEY_CN` is set, otherwise falls back to global.

### CLI options

| Script | Option | Meaning |
|--------|--------|---------|
| both | `-p/--prompt` | required |
| both | `-m/--model` | model name |
| both | `-o/--output` | output file (default: timestamped name in the current directory) |
| both | `--region` | `auto` / `cn` / `global` |
| image | `-s/--size` | `512x512` / `768x768` / `1024x1024` / `1920x1080` / `1080x1920` |
| image | `-n` | number of images (default 1) |
| video | `-s/--seconds` | `4`–`12` (default `5`) |
| video | `-i/--image` | reference image, switches to `mode=reference` |
| video | `--poll-interval` / `--timeout` | polling interval (10s) / timeout (600s). Below ~10s triggers 429 |

> **Size normalization**: requested sizes are not guaranteed. Measured: `512x512` returned **1024x1024**, `1920x1080` returned **1312x736**. If exact dimensions matter, request a size tier (`2K`) with a `ratio` and crop downstream.
>
> **Scope**: text-to-image, text-to-video and image-to-video only. There is **no image-to-image** support — that workflow needs an input image array in `extra_body.image` (and explicitly **not** `tags: ["img2img"]`) and is not implemented here.
>
> **Privacy**: image-to-video base64-encodes your local reference image and uploads it to Agnes. Don't pass sensitive images.
>
> **Latency**: video jobs poll for up to `--timeout` (600s) plus up to 8 backoff retries (~4m45s measured), so a single run can exceed 12 minutes under load.
>
> **Output**: files are written to the current directory and existing files are overwritten without prompting.

### Available models (tested)

| Type | China `api.agnes-ai.cn` | Global `apihub.agnes-ai.com` |
|------|--------------------------|------------------------------|
| Image | `agnes-image-2.1-flash`, `agnes-image-2.5-flash` | also `agnes-image-2.0-flash` |
| Video | `agnes-video-2.5-flash`, `agnes-video-2.5` | same |

> The China region has **no** `agnes-image-2.0-flash`; use `agnes-image-2.5-flash`, which works in both regions.

## Troubleshooting

- **401 `Invalid token`** — key and endpoint are from different regions. They must match.
- **403 `insufficient_user_quota`** — the region's (or that model's) balance is $0. Top up in the matching console; local retries won't help. Measured: the Flash model can still submit while the non-Flash model returns 403 on the same account.
- **429 `Too Many Requests`** — polling too fast. The script backs off and keeps polling; the default interval is 10s. If it persists, raise `--poll-interval`.
- **503 `video_queue_full`** — upstream video queue is full. The script retries with exponential backoff — measured 8 attempts over **4m45s** before giving up. Retry off-peak; switching to `agnes-video-2.5` (separate queue) only helps if that model has balance, otherwise it returns 403.
- **Images are more reliable than video** — measured: two image calls succeeded in 8–9s each, while video submission hit `video_queue_full` on every attempt. When the video queue is full, generate still frames first (`/images/generations` does not use the video queue) and feed them into image-to-video later.

See [`api_reference.md`](skills/agnes-image-video/references/api_reference.md) for the full API and error table.

## License

[MIT](LICENSE) © MONO
