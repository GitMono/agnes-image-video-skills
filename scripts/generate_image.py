#!/usr/bin/env python3
"""
Agnes Image 文生图 CLI。

用法：
  python generate_image.py -p "提示词" [-m 模型名] [-s 尺寸] [-o 输出文件] [--region auto|cn|global]

环境变量：
  AGNES_API_KEY_GLOBAL / AGNES_API_KEY   国际区密钥（global）
  AGNES_API_KEY_CN                      中国区密钥（cn）
"""

import argparse
import datetime
import os
import sys

# 确保能导入同目录的 agnes_api.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import agnes_api

DEFAULT_MODEL = "agnes-image-2.5-flash"
SUPPORTED_SIZES = ["512x512", "768x768", "1024x1024", "1920x1080", "1080x1920"]


def main():
    parser = argparse.ArgumentParser(description="Agnes Image 文生图")
    parser.add_argument("-p", "--prompt", required=True, help="图片描述提示词")
    parser.add_argument("-m", "--model", default=DEFAULT_MODEL, help=f"模型名称（默认 {DEFAULT_MODEL}）")
    parser.add_argument(
        "-s", "--size",
        default="1024x1024",
        choices=SUPPORTED_SIZES,
        help=f"输出尺寸（默认 1024x1024），支持：{', '.join(SUPPORTED_SIZES)}",
    )
    parser.add_argument(
        "-n", "--n",
        type=int,
        default=1,
        help="生成图片数量（默认 1）",
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="输出文件路径（默认用时间戳命名）",
    )
    parser.add_argument(
        "--region",
        default="auto",
        choices=["auto", "cn", "global"],
        help="区域：auto（有 CN 密钥优先用中国区）、cn、global。默认 auto",
    )
    args = parser.parse_args()

    cfg = agnes_api.resolve_region(args.region)

    print(f"区域：{cfg['name']}（{cfg['base_url']}）  模型：{args.model}  尺寸：{args.size}  数量：{args.n}")
    print(f"提示词：{args.prompt}")
    print("  正在请求 Agnes API…")

    payload = {
        "model": args.model,
        "prompt": args.prompt,
        "size": args.size,
        "n": args.n,
    }
    result = agnes_api._post("images/generations", payload, cfg["api_key"], cfg["base_url"])

    # OpenAI 兼容格式：result["data"] 为列表，每项含 url 或 b64_json
    items = result.get("data", [])
    if not items:
        raise RuntimeError(f"API 返回空结果：{result}")

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    saved = []

    for i, item in enumerate(items):
        if args.output and len(items) == 1:
            out = args.output
        elif args.output:
            base, ext = os.path.splitext(args.output)
            out = f"{base}_{i}{ext or '.png'}"
        else:
            out = f"agnes_img_{timestamp}_{i}.png" if len(items) > 1 else f"agnes_img_{timestamp}.png"

        url = item.get("url")
        b64 = item.get("b64_json")
        if url:
            print(f"  下载 [{i+1}/{len(items)}]：{url}")
            agnes_api.download(url, out, cfg["api_key"])
        elif b64:
            import base64
            from pathlib import Path
            Path(out).parent.mkdir(parents=True, exist_ok=True)
            Path(out).write_bytes(base64.b64decode(b64))
            print(f"  解码保存 [{i+1}/{len(items)}]：{out}")
        else:
            print(f"  ⚠️ 项目 [{i}] 无 url 也无 b64_json，跳过。raw={item}")
            continue

        print(f"  已保存：{out}")
        saved.append(out)

    print("\n完成，共生成：")
    for f in saved:
        print(f"  {f}")


if __name__ == "__main__":
    main()
