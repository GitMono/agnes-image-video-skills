"""
Agnes AI API 共用 HTTP 客户端。
封装认证、重试、轮询，供 generate_image.py 和 generate_video.py 使用。
"""

import json
import time
import urllib.request
import urllib.error
from pathlib import Path

# 各区域端点配置。密钥与 Base URL 必须同区域，混用会 401 Invalid token。
# global（国际区）：apihub.agnes-ai.com；cn（中国区）：api.agnes-ai.cn
# 视频任务查询端点 /agnesapi 在根路径（不含 /v1），见 API_HOST。
REGIONS = {
    "global": {
        "name": "global",
        "base_url": "https://apihub.agnes-ai.com/v1",
        "api_host": "https://apihub.agnes-ai.com",
        "key_envs": ("AGNES_API_KEY_GLOBAL", "AGNES_API_KEY"),
    },
    "cn": {
        "name": "cn",
        "base_url": "https://api.agnes-ai.cn/v1",
        "api_host": "https://api.agnes-ai.cn",
        "key_envs": ("AGNES_API_KEY_CN",),
    },
}

# 向后兼容：默认端点为 global 区域
BASE_URL = REGIONS["global"]["base_url"]
API_HOST = REGIONS["global"]["api_host"]


def _get_api_key() -> str:
    """从环境变量 AGNES_API_KEY 读取（旧单密钥方式，缺失时报错退出）。"""
    import os
    key = os.environ.get("AGNES_API_KEY")
    if not key:
        raise EnvironmentError(
            "未找到 AGNES_API_KEY 环境变量。请在运行脚本的终端中设置密钥，例如：\n"
            '  macOS/Linux: export AGNES_API_KEY="sk-your-key"\n'
            '  Windows PowerShell: $env:AGNES_API_KEY="sk-your-key"\n'
            '  Windows CMD: set AGNES_API_KEY="sk-your-key"'
        )
    return key


def _get_key_for(region_cfg: dict) -> str:
    """按区域配置读取密钥：依次尝试 region_cfg['key_envs'] 中各环境变量。"""
    import os
    for env in region_cfg["key_envs"]:
        val = os.environ.get(env)
        if val:
            return val
    raise EnvironmentError(
        f"未找到 {region_cfg['name']} 区域的 API Key。请在运行脚本的终端中设置以下环境变量之一：\n"
        + "\n".join(
            f'  macOS/Linux: export {e}="sk-your-key"\n'
            f'  Windows PowerShell: $env:{e}="sk-your-key"\n'
            f'  Windows CMD: set {e}=sk-your-key'
            for e in region_cfg["key_envs"]
        )
    )


def resolve_region(cli: str = "auto") -> dict:
    """解析区域配置，返回 dict：name / base_url / api_host / api_key。
    cli 取值 auto / cn / global。
    auto：若设置了 AGNES_API_KEY_CN 优先用 cn，否则用 global。"""
    import os
    if cli != "auto":
        region = cli
    else:
        region = "cn" if os.environ.get("AGNES_API_KEY_CN") else "global"
    cfg = dict(REGIONS[region])
    cfg["api_key"] = _get_key_for(cfg)
    return cfg


def _post(path: str, payload: dict, api_key: str, base_url: str, retries: int = 8) -> dict:
    """向 Agnes API 发送 POST 请求，失败重试。
    4xx（参数/认证错误）不重试；5xx 与 video_queue_full 指数退避重试。"""
    url = f"{base_url}/{path}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = json.dumps(payload).encode("utf-8")

    for attempt in range(1, retries + 1):
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            # 429 是频率限制，可退避重试；其余 4xx（参数/认证/额度）重试无用，立即失败
            if 400 <= e.code < 500 and e.code != 429:
                raise RuntimeError(f"HTTP {e.code} 请求失败：{body}") from e
            if attempt < retries:
                wait = min(60, 3 * (2 ** (attempt - 1)))
                # 队列满时额外多等
                if "queue" in body.lower():
                    wait += 10
                print(f"  第 {attempt} 次请求失败（{e.code}），{wait}s 后重试…")
                time.sleep(wait)
            else:
                raise RuntimeError(f"连续 {retries} 次请求失败，最后一次响应：{body}")
        except Exception as ex:
            if attempt < retries:
                wait = min(60, 3 * (2 ** (attempt - 1)))
                print(f"  第 {attempt} 次请求异常：{ex}，{wait}s 后重试…")
                time.sleep(wait)
            else:
                raise

    raise RuntimeError("不应到达此处")


def _get(path: str, api_key: str, base_url: str, retries: int = 3) -> dict:
    """向 Agnes API 发送 GET 请求（用于轮询任务状态）。"""
    url = f"{base_url}/{path}"
    headers = {"Authorization": f"Bearer {api_key}"}

    for attempt in range(1, retries + 1):
        req = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            if 400 <= e.code < 500:
                raise RuntimeError(f"HTTP {e.code} 查询失败：{body}") from e
            if attempt < retries:
                time.sleep(2 ** attempt)
            else:
                raise RuntimeError(f"连续 {retries} 次查询失败：{body}")
        except Exception as ex:
            if attempt < retries:
                time.sleep(2 ** attempt)
            else:
                raise
    raise RuntimeError("不应到达此处")


def download(url: str, out_path: str) -> str:
    """下载媒体文件到指定路径，返回保存路径。
    CDN 输出链接无需认证，统一不携带 Authorization 头：
    密钥只应发往 API 端点，跟随重定向时也不会泄漏到第三方域名。"""
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=300) as resp:
        data = resp.read()

    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return str(path.resolve())


def wait_for_video(video_id: str, model: str, api_key: str, api_host: str, interval: int = 10, timeout: int = 600) -> dict:
    """轮询视频任务（GET {api_host}/agnesapi?video_id=...&model_name=...），直至完成或超时。"""
    deadline = time.time() + timeout
    print(f"  任务已提交（video_id={video_id}），开始轮询（每 {interval}s）…")

    while time.time() < deadline:
        url = f"{api_host}/agnesapi?video_id={video_id}&model_name={model}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key}"}, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            if e.code == 429:
                # 轮询过快触发限流：退避后继续等待任务，不中断
                print(f"  查询被限流（429），{interval * 3}s 后继续轮询…")
                time.sleep(interval * 3)
                continue
            if 400 <= e.code < 500:
                raise RuntimeError(f"HTTP {e.code} 查询失败：{body}") from e
            time.sleep(interval)
            continue

        status = result.get("status", "")
        progress = result.get("progress", "")
        print(f"  状态：{status}  进度：{progress}%")

        if status in ("completed", "succeeded", "success"):
            return result
        if status in ("failed", "error", "cancelled", "canceled"):
            raise RuntimeError(f"任务失败，详情：{json.dumps(result, ensure_ascii=False)}")

        time.sleep(interval)

    raise TimeoutError(
        f"轮询超时（{timeout}s）。video_id={video_id}，\n"
        f"可手动查询：GET {api_host}/agnesapi?video_id={video_id}&model_name={model}"
    )
