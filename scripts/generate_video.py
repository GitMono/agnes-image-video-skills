#!/usr/bin/env python3
"""
Agnes Video 2.5 Flash 视频生成 CLI。
支持文本生视频（mode=text）与图生视频（mode=reference）。

用法：
  python generate_video.py -p "提示词" [-m 模型] [-s 秒] [-o 输出文件] [--region auto|cn|global]   # 文本生视频
  python generate_video.py -p "提示词" -i 参考图.png --region cn                                 # 图生视频（中国区）

环境变量：
  AGNES_API_KEY_GLOBAL / AGNES_API_KEY   国际区密钥（global）
  AGNES_API_KEY_CN                      中国区密钥（cn）
"""

import argparse
import base64
import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import agnes_api

DEFAULT_MODEL = "agnes-video-2.5-flash"
VALID_SECONDS = ["4", "5", "6", "7", "8", "9", "10", "11", "12"]
# Flash 固定 720P；其他值会触发 HTTP 400
FIXED_SIZE = "720P"
DEFAULT_ASPECT = "16:9"


def build_images(image_path: str) -> list:
    """把本地参考图编码为 data URL 列表（reference 模式用）。"""
    img_ext = os.path.splitext(image_path)[1].lower().lstrip(".") or "png"
    mime = f"image/{img_ext}" if img_ext in ("png", "jpg", "jpeg", "webp", "gif") else "image/png"
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return [f"data:{mime};base64,{b64}"]


def main():
    parser = argparse.ArgumentParser(description="Agnes Video 2.5 Flash 视频生成（异步任务）")
    parser.add_argument("-p", "--prompt", required=True, help="视频描述提示词")
    parser.add_argument("-m", "--model", default=DEFAULT_MODEL, help=f"模型名称（默认 {DEFAULT_MODEL}）")
    parser.add_argument(
        "-s", "--seconds",
        default="5", choices=VALID_SECONDS,
        help=f"时长（秒），支持 {', '.join(VALID_SECONDS)}，默认 5s",
    )
    parser.add_argument("-i", "--image", default=None, help="参考图路径（指定后自动切换为 reference 图生视频模式）")
    parser.add_argument("-o", "--output", default=None, help="输出 MP4 文件路径（默认时间戳命名）")
    parser.add_argument(
        "--region",
        default="auto",
        choices=["auto", "cn", "global"],
        help="区域：auto（有 CN 密钥优先用中国区）、cn、global。默认 auto",
    )
    parser.add_argument("--poll-interval", type=int, default=2, help="轮询间隔秒数（默认 2）")
    parser.add_argument("--timeout", type=int, default=600, help="轮询超时秒数（默认 600）")
    args = parser.parse_args()

    cfg = agnes_api.resolve_region(args.region)

    mode = "reference" if args.image else "text"
    print(f"区域：{cfg['name']}（{cfg['base_url']}）  模型：{args.model}  模式：{mode}  时长：{args.seconds}s")

    payload = {
        "model": args.model,
        "prompt": args.prompt,
        "mode": mode,
        "seconds": args.seconds,
        "size": FIXED_SIZE,
        "aspect_ratio": DEFAULT_ASPECT,
    }
    if mode == "reference":
        if not os.path.isfile(args.image):
            sys.exit(f"错误：参考图不存在：{args.image}")
        payload["images"] = build_images(args.image)
        print(f"参考图：{args.image}")

    print("  正在提交视频任务…")
    result = agnes_api._post("videos", payload, cfg["api_key"], cfg["base_url"])

    # 优先用 video_id 查询；缺失时回退 task_id / id
    video_id = result.get("video_id") or result.get("task_id") or result.get("id")
    if not video_id:
        raise RuntimeError(f"响应中找不到 video_id/task_id，原始响应：{result}")

    final = agnes_api.wait_for_video(video_id, args.model, cfg["api_key"], cfg["api_host"],
                                     interval=args.poll_interval, timeout=args.timeout)

    video_url = final.get("url") or (final.get("data", [{}])[0].get("url") if final.get("data") else None)
    if not video_url:
        raise RuntimeError(f"任务完成但无视频 URL，最终响应：{final}")

    out = args.output or f"agnes_vid_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    print("  下载视频…")
    agnes_api.download(video_url, out, cfg["api_key"])
    print(f"\n完成，视频已保存：{out}")


if __name__ == "__main__":
    main()
