# Agnes AI API 参考

> Agnes 分**两个区域**，密钥与 Base URL 必须同区。跨区混用报 401 `Invalid token`。
> 完整文档：国际区 https://agnes-ai.com/doc/overview，中国区 https://www.agnes-ai.cn/zh-Hans/docs/cid5
> 密钥通过环境变量传入（macOS/Linux 写 `~/.zshrc` 或 `~/.bashrc`，Windows 用 `setx` 或 `[Environment]::SetEnvironmentVariable`），调用脚本的终端必须能读到。

---

## 区域端点

| 区域 | Base URL | 轮询根端点 | 密钥环境变量 | 控制台 |
|------|---------|-----------|-------------|--------|
| 中国区 `cn` | `https://api.agnes-ai.cn/v1` | `https://api.agnes-ai.cn/agnesapi` | `AGNES_API_KEY_CN` | platform.agnes-ai.cn |
| 国际区 `global` | `https://apihub.agnes-ai.com/v1` | `https://apihub.agnes-ai.com/agnesapi` | `AGNES_API_KEY_GLOBAL`（或旧名 `AGNES_API_KEY`） | agnes-ai.com |

> 认证：`Authorization: Bearer <key>`。**密钥与端点必须同区**——CN 密钥打到国际区（或反之）都会 401。
> 视频轮询端点 `/agnesapi` 在**根路径**（不含 `/v1`），与 `/v1/videos` 提交端点域名相同但层级不同。

---

## 查询可用模型

```
GET {base}/models
```

返回当前区域、当前密钥可用的模型 ID 列表。两区列表略有差异（2026-11-04 实测）：

- 中国区 `api.agnes-ai.cn`：`agnes-2.5-flash`、`agnes-2.5-pro`、`agnes-2.5-pro-alpha/beta`、`agnes-3.0-flash`、`agnes-image-2.1-flash`、`agnes-image-2.5-flash`、`agnes-video-2.5`、`agnes-video-2.5-flash`
- 国际区 `apihub.agnes-ai.com`：额外多一个 `agnes-image-2.0-flash`

> 模型列表会变化，不确定时先调此接口。**中国区没有 `agnes-image-2.0-flash`**，脚本默认 `agnes-image-2.5-flash` 两区通用。

---

## 图片生成（同步返回）

### 端点

```
POST {base}/images/generations
```

### 请求体

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `model` | string | 是 | `agnes-image-2.5-flash`（推荐）/ `agnes-image-2.1-flash` / `agnes-image-2.0-flash`（仅国际区） |
| `prompt` | string | 是 | 图片描述 |
| `size` | string | 否 | `512x512` / `1024x1024` / `1920x1080` / `1080x1920` |
| `n` | int | 否 | 生成数量，默认 1 |

### 响应

```json
{
  "data": [
    { "url": "https://cos-platform-outputs.agnes-ai.cn/images/t2i/task_xxx/output_xxx.png", "b64_json": "", "revised_prompt": "" }
  ],
  "task_id": "task_xxx"
}
```

国际区 CDN 域名 `platform-outputs.agnes-ai.space`，中国区 `cos-platform-outputs.agnes-ai.cn`。

### 下载图片 URL

CDN 公开链接，**无需带 Bearer 认证头**（带认证反而 401）。脚本先无认证尝试，401/403 时回退带认证兜底。

---

## 视频生成（异步任务）

### 提交任务

```
POST {base}/videos
```

### 请求体

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `model` | string | 是 | `agnes-video-2.5-flash`（默认）/ `agnes-video-2.5` |
| `prompt` | string | 是 | 视频描述 |
| `mode` | string | 是 | `text`（文生）/ `keyframe`（关键帧）/ `reference`（参考图，需配 `images`） |
| `seconds` | string | 否 | 时长，字符串 `"4"`–`"12"`，默认 `"5"`（注意是字符串） |
| `size` | string | 否 | Flash 模型**固定** `"720P"`，传其他值报 400 |
| `aspect_ratio` | string | 否 | 默认 `"16:9"`，可 `"9:16"` |
| `images` | list | `reference` 时必填 | base64 data URL 列表 |

### 提交响应

```json
{ "video_id": "task_xxx" }
```

`video_id` 缺失时回退读 `task_id` / `id` 字段。

### 查询任务（根路径，不含 /v1）

```
GET {api_host}/agnesapi?video_id=<ID>&model_name=<模型>
```

| 字段 | 说明 |
|------|------|
| `status` | `pending` / `processing` / `completed` / `failed` |
| `progress` | 0–100 |
| `url` | 完成后**顶层** `url` 即视频下载地址 |

轮询默认间隔 2 秒，超时 600 秒。

### 常见失败

- `503 video_queue_full`：上游队列容量满（瞬时），脚本对 5xx 与队列满共 8 次指数退避；持续满则换低峰时段，或改用非 Flash 模型 `agnes-video-2.5`（独立队列）。
- `429`：账号级频率限制（非队列满），报错带重置时间，别盲目重试。

---

## 错误码与排查

| HTTP 状态 | 含义 | 应对 |
|-----------|------|------|
| 400 | 参数错误（`size` 非 Flash 固定值、`mode` 非法等） | 修正参数 |
| 401 `Invalid token` | 密钥与端点跨区，或密钥无效 | 密钥和 Base URL 必须同区 |
| 403 `insufficient_user_quota` | 该区域配额为 $0 | 本地重试无效，去对应控制台充值 |
| 404 `model_not_found` | 模型名不存在或该区没有 | 先 `GET /v1/models` 确认该区可用列表 |
| 429 | 频率限制 | 按报错的重置时间等待 |
| 503 `video_queue_full` | 视频队列满（上游容量限制，非本地问题） | 退避重试；持续满则换时段/模型 |
| 500 | 服务端错误 | 可重试 |

---

## 本轮实测结论（2026-11-04）

- **国际区（GLOBAL）密钥**：视频返回 403 `insufficient_user_quota`，`remaining: $0.000000`，配额耗尽，视频出不来。
- **中国区（CN）密钥**：`/v1/models` 与 `/v1/images/generations` 正常（出图成功），但 `/v1/videos` 持续 503 `video_queue_full`。
- 两区配额相互独立。CN 密钥此前误打到国际区 `apihub.agnes-ai.com` 才会 401，换到 `api.agnes-ai.cn` 即通。
- 通用技巧：视频队列满时，先用图片模型出静态素材（图片不走视频队列），备着做图生视频。

---

## 脚本 `--region` 说明

| 取值 | 行为 |
|------|------|
| `auto`（默认） | 检测到 `AGNES_API_KEY_CN` 走中国区，否则走国际区 |
| `cn` | 强制中国区 `api.agnes-ai.cn` + `AGNES_API_KEY_CN` |
| `global` | 强制国际区 `apihub.agnes-ai.com` + `AGNES_API_KEY_GLOBAL`（或 `AGNES_API_KEY`） |
